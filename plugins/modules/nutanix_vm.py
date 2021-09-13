#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2021, Sarat Kumar <saratkumar.k@nutanix.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

DOCUMENTATION = r'''
---
module: nutanix_vm

short_description: VM module which suports VM CRUD operations

version_added: "0.0.1"

description: Create, Update, Delete, Power-on, Power-off Nutanix VM's

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
        - If C(state) is set to C(present) the VM is created, if VM with same name already exists it will updated the VM.
        - If C(state) is set to C(absent) and the VM exists in the cluster, VM with specified name is removed.
        - If C(state) is set to C(poweron) and the VM exists in the cluster, VM with specified name is Powered On.
        - If C(state) is set to C(poweroff) and the VM exists in the cluster, VM with specified name is Powered Off.
        choices:
        - present
        - absent
        - poweron
        - poweroff
        type: str
        default: present
    name:
        description:
        - Name of the Virtual Machine
        type: str
        required: True
    vm_uuid:
        description:
        - Used during VM update, only needed if VM's with same name exits in the cluster.
        type: str
        required: False
    cpu:
        description:
        - Number of CPU's.
        type: int
        required: True
    vcpu:
        description:
        - Number of Cores per CPU.
        type: int
        required: True
    memory:
        description:
        - Virtual Machine memory in (mib), E.g 2048 for 2GB.
        type: int
        required: True
    cluster:
        description:
        - PE Cluster uuid or name where you want to place the VM.
        type: str
        required: True
    power_state:
        description:
        - VM power state
        - Note please send "ON" or "OFF" with quotes.
        - 'Accepted value for this field:'
        - '    - C(ON)'
        - '    - C(OFF)'
        choices:
        - "ON"
        - "OFF"
        type: str
        default: "ON"
    dry_run:
        description:
        - Set value to C(True) to skip vm creation and print the spec for verification.
        type: bool
        default: False
    disk_list:
        description:
        - Virtual Machine Disk list
        type: list
        elements: dict
        required: True
        suboptions:
            uuid:
                description:
                - 'Disk uuid (Computed)'
                type: str
            disk_size_bytes:
                description:
                - 'Disk Size in bytes (Computed)'
                type: int
            disk_size_mib:
                description:
                - 'Disk Size Mib (Optional)'
                type: int
            storage_config:
                description:
                - Disk storage configuration
                type: dict
                suboptions:
                    flash_mode:
                        description:
                        - Flash mode
                        type: str
                    storage_container_reference:
                        description:
                        - Storage container reference configuration
                        type: dict
                        suboptions:
                            uuid:
                                description:
                                - Storage container uuid
                                type: str
                            name:
                                description:
                                - Storage container name
                                type: str
                            kind:
                                description:
                                - Storage container kind
                                type: str
                                default: storage_container
                            url:
                                description:
                                - Storage container url
                                type: str
            device_properties:
                description:
                - Disk device properties
                type: dict
                suboptions:
                    device_type:
                        description:
                        - Device type
                        - 'Accepted value for this field:'
                        - '    - C(DISK)'
                        - '    - C(CDROM)'
                        type: str
                        choices:
                        - DISK
                        - CDROM
                        required: True
                    disk_address:
                        description:
                        - Disk device address
                        type: dict
                        suboptions:
                            device_index:
                                description:
                                - Disk device index
                                type: int
                            adapter_type:
                                description:
                                - Adapter type
                                - 'Accepted value for this field:'
                                - '    - C(SCSI)'
                                - '    - C(PCI)'
                                - '    - C(SATA)'
                                - '    - C(IDE)'
                                type: str
                                choices:
                                - SCSI
                                - PCI
                                - SATA
                                - IDE
                                required: True
            data_source_reference:
                description:
                - Data source reference
                type: dict
                suboptions:
                    uuid:
                        description:
                        - Data source uuid
                        type: str
                    name:
                        description:
                        - Data source Name
                        type: str
                    kind:
                        description:
                        - Data source kind
                        type: str
                        default: image
                    url:
                        description:
                        - Data source url
                        type: str
    nic_list:
        description:
        - Virtual Machine Nic list
        type: list
        elements: dict
        required: True
        suboptions:
            uuid:
                description:
                - Disk uuid (Computed)
                type: str
            nic_type:
                description:
                - Nic Type
                - 'Accepted value for this field:'
                - '    - C(NORMAL_NIC)'
                type: str
                default: NORMAL_NIC
                choices:
                - NORMAL_NIC
            num_queues:
                description:
                - Number of queues
                type: int
            network_function_nic_type:
                description:
                - Network function nic type
                type: str
            vlan_mode:
                description:
                - Network function nic type
                - 'Accepted value for this field:'
                - '    - C(ACCESS)'
                type: str
                default: ACCESS
                choices:
                - ACCESS
            mac_address:
                description:
                - Mac address
                type: str
            model:
                description:
                - Nic Model
                type: str
            is_connected:
                description:
                - Is Connected
                type: bool
                default: True
            ip_endpoint_list:
                description:
                - Ip Endpoint list
                type: list
                elements: dict
                suboptions:
                    ip:
                        description:
                        - IP Address
                        type: str
                    type:
                        description:
                        - Assignment type
                        - 'Accepted value for this field:'
                        - '    - C(ASSIGNED)'
                        - '    - C(LEARNED)'
                        type: str
                        default: ASSIGNED
                        choices:
                        - ASSIGNED
                        - LEARNED
                    prefix_length:
                        description:
                        - Prefix length
                        type: int
                    ip_type:
                        description:
                        - IP Type
                        - 'Accepted value for this field:'
                        - '    - C(STATIC)'
                        - '    - C(DHCP)'
                        type: str
                        choices:
                        - STATIC
                        - DHCP
                    gateway_address_list:
                        description:
                        - Gateway Address
                        type: list
                        elements: str
            secondary_ip_address_list:
                description:
                - Secondary IP address list
                type: list
                elements: str
            network_function_chain_reference:
                description:
                - Network Function chain reference
                type: dict
                suboptions:
                    name:
                        description:
                        - Network Function chain Name
                        type: str
                    kind:
                        description:
                        - Network Function chain kind
                        type: str
                        default: network_function_chain
                    uuid:
                        description:
                        - Network Function chain uuid
                        type: str
            subnet_reference:
                description:
                - Subnet Reference
                type: dict
                required: True
                suboptions:
                    name:
                        description:
                        - Subnet Reference Name
                        type: str
                    kind:
                        description:
                        - Subnet Reference kind
                        type: str
                        default: subnet
                    uuid:
                        description:
                        - Subnet Reference uuid
                        type: str
            trunked_vlan_list:
                description:
                - Trunked vlan
                type: list
                elements: str
    guest_customization:
        description:
        - Virtual Machine Guest Customization
        - 'Valid attributes are:'
        - ' - C(cloud_init) (str): Path of the cloud-init yaml file.'
        - ' - C(sysprep) (str): Path of the sysprep xml file.'
        type: dict
        required: False
        suboptions:
            cloud_init:
                description:
                - Cloud init content
                type: str
                required: False
            cloud_init_file:
                description:
                - Cloud init input file
                type: str
                required: False
            sysprep:
                description:
                - Sysprep content
                type: str
                required: False
            sysprep_file:
                description:
                - Sysprep input file
                type: str
                required: False
            sysprep_install_type:
                description:
                - Sysprep Install type
                - 'Accepted value for this field:'
                - '    - C(FRESH)'
                - '    - C(PREPARED)'
                type: str
                required: False
                default: PREPARED
                choices:
                - FRESH
                - PREPARED
author:
    - Sarat Kumar (@kumarsarath588)
'''

