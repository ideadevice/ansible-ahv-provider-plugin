#!/usr/bin/python

# Copyright: (c) 2021, Sarat Kumar <saratkumar.k@nutanix.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

DOCUMENTATION = r'''
---
module: nutanix_vm_create

short_description: VM Operations module

version_added: "0.0.1"

description: This module takes in VM parameters and does VM operations.

options:

# TO-DO
'''

EXAMPLES = r'''
#TO-DO
'''


RETURN = r'''
#TO-DO
'''

# This structure describes the format of the data expected by the end-points

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

import json
import time
import base64
from ansible.module_utils.basic import AnsibleModule, env_fallback
from ansible_collections.nutanix.nutanix.plugins.module_utils.nutanix_api_client import (
    NutanixApiClient,
    get_vm_uuid,
    get_vm,
    update_vm
)

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
        name=dict(type='str', required=True),
        vm_uuid=dict(type='str', required=False),
        cpu=dict(type='int', required=True),
        vcpu=dict(type='int', required=True),
        memory=dict(type='int', required=True),
        cluster_uuid=dict(type='str', required=True),
        dry_run=dict(type='bool', required=False),
        disk_list=dict(
            type='list',
            required=True,
            data_source_uuid=dict(
                type='str'
            ),
            size_mib=dict(
                type='int'
            ),
            device_type=dict(
                type='str', required=True,
                choices= ["DISK", "CDROM"]
            ),
            adapter_type=dict(
                type='str', required=True,
                choices= ["SCSI", "PCI", "SATA", "IDE"]
            )
        ),
        nic_list=dict(
            type='list',
            required=True,
            uuid=dict(
                type='str',
                required=True
            )
        ),
        state=dict(
            default="present",
            type='str',
            choices=[
            "present",
            "absent",
            "poweron",
            "poweroff"
            ]),
        guest_customization=dict(
            type='dict', required=False,
            cloud_init=dict(
                type='str', 
                required=True
                ),
            sysprep=dict(
                type='str', 
                required=True
                ),
        ),
        force_update=dict(default=False, type='bool', required=False),
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

def create_vm_spec(params, vm_spec, client):
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

    scsi_counter=0
    sata_counter=0
    for disk in params['disk_list']:
        if disk["adapter_type"] == "SCSI":
            counter = scsi_counter
            scsi_counter+=1
        elif disk["adapter_type"] == "SATA":
            counter = sata_counter
            sata_counter+=1

        if "data_source_uuid" in disk:
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
                "uuid": disk["data_source_uuid"]
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
            cloud_init_encoded = base64.b64encode(params["guest_customization"]["cloud_init"].encode('ascii'))
            vm_spec["spec"]["resources"]["guest_customization"] = {
                    "cloud_init": {
                        "user_data" : cloud_init_encoded.decode('ascii')
                        }
                }


    vm_spec["spec"]["cluster_reference"] = { "kind": "cluster", "uuid": params['cluster_uuid'] }

    return vm_spec

