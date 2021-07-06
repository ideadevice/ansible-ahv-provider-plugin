#
# Copyright: (c) 2021, Balu George <balu.george@nutanix.com>
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
    name: nutanix
    plugin_type: inventory
    short_description: Returns nutanix vms ansible inventory
    description: Returns nutanix vms ansible inventory
    options:
      plugin:
        description: Name of the plugin
        required: true
        choices: ['nutanix_vm_inventory', 'nutanix.nutanix.nutanix_vm_inventory']
      pc_hostname:
        description: PC hostname or IP address
        required: true
        type: str
        env:
         - name: PC_HOSTNAME
      pc_username:
        description: PC username
        required: true
        type: str
        env:
         - name: PC_USERNAME
      pc_password:
        description: PC password
        required: true
        type: str
        env:
         - name: PC_PASSWORD
      pc_port:
        description: PC port
        default: 9440
        type: str
        env:
         - name: PC_PORT
      validate_certs:
        description: Set to C(False) to ignore
        default: True
        type: boolean
        env:
         - name: VALIDATE_CERTS
'''

from ansible.plugins.inventory import BaseInventoryPlugin, Constructable, Cacheable
from ansible_collections.nutanix.nutanix.plugins.module_utils.nutanix_api_client import NutanixApiClient, NutanixApiError

class InventoryModule(BaseInventoryPlugin):
    NAME = 'nutanix.nutanix.nutanix_vm_inventory'

    def _create_client(self):
        self.client = NutanixApiClient(self.pc_hostname, self.pc_username, self.pc_password, self.pc_port, self.validate_certs)
        return self.client

    def _get_vm_list(self):
        client = self._create_client()
        vm_list_response = client.request(api_endpoint="v3/vms/list", method="POST", data='{"offset": 0, "length": 100}')
        return vm_list_response.json()

    def _build_inventory(self):
        vars_to_remove = ["disk_list", "vnuma_config", "nic_list", "power_state_mechanism", "host_reference",
                          "serial_port_list", "gpu_list", "storage_config", "boot_config", "guest_customization"]
        vm_list_resp = self._get_vm_list()

        for entity in vm_list_resp["entities"]:
            nic_count = 0
            cluster = entity["status"]["cluster_reference"]["name"]
            vm_name = entity["status"]["name"]
            vm_uuid = entity["metadata"]["uuid"]
            for nics in entity["status"]["resources"]["nic_list"]:
              if nics["nic_type"] == "NORMAL_NIC" and nic_count == 0:
                  for endpoint in nics["ip_endpoint_list"]:
                      if endpoint["type"] == "ASSIGNED":
                          vm_ip = endpoint["ip"]
                          nic_count += 1
                          continue
            # self.inventory.add_host(f"{vm_name}-{vm_uuid}")
            self.inventory.add_group(cluster)
            self.inventory.add_child('all', cluster)
            self.inventory.add_host(vm_name, group=cluster)
            self.inventory.set_variable(vm_name, 'ansible_host', vm_ip)
            self.inventory.set_variable(vm_name, 'uuid', vm_uuid)
            for var in vars_to_remove:
                try:
                    del entity["status"]["resources"][var]
                except:
                    pass
            for key, value in entity["status"]["resources"].items():
                self.inventory.set_variable(vm_name, key, value)

    def verify_file(self, path):
        valid = False
        if super(InventoryModule, self).verify_file(path):
            if path.endswith(('nutanix.yaml', 'nutanix.yml', 'nutanix_host_inventory.yaml', 'nutanix_host_inventory.yml')):
                valid = True
        return valid

    def parse(self, inventory, loader, path, cache):
        super(InventoryModule, self).parse(inventory, loader, path, cache)
        self._read_config_data(path)
        self.pc_hostname = self.get_option('pc_hostname')
        self.pc_username = self.get_option('pc_username')
        self.pc_password = self.get_option('pc_password')
        self.pc_port = self.get_option('pc_port')
        self.validate_certs = self.get_option('validate_certs')

        self._build_inventory()