EXAMPLES = r'''
- name: Create VM
  nutanix.nutanix.nutanix_vm:
    pc_hostname: "{{ pc_hostname }}"
    pc_username: "{{ pc_username }}"
    pc_password: "{{ pc_password }}"
    pc_port: 9440
    state: present
    name: "vm-0001"
    cpu: 4
    vcpu: 2
    memory: 4096
    cluster: "{{ cluster uuid or name }}"
    disk_list:
    - device_properties:
        device_type: DISK
        disk_address:
          adapter_type: SCSI
      data_source_reference:
        name: "{{ image_name }}"
    - device_properties:
        device_type: DISK
        disk_address:
          adapter_type: SCSI
      disk_size_mib: 20480
      storage_config:
        storage_container_reference:
          name: "{{ datastore_name }}"
    nic_list:
    - subnet_reference:
        name: vlan.0
    - subnet_reference:
        name: vlan.889
    ip_endpoint_list:
        - ip: 10.0.0.1
  delegate_to: localhost
  register: create_vm
- debug:
    msg: "{{ create_vm }}"
'''


RETURN = r'''
#TO-DO
'''

import json
import time
import base64
import os
# import yaml  # TO-DO figure out yaml import
from ansible.module_utils.basic import AnsibleModule, env_fallback
from ansible_collections.nutanix.nutanix.plugins.module_utils.nutanix_api_client import (
    NutanixApiClient,
    get_cluster_uuid,
    get_vm_uuid,
    get_vm,
    create_vm,
    update_vm,
    delete_vm,
    update_powerstate_vm,
    get_subnet_uuid,
    get_image_uuid,
    get_cluster_storage_container_map,
    is_uuid,
    set_payload_keys,
    task_poll,
    has_changed,
    read_file
)


