#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2021, Sarat Kumar <saratkumar.k@nutanix.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

DOCUMENTATION = r'''
---
module: nutanix_subnet

short_description: Subnet module which suports Subnet CRUD operations

version_added: "0.0.1"

description: Create, Update, Delete Subnets

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
    state:
        description:
        - Specify state of Virtual Machine
        - If C(state) is set to C(present) the Subnet is created, if Subnet with same name already exists it will updated the Subnet.
        - If C(state) is set to C(absent) and the Subnet exists in the cluster, Subnet with specified name is removed.
        choices:
        - present
        - absent
        type: str
        default: present
    dry_run:
        description:
        - Set value to C(True) to skip Subnet creation and print the spec for verification.
        type: bool
        default: False
    name:
        description:
        - Name of the Subnet
        type: str
        required: True
    subnet_uuid:
        description:
        - Used during Subnet update/delete, only needed if Subnet with same name exits in the cluster.
        type: str
    vlan_id:
        description:
        - Vlan ID
        type: int
        required: True
    cluster:
        description:
        - PE Cluster uuid or name where you want to create the subnet.
        type: str
        required: True
    vswitch_name:
        description:
        - Name of the Vswitch
        type: str
        required: True
    virtual_switch_uuid:
        description:
        - Virtual Machine memory in (mib), E.g 2048 for 2GB.
        type: str
        required: True
    subnet_type:
        description:
        - Subnet type
        type: str
        default: "VLAN"
    ip_config:
        description:
        - IP address management options
        type: dict
        suboptions:
            default_gateway_ip:
                description:
                - Default Gateway
                type: str
            dhcp_server_address:
                description:
                - DHCP server address
                type: dict
                suboptions:
                    ip:
                        description:
                        - Override DHCP Server IP
                        type: str
            pool_list:
                description:
                - DHCP pool list
                type: list
                elements: dict
                suboptions:
                    range:
                        description:
                        - Range of IP's space seperated e.g. 10.0.0.10 10.0.0.30
                        type: str
            prefix_length:
                description:
                - Prefix Length
                type: int
                required: True
            subnet_ip:
                description:
                - Subnet IP
                type: str
                required: True
            dhcp_options:
                description:
                - DHCP Options
                type: dict
                suboptions:
                    domain_name_server_list:
                        description:
                        - DNS server list
                        type: list
                        elements: str
                    domain_name:
                        description:
                        - Domain name
                        type: str
author:
    - Sarat Kumar (@kumarsarath588)
'''

EXAMPLES = r'''
- name: Create Subnet
  nutanix.nutanix.nutanix_subnet:
    pc_hostname: "{{ pc_hostname }}"
    pc_username: "{{ pc_username }}"
    pc_password: "{{ pc_password }}"
    pc_port: 9440
    state: present
    name: "vlan.1"
    vlan_id: 1
    vswitch_name: "vs0"
    virtual_switch_uuid:  "7527f349-b772-4b17-be71-41af0492c4ba"
  delegate_to: localhost
  register: create_subnet
- debug:
    msg: "{{ create_subnet }}"
'''


RETURN = r'''
#TO-DO
'''

import json
import time
import base64
import os
# import yaml #TO-DO figure out yaml import
from ansible.module_utils.basic import AnsibleModule, env_fallback
from ansible_collections.nutanix.nutanix.plugins.module_utils.nutanix_api_client import (
    NutanixApiClient,
    get_subnet_uuid,
    get_subnet,
    create_subnet,
    update_subnet,
    delete_subnet,
    task_poll,
    get_cluster_uuid,
    get_cluster_vswitch_uuid,
    set_payload_keys,
    has_changed,
    is_uuid
)


SUBNET_PAYLOAD = {
    "metadata": {
        "kind": "subnet"
    },
    "spec": {
        "name": "",
        "resources": {
            "ip_config": {},
            "subnet_type": "VLAN",
            "vlan_id": 0,
            "is_external": False,
            "virtual_switch_uuid": ""
        },
        "cluster_reference": {
            "kind": "cluster",
            "uuid": ""
        }
    },
    "api_version": "3.1.0"
}

IP_CONFIG = {
    "default_gateway_ip": "",
    "dhcp_server_address": {
        "ip": ""
    },
    "pool_list": [
        {
            "range": ""
        }
    ],
    "prefix_length": 0,
    "subnet_ip": "",
    "dhcp_options": {
        "domain_name_server_list": [""],
        "domain_name": ""
    }
}


