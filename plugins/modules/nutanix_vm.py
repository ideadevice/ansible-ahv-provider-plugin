#!/usr/bin/python

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
        - PE Cluster uuid/name where you want to place the VM.
        type: str
        required: True
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
        suboptions:
            clone_from_image:
                description:
                - Name/UUID of the image
                type: str
            size_mib:
                description:
                - Disk Size
                type: int
            device_type:
                description:
                - Disk Device type
                - 'Accepted value for this field:'
                - '    - C(DISK)'
                - '    - C(CDROM)'
                choices:
                - DISK
                - CDROM
                type: str
                required: True
            adapter_type:
                description:
                - Disk Adapter type
                - 'Accepted value for this field:'
                - '    - C(SCSI)'
                - '    - C(PCI)'
                - '    - C(SATA)'
                - '    - C(IDE)'
                choices:
                - SCSI
                - PCI
                - SATA
                - IDE
                type: str
                required: True
        required: True
    nic_list:
        description:
        - Virtual Machine Nic list
        type: list
        elements: dict
        suboptions:
            uuid:
                description:
                - Subnet UUID
                type: str
                required: True
        required: True
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
                required: True
            sysprep:
                description:
                - Sysprep content
                type: str
                required: True
            sysprep_install_type:
                description:
                - Sysprep Install type
                - 'Accepted value for this field:'
                - '    - C(FRESH)'
                - '    - C(PREPARED)'
                type: str
                required: False
                choices:
                - FRESH
                - PREPARED
author:
    - Sarat Kumar (@kumarsarath588)
'''

EXAMPLES = r'''
- name: Create VM
  hosts: localhost
  collections:
  - nutanix.nutanix
  tasks:
  - nutanix_vm:
    pc_hostname: "{{ pc_hostname }}"
    pc_username: "{{ pc_username }}"
    pc_password: "{{ pc_password }}"
    pc_port: 9440
    validate_certs: False
    name: "vm-0001"
    cpu: 2
    vcpu: 2
    memory: 2048
    cluster: "{{ cluster name or uuid }}"
    disk_list:
    - device_type: DISK
      clone_from_image: "{{ image name or uuid }}"
      adapter_type: SCSI
    - device_type: DISK
      adapter_type: SCSI
      size_mib: 10240
    nic_list:
    - uuid: "{{ nic name or uuid }}"
    guest_customization:
      cloud_init: |-
          #cloud-config
          users:
            - name: centos
              sudo: ['ALL=(ALL) NOPASSWD:ALL']
          chpasswd:
            list: |
              centos:nutanix/4u
            expire: False
          ssh_pwauth: true
    register: vm
  - debug:
      msg: "{{ vm }}"