VM_PAYLOAD = {
    "metadata": {
        "kind": "vm",
        "spec_version": 0
    },
    "spec": {
        "cluster_reference": {
            "kind": "kind",
            "name": "name",
            "uuid": "uuid"
        },
        "name": "name",
        "resources": {
            "disk_list": [],
            "memory_size_mib": 0,
            "nic_list": [],
            "num_sockets": 0,
            "num_vcpus_per_socket": 0,
            "power_state": "power_state"
        }
    }
}

DISK_PAYLOAD = {
    "uuid": "",
    "storage_config": {
        "flash_mode": "",
        "storage_container_reference": {
            "url": "",
            "kind": "",
            "uuid": "",
            "name": ""
        }
    },
    "device_properties": {
        "device_type": "",
        "disk_address": {
            "device_index": 0,
            "adapter_type": ""
        }
    },
    "data_source_reference": {
        "url": "",
        "kind": "",
        "uuid": "",
        "name": ""
    },
    "disk_size_mib": 0
}

NIC_PAYLOAD = {
    "nic_type": "",
    "uuid": "",
    "ip_endpoint_list": [
        {
            "ip": "",
            "type": "",
            "gateway_address_list": [
                ""
            ],
            "prefix_length": 0,
            "ip_type": ""
        }
    ],
    "num_queues": 0,
    "secondary_ip_address_list": [
        ""
    ],
    "network_function_nic_type": "",
    "network_function_chain_reference": {
        "kind": "",
        "name": "",
        "uuid": ""
    },
    "vlan_mode": "",
    "mac_address": "",
    "subnet_reference": {
        "kind": "subnet",
        "name": "",
        "uuid": ""
    },
    "model": "",
    "is_connected": True,
    "trunked_vlan_list": [
        0
    ]
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
                "absent",
                "poweron",
                "poweroff"
            ]
        ),
        name=dict(type='str', required=True),
        vm_uuid=dict(type='str'),
        cpu=dict(type='int', required=True),
        vcpu=dict(type='int', required=True),
        memory=dict(type='int', required=True),
        cluster=dict(type='str', required=True),
        power_state=dict(type='str', default="ON", choices=["ON", "OFF"]),
        dry_run=dict(default=False, type='bool'),
        disk_list=dict(
            type='list',
            required=True,
            elements='dict',
            options=dict(
                uuid=dict(
                    type='str'
                ),
                disk_size_bytes=dict(
                    type='int'
                ),
                disk_size_mib=dict(
                    type='int'
                ),
                storage_config=dict(
                    type='dict',
                    options=dict(
                        flash_mode=dict(
                            type='str'
                        ),
                        storage_container_reference=dict(
                            type='dict',
                            options=dict(
                                uuid=dict(
                                    type='str'
                                ),
                                name=dict(
                                    type='str'
                                ),
                                kind=dict(
                                    type='str',
                                    default="storage_container"
                                ),
                                url=dict(
                                    type='str'
                                )
                            )
                        )
                    )
                ),
                device_properties=dict(
                    type='dict',
                    options=dict(
                        device_type=dict(
                            type='str',
                            required=True,
                            choices=["DISK", "CDROM"]
                        ),
                        disk_address=dict(
                            type='dict',
                            options=dict(
                                device_index=dict(
                                    type='int'
                                ),
                                adapter_type=dict(
                                    type='str',
                                    required=True,
                                    choices=["SCSI", "PCI", "SATA", "IDE"]
                                )
                            )
                        )
                    )
                ),
                data_source_reference=dict(
                    type='dict',
                    options=dict(
                        uuid=dict(
                            type='str'
                        ),
                        name=dict(
                            type='str'
                        ),
                        kind=dict(
                            type='str',
                            default="image"
                        ),
                        url=dict(
                            type='str'
                        )
                    )
                )
            )
        ),
        nic_list=dict(
            type='list',
            required=True,
            elements='dict',
            options=dict(
                uuid=dict(
                    type='str'
                ),
                nic_type=dict(
                    type='str',
                    default="NORMAL_NIC",
                    choices=["NORMAL_NIC"]
                ),
                num_queues=dict(
                    type='int'
                ),
                network_function_nic_type=dict(
                    type='str'
                ),
                vlan_mode=dict(
                    type='str',
                    default="ACCESS",
                    choices=["ACCESS"]
                ),
                mac_address=dict(
                    type='str'
                ),
                model=dict(
                    type='str'
                ),
                is_connected=dict(
                    type='bool',
                    default=True
                ),
                ip_endpoint_list=dict(
                    type='list',
                    elements='dict',
                    options=dict(
                        ip=dict(
                            type='str'
                        ),
                        type=dict(
                            type='str',
                            default="ASSIGNED",
                            choices=["ASSIGNED", "LEARNED"]
                        ),
                        prefix_length=dict(
                            type='int'
                        ),
                        ip_type=dict(
                            type='str',
                            choices=["STATIC", "DHCP"]
                        ),
                        gateway_address_list=dict(
                            type='list',
                            elements='str'
                        )
                    )
                ),
                secondary_ip_address_list=dict(
                    type='list',
                    elements='str'
                ),
                network_function_chain_reference=dict(
                    type='dict',
                    options=dict(
                        name=dict(
                            type='str'
                        ),
                        kind=dict(
                            type='str',
                            default="network_function_chain"
                        ),
                        uuid=dict(
                            type='str'
                        )
                    )
                ),
                subnet_reference=dict(
                    type='dict',
                    required=True,
                    options=dict(
                        name=dict(
                            type='str'
                        ),
                        kind=dict(
                            type='str',
                            default="subnet"
                        ),
                        uuid=dict(
                            type='str'
                        )
                    )
                ),
                trunked_vlan_list=dict(
                    type='list',
                    elements='str'
                ),
            )
        ),
        guest_customization=dict(
            type='dict',
            required=False,
            options=dict(
                cloud_init=dict(
                    type='str',
                ),
                cloud_init_file=dict(
                    type='str',
                ),
                sysprep=dict(
                    type='str',
                ),
                sysprep_file=dict(
                    type='str',
                ),
                sysprep_install_type=dict(
                    type='str',
                    choices=["FRESH", "PREPARED"],
                    default="PREPARED"
                )
            )
        )
    )

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

    # Create api client
    client = NutanixApiClient(module)
    result = entry_point(module, client)
    module.exit_json(**result)


