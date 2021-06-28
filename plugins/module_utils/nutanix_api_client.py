# -*- coding: utf-8 -*-
# Copyright: (c) 2021, Nutanix
# Copyright: (c) 2021, Balu George <balu.george@nutanix.com>

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import json

try:
    import requests
    import requests.exceptions
except Exception as e:
    raise Exception(f"Failed to import: {e}")


class NutanixApiError(Exception):
    pass

class NutanixApiClient(object):
    """Nutanix Rest API client"""
    def __init__(self, pc_hostname, pc_username, pc_password, pc_port, validate_certs, **kwargs):
        self.api_base = f"https://{pc_hostname}:{pc_port}/api/nutanix"
        self.auth = (pc_username, pc_password)
        self.validate_certs = validate_certs
        self.session = requests.Session()
        if not validate_certs:
            from urllib3.exceptions import InsecureRequestWarning
            requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

    def request(self, api_endpoint, method, data, timeout=20):
        self.api_url = f"{self.api_base}/{api_endpoint}"
        headers = {'Content-Type': 'application/json',  'Accept':'application/json'}
        try:
            response = self.session.request(method=method, url=self.api_url, auth=self.auth, data=data, headers=headers, verify=self.validate_certs, timeout=timeout)
        except requests.exceptions.RequestException as cerr:
            raise NutanixApiError(f"Request failed {str(cerr)}")

        if response.ok:
            return response
        else:
            raise NutanixApiError(f"Request failed to complete, response code {response.status_code}, content {response.content}")


async def list_vms(filter, client):
    vm_list_response = client.request(api_endpoint="v3/vms/list", method="POST", data=json.dumps(filter))
    return json.loads(vm_list_response.content)

async def get_vm_uuid(params, client):
    length = 2
    offset = 0
    total_matches = 1
    vm_name = params['name']
    filter = {"filter": "vm_name==%s" % vm_name }
    while offset < total_matches:
        vms_list = await list_vms(filter, client)
        for vm in vms_list["entities"]:
            if vm["status"]["name"] == vm_name:
                return vm["metadata"]["uuid"]

        total_matches = vms_list["total_matches"]
        offset += length
    return None


async def get_vm(vm_uuid, client):
    get_virtual_machine = client.request(api_endpoint="v3/vms/%s" % vm_uuid, method="GET", data=None)
    return json.loads(get_virtual_machine.content)

async def update_vm(vm_uuid, data, client):
    response = client.request(api_endpoint="v3/vms/%s" % vm_uuid, method="PUT", data=json.dumps(data))
    return json.loads(response.content)["status"]["execution_context"]["task_uuid"]
