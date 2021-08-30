#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2021, Balu George <balu.george@nutanix.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

DOCUMENTATION = r'''
---
module: nutanix_vm_info

short_description: Basic vm info module which supports vm list operation

version_added: "0.0.1"

description: List Nutanix vms and fetch vm info

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
    validate_certs:
        description:
        - Set value to C(False) to skip validation for self signed certificates
        - This is not recommended for production setup
        type: bool
        default: True
    data:
        description:
        - List filter payload.
        - 'Valid attributes are:'
        - ' - C(filter) (str): filter string'
        - ' - C(length) (int): length'
        - ' - C(offset) (str): offset'
        - ' - C(sort_attribute) (str): sort attribute'
        - ' - C(sort_order) (str): sort order'
        - '   - Accepted values:'
        - '     - ASCENDING'
        - '     - DESCENDING'
        type: dict
        required: False
        suboptions:
            filter:
                description:
                - Filter
                type: str
            length:
                description:
                - Length
                type: int
            offset:
                description:
                - Offset
                type: int
            sort_attribute:
                description:
                - Sort Attribute, specify ASCENDING or DESCENDING
                type: str
            sort_order:
                description:
                - Sort Order
                type: str

author:
    - Balu George (@balugeorge)
'''

EXAMPLES = r'''
- name: List vms
  nutanix.nutanix.nutanix_vm_info:
    pc_hostname: "{{ pc_hostname }}"
    pc_username: "{{ pc_username }}"
    pc_password: "{{ pc_password }}"
    pc_port: 9440
    validate_certs: False
    data:
        filter: "vm_name=={{ vm_name }}"
        offset: 0
        length: 100
  register: result
- debug:
    var: "{{ result.vms }}"

'''

RETURN = r'''
## TO-DO
'''

from ansible.module_utils.basic import AnsibleModule, env_fallback
from ansible_collections.nutanix.nutanix.plugins.module_utils.nutanix_api_client import (
    NutanixApiClient,
    list_vms
)


def set_list_payload(data):
    length = 100
    offset = 0
    filter = ''

    payload = {"filter": filter, "length": length, "offset": offset}

    if data and "length" in data:
        payload["length"] = data["length"]
    if data and "offset" in data:
        payload["offset"] = data["offset"]
    if data and "filter" in data:
        payload["filter"] = data["filter"]
    if data and "sort_attribute" in data:
        payload["sort_attribute"] = data["sort_attribute"]
    if data and "sort_order" in data:
        payload["sort_order"] = data["sort_order"]

    return payload


def get_vm_list():

    module_args = dict(
        pc_hostname=dict(type='str', required=True,
                         fallback=(env_fallback, ["PC_HOSTNAME"])),
        pc_username=dict(type='str', required=True,
                         fallback=(env_fallback, ["PC_USERNAME"])),
        pc_password=dict(type='str', required=True, no_log=True,
                         fallback=(env_fallback, ["PC_PASSWORD"])),
        pc_port=dict(default="9440", type='str', required=False),
        data=dict(
            type='dict',
            required=False,
            options=dict(
                filter=dict(type='str'),
                length=dict(type='int'),
                offset=dict(type='int'),
                sort_attribute=dict(type='str'),
                sort_order=dict(type='str')
            )
        ),
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
        vms_spec={},
        vm_status={},
        vms={},
        meta={}
    )

    # Return initial result dict for dry run without execution
    if module.check_mode:
        module.exit_json(**result)

    # Create api client
    client = NutanixApiClient(module)

    # List VMs
    spec_list, status_list, vm_list, meta_list = [], [], [], []
    data = set_list_payload(module.params['data'])
    length = data["length"]
    offset = data["offset"]
    total_matches = 99999

    while offset < total_matches:
        data["offset"] = offset
        vms_list = list_vms(data, client)
        for entity in vms_list["entities"]:
            spec_list.append(entity["spec"])
            status_list.append(entity["status"])
            vm_list.append(entity["status"]["name"])
            meta_list.append(entity["metadata"])

        total_matches = vms_list["metadata"]["total_matches"]
        offset += length

    result["vms_spec"] = spec_list
    result["vm_status"] = status_list
    result["vms"] = vm_list
    result["meta"] = meta_list

    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(**result)


def main():
    get_vm_list()


if __name__ == '__main__':
    main()
