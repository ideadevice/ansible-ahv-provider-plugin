#
# Copyright: (c) 2021, Balu George <balu.george@nutanix.com>
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
    name: nutanix_vm_inventory
    plugin_type: inventory
    short_description: Returns nutanix vms ansible inventory
    requirements:
    - requests
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

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

from ansible.errors import AnsibleError
from ansible.plugins.inventory import BaseInventoryPlugin

class InventoryModule(BaseInventoryPlugin):
    '''Nutanix VM dynamic invetory parser for ansible'''

    NAME = 'nutanix.nutanix.nutanix_vm_inventory'

    def __init__(self):
        super(InventoryModule, self).__init__()
        self.session = None

    def _get_create_session(self):
        '''Create session'''
        if not self.session:
            self.session = requests.Session()
            if not self.validate_certs:
                self.session.verify = self.validate_certs
                from urllib3.exceptions import InsecureRequestWarning
                requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

        return self.session

    def _get_vm_list(self):
        '''Get a list of existing VMs'''
        api_url = f"https://{self.pc_hostname}:{self.pc_port}/api/nutanix/v3/vms/list"
        auth = (self.pc_username, self.pc_password)
        headers = {'Content-Type': 'application/json',  'Accept':'application/json'}
        payload = '{"offset": 0, "length": 100}'

        session = self._get_create_session()
        vm_list_response = session.post(url=api_url, auth=auth, headers=headers, data=payload)

        return vm_list_response.json()

    def _build_inventory(self):
        '''Build inventory from API response'''
        vars_to_remove = ["disk_list", "vnuma_config", "nic_list", "power_state_mechanism", "host_reference",
                          "serial_port_list", "gpu_list", "storage_config", "boot_config", "guest_customization"]
        vm_list_resp = self._get_vm_list()

        for entity in vm_list_resp["entities"]:
            nic_count = 0
            cluster = entity["status"]["cluster_reference"]["name"]
            # self.inventory.add_host(f"{vm_name}-{vm_uuid}")
            vm_name = entity["status"]["name"]
            vm_uuid = entity["metadata"]["uuid"]

            # Get VM IP
            for nics in entity["status"]["resources"]["nic_list"]:
              if nics["nic_type"] == "NORMAL_NIC" and nic_count == 0:
                  for endpoint in nics["ip_endpoint_list"]:
                      if endpoint["type"] == "ASSIGNED":
                          vm_ip = endpoint["ip"]
                          nic_count += 1
                          continue

            # Add inventory groups and hosts to inventory groups
            self.inventory.add_group(cluster)
            self.inventory.add_child('all', cluster)
            self.inventory.add_host(vm_name, group=cluster)
            self.inventory.set_variable(vm_name, 'ansible_host', vm_ip)
            self.inventory.set_variable(vm_name, 'uuid', vm_uuid)

            # Add hostvars
            for var in vars_to_remove:
                try:
                    del entity["status"]["resources"][var]
                except:
                    pass
            for key, value in entity["status"]["resources"].items():
                self.inventory.set_variable(vm_name, key, value)

    def verify_file(self, path):
        '''Verify inventory configuration file'''
        valid = False
        if super(InventoryModule, self).verify_file(path):
            if path.endswith(('nutanix.yaml', 'nutanix.yml', 'nutanix_host_inventory.yaml', 'nutanix_host_inventory.yml')):
                valid = True
        return valid

    def parse(self, inventory, loader, path, cache):
        '''Parse inventory'''
        if not HAS_REQUESTS:
            raise AnsibleError("Missing python 'requests' package")

        super(InventoryModule, self).parse(inventory, loader, path, cache)
        self._read_config_data(path)

        self.pc_hostname = self.get_option('pc_hostname')
        self.pc_username = self.get_option('pc_username')
        self.pc_password = self.get_option('pc_password')
        self.pc_port = self.get_option('pc_port')
        self.validate_certs = self.get_option('validate_certs')

        self._build_inventory()
