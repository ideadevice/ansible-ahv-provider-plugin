#!/usr/bin/python

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
    vm_name:
        description:
        - VM Name
        - Takes precedence over filter value under data
        type: str
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
        default: {"offset": 0, "length": 500, "sort_attribute": "", "sort_order": "ASCENDING"}
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
                - Sort Attribute to sort with. Passed along with sort_order.
                type: str
            sort_order:
                description:
                - Sort Order, specify ASCENDING or DESCENDING. Passed along with sort_attribute.
                type: str
                choices:
                - ASCENDING
                - DESCENDING

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

from ansible.module_utils.basic import env_fallback
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.nutanix.nutanix.plugins.module_utils.nutanix_api_client import (
    NutanixApiClient,
    list_entities
)


def set_list_payload(data):
    """
    This routine helps to set payload for list API call
    Args:
        data(obj): data object
    Returns:
        payload(dict): will have post payload dict
    """
    payload = {}

    if data:
        if "length" in data:
            payload["length"] = data["length"]
        if "offset" in data:
            payload["offset"] = data["offset"]
        if "filter" in data:
            payload["filter"] = data["filter"]
        if "sort_attribute" in data:
            payload["sort_attribute"] = data["sort_attribute"]
        if "sort_order" in data:
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
        pc_port=dict(default="9440", type='str'),
        vm_name=dict(type="str"),
        data=dict(
            type='dict',
            default={"offset": 0, "length": 500,
                     "sort_attribute": "", "sort_order": "ASCENDING"},
            options=dict(
                filter=dict(type='str'),
                length=dict(type='int'),
                offset=dict(type='int'),
                sort_attribute=dict(type='str'),
                sort_order=dict(
                    type='str',
                    choices=[
                        "ASCENDING",
                        "DESCENDING"
                    ]
                )
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
    vm_name = module.params.get("vm_name")
    spec_list, status_list, vm_name_list, meta_list = [], [], [], []
    data = set_list_payload(module.params['data'])
    result["data"] = data
    length = data["length"]
    offset = data["offset"]
    total_matches = 99999
    if vm_name:
        data["filter"] = "vm_name=={0}".format(vm_name)

    while offset < total_matches:
        data["offset"] = offset
        vms_list = list_entities('vms', data, client)
        for entity in vms_list["entities"]:
            spec_list.append(entity["spec"])
            status_list.append(entity["status"])
            vm_name_list.append(entity["status"]["name"])
            meta_list.append(entity["metadata"])

        total_matches = vms_list["metadata"]["total_matches"]
        offset += length

    if spec_list:
        result["vms_spec"] = spec_list
        result["vm_status"] = status_list
        result["vms"] = vm_name_list
        result["meta"] = meta_list
    else:
        module.fail_json("Could not find VM: {0}".format(vm_name))

    module.exit_json(**result)


def main():
    get_vm_list()


if __name__ == '__main__':
    main()
