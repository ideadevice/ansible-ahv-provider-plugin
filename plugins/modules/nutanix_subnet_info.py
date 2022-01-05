#!/usr/bin/python

# Copyright: (c) 2021, Balu George <saratkumar.k@nutanix.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

DOCUMENTATION = r'''
---
module: nutanix_subnet_info

short_description: Basic subnet info module which supports subnet list operation

version_added: "0.0.1"

description: List Nutanix subnet and fetch subnet info

options:
    pc_hostname:
        description:
        - PC hostname or IP address; export PC_HOSTNAME=<PC_IP>
        type: str
        required: True
    pc_username:
        description:
        - PC username; export PC_USERNAME=<PC_USERNAME>
        type: str
        required: True
    pc_password:
        description:
        - PC password; export PC_PASSWORD=<PC_PASSWORD>
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
    - Sarat Kumar (@kumarsarath588)
'''

EXAMPLES = r'''
- name: List Subnet
  nutanix.nutanix.nutanix_subnet_info:
    pc_hostname: "{{ pc_hostname }}"
    pc_username: "{{ pc_username }}"
    pc_password: "{{ pc_password }}"
    pc_port: 9440
    validate_certs: False
    data:
        filter: "name=={{ subnet_name }}"
        offset: 0
        length: 100
  register: subnet_list
- debug:
    var: "{{ subnet_list.subnets }}"
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
    length = 100
    offset = 0
    filter = ''

    payload = {"filter": filter, "length": length, "offset": offset}

    if data:
        if data["length"]:
            payload["length"] = data["length"]
        if data["offset"]:
            payload["offset"] = data["offset"]
        if data["filter"]:
            payload["filter"] = data["filter"]
        if data["sort_attribute"]:
            payload["sort_attribute"] = data["sort_attribute"]
        if data["sort_order"]:
            payload["sort_order"] = data["sort_order"]

    return payload


def get_subnet_list():

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
                sort_order=dict(
                    type='str',
                    choices=[
                        "ASCENDING",
                        "DESCENDING"
                    ]
                )
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
        subnet_spec={},
        subnet_status={},
        subnets={},
        subnet_meta={}
    )

    # return initial result dict for dry run without execution
    if module.check_mode:
        module.exit_json(**result)

    # Instantiate api client
    client = NutanixApiClient(module)

    # List Subnets
    spec_list, status_list, subnet_name_list, meta_list = [], [], [], []
    data = set_list_payload(module.params['data'])
    length = data["length"]
    offset = data["offset"]
    total_matches = 99999

    while offset < total_matches:
        data["offset"] = offset
        subnets_list = list_entities('subnets', data, client)
        for entity in subnets_list["entities"]:
            spec_list.append(entity["spec"])
            status_list.append(entity["status"])
            subnet_name_list.append(entity["status"]["name"])
            meta_list.append(entity["metadata"])

        total_matches = subnets_list["metadata"]["total_matches"]
        offset += length

    result["subnet_spec"] = spec_list
    result["subnet_status"] = status_list
    result["subnets"] = subnet_name_list
    result["subnet_meta"] = meta_list

    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(**result)


def main():
    get_subnet_list()


if __name__ == '__main__':
    main()