def entry_point(module, client):
    """
    This routine is the entry point to select appropriate operation based on state
    Args:
        module(obj): Ansible module object
        client(obj): Rest client obj
    Returns:
        (func): VM operation function
    """
    if module.params["state"] == "present":
        operation = "create"
    elif module.params["state"] == "absent":
        operation = "delete"
    else:
        operation = module.params["state"]

    func = globals()["_" + operation]

    return func(module.params, client)


def create_vm_spec(params, vm_spec, client):
    """
    This routine helps to generate update spec of vm
    Args:
        params(obj): Ansible params object
        vm_spec(dict): Reference VM spec
        client(obj): Rest client obj
    Returns:
        vm_spec(dict): VM spec
    """
    nic_list = []
    disk_list = []

    if is_uuid(params['cluster']):
        cluster_uuid = params['cluster']
        cluster_name = None
    else:
        cluster_name = params['cluster']
        cluster_uuid = get_cluster_uuid(params['cluster'], client)
        if cluster_uuid:
            cluster_uuid = cluster_uuid[0]
        else:
            error = "Could not find cluster '{0}'.".format(params['cluster'])
            return None, error

    if params['nic_list']:
        for nic in params['nic_list']:
            if "subnet_reference" not in nic:
                error = "Invalid Nic params {0}.".format(nic)
                return None, error

            if nic["subnet_reference"]["uuid"]:
                nic_uuid = nic["subnet_reference"]["uuid"]
            elif nic["subnet_reference"]["name"]:
                nic_name = nic["subnet_reference"]["name"]
                nic_uuids = get_subnet_uuid(nic_name, client)
                if nic_uuids:
                    nic_uuid = nic_uuids[0]
                else:
                    error = "Could not find subnet '{0}'.".format(nic_name)
                    return None, error
            else:
                error = "Either nic uuid or Name should be passed in nic '{0}'.".format(nic)
                return None, error

            nic["subnet_reference"]["uuid"] = nic_uuid
            nic_payload = set_payload_keys(nic, NIC_PAYLOAD, {})
            nic_list.append(nic_payload)

    if params['disk_list']:
        scsi_counter = 0
        sata_counter = 0
        for disk in params['disk_list']:
            image_name = None
            if disk["device_properties"]["disk_address"]["adapter_type"] == "SCSI":
                counter = scsi_counter
                scsi_counter += 1
            elif disk["device_properties"]["disk_address"]["adapter_type"] == "SATA":
                counter = sata_counter
                sata_counter += 1

            if (
                "data_source_reference" not in disk and
                "size_mib" not in disk and
                "volume_group_reference" not in disk
            ):
                error = "Invalid disk params {0}.".format(disk)
                return None, error

            if disk["data_source_reference"]:
                if disk["data_source_reference"]["uuid"]:
                    image_uuid = disk["data_source_reference"]["uuid"]
                elif disk["data_source_reference"]["name"]:
                    image_name = disk["data_source_reference"]["name"]
                    image_uuids = get_image_uuid(image_name, client)
                    if image_uuids:
                        image_uuid = image_uuids[0]
                    else:
                        error = "Could not find image '{0}'.".format(image_name)
                        return None, error
                else:
                    error = "Either disk uuid or Name should be passed in disk index '{0}'.".format(counter)
                    return None, error

                disk["device_properties"]["disk_address"]["device_index"] = counter
                disk["data_source_reference"]["uuid"] = image_uuid
            else:
                disk["device_properties"]["disk_address"]["device_index"] = counter

            if disk["storage_config"]:
                if disk["storage_config"]["storage_container_reference"]:
                    if disk["storage_config"]["storage_container_reference"]["uuid"]:
                        sc_uuid = disk["storage_config"]["storage_container_reference"]["uuid"]
                    elif disk["storage_config"]["storage_container_reference"]["name"]:
                        sc_name = disk["storage_config"]["storage_container_reference"]["name"]
                        cluster_sc_uuid_map = get_cluster_storage_container_map(sc_name, client)
                        if cluster_sc_uuid_map:
                            try:
                                sc_uuid = cluster_sc_uuid_map[cluster_uuid]
                            except KeyError:
                                error = "Storage container '{0}' provided doesn't exists in the given cluster '{1}'.".format(sc_name, cluster_uuid)
                                return None, error
                        else:
                            error = "Storage container '{0}' provided doesn't exists in the given cluster '{1}'.".format(sc_name, cluster_uuid)
                            return None, error
                    else:
                        error = "Either storage container uuid or Name should be passed in disk index '{0}'.".format(counter)
                        return None, error

                    disk["storage_config"]["storage_container_reference"]["uuid"] = sc_uuid

            disk_payload = set_payload_keys(disk, DISK_PAYLOAD, {})

            if image_name:
                del disk_payload["data_source_reference"]["name"]

            disk_list.append(disk_payload)

    vm_spec["spec"]["name"] = params['name']
    vm_spec["spec"]["resources"]["num_sockets"] = params['cpu']
    vm_spec["spec"]["resources"]["num_vcpus_per_socket"] = params['vcpu']
    vm_spec["spec"]["resources"]["memory_size_mib"] = params['memory']
    vm_spec["spec"]["resources"]["nic_list"] = nic_list
    vm_spec["spec"]["resources"]["disk_list"] = disk_list
    vm_spec["spec"]["cluster_reference"] = {"kind": "cluster", "uuid": cluster_uuid}
    if cluster_name:
        vm_spec["spec"]["cluster_reference"]["name"] = cluster_name

    if params["power_state"]:
        vm_spec["spec"]["resources"]["power_state"] = params["power_state"]
    else:
        vm_spec["spec"]["resources"]["power_state"] = "ON"

    if params["guest_customization"]:
        if (
            params["guest_customization"]["cloud_init"] and
            params["guest_customization"]["cloud_init_file"]
        ):
            error = "Please pass one of 'cloud_init' or 'cloud_init_file'."
            return None, error

        if params["guest_customization"]["cloud_init"]:
            cloud_init_encoded = base64.b64encode(
                params["guest_customization"]["cloud_init"].encode('ascii')
            )
            vm_spec["spec"]["resources"]["guest_customization"] = {
                "cloud_init": {
                    "user_data": cloud_init_encoded.decode('ascii')
                }
            }
        elif params["guest_customization"]["cloud_init_file"]:
            file_path = params["guest_customization"]["cloud_init_file"]
            if not os.path.exists(file_path):
                error = "Cloud-init yaml file '{0}' not found.'.".format(file_path)
                return None, error
            # try:
            #     yaml.load(read_file(file_path), Loader=yaml.FullLoader)
            # except yaml.YAMLError as e:
            #     error = """Invalid yaml file '{0}'.
            #     ERROR: {1}.""".format(file_path, e)
            #     return None, error

            cloud_init_content = read_file(file_path)
            cloud_init_encoded = base64.b64encode(
                cloud_init_content.encode('ascii')
            )
            vm_spec["spec"]["resources"]["guest_customization"] = {
                "cloud_init": {
                    "user_data": cloud_init_encoded.decode('ascii')
                }
            }
        if (
            params["guest_customization"]["sysprep"] and
            params["guest_customization"]["sysprep_file"]
        ):
            error = "Please pass one of 'sysprep' or 'sysprep_file'."
            return None, error

        if params["guest_customization"]["sysprep"]:
            sysprep_init_encoded = base64.b64encode(
                params["guest_customization"]["sysprep"].encode('ascii')
            )
            vm_spec["spec"]["resources"]["guest_customization"] = {
                "sysprep": {
                    "install_type": params["guest_customization"]["sysprep_install_type"],
                    "unattend_xml": sysprep_init_encoded.decode('ascii')
                }
            }
        elif params["guest_customization"]["sysprep_file"]:
            file_path = params["guest_customization"]["sysprep_file"]
            if not os.path.exists(file_path):
                error = "Sysprep xml file '{0}' not found.'.".format(file_path)
                return None, error

            sysprep_content = read_file(file_path)
            sysprep_init_encoded = base64.b64encode(
                sysprep_content.encode('ascii')
            )
            vm_spec["spec"]["resources"]["guest_customization"] = {
                "sysprep": {
                    "install_type": params["guest_customization"]["sysprep_install_type"],
                    "unattend_xml": sysprep_init_encoded.decode('ascii')
                }
            }

    return vm_spec, None


