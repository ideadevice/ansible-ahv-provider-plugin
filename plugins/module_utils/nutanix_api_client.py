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

length = 250


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
            self.module.fail_json("Request failed {0}".format(str(cerr)))

        if response.ok:
            return response
        else:
            self.module.fail_json("Request failed to complete, response code {0}, content {1}".format(
                response.status_code, response.content))

    def check_dependencies(self):
        if not HAS_REQUESTS:
            self.module.fail_json(
                msg=missing_required_lib('requests'),
                exception=REQUESTS_IMPORT_ERROR)


def task_poll(task_uuid, client):
    """
    This routine helps to poll given task and check if task is SUCCEEDED or FAILED
    Args:
        task_uuid(str): task uuid
        client(obj): Rest client obj
    Returns:
        Returns None in-case of SUCCESS else error_output incase of FAILURE
    """
    while True:
        response = client.request(
            api_endpoint="v3/tasks/{0}".format(task_uuid), method="GET", data=None)
        if response.json()["status"] == "SUCCEEDED":
            return None
        elif response.json()["status"] == "FAILED":
            error_out = response.json()["error_detail"]
            return error_out
        time.sleep(10)


def list_entities(api, filter, client):
    """
    This routine helps to list entities of a given api resource name and filter
    Args:
        api(str): api resource name
        filter(dict): filter payload
        client(obj): Rest client obj
    Returns:
        response.json()(dict): json object response
    """
    response = client.request(
        api_endpoint="v3/{0}/list".format(api), method="POST", data=json.dumps(filter))
    return response.json()


def get_vm_uuid(params, client):
    """
    This routine helps to get vm uuid list of given name
    Args:
        params(obj): ansible params object
        client(obj): Rest client obj
    Returns:
        vm_uuid(list): List of vm uuid's of given name
    """
    offset = 0
    total_matches = 99999
    vm_name = params['name']
    vm_uuid = []
    while offset < total_matches:
        filter = {"filter": "vm_name=={0}".format(
            vm_name), "length": length, "offset": offset}
        vms_list = list_entities('vms', filter, client)
        for vm in vms_list["entities"]:
            if vm["status"]["name"] == vm_name:
                vm_uuid.append(vm["metadata"]["uuid"])

        total_matches = vms_list["metadata"]["total_matches"]
        offset += length

    return vm_uuid


def get_vm(vm_uuid, client):
    """
    This routine helps to get vm spec
    Args:
        vm_uuid(str): vm uuid
        client(obj): Rest client obj
    Returns:
        get_virtual_machine.json()(dict): vm json object
    """
    get_virtual_machine = client.request(
        api_endpoint="v3/vms/{0}".format(vm_uuid), method="GET", data=None)
    return get_virtual_machine.json()


def create_vm(data, client):
    """
    This routine helps to create vm
    Args:
        data(dict): vm payload data
        client(obj): Rest client obj
    Returns:
        task_uuid(str): task uuid
        image_uuid(str): image uuid
    """
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
    """
    This routine helps to update vm
    Args:
        vm_uuid(str): vm uuid
        data(dict): image payload data
        client(obj): Rest client obj
    Returns:
        task_uuid(str): task uuid
    """
    response = client.request(
        api_endpoint="v3/vms/{0}".format(vm_uuid), method="PUT", data=json.dumps(data))
    return response.json()["status"]["execution_context"]["task_uuid"]


def delete_vm(vm_uuid, client):
    """
    This routine helps to delete vm
    Args:
        vm_uuid(str): vm uuid
        client(obj): Rest client obj
    Returns:
        task_uuid(str): task uuid
    """
    response = client.request(
        api_endpoint="v3/vms/{0}".format(vm_uuid), method="DELETE", data=None)
    return response.json()["status"]["execution_context"]["task_uuid"]


def update_powerstate_vm(vm_uuid, client, mechanism, power_state):
    """
    This routine helps update vm power state
    Args:
        vm_uuid(str): image name
        client(obj): Rest client obj
        mechanism(str): power state mechanism
        power_state(str): power state
    Returns:
        power_state(method): update vm
    """
    data = get_vm(vm_uuid, client)

    if "status" in data:
        del data["status"]

    data["spec"]["resources"]["power_state"] = power_state

    if "power_state_mechanism" in data["spec"]["resources"]:
        data["spec"]["resources"]["power_state_mechanism"]["mechanism"] = mechanism
    else:
        data["spec"]["resources"] = {
            "power_state_mechanism": {
                "mechanism": mechanism
            }
        }

    return update_vm(vm_uuid, data, client)


