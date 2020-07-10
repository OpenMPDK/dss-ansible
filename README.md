# facebook_deploy

Ansible automated deployment for Facebook Project

## Requirements

To deploy the cluster using Ansible, the host system must use Ansible version 2.9 or later.

## Configure

Add hosts to the inventory file `hosts` according to their group.

Ensure that SSH key authentication is configured for all hosts in your cluster. See <https://docs.ansible.com/ansible/latest/user_guide/connection_details.html> for details.

### Inventory requirements

#### Server requirements

* Pre-deployed with Supported version of CentOS:
  - 7.4 1708
  - 7.8 2003
* Hostnames pre-configured
* Manangement NIC configured and accessible by the Ansible deployment host
* Manangement NIC has internet access
* Mellanox ConnectX-6 adapter(s) installed
* Hostnames should be defined and contain a unique number between 1-255 at the end of the name
  - Example: `testhost01` (zero-padding not required)
  - This number will be used to configure IP addresses of all ConnectX-6 adapters (last octet)
  - If a unique number between 1-255 cannot be derived from the hostname, the Ansible inventory ID will be used instead
  - IP prefix, netmask and VLAN ID can be user-defined in `group_vars/servers.yml`
* ConnectX-6 adapters must be connected to Onyx Switch (Status: `up`)
* Number of `up` ConnectX-6 adapters must be an even number
* Number of `up` ConnectX-6 adapters must match combined number of `rocev2_vlans` and `tcp_vlans` defined in `group_vars/servers.yml`
* Samsung PM983 SSD's installed (Model: `SAMSUNG MZ4LB3T8HALS-00003`)
  - KVSSD model can be user-defined in `group_vars/servers.yml`

#### Client requirements

* Pre-deployed with any x86_64 linux OS (Prefered: CentOS 7.4 1708)
* Hostnames pre-configured
* Manangement NIC configured and accessible by the Ansible deployment host

## Deploy

To deploy the cluster, use: `ansible-playbook deploy_all.yml`

Note that priviledged credentials are required. By default, `sudo` is used. If a password is required for `sudo`, it can be provided from the command line using the `-K` or `--ask-become-pass` flag. See <https://docs.ansible.com/ansible/latest/user_guide/become.html> for additional details.