def main():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        pc_hostname=dict(
            type='str', required=True, fallback=(env_fallback, ["PC_HOSTNAME"])
        ),
        pc_username=dict(
            type='str', required=True, fallback=(env_fallback, ["PC_USERNAME"])
        ),
        pc_password=dict(
            type='str', required=True, no_log=True, fallback=(env_fallback, ["PC_PASSWORD"])
        ),
        pc_port=dict(default="9440", type='str'),
        validate_certs=dict(default=True, type='bool'),
        state=dict(
            default="present",
            type='str',
            choices=[
                "present",
                "absent"
            ]
        ),
        name=dict(type='str', required=True),
        subnet_uuid=dict(type='str'),
        vlan_id=dict(type='int', required=True),
        cluster=dict(type='str', required=True),
        vswitch_name=dict(type='str', required=True),
        subnet_type=dict(default="VLAN", type='str'),
        virtual_switch_uuid=dict(type='str', required=True),
        dry_run=dict(default=False, type='bool'),
        ip_config=dict(
            type='dict',
            options=dict(
                default_gateway_ip=dict(
                    type='str'
                ),
                dhcp_server_address=dict(
                    type='dict',
                    options=dict(
                        ip=dict(
                            type='str'
                        )
                    )
                ),
                pool_list=dict(
                    type='list',
                    elements='dict',
                    options=dict(
                        range=dict(
                            type='str'
                        )
                    )
                ),
                prefix_length=dict(
                    type='int',
                    required=True
                ),
                subnet_ip=dict(
                    type='str',
                    required=True
                ),
                dhcp_options=dict(
                    type='dict',
                    options=dict(
                        domain_name_server_list=dict(
                            type='list',
                            elements='str'
                        ),
                        domain_name=dict(
                            type='str'
                        )
                    )
                )
            )
        )
    )

    # the AnsibleModule object will be our abstraction working with Ansible
    # this includes instantiation, a couple of common attr would be the
    # args/params passed to the execution, as well as if the module
    # supports check mode
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    if not module.params["pc_hostname"]:
        module.fail_json("pc_hostname cannot be empty")
    if not module.params["pc_username"]:
        module.fail_json("pc_username cannot be empty")
    if not module.params["pc_password"]:
        module.fail_json("pc_password cannot be empty")

    # Instantiate api client
    client = NutanixApiClient(module)
    result = entry_point(module, client)
    module.exit_json(**result)


def entry_point(module, client):
    if module.params["state"] == "present":
        operation = "create"
    elif module.params["state"] == "absent":
        operation = "delete"
    else:
        operation = module.params["state"]

    func = globals()["_" + operation]

    return func(module.params, client)


def create_subnet_spec(params, subnet_spec, client):

    ip_config = None

    if is_uuid(params['cluster']):
        cluster_uuid = params['cluster']
    else:
        cluster_name = params['cluster']
        cluster_uuid = get_cluster_uuid(cluster_name, client)
        if cluster_uuid:
            cluster_uuid = cluster_uuid[0]
        else:
            error = "Could not find cluster '{0}'.".format(params['cluster'])
            return None, error

    if not params["virtual_switch_uuid"] and not params["vswitch_name"]:
        error = "Please pass 'vswitch_name' or 'virtual_switch_uuid'."
        return None, error

    if params["virtual_switch_uuid"]:
        virtual_switch_uuid = params["virtual_switch_uuid"]
        vswitch_name = None
    else:
        vswitch_name = params["vswitch_name"]
        cluster_virtual_switch_maps = get_cluster_vswitch_uuid(vswitch_name, cluster_uuid, client)
        if cluster_virtual_switch_maps:
            try:
                virtual_switch_uuid = cluster_virtual_switch_maps[cluster_uuid]
            except KeyError:
                error = "Virtual Switch '{0}' provided doesn't exists in the given cluster '{1}'.".format(vswitch_name, cluster_uuid)
                return None, error
        else:
            error = "Could not find Vswitch '{0}'.".format(vswitch_name)
            return None, error

    if params['ip_config']:
        ip_config = set_payload_keys(params['ip_config'], IP_CONFIG, {})

    subnet_spec["spec"]["name"] = params['name']
    subnet_spec["spec"]["resources"]["subnet_type"] = params['subnet_type']
    subnet_spec["spec"]["resources"]["vlan_id"] = params['vlan_id']
    subnet_spec["spec"]["resources"]["virtual_switch_uuid"] = virtual_switch_uuid
    if ip_config:
        if "subnet_ip" not in ip_config:
            error = "Network address 'subnet_ip' is not specified."
            return None, error
        if "prefix_length" not in ip_config:
            error = "Network address 'prefix_length' is not specified."
            return None, error
        subnet_spec["spec"]["resources"]["ip_config"] = ip_config

    subnet_spec["spec"]["cluster_reference"] = {"kind": "cluster", "uuid": cluster_uuid}

    return subnet_spec, None


