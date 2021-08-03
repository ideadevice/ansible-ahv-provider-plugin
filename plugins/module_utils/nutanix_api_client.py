# -*- coding: utf-8 -*-
# Copyright: (c) 2021, Nutanix
# Copyright: (c) 2021, Balu George <balu.george@nutanix.com>

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import json
import traceback
import time
import uuid
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
        self.api_base = "https://{0}:{1}/api/nutanix".format(
            pc_hostname, pc_port)
        self.auth = (pc_username, pc_password)
        # Ensure that all deps are present
        self.check_dependencies()
        # Create session
        self.session = requests.Session()
        if not self.validate_certs:
            from urllib3.exceptions import InsecureRequestWarning
            requests.packages.urllib3.disable_warnings(
                category=InsecureRequestWarning)

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
            raise NutanixApiError("Request failed to complete, response code {0}, content {1}".format(
                response.status_code, response.content))

    def check_dependencies(self):
        if not HAS_REQUESTS:
            self.module.fail_json(
                msg=missing_required_lib('requests'),
                exception=REQUESTS_IMPORT_ERROR)


def task_poll(task_uuid, client):
    while True:
        response = client.request(
            api_endpoint="v3/tasks/{0}".format(task_uuid), method="GET", data=None)
        if response.json()["status"] == "SUCCEEDED":
            return None
        elif response.json()["status"] == "FAILED":
            error_out = response.json()["error_detail"]
            return error_out
        time.sleep(5)


def list_vms(filter, client):
    vm_list_response = client.request(
        api_endpoint="v3/vms/list", method="POST", data=json.dumps(filter))
    return vm_list_response.json()


def get_vm_uuid(params, client):
    length = 100
    offset = 0
    total_matches = 99999
    vm_name = params['name']
    vm_uuid = []
    while offset < total_matches:
        filter = {"filter": "vm_name=={0}".format(
            vm_name), "length": length, "offset": offset}
        vms_list = list_vms(filter, client)
        for vm in vms_list["entities"]:
            if vm["status"]["name"] == vm_name:
                vm_uuid.append(vm["metadata"]["uuid"])

        total_matches = vms_list["metadata"]["total_matches"]
        offset += length

    return vm_uuid


def get_vm(vm_uuid, client):
    get_virtual_machine = client.request(
        api_endpoint="v3/vms/{0}".format(vm_uuid), method="GET", data=None)
    return get_virtual_machine.json()


def create_vm(data, client):
    response = client.request(
        api_endpoint="v3/vms",
        method="POST",
        data=json.dumps(data)
    )
    json_content = response.json()
    return (
        json_content["status"]["execution_context"]["task_uuid"],
        json_content["metadata"]["uuid"]
    )


def update_vm(vm_uuid, data, client):
    response = client.request(
        api_endpoint="v3/vms/{0}".format(vm_uuid), method="PUT", data=json.dumps(data))
    return response.json()["status"]["execution_context"]["task_uuid"]


def delete_vm(vm_uuid, client):
    response = client.request(
        api_endpoint="v3/vms/{0}".format(vm_uuid), method="DELETE", data=None)
    return response.json()["status"]["execution_context"]["task_uuid"]


def list_images(filter, client):
    image_list_response = client.request(
        api_endpoint="v3/images/list", method="POST", data=json.dumps(filter))
    return image_list_response.json()


def get_image_uuid(image_name, client):
    length = 250
    offset = 0
    total_matches = 99999
    image_uuid = []
    while offset < total_matches:
        filter = {"filter": "name=={0}".format(
            image_name), "length": length, "offset": offset}
        image_list = list_images(filter, client)
        for subnet in image_list["entities"]:
            if subnet["status"]["name"] == image_name:
                image_uuid.append(subnet["metadata"]["uuid"])

        total_matches = image_list["metadata"]["total_matches"]
        offset += length

    return image_uuid


def get_image(image_uuid, client):
    get_image = client.request(
        api_endpoint="v3/images/{0}".format(image_uuid), method="GET", data=None)
    return get_image.json()


def create_image(data, client):
    response = client.request(
        api_endpoint="v3/images",
        method="POST",
        data=json.dumps(data)
    )
    json_content = response.json()
    return (
        json_content["status"]["execution_context"]["task_uuid"],
        json_content["metadata"]["uuid"]
    )


def update_image(image_uuid, data, client):
    response = client.request(
        api_endpoint="v3/images/{0}".format(image_uuid), method="PUT", data=json.dumps(data))
    return response.json()["status"]["execution_context"]["task_uuid"]


def delete_image(image_uuid, client):
    response = client.request(
        api_endpoint="v3/images/{0}".format(image_uuid), method="DELETE", data=None)
    return response.json()["status"]["execution_context"]["task_uuid"]


def list_clusters(filter, client):
    cluster_list_response = client.request(
        api_endpoint="v3/clusters/list", method="POST", data=json.dumps(filter))
    return cluster_list_response.json()


def get_cluster_uuid(cluster_name, client):
    length = 250
    offset = 0
    total_matches = 99999
    cluster_uuid = []
    while offset < total_matches:
        filter = {"filter": "name=={0}".format(
            cluster_name), "length": length, "offset": offset}
        cluster_list = list_clusters(filter, client)
        for cluster in cluster_list["entities"]:
            if cluster["status"]["name"] == cluster_name:
                cluster_uuid.append(cluster["metadata"]["uuid"])

        total_matches = cluster_list["metadata"]["total_matches"]
        offset += length

    return cluster_uuid


def list_subnets(filter, client):
    subnet_list_response = client.request(
        api_endpoint="v3/subnets/list", method="POST", data=json.dumps(filter))
    return subnet_list_response.json()


def get_subnet_uuid(subnet_name, client):
    length = 250
    offset = 0
    total_matches = 99999
    subnet_uuid = []
    while offset < total_matches:
        filter = {"filter": "name=={0}".format(
            subnet_name), "length": length, "offset": offset}
        subnet_list = list_subnets(filter, client)
        for subnet in subnet_list["entities"]:
            if subnet["status"]["name"] == subnet_name:
                subnet_uuid.append(subnet["metadata"]["uuid"])

        total_matches = subnet_list["metadata"]["total_matches"]
        offset += length

    return subnet_uuid


def is_uuid(UUID):
    try:
        uuid.UUID(UUID)
        return True
    except ValueError:
        return False