def update_vm_spec(params, current_vm_payload, client):
    """
    This routine helps to generate update spec of vm
    Args:
        params(obj): Ansible params object
        current_vm_payload(dict): Existing VM spec
        client(obj): Rest client obj
    Returns:
        updated_vm_payload(dict): Updated vm spec
    """
    new_vm_payload, error = create_vm_spec(params, VM_PAYLOAD, client)
    if error:
        return new_vm_payload, error

    new_vm_spec = new_vm_payload["spec"]
    current_vm_spec = current_vm_payload["spec"]

    has_changed_status = has_changed(new_vm_spec, current_vm_spec)

    new_vm_spec_disk_length = len(new_vm_spec["resources"]["disk_list"])
    current_vm_spec_disk_length = len(current_vm_spec["resources"]["disk_list"])

    new_vm_disk_list = new_vm_spec["resources"]["disk_list"]
    current_vm_disk_list = current_vm_spec["resources"]["disk_list"]

    if "guest_customization" in current_vm_spec["resources"]:
        current_vm_spec_disk_length = (current_vm_spec_disk_length - 1)

    if new_vm_spec_disk_length != current_vm_spec_disk_length:
        has_changed_status = True
        if new_vm_spec_disk_length > current_vm_spec_disk_length:
            diff_length = new_vm_spec_disk_length - current_vm_spec_disk_length
            diff_disk_list = new_vm_disk_list[-diff_length:]
            for disk in diff_disk_list:
                current_vm_disk_list.append(disk)
        elif new_vm_spec_disk_length < current_vm_spec_disk_length:
            if current_vm_spec["resources"]["guest_customization"]:
                new_vm_spec_disk_length = (new_vm_spec_disk_length + 1)
            current_vm_disk_list = current_vm_disk_list[:new_vm_spec_disk_length]

    if has_changed_status:
        for i, disk in enumerate(current_vm_disk_list):
            if disk["device_properties"]["device_type"] == "DISK":
                if "disk_size_mib" in new_vm_disk_list[i]:
                    if disk["disk_size_mib"] < new_vm_disk_list[i]["disk_size_mib"]:
                        disk["disk_size_mib"] = new_vm_disk_list[i]["disk_size_mib"]

    new_vm_spec_nic_length = len(new_vm_spec["resources"]["nic_list"])
    current_vm_spec_nic_length = len(current_vm_spec["resources"]["nic_list"])

    new_vm_nic_list = new_vm_spec["resources"]["nic_list"]
    current_vm_nic_list = current_vm_spec["resources"]["nic_list"]

    if new_vm_spec_nic_length != current_vm_spec_nic_length:
        has_changed_status = True
        if new_vm_spec_nic_length > current_vm_spec_nic_length:
            diff_length = new_vm_spec_nic_length - current_vm_spec_nic_length
            diff_nic_list = new_vm_nic_list[-diff_length:]
            for nic in diff_nic_list:
                current_vm_nic_list.append(nic)
        elif new_vm_spec_nic_length < current_vm_spec_nic_length:
            current_vm_nic_list = current_vm_nic_list[:new_vm_spec_nic_length]

    updated_vm_payload = current_vm_payload

    if not has_changed_status:
        return has_changed_status, None

    updated_vm_payload["spec"]["name"] = params['name']
    updated_vm_payload["spec"]["resources"]["num_sockets"] = params['cpu']
    updated_vm_payload["spec"]["resources"]["num_vcpus_per_socket"] = params['vcpu']
    updated_vm_payload["spec"]["resources"]["memory_size_mib"] = params['memory']

    updated_vm_payload["spec"]["resources"]["nic_list"] = current_vm_nic_list
    updated_vm_payload["spec"]["resources"]["disk_list"] = current_vm_disk_list
    updated_vm_payload["metadata"]["spec_version"] += 1

    if params["power_state"]:
        updated_vm_payload["spec"]["resources"]["power_state"] = params["power_state"]

    return updated_vm_payload, None


