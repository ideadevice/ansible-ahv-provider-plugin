#!/usr/bin/python

# Copyright: (c) 2021, Balu George <balu.george@nutanix.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: nutanix_images

short_description: Images module which supports image crud operations

version_added: "0.0.1"

description: Create, update and delete Nutanix images

options:
    pc_hostname:
        description:
        - PC hostname or IP address
        type: str
        required: True
    pc_username:
        description:
        - PC username
        type: str
        required: True
    pc_password:
        description:
        - PC password
        required: True
        type: str
    pc_port:
        description:
        - PC port
        type: str
        default: 9440
        required: False
    images:
        description:
        - Image details
        type: list
        elements: dict
        suboptions:
            image_name:
                description:
                - Name of the image
                type: str
            image_type:
                description:
                - Image type, specify ISO_IMAGE or DISK_IMAGE
                type: str
            source_uri:
                description:
                - Image url
                type: str
        required: True
    validate_certs:
        description:
        - Set value to C(False) to skip validation for self signed certificates
        - This is not recommended for production setup
        type: bool
        default: True
    state:
        description:
        - Specify state of image
        - If C(state) is set to C(present) the image is created, nutanix supports multiple images with the same name
        - If C(state) is set to C(absent) and the image is present, all images with the specified name are removed
        type: str
        default: present
author:
    - Balu George (@balugeorge)
'''

EXAMPLES = r'''
- name: List images
  nutanix.nutanix.nutanix_images:
    pc_hostname: "{{ pc_hostname }}"
    pc_username: "{{ pc_username }}"
    pc_password: "{{ pc_password }}"
    pc_port: 9440
    images:
    - image_name: "{{ image_name }}"
      image_type: "{{ image_type }}"
      source_uri: "{{ source_uri }}"
    validate_certs: False
    state: present
  register: result
  async: 600
  poll: 0
- name: Wait for image creation
  async_status:
    jid: "{{ result.ansible_job_id }}"
  register: job_result
  until: job_result.finished
  retries: 30
  delay: 5
