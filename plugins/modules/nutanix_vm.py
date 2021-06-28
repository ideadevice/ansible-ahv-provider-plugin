#!/usr/bin/python

# Copyright: (c) 2021, Sarat Kumar <saratkumar.k@nutanix.com>
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
from ansible_collections.nutanix.nutanix.plugins.module_utils.nutanix_api_client import NutanixApiClient, NutanixApiError

async def main():
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
            "update"
            ]),
        guest_customization=dict(type='dict', required=False),
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
    client = NutanixApiClient(**module.params)
    result = await entry_point(module, client)
    module.exit_json(**result)

async def entry_point(module, client):

    if module.params["state"] == "present":
        operation = "create"
    elif module.params["state"] == "absent":
        operation = "delete"
    else:
        operation = module.params["state"]

    func = globals()["_" + operation]

    return await func(module.params, client)

async def _create(params, client):

    result = dict(
        changed=False,
        vm_uuid='',
        vm_ip_address='',
        vm_status={}
    )

    # Create VM Spec
    vm_spec = CREATE_PAYLOAD
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

async def _delete(params, client):

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

if __name__ == "__main__":
    import asyncio

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