def _create(params, client):
    """
    This routine helps to create the given VM
    Args:
        params(obj): Ansible params object
        client(obj): Rest client obj
    Returns:
        result(obj): Ansible result object
    """
    vm_uuid = None
    check_for_ip = False
    ip_poll_max_retries = 180
    ip_poll_interval = 5

    if params["vm_uuid"]:
        vm_uuid = params["vm_uuid"]

    result = dict(
        changed=False,
        vm_uuid='',
        vm_ip_address='',
        vm_status={}
    )

    # Check VM existance
    vm_uuid_list = get_vm_uuid(params, client)

    if len(vm_uuid_list) > 1 and not vm_uuid:
        result["failed"] = True
        result["msg"] = """Multiple Vm's with same name '%s' exists in the cluster.
        please give different name or specify vm_uuid if you want to update vm""" % params["name"]
        result["vm_uuid"] = vm_uuid_list
        return result
    elif len(vm_uuid_list) >= 1 or vm_uuid:
        return _update(params, client, vm_uuid=vm_uuid)

    # Create VM Spec
    vm_payload, error = create_vm_spec(params, VM_PAYLOAD, client)
    if error:
        result["failed"] = True
        result["msg"] = error
        return result

    if params['dry_run'] is True:
        result["vm_spec"] = vm_payload
        return result

    if params['power_state']:
        if params['power_state'] == "ON":
            check_for_ip = True

    # Create VM
    task_uuid, vm_uuid = create_vm(vm_payload, client)

    task_status = task_poll(task_uuid, client)
    if task_status:
        result["failed"] = True
        result["msg"] = task_status
        return result

    retries = 0
    while check_for_ip:
        response = client.request(api_endpoint="v3/vms/%s" % vm_uuid, method="GET", data=None)
        json_content = json.loads(response.content)
        result["vm_status"] = json_content["status"]
        result["vm_ip_address"] = ""
        if len(json_content["status"]["resources"]["nic_list"]) > 0:
            if len(json_content["status"]["resources"]["nic_list"][0]["ip_endpoint_list"]) > 0:
                if json_content["status"]["resources"]["nic_list"][0]["ip_endpoint_list"][0]["ip"] != "":
                    result["vm_ip_address"] = json_content["status"]["resources"]["nic_list"][0]["ip_endpoint_list"][0]["ip"]
                    break
        time.sleep(ip_poll_interval)
        retries = (retries + 1)
        if retries > ip_poll_max_retries:
            break

    result["vm_uuid"] = vm_uuid
    result["changed"] = True

    return result


