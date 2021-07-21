#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2021, Balu George <balu.george@nutanix.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r"""
---
module: nutanix_image

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
    image_name:
        description:
        - Image name
        type: str
        required: True
    image_type:
        description:
        - Image type, ISO_IMAGE or DISK_IMAGE
        - Auto detetected based on image extension
        type: str
    image_url:
        description:
        - Image url
        type: str
        required: True
    force:
        description:
        - Used with C(present) or C(absent)
        - Creates of multiple images with same name when set to true with C(present)
        - Deletes all image with the same name when set to true with C(absent)
        type: bool
        default: False
    image_uuid:
        description:
        - Image UUID
        - Specify image for update if there are multiple images with the same name
        type: str
    new_image_name:
        description:
        - New image name for image update
        type: str
    new_image_type:
        description:
        - New image name for image update
        - Accepts ISO_IMAGE or DISK_IMAGE
        type: str
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
    data:
        description:
        - Filter payload
        - 'Valid attributes are:'
        - ' - C(length) (int): length'
        - ' - C(offset) (str): offset'
        type: dict
        suboptions:
            length:
                description:
                - Length
                type: int
            offset:
                description:
                - Offset
                type: int
author:
    - Balu George (@balugeorge)
"""

EXAMPLES = r"""
- name: Create image
  nutanix.nutanix.nutanix_image:
    pc_hostname: "{{ pc_hostname }}"
    pc_username: "{{ pc_username }}"
    pc_password: "{{ pc_password }}"
    pc_port: 9440
    image_name: "{{ image_name }}"
    image_type: "{{ image_type }}"
    image_url: "{{ image_url }}"
    state: present
  delegate_to: localhost
  register: create_image
  async: 600
  poll: 0
- name: Wait for image creation
  async_status:
    jid: "{{ create_image.ansible_job_id }}"
  register: job_result
  until: job_result.finished
  retries: 30
  delay: 5

- name: Delete image
  nutanix.nutanix.nutanix_image:
    pc_hostname: "{{ pc_hostname }}"
    pc_username: "{{ pc_username }}"
    pc_password: "{{ pc_password }}"
    pc_port: 9440
    image_name: "{{ image_name }}"
    state: absent
  delegate_to: localhost
  register: delete_image
  async: 600
  poll: 0
- name: Wait for image deletion
  async_status:
    jid: "{{ delete_image.ansible_job_id }}"
  register: job_result
  until: job_result.finished
  retries: 30
  delay: 5

- name: Update image
  nutanix.nutanix.nutanix_image:
    pc_hostname: "{{ pc_hostname }}"
    pc_username: "{{ pc_username }}"
    pc_password: "{{ pc_password }}"
    pc_port: 9440
    image_name: "{{ image_name }}"
    new_image_name: "{{ new_image_name }}"
    new_image_type: "{{ new_image_type }}"
    state: present
  delegate_to: localhost
  register: update_image
  async: 600
  poll: 0
- name: Wait for image update
  async_status:
    jid: "{{ update_image.ansible_job_id }}"
  register: job_result
  until: job_result.finished
  retries: 30
  delay: 5