def get_image_uuid(image_name, client):
    """
    This routine helps to get image uuid list of given name
    Args:
        image_name(str): image name
        client(obj): Rest client obj
    Returns:
        image_uuid(list): List of image uuid's of given name
    """
    offset = 0
    total_matches = 99999
    image_uuid = []
    while offset < total_matches:
        filter = {"filter": "name=={0}".format(
            image_name), "length": length, "offset": offset}
        image_list = list_entities('images', filter, client)
        for subnet in image_list["entities"]:
            if subnet["status"]["name"] == image_name:
                image_uuid.append(subnet["metadata"]["uuid"])

        total_matches = image_list["metadata"]["total_matches"]
        offset += length

    return image_uuid


def get_image(image_uuid, client):
    """
    This routine helps to get image spec
    Args:
        image_uuid(str): image uuid
        client(obj): Rest client obj
    Returns:
        get_image.json()(dict): image json object
    """
    get_image = client.request(
        api_endpoint="v3/images/{0}".format(image_uuid), method="GET", data=None)
    return get_image.json()


def create_image(data, client):
    """
    This routine helps to create image
    Args:
        data(dict): image payload data
        client(obj): Rest client obj
    Returns:
        task_uuid(str): task uuid
        image_uuid(str): image uuid
    """
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
    """
    This routine helps to update image
    Args:
        image_uuid(str): image uuid
        data(dict): image payload data
        client(obj): Rest client obj
    Returns:
        task_uuid(str): task uuid
    """
    response = client.request(
        api_endpoint="v3/images/{0}".format(image_uuid), method="PUT", data=json.dumps(data))
    return response.json()["status"]["execution_context"]["task_uuid"]


def delete_image(image_uuid, client):
    """
    This routine helps to delete image
    Args:
        image_uuid(str): image uuid
        client(obj): Rest client obj
    Returns:
        task_uuid(str): task uuid
    """
    response = client.request(
        api_endpoint="v3/images/{0}".format(image_uuid), method="DELETE", data=None)
    return response.json()["status"]["execution_context"]["task_uuid"]


def get_cluster_uuid(cluster_name, client):
    """
    This routine helps to get cluster uuid list using given name
    Args:
        cluster_name(str): cluster name
        client(obj): Rest client obj
    Returns:
        cluster_uuid(list): List of Cluster uuid's of given name
    """
    offset = 0
    total_matches = 99999
    cluster_uuid = []
    while offset < total_matches:
        filter = {"filter": "name=={0}".format(
            cluster_name), "length": length, "offset": offset}
        cluster_list = list_entities('clusters', filter, client)
        for cluster in cluster_list["entities"]:
            if cluster["status"]["name"] == cluster_name:
                cluster_uuid.append(cluster["metadata"]["uuid"])

        total_matches = cluster_list["metadata"]["total_matches"]
        offset += length

    return cluster_uuid


def get_subnet(subnet_uuid, client):
    get_subnet = client.request(
        api_endpoint="v3/subnets/{0}".format(subnet_uuid), method="GET", data=None)
    return get_subnet.json()


def get_subnet_uuid(subnet_name, client):
    """
    This routine helps to get subnet uuid list using given name
    Args:
        subnet_name(str): Subnet name
        client(obj): Rest client obj
    Returns:
        subnet_uuid(list): List of Subnet uuid's of given name
    """
    offset = 0
    total_matches = 99999
    subnet_uuid = []
    while offset < total_matches:
        filter = {"filter": "name=={0}".format(
            subnet_name), "length": length, "offset": offset}
        subnet_list = list_entities('subnets', filter, client)
        for subnet in subnet_list["entities"]:
            if subnet["status"]["name"] == subnet_name:
                subnet_uuid.append(subnet["metadata"]["uuid"])

        total_matches = subnet_list["metadata"]["total_matches"]
        offset += length

    return subnet_uuid


def create_subnet(data, client):
    response = client.request(
        api_endpoint="v3/subnets",
        method="POST",
        data=json.dumps(data)
    )
    json_content = response.json()
    return (
        json_content["status"]["execution_context"]["task_uuid"],
        json_content["metadata"]["uuid"]
    )


def update_subnet(vm_uuid, data, client):
    response = client.request(
        api_endpoint="v3/subnets/{0}".format(vm_uuid), method="PUT", data=json.dumps(data))
    return response.json()["status"]["execution_context"]["task_uuid"]


def delete_subnet(vm_uuid, client):
    response = client.request(
        api_endpoint="v3/subnets/{0}".format(vm_uuid), method="DELETE", data=None)
    return response.json()["status"]["execution_context"]["task_uuid"]


def groups_call(filter, client):
    """
    Groups rest call
    Args:
        filter(dict): Filter payload
        client(obj): Rest client obj
    Returns:
        groups_response.json()(dict): json response
    """
    groups_response = client.request(
        api_endpoint="v3/groups", method="POST", data=json.dumps(filter))
    return groups_response.json()