def update_subnet_spec(params, current_subnet_payload, client):

    has_changed_status = False
    new_subnet_payload, error = create_subnet_spec(params, SUBNET_PAYLOAD, client)

    if error:
        return new_subnet_payload, error

    current_subnet_spec = current_subnet_payload["spec"]
    new_subnet_spec = new_subnet_payload["spec"]

    if "vswitch_name" in current_subnet_spec["resources"]:
        del current_subnet_spec["resources"]["vswitch_name"]

    if "name" in current_subnet_spec["cluster_reference"]:
        del current_subnet_spec["cluster_reference"]["name"]

    if (
        not has_changed(current_subnet_spec, new_subnet_spec) and
        not has_changed(new_subnet_spec, current_subnet_spec)
    ):
        return False, None

    if has_changed(
        current_subnet_spec["resources"]["vlan_id"],
        new_subnet_spec["resources"]["vlan_id"]
    ):
        error = "Cannot update current vlan id '{0}' to new vlan id {1}.".format(
            current_subnet_spec["resources"]["vlan_id"], new_subnet_spec["resources"]["vlan_id"]
        )
        return None, error

    if has_changed(
        current_subnet_spec["cluster_reference"],
        new_subnet_spec["cluster_reference"]
    ):
        error = "Cannot update cluster for existing subnet."
        return None, error

    if has_changed(
        current_subnet_spec["resources"]["virtual_switch_uuid"],
        new_subnet_spec["resources"]["virtual_switch_uuid"]
    ):
        has_changed_status = True
        current_subnet_spec["resources"]["virtual_switch_uuid"] = new_subnet_spec["resources"]["virtual_switch_uuid"]

    if "ip_config" in new_subnet_spec["resources"]:
        has_changed_status = True
        current_subnet_spec["resources"]["ip_config"] = new_subnet_spec["resources"]["ip_config"]
    else:
        if "ip_config" in current_subnet_spec["resources"]:
            has_changed_status = True
            del current_subnet_spec["resources"]["ip_config"]

    current_subnet_payload["spec"] = current_subnet_spec

    if has_changed_status:
        return current_subnet_payload, None

    return has_changed_status, None


def _create(params, client):

    subnet_uuid = None

    if params["subnet_uuid"]:
        subnet_uuid = params["subnet_uuid"]

    result = dict(
        changed=False,
        subnet_uuid=''
    )

    # Check Subnet existance
    subnet_uuid_list = get_subnet_uuid(params["name"], client)

    if len(subnet_uuid_list) > 1 and not subnet_uuid:
        result["failed"] = True
        result["msg"] = """Multiple Subnets's with same name '{0}' exists in the cluster.
        please give different name or specify subnet_uuid if you want to update an existing Subnet""".format(params["name"])
        result["subnet_uuid"] = subnet_uuid_list
        return result
    elif len(subnet_uuid_list) >= 1 or subnet_uuid:
        return _update(params, client, subnet_uuid=subnet_uuid)

    # Create Subnet Spec
    subnet_payload, error = create_subnet_spec(params, SUBNET_PAYLOAD, client)
    if error:
        result["failed"] = True
        result["msg"] = error
        return result

    if params['dry_run'] is True:
        result["subnet_spec"] = subnet_payload
        return result

    # Create Subnet
    task_uuid, subnet_uuid = create_subnet(subnet_payload, client)

    task_status = task_poll(task_uuid, client)
    if task_status:
        result["failed"] = True
        result["msg"] = task_status
        return result

    result["subnet_uuid"] = subnet_uuid
    result["changed"] = True

    return result


def _update(params, client, subnet_uuid=None):

    result = dict(
        changed=False,
        subnet_spec={},
        updated_subnet_spec={},
        task_uuid=''
    )

    if not subnet_uuid:
        subnet_uuid = get_subnet_uuid(params["name"], client)[0]

    current_subnet_payload = get_subnet(subnet_uuid, client)
    if "status" in current_subnet_payload:
        del current_subnet_payload["status"]

    # Update Subnet spec
    updated_subnet_payload, error = update_subnet_spec(params, current_subnet_payload, client)
    if error:
        result["failed"] = True
        result["msg"] = error
        return result

    if not updated_subnet_payload:
        result["msg"] = "Nothing to updated in the Subnet."
        return result

    result["updated_subnet_spec"] = updated_subnet_payload

    if params['dry_run'] is True:
        return result

    task_uuid = update_subnet(subnet_uuid, updated_subnet_payload, client)
    result["task_uuid"] = task_uuid

    task_status = task_poll(task_uuid, client)
    if task_status:
        result["failed"] = True
        result["msg"] = task_status
        return result

    result["changed"] = True

    return result


def _delete(params, client):

    result = dict(
        changed=False,
        task_uuid='',
    )

    subnet_uuid = None
    subnet_name = params["name"]

    if params["subnet_uuid"]:
        subnet_uuid = params["subnet_uuid"]
    else:
        subnet_uuid_list = get_subnet_uuid(params["name"], client)
        if not subnet_uuid_list:
            result["failed"] = True
            result["msg"] = "Subnet with given name '{0}' not found.".format(subnet_name)
            return result

        if len(subnet_uuid_list) > 1:
            result["failed"] = True
            result["msg"] = """Multiple Subnets's with same name '{0}' exists in the cluster.
                Specify subnet_uuid of the Subnet you want to delete.""".format(subnet_name)
            result["subnet_uuid"] = subnet_uuid_list
            return result

        subnet_uuid = subnet_uuid_list[0]

    # Delete Subnet
    task_uuid = delete_subnet(subnet_uuid, client)

    result["task_uuid"] = task_uuid

    task_status = task_poll(task_uuid, client)
    if task_status:
        result["failed"] = True
        result["msg"] = task_status
        return result

    result["changed"] = True

    return result


if __name__ == '__main__':
    main()