def _update(params, client, vm_uuid=None):
    """
    This routine helps to update the given VM
    Args:
        params(obj): Ansible params object
        client(obj): Rest client obj
    Returns:
        result(obj): Ansible result object
    """
    result = dict(
        changed=False,
        vm_spec={},
        updated_vm_spec={},
        task_uuid=''
    )

    need_restart = False

    if not vm_uuid:
        vm_uuid = get_vm_uuid(params, client)[0]

    current_vm_payload = get_vm(vm_uuid, client)

    current_vm_disk_list_length = len(current_vm_payload["spec"]["resources"]["disk_list"])
    if "guest_customization" in current_vm_payload["spec"]["resources"]:
        current_vm_disk_list_length = (current_vm_disk_list_length - 1)

    new_vm_disk_list_length = len(params["disk_list"])

    if (
        params['cpu'] < current_vm_payload["status"]["resources"]["num_sockets"] or
        params['vcpu'] < current_vm_payload["status"]["resources"]["num_vcpus_per_socket"] or
        params['memory'] < current_vm_payload["status"]["resources"]["memory_size_mib"] or
        len(params['nic_list']) < len(current_vm_payload["status"]["resources"]["nic_list"]) or
        new_vm_disk_list_length < current_vm_disk_list_length
    ):
        if current_vm_payload["status"]["resources"]["power_state"] == "ON":
            need_restart = True

    if "status" in current_vm_payload:
        del current_vm_payload["status"]

    # Update VM spec
    updated_vm_payload, error = update_vm_spec(params, current_vm_payload, client)
    if error:
        result["failed"] = True
        result["msg"] = error
        return result

    if not updated_vm_payload:
        result["msg"] = "VM is in same state."
        return result

    result["updated_vm_spec"] = updated_vm_payload

    if params['dry_run'] is True:
        return result

    # Poweroff the VM
    if need_restart:
        mechanism = "HARD"
        power_state = "OFF"

        task_uuid = update_powerstate_vm(vm_uuid, client, mechanism, power_state)
        task_status = task_poll(task_uuid, client)
        if task_status:
            result["failed"] = True
            result["msg"] = task_status
            return result

        updated_vm_payload["metadata"]["entity_version"] = "%d" % (
            int(updated_vm_payload["metadata"]["entity_version"]) + 1
        )

    task_uuid = update_vm(vm_uuid, updated_vm_payload, client)
    result["task_uuid"] = task_uuid

    task_status = task_poll(task_uuid, client)
    if task_status:
        result["failed"] = True
        result["msg"] = task_status
        return result

    result["changed"] = True

    return result