def get_cluster_storage_container_map(storage_container_name, client):
    """
    This routine helps to create map of cluster_uuid : storage_container_uuid
    Args:
        storage_container_name(str): Storage container name
        client(obj): Rest client obj
    Returns:
        cluster_sc_map(dict): map of cluster_uuid : storage_container_uuid
    """
    offset = 0
    total_matches = 99999
    cluster_sc_map = {}
    while offset < total_matches:
        filter = {
            "entity_type": "storage_container",
            "group_member_attributes": [
                {
                    "attribute": "cluster"
                },
                {
                    "attribute": "container_name"
                }
            ],
            "group_member_count": length,
            "group_member_offset": offset
        }
        sc_list = groups_call(filter, client)
        for sc in sc_list["group_results"][0]["entity_results"]:
            for attribute in sc["data"]:
                if attribute["name"] == "container_name":
                    sc_name = attribute["values"][0]["values"][0]
                if attribute["name"] == "cluster":
                    cluster = attribute["values"][0]["values"][0]
                entity_id = sc["entity_id"]

            if sc_name == storage_container_name:
                cluster_sc_map[cluster] = entity_id

        total_matches = sc_list["total_entity_count"]
        offset += length

    return cluster_sc_map


def get_cluster_vswitch_uuid(vswitch_name, cluster_uuid, client):
    length = 250
    offset = 0
    total_matches = 99999
    cluster_vs_map = {}
    while offset < total_matches:
        filter = {
            "entity_type": "distributed_virtual_switch",
            "group_member_attributes": [
                {
                    "attribute": "name"
                },
                {
                    "attribute": "cluster_configuration_list.cluster_uuid"
                },
                {
                    "attribute": "default"
                }
            ],
            "group_member_count": length,
            "group_member_offset": offset,
            "filter_criteria": "cluster_configuration_list.cluster_uuid=cs={0}".format(cluster_uuid)
        }
        vs_list = groups_call(filter, client)
        for vs in vs_list["group_results"][0]["entity_results"]:
            for attribute in vs["data"]:
                if attribute["name"] == "name":
                    sc_name = attribute["values"][0]["values"][0]
                if attribute["name"] == "cluster_configuration_list.cluster_uuid":
                    cluster = attribute["values"][0]["values"][0]
                entity_id = vs["entity_id"]

            if sc_name == vswitch_name:
                cluster_vs_map[cluster] = entity_id

        total_matches = vs_list["total_entity_count"]
        offset += length

    return cluster_vs_map


def is_uuid(UUID):
    """
    This routine helps to determine given UUID is a valid uuid or not
    Args:
        UUID(str): UUID string
    Returns:
        (bool): returns True/False
    """
    try:
        uuid.UUID(UUID)
        return True
    except ValueError:
        return False


def set_payload_keys(params, payload_format, payload):
    """
    This routine helps to create dict from ansible input values. ignoring all the null values
    Args:
        params(obj): Ansible input object
        payload_format(dict): Reference dict
        payload(dict): Sets payload dict based on given params
    Returns:
        payload(dict): returns final dict after setting all the params
    """
    if type(params) is str or type(params) is int:
        return params
    else:
        for i in payload_format.keys():
            if params[i] is None:
                continue
            elif type(params[i]) is dict:
                payload[i] = set_payload_keys(params[i], payload_format[i], {})
            elif type(params[i]) is list:
                payload[i] = []
                for item in params[i]:
                    payload[i].append(set_payload_keys(item, payload_format[i][0], {}))
            elif type(params[i]) is str or type(params[i]) is int:
                payload[i] = params[i]
        return payload


def has_changed(source_payload, destination_payload):
    """
    This routine helps to compare 2 objects and find for differences.
    Args:
        source_payload(dict): Source payload dict
        destination_payload(dict): Destination payload dict
    Returns:
        status(bool): returns bool value after comparision
    """
    status = False
    if type(source_payload) is str or type(source_payload) is int:
        if source_payload != destination_payload:
            return True
    else:
        for key in source_payload.keys():
            if type(source_payload[key]) is dict:
                try:
                    status = has_changed(source_payload[key], destination_payload[key])
                except KeyError:
                    status = True
            elif type(source_payload[key]) is list:
                for i, item in enumerate(source_payload[key]):
                    try:
                        status = has_changed(item, destination_payload[key][i])
                    except IndexError:
                        status = True
            elif type(source_payload[key]) is str or type(source_payload[key]) is int:
                try:
                    if source_payload[key] != destination_payload[key]:
                        return True
                except KeyError:
                    return True

            if status:
                return status
    return status


def read_file(filename):
    """
    This routine helps to read the given file
    Args:
        filename(str): name of the file to be read
    Returns:
        f.read()(byte): byte string
    """
    with open(filename, "r", encoding='utf-8') as f:
        return f.read()