def update_vm_spec(params, vm, client):

    nic_list = []
    disk_list = []
    vm_spec = vm["spec"]
    spec_nic_list = vm_spec["resources"]["nic_list"]
    spec_disk_list = vm_spec["resources"]["disk_list"]

    param_disk_list = params['disk_list']
    param_nic_list = params['nic_list']

    scsi_counter=0
    sata_counter=0
    for i in range(len(param_disk_list)):
        disk = param_disk_list[i]
        if disk["adapter_type"] == "SCSI":
            counter = scsi_counter
            scsi_counter+=1
        elif disk["adapter_type"] == "SATA":
            counter = sata_counter
            sata_counter+=1

        if "data_source_uuid" in disk:
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
                    "uuid": disk["data_source_uuid"]
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

    for i in range(len(param_nic_list)):
        try:
            spec_nic = spec_nic_list[i]
            nic_list.append(spec_nic)
        except IndexError:
            nic_list.append({
                "nic_type": "NORMAL_NIC",
                "vlan_mode": "ACCESS",
                "subnet_reference": {
                    "kind": "subnet",
                    "uuid": param_nic_list[i]["uuid"]
                },
                "is_connected": True
            })

    vm["spec"]["resources"]["num_sockets"] = params['cpu']
    vm["spec"]["resources"]["num_vcpus_per_socket"] = params['vcpu']
    vm["spec"]["resources"]["memory_size_mib"] = params['memory']
    vm["spec"]["resources"]["power_state"] = "ON"
    vm["spec"]["resources"]["nic_list"] = nic_list
    vm["spec"]["resources"]["disk_list"] = disk_list
    vm["metadata"]["spec_version"] += 1

    return vm

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
        result["msg"] = "Multiple Vm's with same name '%s' exists in the cluster. please give different name or specify vm_uuid if you want to update vm" % params["name"]
        result["vm_uuid"] = vm_uuid_list
        return result
    elif len(vm_uuid_list) >= 1 or vm_uuid:
        return _update(params, client, vm_uuid=vm_uuid)
    

    # Create VM Spec
    vm_spec = CREATE_PAYLOAD
    vm_spec = create_vm_spec(params, vm_spec, client)

    if params["dry_run"] == True:
        result["vm_spec"] = vm_spec
        return result

    # Create VM
    response = client.request(api_endpoint="v3/vms" , method="POST", data=json.dumps(vm_spec))
    task_uuid = json.loads(response.content)["status"]["execution_context"]["task_uuid"]
    vm_uuid = json.loads(response.content)["metadata"]["uuid"]

    # Poll for task completion
    while True:
        response = client.request(api_endpoint="v3/tasks/%s" % task_uuid, method="GET", data=None)
        if json.loads(response.content)["status"] == "SUCCEEDED":
            break
        elif json.loads(response.content)["status"] == "FAILED":
            result["failed"] = True
            result["msg"] = json.loads(response.content)["error_detail"]
            return result
        time.sleep(5)

    while True:
        response = client.request(api_endpoint="v3/vms/%s" % vm_uuid, method="GET", data=None)
        if len(json.loads(response.content)["status"]["resources"]["nic_list"]) > 0:
            if len(json.loads(response.content)["status"]["resources"]["nic_list"][0]["ip_endpoint_list"]) > 0:
                if json.loads(response.content)["status"]["resources"]["nic_list"][0]["ip_endpoint_list"][0]["ip"] != "":
                    result["vm_status"] = json.loads(response.content)["status"]
                    result["vm_ip_address"] = json.loads(response.content)["status"]["resources"]["nic_list"][0]["ip_endpoint_list"][0]["ip"]
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
        task_uuid = ''
    )

    if not vm_uuid:
        vm_uuid = get_vm_uuid(params, client)[0]

    """if not vm_uuid:
        result["failed"] = True
        result["msg"] = "Vm '%s' doesnot exists in the Cluster." % params["name"]
        return result"""

    vm_json = get_vm(vm_uuid, client)

    # Poweroff the VM
    if vm_json["status"]["resources"]["power_state"] == "ON":

        del vm_json["status"]
        vm_json["spec"]["resources"]["power_state"] = "OFF"
        vm_json["metadata"]["spec_version"] += 1

        task_uuid = update_vm(vm_uuid, vm_json, client)

        # Poll for task completion
        while True:
            response = client.request(api_endpoint="v3/tasks/%s" % task_uuid, method="GET", data=None)
            if json.loads(response.content)["status"] == "SUCCEEDED":
                break
            elif json.loads(response.content)["status"] == "FAILED":
                result["failed"] = True
                result["msg"] = json.loads(response.content)["error_detail"]
                return result
            time.sleep(5)
        vm_json["metadata"]["entity_version"] = "%d"% (int(vm_json["metadata"]["entity_version"]) + 1)

    # Update the VM
    if "status" in vm_json:
        del vm_json["status"]
    updated_vm_spec = update_vm_spec(params, vm_json, client)
    updated_vm_spec["spec"]["resources"]["power_state"] = "ON"
    result["updated_vm_spec"] = updated_vm_spec

    task_uuid = update_vm(vm_uuid, updated_vm_spec, client)
    result["task_uuid"] = task_uuid
    result["changed"] = True

    # Poll for task completion
    while True:
        response = client.request(api_endpoint="v3/tasks/%s" % task_uuid, method="GET", data=None)
        if json.loads(response.content)["status"] == "SUCCEEDED":
            break
        elif json.loads(response.content)["status"] == "FAILED":
            result["failed"] = True
            result["msg"] = json.loads(response.content)["error_detail"]
            return result
        time.sleep(5)

    return result

def _delete(params, client):

    vm_uuid = ''

    result = dict(
        changed=False,
        task_uuid='',
    )

    data = {"filter": "vm_name==%s" % params["name"] }
    response = client.request(api_endpoint="v3/vms/list", method="POST", data=json.dumps(data))
    for entity in json.loads(response.content)["entities"]:
        if entity["status"]["name"] == params["name"]:
            vm_uuid = entity["metadata"]["uuid"]

    if vm_uuid == "":
        result["failed"] = True
        result["msg"] = "Vm '%s' doesnot exists in the Cluster." % params["name"]
        return result

    # Delete VM
    response = client.request(api_endpoint="v3/vms/%s" % vm_uuid, method="DELETE", data=None)
    task_uuid = json.loads(response.content)["status"]["execution_context"]["task_uuid"]

    result["task_uuid"] = task_uuid
    result["changed"] = True

    # Poll for task completion
    while True:
        response = client.request(api_endpoint="v3/tasks/%s" % task_uuid, method="GET", data=None)
        if json.loads(response.content)["status"] == "SUCCEEDED":
            break
        elif json.loads(response.content)["status"] == "FAILED":
            result["failed"] = True
            result["msg"] = json.loads(response.content)["error_detail"]
            return result
        time.sleep(5)

    return result

if __name__ == '__main__':
    main()