"""

RETURN = r"""
## TO-DO
"""

import json
import copy
import time
from os.path import splitext
from urllib.parse import urlparse
from ansible.module_utils.basic import AnsibleModule, env_fallback
from ansible_collections.nutanix.nutanix.plugins.module_utils.nutanix_api_client import (
    NutanixApiClient,
    create_image,
    update_image,
    list_images,
    delete_image,
    task_poll)


CREATE_PAYLOAD = """{
  "spec": {
    "name": "IMAGE_NAME",
    "resources": {
      "image_type": "IMAGE_TYPE",
      "source_uri": "IMAGE_URL",
      "source_options": {
        "allow_insecure_connection": false
      }
    },
    "description": ""
  },
  "api_version": "3.1.0",
  "metadata": {
    "kind": "image",
    "name": "IMAGE_NAME"
  }
}"""


def set_list_payload(data):
    length = 100
    offset = 0
    payload = {"length": length, "offset": offset}

    if data and "length" in data:
        payload["length"] = data["length"]
    if data and "offset" in data:
        payload["offset"] = data["offset"]

    return payload


def generate_argument_spec(result):
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        pc_hostname=dict(type="str", required=True,
                         fallback=(env_fallback, ["PC_HOSTNAME"])),
        pc_username=dict(type="str", required=True,
                         fallback=(env_fallback, ["PC_USERNAME"])),
        pc_password=dict(type="str", required=True, no_log=True,
                         fallback=(env_fallback, ["PC_PASSWORD"])),
        pc_port=dict(type="str", default="9440"),
        image_name=dict(type="str", required=True),
        image_type=dict(type="str"),
        image_url=dict(type="str", required=True),
        image_uuid=dict(type="str"),
        state=dict(type="str", default="present"),
        force=dict(type="bool", default=False),
        new_image_name=dict(type="str"),
        new_image_type=dict(type="str"),
        data=dict(
            type="dict",
            required=False,
            options=dict(
                length=dict(type="int"),
                offset=dict(type="int")
            )
        ),
        validate_certs=dict(type="bool", default=True),
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    # return initial result dict for dry run
    if module.check_mode:
        module.exit_json(**result)

    return module


def create_image_spec(module):

    image_name = module.params.get("image_name")
    image_url = module.params.get("image_url")
    image_type = module.params.get("image_type")
    if not image_type:
        parsed_url = urlparse(image_url)
        path, extension = splitext(parsed_url.path)
        if extension == ".iso":
            image_type = "ISO_IMAGE"
        elif extension == ".qcow2":
            image_type = "DISK_IMAGE"
        else:
            module.fail_json(
                "Unable to identify image_type, specify the value manually")

    create_payload = json.loads(CREATE_PAYLOAD)

    create_payload["metadata"]["name"] = image_name
    create_payload["spec"]["name"] = image_name
    create_payload["spec"]["resources"]["image_type"] = image_type
    create_payload["spec"]["resources"]["source_uri"] = image_url

    return create_payload


def _create(module, client, result):
    image_count = 0
    image_spec = create_image_spec(module)
    image_uuid_list = []
    data = set_list_payload(module.params["data"])
    image_name = module.params.get("image_name")
    force_create = module.params.get("force")

    if image_name:
        image_list_data = list_images(data, client)
        for entity in image_list_data["entities"]:
            if image_name == entity["status"]["name"]:
                image_uuid = entity["metadata"]["uuid"]
                image_uuid_list.append(image_uuid)
                image_update_spec = entity
                image_count += 1
            if image_count > 0 and not force_create:
                result["msg"] = "Found existing images with name {0}, use force option to create new image".format(
                    image_name)
                result["failed"] = True
                return result

    # Create Image
    task_uuid, image_uuid = create_image(image_spec, client)

    task_status = task_poll(task_uuid, client)
    if task_status:
        result["failed"] = True
        result["msg"] = task_status
        return result

    result["image_uuid"] = image_uuid
    result["changed"] = True
    return result


def _update(module, client, result):
    image_count = 0
    task_uuid_list, image_list, image_uuid_list = [], [], []
    data = set_list_payload(module.params["data"])
    image_name = module.params.get("image_name")
    new_image_name = module.params.get("new_image_name")
    new_image_type = module.params.get("new_image_type")
    image_uuid_for_update = module.params.get("image_uuid")

    if image_name and (new_image_name or new_image_type):
        image_list_data = list_images(data, client)
        for entity in image_list_data["entities"]:
            if image_name == entity["status"]["name"]:
                image_uuid = entity["metadata"]["uuid"]
                image_uuid_list.append(image_uuid)
                image_update_spec = entity
                # Remove status and update image name
                del image_update_spec["status"]
                if new_image_name:
                    image_update_spec["spec"]["name"] = new_image_name
                if new_image_type:
                    image_update_spec["spec"]["resources"]["image_type"] = new_image_type
                update = True
                image_count += 1
            elif image_count > 1 and not image_uuid_for_update:
                result["msg"] = "Found multiple images with name {0}, specify image_uuid".format(
                    image_name)
                result["failed"] = True
                return result
        if image_count > 1 and image_uuid_for_update:
            image_uuid = image_uuid_for_update
        elif image_count == 0:
            result["msg"] = "Could not find any image with name {0}".format(
                image_name)
            result["failed"] = True
            return result
        if not image_uuid_list:
            result["msg"] = "Could not find UUID for image {0}".format(
                image_name)
            result["failed"] = True
            return result
        if update:
            task_uuid = update_image(image_uuid, image_update_spec, client)

    # Check task status for image update
    task_status = task_poll(task_uuid, client)
    if task_status:
        result["failed"] = True
        result["msg"] = task_status
        return result

    result["changed"] = True
    return result


def _delete(module, client, result):
    data = set_list_payload(module.params["data"])
    force_delete = module.params.get("force")

    task_uuid_list, image_list, image_uuid_list = [], [], []
    image_count = 0

    image_name = module.params.get("image_name")
    if image_name:
        image_list_data = list_images(data, client)
        for entity in image_list_data["entities"]:
            if image_name == entity["status"]["name"]:
                image_uuid = entity["metadata"]["uuid"]
                image_uuid_list.append(image_uuid)
                image_update_spec = entity
                image_count += 1
            if image_count > 1 and not force_delete:
                result["msg"] = "Found multiple images with name {0}, specify image_uuid or use force option to remove all images".format(
                    image_name)
                result["failed"] = True
                return result
        if image_count == 0:
            result["msg"] = "Did not find any image with name {0}".format(
                image_name)
            result["failed"] = True
            return result
        if not image_uuid_list:
            result["msg"] = "Could not find UUID for image {0}".format(
                image_name)
            result["failed"] = True
            return result
        # Delete all images with duplicate names when force is set to true
        if image_count > 1 and force_delete:
            for uuid in image_uuid_list:
                task_uuid = delete_image(uuid, client)
                task_uuid_list.append(task_uuid)
        elif image_count == 1:
            result["image_count"] = 1
            result["changed"] = True
            task_uuid = delete_image(image_uuid, client)
            # Check task status for removal of a single image
            if task_uuid:
                task_status = task_poll(task_uuid, client)
                if task_status:
                    result["failed"] = True
                    result["msg"] = task_status
                    return result
    else:
        result["failed"] = True
        return result

    # Check status of all deletion tasks for removal of multiple images with duplicate names
    if task_uuid_list:
        result["msg"] = []
        for tuuid in task_uuid_list:
            task_status = task_poll(tuuid, client)
            if task_status:
                result["failed"] = True
                result["msg"].append(task_status)
        return result

    return result


def main():
    # Seed result dict
    result_init = dict(
        changed=False,
        ansible_facts=dict(),
    )

    # Generate arg spec and call function
    arg_spec = generate_argument_spec(result_init)
    nimage_name = arg_spec.params.get("new_image_name")
    nimage_type = arg_spec.params.get("new_image_type")

    # Instantiate api client
    api_client = NutanixApiClient(arg_spec)
    if arg_spec.params.get("state") == "present" and (nimage_name or nimage_type):
        result = _update(arg_spec, api_client, result_init)
    elif arg_spec.params.get("state") == "present":
        result = _create(arg_spec, api_client, result_init)
    elif arg_spec.params.get("state") == "absent":
        result = _delete(arg_spec, api_client, result_init)

    arg_spec.exit_json(**result)


if __name__ == "__main__":
    main()