def _delete(params, client):
    """
    This routine helps to delete the given VM
    Args:
        params(obj): Ansible params object
        client(obj): Rest client obj
    Returns:
        result(obj): Ansible result object
    """
    result = dict(
        changed=False,
        task_uuid='',
    )

    vm_uuid = None
    vm_name = params["name"]

    if params["vm_uuid"]:
        vm_uuid = params["vm_uuid"]
    else:
        vm_uuid_list = get_vm_uuid(params, client)
        if not vm_uuid_list:
            result["msg"] = "VM with given name '{0}' not found.".format(vm_name)
            return result

        if len(vm_uuid_list) > 1:
            result["failed"] = True
            result["msg"] = """Multiple Vm's with same name '{0}' exists in the cluster.
                Specify vm_uuid of the VM you want to delete.""".format(vm_name)
            result["vm_uuid"] = vm_uuid_list
            return result

        vm_uuid = vm_uuid_list[0]

    # Delete VM
    task_uuid = delete_vm(vm_uuid, client)

    result["task_uuid"] = task_uuid

    task_status = task_poll(task_uuid, client)
    if task_status:
        result["failed"] = True
        result["msg"] = task_status
        return result

    result["changed"] = True

    return result


def _poweron(params, client):
    """
    This routine helps to power on the given VM
    Args:
        params(obj): Ansible params object
        client(obj): Rest client obj
    Returns:
        result(obj): Ansible result object
    """
    result = dict(
        changed=False,
        task_uuid='',
    )

    vm_uuid = None
    vm_name = params["name"]
    mechanism = "HARD"
    power_state = "ON"

    if params["vm_uuid"]:
        vm_uuid = params["vm_uuid"]
    else:
        vm_uuid_list = get_vm_uuid(params, client)
        if not vm_uuid_list:
            result["failed"] = True
            result["msg"] = "VM with given name '{0}' not found.".format(vm_name)
            return result

        if len(vm_uuid_list) > 1:
            result["failed"] = True
            result["msg"] = """Multiple Vm's with same name '{0}' exists in the cluster.
                Specify vm_uuid of the VM you want to poweron.""".format(vm_name)
            result["vm_uuid"] = vm_uuid_list
            return result

        vm_uuid = vm_uuid_list[0]

    # Power on VM
    task_uuid = update_powerstate_vm(vm_uuid, client, mechanism, power_state)

    result["task_uuid"] = task_uuid

    task_status = task_poll(task_uuid, client)
    if task_status:
        result["failed"] = True
        result["msg"] = task_status
        return result

    result["changed"] = True

    return result


def _poweroff(params, client):
    """
    This routine helps to power off the given VM
    Args:
        params(obj): Ansible params object
        client(obj): Rest client obj
    Returns:
        result(obj): Ansible result object
    """
    result = dict(
        changed=False,
        task_uuid='',
    )

    vm_uuid = None
    vm_name = params["name"]
    mechanism = "HARD"
    power_state = "OFF"

    if params["vm_uuid"]:
        vm_uuid = params["vm_uuid"]
    else:
        vm_uuid_list = get_vm_uuid(params, client)
        if not vm_uuid_list:
            result["failed"] = True
            result["msg"] = "VM with given name '{0}' not found.".format(vm_name)
            return result

        if len(vm_uuid_list) > 1:
            result["failed"] = True
            result["msg"] = """Multiple Vm's with same name '{0}' exists in the cluster.
                Specify vm_uuid of the VM you want to poweroff.""".format(vm_name)
            result["vm_uuid"] = vm_uuid_list
            return result

        vm_uuid = vm_uuid_list[0]

    # Power off VM
    task_uuid = update_powerstate_vm(vm_uuid, client, mechanism, power_state)

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
