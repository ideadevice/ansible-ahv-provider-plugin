#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2021, Balu George <balu.george@nutanix.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r"""
---
module: nutanix_image_info

short_description: Basic imageinfo module which supports imagelist operation

version_added: "0.0.1"

description: Longer description for nutanix info module.

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
        type: str
        required: True
    pc_port:
        description:
        - PC port
        type: str
        default: 9440
    image_name:
        description:
        - Image name
        type: str
    validate_certs:
        description:
        - Set value to C(False) to skip validation for self signed certificates
        - This is not recommended for production setup
        type: bool
        default: True
    data:
        description:
        - Filter payload
        - 'Valid attributes are:'
        - ' - C(length) (int): length'
        - ' - C(offset) (str): offset'
        type: dict
        default: {"offset": 0, "length": 500}
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
- name: List images
  nutanix.nutanix.nutanix_image_info:
    pc_hostname: "{{ pc_hostname }}"
    pc_username: "{{ pc_username }}"
    pc_password: "{{ pc_password }}"
    pc_port: 9440
    validate_certs: False
  register: image_list
- debug:
    msg: "{{ image_list.images }}"

- name: Get image details
  nutanix.nutanix.nutanix_image_info:
    pc_hostname: "{{ pc_hostname }}"
    pc_username: "{{ pc_username }}"
    pc_password: "{{ pc_password }}"
    pc_port: 9440
    image_name: "{{ image_name }}"
    validate_certs: False
  register: image_details
- debug:
    msg: "{{ image_details.image }}"
"""

RETURN = r"""
## TO-DO
"""

from ansible.module_utils.basic import AnsibleModule, env_fallback
from ansible_collections.nutanix.nutanix.plugins.module_utils.nutanix_api_client import NutanixApiClient, list_entities


def set_list_payload(data):
    """Generate payload for pagination support"""
    payload = {}

    if data:
        if "length" in data:
            payload["length"] = data["length"]
        if "offset" in data:
            payload["offset"] = data["offset"]
        if "filter" in data:
            payload["filter"] = data["filter"]

    return payload


def get_image_list():
    """
    Get a list of all images
    """
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        pc_hostname=dict(type="str", required=True,
                         fallback=(env_fallback, ["PC_HOSTNAME"])),
        pc_username=dict(type="str", required=True,
                         fallback=(env_fallback, ["PC_USERNAME"])),
        pc_password=dict(type="str", required=True, no_log=True,
                         fallback=(env_fallback, ["PC_PASSWORD"])),
        pc_port=dict(type="str", default="9440"),
        image_name=dict(type="str"),
        data=dict(
            type="dict",
            default={"offset": 0, "length": 500},
            options=dict(
                length=dict(type="int"),
                offset=dict(type="int")
            )
        ),
        validate_certs=dict(type="bool", default=True, fallback=(
            env_fallback, ["VALIDATE_CERTS"])),
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    # Seed result dict
    result = dict(
        changed=False,
        ansible_facts={},
    )

    # Return initial result dict for dry run without execution
    if module.check_mode:
        module.exit_json(**result)

    # Create api client
    client = NutanixApiClient(module)

    # Get image list/details
    image_name = module.params.get("image_name")
    spec_list, status_list, image_list, meta_list = [], [], [], []
    data = set_list_payload(module.params['data'])
    image_list_data = list_entities('images', data, client)

    for entity in image_list_data["entities"]:
        # Identify image list operation from image spec request
        if image_name == entity["status"]["name"]:
            result["image"] = entity
            result["image_uuid"] = entity["metadata"]["uuid"]
            module.exit_json(**result)
        else:
            spec_list.append(entity["spec"])
            status_list.append(entity["status"])
            image_list.append(entity["status"]["name"])
            meta_list.append(entity["metadata"])

    if image_name and result.get("image") is None:
        module.fail_json("Could not find image: {0}".format(image_name))
    elif spec_list and status_list and image_list and meta_list:
        result["image_spec"] = spec_list
        result["image_status"] = status_list
        result["images"] = image_list
        result["meta_list"] = meta_list

    module.exit_json(**result)


def main():
    get_image_list()


if __name__ == '__main__':
    main()
