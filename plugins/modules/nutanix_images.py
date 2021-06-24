#!/usr/bin/python

# Copyright: (c) 2021, Balu George <balu.george@nutanix.com>
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: nutanix_images

short_description: images module which supports image crud operations

version_added: "0.0.1"

description:

##TO-DO
author:
    - Balu George (@balugeorge)
'''

EXAMPLES = r'''
## TO-DO
'''

RETURN = r'''
## TO-DO
'''

import json
import copy
import time
from ansible.module_utils.basic import env_fallback
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.nutanix.nutanix.plugins.module_utils.nutanix_api_client import NutanixApiClient, NutanixApiError


def generate_argument_spec():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        pc_hostname=dict(type='str', required=True, fallback=(env_fallback, ["PC_HOSTNAME"])),
        pc_username=dict(type='str', required=True, fallback=(env_fallback, ["PC_USERNAME"])),
        pc_password=dict(type='str', required=True, no_log=True, fallback=(env_fallback, ["PC_PASSWORD"])),
        pc_port=dict(default="9440", type='str', required=False),
        image_details=dict(type='list', required=True),
        state=dict(default='present', type='str'),
        data=dict(default="{}", type='str', required=False),
        validate_certs=dict(default=True, type='bool', required=False),
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    # return initial result dict for dry run without execution
    if module.check_mode:
        module.exit_json(**result)

    return module

def create_images(module, client, result):
    batch_spec = {
        "action_on_failure": "CONTINUE",
        "execution_order": "NON_SEQUENTIAL",
        "api_request_list":
        [],
        "api_version": "3.0"
    }

    image_spec = {
        "operation": "POST",
        "path_and_params": "/api/nutanix/v3/images",
        "body":
            {
                "spec":
                {
                    "name": "",
                    "resources":
                    {
                        "image_type": "",
                        "source_uri": ""
                    }
                },
                "metadata":
                {
                    "kind": "image"
                },
                "api_version": "3.1.0"
            }
    }

    image_details = module.params.get("image_details")
    task_uuid_list, image_list, created_image_list = [], [], []

    for image in image_details:
        api_image_spec = copy.deepcopy(image_spec)
        image_name = image.get("image_name")
        image_type = image.get("image_type")
        source_uri = image.get("source_uri")
        # api_image_spec['body']['spec']['name'] = image_name
        if image_name and image_type and source_uri:
            api_image_spec['body']['spec']['name'] = image_name
            api_image_spec['body']['spec']['resources']['image_type'] = image_type
            api_image_spec['body']['spec']['resources']['source_uri'] = source_uri
        batch_spec['api_request_list'].append(api_image_spec)

    # Create Images
    image_create_resp = client.request(api_endpoint="v3/batch", method="POST", data=json.dumps(batch_spec))

    # result["image_status"] = image_create_resp.json()
    result["changed"] = True
    result["msg"] = []

    # task_uuid_list = []
    for resp in image_create_resp.json()['api_response_list']:
        if resp['status'] == '202':
            image_list.append(resp['api_response']['spec']['name'])
            task_uuid_list.append(resp['api_response']['status']['execution_context']['task_uuid'])
        else:
            result["msg"].append(resp)
            result["failed"] = True

    if task_uuid_list:
        for task_uuid in task_uuid_list:
            tasks_state = None
            while tasks_state == None:
                task_resp = client.request(api_endpoint=f"v3/tasks/{task_uuid}", method="GET", data=None)
                if task_resp.json()["status"] == "SUCCEEDED":
                    created_image_list.append(image_list[task_uuid_list.index(task_uuid)])
                    tasks_state = "SUCCEEDED"
                elif task_resp.json()["status"] == "FAILED":
                    result["failed"] = True
                    result["msg"].append(task_resp.json()["error_detail"])
                    tasks_state = "FAILED"
                else:
                    time.sleep(5)
        if created_image_list:
            result["msg"].append(f"Created image(s): {created_image_list}")

    return result

def list_images(client):
    return client.request(api_endpoint="v3/images/list", method="POST", data='{"offset": 0, "length": 100}')

def main():
    # Seed result dict
    result_init = dict(
        changed=False,
        ansible_facts=dict(),
    )
    # Generate arg spec and call function
    arg_spec = generate_argument_spec()
    # Instantiate api client
    api_client = NutanixApiClient(**arg_spec.params)
    if arg_spec.params["state"] == "present":
        result = create_images(arg_spec, api_client, result_init)

    arg_spec.exit_json(**result)

if __name__ == '__main__':
    main()