'''

RETURN = r'''
## TO-DO
'''

import json
import copy
import time
from ansible.module_utils.basic import env_fallback
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.nutanix.nutanix.plugins.module_utils.nutanix_api_client import NutanixApiClient


def generate_argument_spec(result):
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        pc_hostname=dict(type='str', required=True,
                         fallback=(env_fallback, ["PC_HOSTNAME"])),
        pc_username=dict(type='str', required=True,
                         fallback=(env_fallback, ["PC_USERNAME"])),
        pc_password=dict(type='str', required=True, no_log=True,
                         fallback=(env_fallback, ["PC_PASSWORD"])),
        pc_port=dict(default="9440", type='str', required=False),
        images=dict(
            type='list',
            required=True,
            elements='dict',
            options=dict(
                image_name=dict(type='str'),
                image_type=dict(type='str'),
                source_uri=dict(type='str')
            )
        ),
        state=dict(default='present', type='str'),
        validate_certs=dict(default=True, type='bool', required=False),
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    # return initial result dict for dry run without execution
    if module.check_mode:
        module.exit_json(**result)

    return module


def create_images(module, client, result):
    batch_spec = {
        "action_on_failure": "CONTINUE",
        "execution_order": "NON_SEQUENTIAL",
        "api_request_list":
        [],
        "api_version": "3.0"
    }

    image_spec = {
        "operation": "POST",
        "path_and_params": "/api/nutanix/v3/images",
        "body":
            {
                "spec":
                {
                    "name": "",
                    "resources":
                    {
                        "image_type": "",
                        "source_uri": ""
                    }
                },
                "metadata":
                {
                    "kind": "image"
                },
                "api_version": "3.1.0"
            }
    }

    images = module.params.get("images")
    task_uuid_list, image_list, created_image_list = [], [], []

    for image in images:
        api_image_spec = copy.deepcopy(image_spec)
        image_name = image.get("image_name")
        image_type = image.get("image_type")
        source_uri = image.get("source_uri")
        if image_name and image_type and source_uri:
            api_image_spec["body"]["spec"]["name"] = image_name
            api_image_spec["body"]["spec"]["resources"]["image_type"] = image_type
            api_image_spec["body"]["spec"]["resources"]["source_uri"] = source_uri
        batch_spec["api_request_list"].append(api_image_spec)

    # Create Images
    image_create_resp = client.request(
        api_endpoint="v3/batch", method="POST", data=json.dumps(batch_spec))

    result["changed"] = True
    result["msg"] = []

    for resp in image_create_resp.json()["api_response_list"]:
        if resp["status"] == '202':
            image_list.append(resp["api_response"]["spec"]["name"])
            task_uuid_list.append(
                resp["api_response"]["status"]["execution_context"]["task_uuid"])
        else:
            result["msg"].append(resp)
            result["failed"] = True

    if task_uuid_list:
        for task_uuid in task_uuid_list:
            tasks_state = None
            while tasks_state is None:
                task_resp = client.request(api_endpoint="v3/tasks/{0}".format(task_uuid), method="GET", data=None)
                if task_resp.json()["status"] == "SUCCEEDED":
                    created_image_list.append(
                        image_list[task_uuid_list.index(task_uuid)])
                    tasks_state = "SUCCEEDED"
                elif task_resp.json()["status"] == "FAILED":
                    result["failed"] = True
                    result["msg"].append(task_resp.json()["error_detail"])
                    tasks_state = "FAILED"
                else:
                    time.sleep(5)
        if created_image_list:
            result["msg"].append("Created image(s): {0}".format(created_image_list))

    return result


def list_images(client):
    return client.request(api_endpoint="v3/images/list", method="POST", data='{"offset": 0, "length": 100}')


def update_image(module, client, result):
    image_list_response = list_images(client)

    images = module.params.get("images")
    task_uuid_list, image_list, updated_image_list, image_uuid_list = [], [], [], []
    result["msg"] = []
    image_count = 0

    for image in images:
        update = False
        image_name = image.get("image_name")
        updated_image_name = image.get("updated_image_name")
        image_list.append(image_name)
        if image_name and updated_image_name:
            for entity in image_list_response.json()["entities"]:
                if image_name == entity["status"]["name"] and image_count <= 1:
                    image_uuid = entity["metadata"]["uuid"]
                    # image_uuid_list.append(image_uuid)
                    image_update_spec = entity
                    del image_update_spec["status"]
                    # image_update_spec["metadata"]["spec_version"] += 1
                    image_update_spec["spec"]["name"] = updated_image_name
                    update = True
                    image_count += 1
                elif image_count > 1:
                    result["msg"] = "Found multiple images with name {0}, specify image_uuid".format(image_name)
                    result["failed"] = True
                    update = False
                    return result
            if image_count == 0:
                result["msg"] = "Did not find any image with name {0}".format(image_name)
                result["failed"] = True
                return result
            if not image_uuid_list:
                result["msg"] = "Could not find UUID for image(s) {0}".format(image_list)
                result["failed"] = True
                return result
        if update:
            # Update image
            image_update_resp = client.request(api_endpoint="v3/images/{0}".format(image_uuid), method="PUT", data=json.dumps(image_update_spec))
            del image_update_spec
            if image_update_resp.ok:
                task_uuid_list.append(image_update_resp.json()[
                                      "status"]["execution_context"]["task_uuid"])
            else:
                result["msg"] = image_update_resp.json()
                result["failed"] = True

    if task_uuid_list:
        for task_uuid in task_uuid_list:
            tasks_state = None
            while tasks_state is None:
                task_resp = client.request(api_endpoint="v3/tasks/{0}".format(task_uuid), method="GET", data=None)
                if task_resp.json()["status"] == "SUCCEEDED":
                    tasks_state = "SUCCEEDED"
                elif task_resp.json()["status"] == "FAILED":
                    result["failed"] = True
                    result["msg"] = task_resp.json()["error_detail"]
                    tasks_state = "FAILED"
                else:
                    time.sleep(5)

    return result


def delete_images(module, client, result):
    batch_spec = {
        "action_on_failure": "CONTINUE",
        "execution_order": "NON_SEQUENTIAL",
        "api_request_list":
        [],
        "api_version": "3.0"
    }

    image_spec = {
        "operation": "DELETE",
        "path_and_params": "/api/nutanix/v3/images/"
    }

    # Get image list of filtering out image uuid
    image_list_response = list_images(client)
    images = module.params.get("images")

    image_uuid_list, image_list = [], []
    for image in images:
        image_name = image.get("image_name")
        image_list.append(image_name)
        if image_name:
            for entity in image_list_response.json()["entities"]:
                api_image_spec = copy.deepcopy(image_spec)
                if image_name == entity["status"]["name"]:
                    image_uuid = entity["metadata"]["uuid"]
                    image_uuid_list.append(image_uuid)
                    api_image_spec["path_and_params"] += image_uuid
                    batch_spec["api_request_list"].append(api_image_spec)
            if not image_uuid_list:
                result["msg"] = "Could not find UUID for image(s) {0}".format(image_list)
                result["failed"] = True

    image_delete_resp = client.request(
        api_endpoint="v3/batch", method="DELETE", data=json.dumps(batch_spec))
    result["changed"] = True

    task_uuid_list = []
    for resp in image_delete_resp.json()["api_response_list"]:
        if resp["status"] == '202':
            task_uuid_list.append(
                resp["api_response"]["status"]["execution_context"]["task_uuid"])
        else:
            result["msg"] = resp
            result["failed"] = True

    if task_uuid_list:
        for task_uuid in task_uuid_list:
            tasks_state = None
            while tasks_state is None:
                task_resp = client.request(api_endpoint="v3/tasks/{0}".format(task_uuid), method="GET", data=None)
                if task_resp.json()["status"] == "SUCCEEDED":
                    tasks_state = "SUCCEEDED"
                elif task_resp.json()["status"] == "FAILED":
                    result["failed"] = True
                    result["msg"] = task_resp.json()["error_detail"]
                    tasks_state = "FAILED"
                time.sleep(5)

    return result


def main():
    # Seed result dict
    result_init = dict(
        changed=False,
        ansible_facts=dict(),
    )

    # Generate arg spec and call function
    arg_spec = generate_argument_spec(result_init)

    # Instantiate api client
    api_client = NutanixApiClient(arg_spec)
    if arg_spec.params["state"] == "present":
        result = create_images(arg_spec, api_client, result_init)
    elif arg_spec.params["state"] == "update":
        result = update_image(arg_spec, api_client, result_init)
    elif arg_spec.params["state"] == "absent":
        result = delete_images(arg_spec, api_client, result_init)

    arg_spec.exit_json(**result)


if __name__ == '__main__':
    main()
