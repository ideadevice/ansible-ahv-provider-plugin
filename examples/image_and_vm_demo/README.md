# Image and VM demo instructions

## Prerequisites
- Make sure the Nutanix collection is installed using `ansible-galaxy collection install <nutanix collection tar.gz>`
- Go to `group_vars/all.yml` and modify following attributes according to your environment:
    - `cluster_uuid`: UUID of the PE where you want to deploy a new VM
    - `subnet_uuid`: UUID of the subnet where you want to deploy a new VM
    - `public_key_path`: Path to the public SSH key that needs to be passed to the VM cloud-init script
- (Optional) Remove the `ansible_python_interpreter` 
- Export following environment variables:
    - export PC_HOSTNAME=<hostname of your Prism Central instance>
    - export PC_USERNAME=<user that has access to your Prism Central instance>
    - export PC_PASSWORD=<password of the user that has access to your Prism Central instance>
    - export VALIDATE_CERTS=False
       ==> Set to True in case certification validation is required

## Steps
Run following commands to perform the demo:
- Upload image: `ansible-playbook 1_image_demo.yml --extra-vars="state=present"`
- Create VM: `ansible-playbook 2_vm_demo.yml --extra-vars="state=present"`
- Check the output of both playbooks since they contain interesting debug info

## Cleanup
Commands to remove all provisioned objects:
- `ansible-playbook 2_vm_demo.yml --extra-vars="state=absent"`
- `ansible-playbook 1_image_demo.yml --extra-vars="state=absent"`