'''


RETURN = r'''
#TO-DO
'''

import json
import time
import base64
from ansible.module_utils.basic import AnsibleModule, env_fallback
from ansible_collections.nutanix.nutanix.plugins.module_utils.nutanix_api_client import (
    NutanixApiClient,
    get_vm_uuid,
    get_vm,
    create_vm,
    update_vm,
    delete_vm,
    task_poll
)


CREATE_PAYLOAD = {
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
        pc_port=dict(default="9440", type='str', required=False),
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
        vm_uuid=dict(type='str', required=False),
        cpu=dict(type='int', required=True),
        vcpu=dict(type='int', required=True),
        memory=dict(type='int', required=True),
        cluster=dict(type='str', required=True),
        dry_run=dict(
            default=False,
            type='bool',
            required=False
        ),
        disk_list=dict(
            type='list',
            required=True,
            elements='dict',
            options=dict(
                clone_from_image=dict(
                    type='str'
                ),
                size_mib=dict(
                    type='int'
                ),
                device_type=dict(
                    type='str',
                    required=True,
                    choices=["DISK", "CDROM"]
                ),
                adapter_type=dict(
                    type='str',
                    required=True,
                    choices=["SCSI", "PCI", "SATA", "IDE"]
                )
            )
        ),
        nic_list=dict(
            type='list',
            required=True,
            elements='dict',
            options=dict(
                uuid=dict(
                    type='str',
                    required=True
                )
            )
        ),
        guest_customization=dict(
            type='dict',
            required=False,
            options=dict(
                cloud_init=dict(
                    type='str',
                    required=True
                ),
                sysprep=dict(
                    type='str',
                    required=True
                ),
                sysprep_install_type=dict(
                    type='str',
                    required=False,
                    choices=["FRESH", "PREPARED"]
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


def create_vm_spec(params, vm_spec):
    nic_list = []
    disk_list = []

    for nic in params['nic_list']:
        nic_list.append({
            "nic_type": "NORMAL_NIC",
            "vlan_mode": "ACCESS",
            "subnet_reference": {
                "kind": "subnet",
                "uuid": nic["uuid"]
            },
            "is_connected": True
        })

    scsi_counter = 0
    sata_counter = 0
    for disk in params['disk_list']:
        if disk["adapter_type"] == "SCSI":
            counter = scsi_counter
            scsi_counter += 1
        elif disk["adapter_type"] == "SATA":
            counter = sata_counter
            sata_counter += 1

        if "clone_from_image" in disk:
            disk_list.append({
                "device_properties": {
                    "disk_address": {
                        "device_index": counter,
                        "adapter_type": disk["adapter_type"]
                    },
                    "device_type": disk["device_type"]
                },
                "data_source_reference": {
                    "kind": "image",
                    "uuid": disk["clone_from_image"]
                }
            })
        else:
            disk_list.append({
                "device_properties": {
                    "disk_address": {
                        "device_index": counter,
                        "adapter_type": disk["adapter_type"]
                    },
                    "device_type": disk["device_type"]
                },
                "disk_size_mib": disk["size_mib"]
            })

    vm_spec["spec"]["name"] = params['name']
    vm_spec["spec"]["resources"]["num_sockets"] = params['cpu']
    vm_spec["spec"]["resources"]["num_vcpus_per_socket"] = params['vcpu']
    vm_spec["spec"]["resources"]["memory_size_mib"] = params['memory']
    vm_spec["spec"]["resources"]["power_state"] = "ON"
    vm_spec["spec"]["resources"]["nic_list"] = nic_list
    vm_spec["spec"]["resources"]["disk_list"] = disk_list

    if params["guest_customization"]:
        if "cloud_init" in params["guest_customization"]:
            cloud_init_encoded = base64.b64encode(
                params["guest_customization"]["cloud_init"].encode('ascii')
            )
            vm_spec["spec"]["resources"]["guest_customization"] = {
                "cloud_init": {
                    "user_data": cloud_init_encoded.decode('ascii')
                }
            }
        if "sysprep" in params["guest_customization"]:
            sysprep_init_encoded = base64.b64encode(
                params["guest_customization"]["sysprep"].encode('ascii')
            )
            vm_spec["spec"]["resources"]["guest_customization"] = {
                "sysprep": {
                    "install_type": params["guest_customization"]["sysprep_install_type"],
                    "unattend_xml": sysprep_init_encoded.decode('ascii')
                }
            }

    vm_spec["spec"]["cluster_reference"] = {"kind": "cluster", "uuid": params['cluster']}

    return vm_spec


def update_vm_spec(params, vm_data):

    nic_list = []
    disk_list = []
    guest_customization_cdrom = None
    vm_spec = vm_data["spec"]
    spec_nic_list = vm_spec["resources"]["nic_list"]
    spec_disk_list = vm_spec["resources"]["disk_list"]

    param_disk_list = params['disk_list']
    param_nic_list = params['nic_list']

    if params["guest_customization"]:
        if (
            "cloud_init" in params["guest_customization"] or
            "sysprep" in params["guest_customization"]
        ):
            guest_customization_cdrom = spec_disk_list.pop()

    scsi_counter = 0
    sata_counter = 0
    for i, disk in enumerate(param_disk_list):
        if disk["adapter_type"] == "SCSI":
            counter = scsi_counter
            scsi_counter += 1
        elif disk["adapter_type"] == "SATA":
            counter = sata_counter
            sata_counter += 1

        if "clone_from_image" in disk:
            try:
                spec_disk = spec_disk_list[i]
                disk_list.append(spec_disk)
            except IndexError:
                disk_list.append({
                    "device_properties": {
                        "disk_address": {
                            "device_index": counter,
                            "adapter_type": disk["adapter_type"]
                        },
                        "device_type": disk["device_type"]
                    },
                    "data_source_reference": {
                        "kind": "image",
                        "uuid": disk["clone_from_image"]
                    }
                })
        else:
            try:
                spec_disk = spec_disk_list[i]
                if spec_disk["disk_size_mib"] != disk["size_mib"]:
                    spec_disk["disk_size_mib"] = disk["size_mib"]
                disk_list.append(spec_disk)
            except IndexError:
                disk_list.append({
                    "device_properties": {
                        "disk_address": {
                            "device_index": counter,
                            "adapter_type": disk["adapter_type"]
                        },
                        "device_type": disk["device_type"]
                    },
                    "disk_size_mib": disk["size_mib"]
                })

    if guest_customization_cdrom:
        disk_list.append(guest_customization_cdrom)

    for i, nic in enumerate(param_nic_list):
        try:
            spec_nic = spec_nic_list[i]
            nic_list.append(spec_nic)
        except IndexError:
            nic_list.append({
                "nic_type": "NORMAL_NIC",
                "vlan_mode": "ACCESS",
                "subnet_reference": {
                    "kind": "subnet",
                    "uuid": nic["uuid"]
                },
                "is_connected": True
            })

    vm_data["spec"]["resources"]["num_sockets"] = params['cpu']
    vm_data["spec"]["resources"]["num_vcpus_per_socket"] = params['vcpu']
    vm_data["spec"]["resources"]["memory_size_mib"] = params['memory']
    vm_data["spec"]["resources"]["power_state"] = "ON"
    vm_data["spec"]["resources"]["nic_list"] = nic_list
    vm_data["spec"]["resources"]["disk_list"] = disk_list
    vm_data["metadata"]["spec_version"] += 1

    return vm_data


def _create(params, client):

    vm_uuid = None

    if "vm_uuid" in params:
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
    vm_spec = CREATE_PAYLOAD
    vm_spec = create_vm_spec(params, vm_spec)

    if params['dry_run'] is True:
        result["vm_spec"] = vm_spec
        return result

    # Create VM
    task_uuid, vm_uuid = create_vm(vm_spec, client)

    task_status = task_poll(task_uuid, client)
    if task_status:
        result["failed"] = True
        result["msg"] = task_status
        return result

    while True:
        response = client.request(api_endpoint="v3/vms/%s" % vm_uuid, method="GET", data=None)
        json_content = json.loads(response.content)
        if len(json_content["status"]["resources"]["nic_list"]) > 0:
            if len(json_content["status"]["resources"]["nic_list"][0]["ip_endpoint_list"]) > 0:
                if json_content["status"]["resources"]["nic_list"][0]["ip_endpoint_list"][0]["ip"] != "":
                    result["vm_status"] = json_content["status"]
                    result["vm_ip_address"] = json_content["status"]["resources"]["nic_list"][0]["ip_endpoint_list"][0]["ip"]
                    break
        time.sleep(5)

    result["vm_uuid"] = vm_uuid
    result["changed"] = True

    return result


def _update(params, client, vm_uuid=None):

    result = dict(
        changed=False,
        vm_spec={},
        updated_vm_spec={},
        task_uuid=''
    )

    if not vm_uuid:
        vm_uuid = get_vm_uuid(params, client)[0]

    vm_json = get_vm(vm_uuid, client)

    # Poweroff the VM
    if vm_json["status"]["resources"]["power_state"] == "ON":

        del vm_json["status"]
        vm_json["spec"]["resources"]["power_state"] = "OFF"
        vm_json["metadata"]["spec_version"] += 1

        task_uuid = update_vm(vm_uuid, vm_json, client)

        task_status = task_poll(task_uuid, client)
        if task_status:
            result["failed"] = True
            result["msg"] = task_status
            return result

        vm_json["metadata"]["entity_version"] = "%d" % (
            int(vm_json["metadata"]["entity_version"]) + 1
        )

    # Update the VM
    if "status" in vm_json:
        del vm_json["status"]
    updated_vm_spec = update_vm_spec(params, vm_json)
    updated_vm_spec["spec"]["resources"]["power_state"] = "ON"
    result["updated_vm_spec"] = updated_vm_spec

    if params['dry_run'] is True:
        return result

    task_uuid = update_vm(vm_uuid, updated_vm_spec, client)
    result["task_uuid"] = task_uuid

    task_status = task_poll(task_uuid, client)
    if task_status:
        result["failed"] = True
        result["msg"] = task_status
        return result

    result["changed"] = True

    return result


def _delete(params, client):

    vm_uuid = None

    if "vm_uuid" in params:
        vm_uuid = params["vm_uuid"]

    result = dict(
        changed=False,
        task_uuid='',
    )

    vm_uuid_list = get_vm_uuid(params, client)
    if len(vm_uuid_list) > 1 and not vm_uuid:
        result["failed"] = True
        result["msg"] = """Multiple Vm's with same name '%s' exists in the cluster.
            Specify vm_uuid of the VM you want to delete.""" % params["name"]
        result["vm_uuid"] = vm_uuid_list
        return result

    if not vm_uuid:
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


if __name__ == '__main__':
    main()
