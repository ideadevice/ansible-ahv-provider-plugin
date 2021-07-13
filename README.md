# ansible-ahv-provider-plugin
Ansible plugins to interact with AHV APIs

# Building and installing the collection locally
```
ansible-galaxy collection build
ansible-galaxy collection install nutanix-nutanix-0.0.1.tar.gz
```
_Add `--force` option for rebuilding or reinstalling to overwrite existing data_

# Included modules
```
nutanix_image_info
nutanix_image
nutanix_vm_info
nutanix_vm
```

# Inventory plugin
`nutanix_vm_inventory`

# Module documentation and examples
```
ansible-doc nutanix.nutanix.<module_name>
```

# Examples
## Playbook to print name of vms in PC
```
- hosts: localhost
  collections:
  - nutanix.nutanix
  tasks:
  - nutanix_vm_info:
      pc_hostname: {{ pc_hostname }}
      pc_username: {{ pc_username }}
      pc_password: {{ pc_password }}
      validate_certs: False
    register: result
  - debug:
      msg: "{{ result.vms }}"
```
