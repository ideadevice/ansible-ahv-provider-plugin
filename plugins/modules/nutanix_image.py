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
    image_uuid:
        description:
        - Image UUID
        - Specify image for update if there are multiple images with the same name
        type: str
    description:
        description:
        - Image description
        type: str
    cluster_name:
        description:
        - Cluster name for image placement in the cluster
        - Image is placed directly on all clusters by default
        type: str
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
                default: 100
            offset:
                description:
                - Offset
                type: int
                default: 0
    state:
        description:
        - Specify state of image
        - If C(state) is set to C(present) the image is created, nutanix supports multiple images with the same name
        - If C(state) is set to C(absent) and the image is present, all images with the specified name are removed
        type: str
        default: present
    force:
        description:
        - Used with C(present) or C(absent)
        - Creates of multiple images with same name when set to true with C(present)
        - Deletes all image with the same name when set to true with C(absent)
        type: bool
        default: False
    validate_certs:
        description:
        - Set value to C(False) to skip validation for self signed certificates
        - This is not recommended for production setup
        type: bool
        default: True
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
    image_description: "{{ Image description }}"
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
  retries: 15
  delay: 10

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
  retries: 15
  delay: 10

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
  retries: 15
  delay: 10
"""

RETURN = r"""
## TO-DO
"""

import json
import copy
from os.path import splitext
from urllib.parse import urlparse
from ansible.module_utils.basic import AnsibleModule, env_fallback
from ansible_collections.nutanix.nutanix.plugins.module_utils.nutanix_api_client import (
    NutanixApiClient,
    create_image,
    update_image,
    list_images,
    get_image,
    delete_image,
    list_clusters,
    task_poll)


CREATE_PAYLOAD = """{
  "spec": {
    "name": "IMAGE_NAME",
    "resources": {
      "image_type": "IMAGE_TYPE",
      "source_uri": "IMAGE_URL",
      "initial_placement_ref_list": [
        {
          "kind": "cluster",
          "uuid": "CLUSTER_UUID"
        }
      ],
      "source_options": {
        "allow_insecure_connection": true
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
    """Generate default payload for pagination support"""
    # FIQL filters are not supported in images and clusters API
    length = 100
    offset = 0
    payload = {"length": length, "offset": offset}

    if data and "length" in data:
        payload["length"] = data["length"]
    if data and "offset" in data:
        payload["offset"] = data["offset"]

    return payload


def generate_argument_spec(result):
    """Generate a dict with all user arguments"""
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
        description=dict(type="str"),
        cluster_name=dict(type="str"),
        data=dict(
            type="dict",
            options=dict(
                length=dict(type="int", default=100),
                offset=dict(type="int", default=0)
            )
        ),
        state=dict(type="str", default="present"),
        force=dict(type="bool", default=False),
        validate_certs=dict(type="bool", default=True),
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    # Return initial result dict for dry run
    if module.check_mode:
        module.exit_json(**result)

    return module


def check_if_image_is_present(module, client):
    """Check if an image is present in PC"""
    match_name, match_state, only_match_type = False, False, False
    image_uuid = None
    image_name = module.params.get("image_name")
    image_type = module.params.get("image_type")
    image_url = module.params.get("image_url")
    data = set_list_payload(module.params["data"])
    image_list_data = list_images(data, client)
    # Check for existing image in PC
    for entity in image_list_data["entities"]:
        if image_name == entity["status"]["name"]:
            match_name = True
            image_uuid = entity["metadata"]["uuid"]
            if image_type == entity["status"]["resources"]["image_type"] and image_url == entity["status"]["resources"]["source_uri"]:
                match_state = True
                break
            elif image_type == entity["status"]["resources"]["image_type"]:
                only_match_type = True
                break

    return match_name, match_state, only_match_type, image_uuid


def create_image_spec(module, client, result):
    """Generate spec for image creation"""
    cluster_validated = False
    image_name = module.params.get("image_name")
    image_url = module.params.get("image_url")
    image_type = module.params.get("image_type")
    image_description = module.params.get("description")
    cluster_name = module.params.get("cluster_name")
    create_payload = json.loads(CREATE_PAYLOAD)

    # Auto detect image_type based on url extension
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

    # Get cluster UUID
    if cluster_name:
        cluster_payload = set_list_payload(module.params.get("data"))
        cluster_data = list_clusters(cluster_payload, client)
        for entity in cluster_data["entities"]:
            if entity["status"]["name"] == cluster_name:
                # To-do: change cluster_name to a list for supporting multiple clusters
                create_payload["spec"]["resources"]["initial_placement_ref_list"][0]["uuid"] = entity["metadata"]["uuid"]
                cluster_validated = True
        if not cluster_validated:
            module.fail_json(
                "Could not find cluster with name {0}".format(cluster_name))
    else:
        del create_payload["spec"]["resources"]["initial_placement_ref_list"]

    create_payload["metadata"]["name"] = image_name
    create_payload["spec"]["name"] = image_name
    create_payload["spec"]["resources"]["image_type"] = image_type
    create_payload["spec"]["resources"]["source_uri"] = image_url
    if image_description:
        create_payload["spec"]["description"] = image_description

    return create_payload


def _create(module, client, result):
    """Create image"""
    image_count = 0
    image_uuid_list = []
    image_spec = create_image_spec(module, client, result)
    image_name = module.params.get("image_name")
    force_create = module.params.get("force")

    # Check if image is present
    match_name, match_state, only_match_type, image_uuid = check_if_image_is_present(
        module, client)
    if match_state:
        return result
    elif only_match_type:
        module.fail_json(
            "Image url does not match that of existing image")
    elif match_name:
        return _update(module, client, result, image_uuid)

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


def _update(module, client, result, image_uuid):
    """Update Image"""
    image_count = 0
    data = set_list_payload(module.params["data"])
    image_name = module.params.get("image_name")
    image_type = module.params.get("image_type")
    image_description = module.params.get("description")
    image_uuid_for_update = module.params.get("image_uuid")
    image_description = module.params.get("image_description")
    if image_uuid_for_update:
        image_uuid = image_uuid_for_update
    # Get image spec
    image_spec = get_image(image_uuid, client)

    # Update image spec
    del image_spec["status"]
    image_spec["spec"]["resources"]["image_type"] = image_type
    if image_description:
        image_spec["spec"]["description"] = image_description
    else:
        image_uuid = image_spec["metadata"]["uuid"]

    # Update image
    task_uuid = update_image(image_uuid, image_spec, client)

    # Poll task status for image update
    task_status = task_poll(task_uuid, client)
    if task_status:
        result["failed"] = True
        result["msg"] = task_status
        return result

    result["changed"] = True
    return result


def _delete(module, client, result):
    """Delete image(s)"""
    image_count = 0
    task_uuid_list, image_list, image_uuid_list = [], [], []
    data = set_list_payload(module.params["data"])
    force_delete = module.params.get("force")
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
            result["msg"] = "Could not find any image with name {0}".format(
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
    """Main function"""
    # Seed result dict
    result_init = dict(
        changed=False,
        ansible_facts=dict(),
    )

    # Generate arg spec and call function
    arg_spec = generate_argument_spec(result_init)

    # Create api client
    api_client = NutanixApiClient(arg_spec)
    if arg_spec.params.get("state") == "present":
        result = _create(arg_spec, api_client, result_init)
    elif arg_spec.params.get("state") == "absent":
        result = _delete(arg_spec, api_client, result_init)

    arg_spec.exit_json(**result)


if __name__ == "__main__":
    main()
