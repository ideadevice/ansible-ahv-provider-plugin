#!/usr/bin/python

# Copyright: (c) 2021, Balu George <balu.george@nutanix.com>
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
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
        required: True
        type: str
    pc_port:
        description:
        - PC port
        type: str
        default: 9440
        required: False
author:
    - Balu George (@balugeorge)
'''

EXAMPLES = r'''
- name: List images
  nutanix.nutanix.nutanix_image_info:
    pc_hostname: {{ pc_hostname }}
    pc_username: {{ pc_username }}
    pc_password: {{ pc_password }}
    pc_port: 9440
    validate_certs: False
  register: result
- debug:
    var: {{ result.image }}
'''

RETURN = r'''
## TO-DO
'''

import json
from ansible.module_utils.basic import env_fallback
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.nutanix.nutanix.plugins.module_utils.nutanix_api_client import NutanixApiClient


def get_image_list():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        pc_hostname=dict(type='str', required=True, fallback=(env_fallback, ["PC_HOSTNAME"])),
        pc_username=dict(type='str', required=True, fallback=(env_fallback, ["PC_USERNAME"])),
        pc_password=dict(type='str', required=True, no_log=True, fallback=(env_fallback, ["PC_PASSWORD"])),
        pc_port=dict(default="9440", type='str', required=False),
        image_name=dict(type='str', required=False),
        data=dict(default="{}", type='str', required=False),
        validate_certs=dict(default=True, type='bool', required=False),
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    # Seed result dict
    result = dict(
        changed=False,
        ansible_facts=dict(),
    )

    # return initial result dict for dry run without execution
    if module.check_mode:
        module.exit_json(**result)

    # Instantiate api client
    client = NutanixApiClient(module)

    # Get Image list
    data = module.params['data']
    image_list_response = client.request(api_endpoint="v3/images/list", method="POST", data=data)

    image_name = module.params.get("image_name")
    spec_list, status_list, image_list = [], [], []
    for entity in json.loads(image_list_response.content)["entities"]:
        if image_name == entity["status"]["name"]:
            result["image"] = entity
            result["image_uuid"] = entity["metadata"]["uuid"]
            break
        else:
            spec_list.append(entity["spec"])
            status_list.append(entity["status"])
            image_list.append(entity["status"]["name"])

    if spec_list and status_list and image_list:
        result["image_spec"] = spec_list
        result["image_status"] = status_list
        result["images"] = image_list

    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(**result)


def main():
    get_image_list()

if __name__ == '__main__':
    main()
