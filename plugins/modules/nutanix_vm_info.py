#!/usr/bin/python

# Copyright: (c) 2021, Balu George <balu.george@nutanix.com>
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: nutanix_vm_info

short_description: Basic vm info module which supports vm list operation

version_added: "0.0.1"

description: This is my longer description explaining my test info module.

options:
    hostname:
        description:
        - PC hostname or IP address
        type: str
        required: True
    username:
        description:
        - PC username
        type: str
        required: True
    password:
        description:
        - PC password
        required: True
        type: str
    port:
        description:
        - PC port
        type: str
        default: 9440
        required: False
author:
    - Balu George (@balugeorge)
'''

EXAMPLES = r'''
# Pass in a message
- name: Test with a message
  nutanix.nutanix.my_vm_info:
    hostname: {{ pc_hostname }}
    username: {{ pc_username }}
    password: {{ pc_password }}
    port: 9440
    data: {}
    validate_certs: False
  register: result
- debug:
    var: result.entities
'''

RETURN = r'''
# Todo
'''

import json
from ansible.module_utils.basic import env_fallback
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.nutanix.nutanix.plugins.module_utils.nutanix_api_client import NutanixApiClient, NutanixApiError


def get_vm_list():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        pc_hostname=dict(type='str', required=True, fallback=(env_fallback, ["PC_HOSTNAME"])),
        pc_username=dict(type='str', required=True, fallback=(env_fallback, ["PC_USERNAME"])),
        pc_password=dict(type='str', required=True, no_log=True, fallback=(env_fallback, ["PC_PASSWORD"])),
        pc_port=dict(default="9440", type='str', required=False),
        data=dict(default="{}", type='str', required=False),
        validate_certs=dict(default=True, type='bool', required=False),
    )

    # the AnsibleModule object will be our abstraction working with Ansible
    # this includes instantiation, a couple of common attr would be the
    # args/params passed to the execution, as well as if the module
    # supports check mode
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    # Create an empty result dict
    result = {}

    # if the user is working with this module in only check mode we do not
    # want to make any changes to the environment, just return the current
    # state with no modifications
    if module.check_mode:
        module.exit_json(**result)

    # Instantiate api client
    client = NutanixApiClient(**module.params)

    # List VMs
    data = module.params['data']
    vm_list_response = client.request(api_endpoint="v3/vms/list", method="POST", data=data)
    spec_list, status_list, vm_list, meta_list = [], [], [], []
    for entity in json.loads(vm_list_response.content)["entities"]:
        spec_list.append(entity["spec"])
        status_list.append(entity["status"])
        vm_list.append(entity["status"]["name"])
        meta_list.append(entity["metadata"])
    result["vms_spec"] = spec_list
    result["vm_status"] = status_list
    result["vms"] = vm_list
    result["meta"] = meta_list

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(**result)


def main():
    get_vm_list()


if __name__ == '__main__':
    main()
