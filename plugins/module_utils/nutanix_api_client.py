# -*- coding: utf-8 -*-
# Copyright: (c) 2021, Nutanix
# Copyright: (c) 2021, Balu George <balu.george@nutanix.com>

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import json
import traceback
import time
from ansible.module_utils.basic import missing_required_lib

try:
    import requests
    import requests.exceptions
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    REQUESTS_IMPORT_ERROR = traceback.format_exc()


class NutanixApiError(Exception):
    pass


class NutanixApiClient(object):
    """Nutanix Rest API client"""
    def __init__(self, module):
        self.module = module
        pc_hostname = module.params["pc_hostname"]
        pc_username = module.params["pc_username"]
        pc_password = module.params["pc_password"]
        pc_port = module.params["pc_port"]
        self.validate_certs = module.params["validate_certs"]
        self.api_base = "https://{0}:{1}/api/nutanix".format(pc_hostname, pc_port)
        self.auth = (pc_username, pc_password)
        # Ensure that all deps are present
        self.check_dependencies()
        # Create session
        self.session = requests.Session()
        if not self.validate_certs:
            from urllib3.exceptions import InsecureRequestWarning
            requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

    def request(self, api_endpoint, method, data, timeout=20):
        self.api_url = "{0}/{1}".format(self.api_base, api_endpoint)
        headers = {'Content-Type': 'application/json',
                   'Accept': 'application/json'}
        try:
            response = self.session.request(method=method, url=self.api_url, auth=self.auth,
                                            data=data, headers=headers, verify=self.validate_certs, timeout=timeout)
        except requests.exceptions.RequestException as cerr:
            raise NutanixApiError("Request failed {0}".format(str(cerr)))

        if response.ok:
            return response
        else:
            raise NutanixApiError("Request failed to complete, response code {0}, content {1}".format(response.status_code, response.content))

    def check_dependencies(self):
        if not HAS_REQUESTS:
            self.module.fail_json(
                msg=missing_required_lib('requests'),
                exception=REQUESTS_IMPORT_ERROR)


def list_vms(filter, client):
    vm_list_response = client.request(
        api_endpoint="v3/vms/list", method="POST", data=json.dumps(filter))
    return json.loads(vm_list_response.content)


def get_vm_uuid(params, client):
    length = 100
    offset = 0
    total_matches = 99999
    vm_name = params['name']
    vm_uuid = []
    while offset < total_matches:
        filter = {"filter": "vm_name==%s" %
                  vm_name, "length": length, "offset": offset}
        vms_list = list_vms(filter, client)
        for vm in vms_list["entities"]:
            if vm["status"]["name"] == vm_name:
                vm_uuid.append(vm["metadata"]["uuid"])

        total_matches = vms_list["metadata"]["total_matches"]
        offset += length

    return vm_uuid


def get_vm(vm_uuid, client):
    get_virtual_machine = client.request(
        api_endpoint="v3/vms/%s" % vm_uuid, method="GET", data=None)
    return json.loads(get_virtual_machine.content)


def create_vm(data, client):
    response = client.request(
        api_endpoint="v3/vms",
        method="POST",
        data=json.dumps(data)
    )
    json_content = json.loads(response.content)
    return (
        json_content["status"]["execution_context"]["task_uuid"],
        json_content["metadata"]["uuid"]
    )


def update_vm(vm_uuid, data, client):
    response = client.request(api_endpoint="v3/vms/%s" %
                              vm_uuid, method="PUT", data=json.dumps(data))
    return json.loads(response.content)["status"]["execution_context"]["task_uuid"]


def delete_vm(vm_uuid, client):
    response = client.request(api_endpoint="v3/vms/%s" % vm_uuid, method="DELETE", data=None)
    return json.loads(response.content)["status"]["execution_context"]["task_uuid"]


def task_poll(task_uuid, client):
    while True:
        response = client.request(api_endpoint="v3/tasks/%s" % task_uuid, method="GET", data=None)
        if json.loads(response.content)["status"] == "SUCCEEDED":
            return None
        elif json.loads(response.content)["status"] == "FAILED":
            error_out = json.loads(response.content)["error_detail"]
            return error_out
        time.sleep(5)
