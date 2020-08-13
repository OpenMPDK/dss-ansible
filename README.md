# deploy

Ansible automated deployment for DSS software

## Requirements

To deploy the cluster using Ansible, the host system must use Ansible version 2.9 or later.

To check the currently-installed version of ansible:
```
ansible --version
```

To install the latest version of ansible:
* Install pip:
```
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python3 get-pip.py
```
* Install ansible:
```
python3 -m pip install ansible
```

## Configure inventory

Add hosts to the inventory file `hosts` according to their group:
* servers
  * Hosts to deploy the co-located NKV target, host, and minio software package
* clients
  * Hosts to execute the NKV benchmark software against the server cluster
* onyx
  * Mellanox Onyx switch

Please consult the Ansible documentation, [How to build your inventory](https://docs.ansible.com/ansible/latest/user_guide/intro_inventory.html).

Ensure that SSH key authentication is configured for all hosts in your cluster. Please consult the Ansible documentation, [Connection details](https://docs.ansible.com/ansible/latest/user_guide/connection_details.html).

Note that Mellanox Onyx does not support key-based authentication. Therefore it is required to specify both `ansible_user` and `ansible_ssh_pass` for your Onyx switch.
It is recommended to use [Ansible vault](https://docs.ansible.com/ansible/latest/user_guide/playbooks_best_practices.html#best-practices-for-variables-and-vaults) to store your credentials.

### Inventory requirements

#### Server requirements

* Pre-deployed with CentOS version `7.4 1708`
  * Alternate versions of CentOS are supported but have not been 100% tested by the DSS team:
    - 7.5 1804
    - 7.6 1810
    - 7.7 1908
    - 7.8 2003
* Manangement NIC configured and accessible by the Ansible deployment host
* Manangement NIC has internet access
* Mellanox ConnectX-6 adapter(s) installed
  - ConnectX-4 and 5 also supported
* It is recommended for hostnames to be defined and contain a unique number between 1-255 at the end of the name
  - Example: `testhost01` (zero-padding not required)
  - This number will be used to configure the last octet of the IP addresses of all high-speed ConnectX adapters
  - If a unique number between 1-255 cannot be derived from the hostname, Ansible will automatically assign a unique inventory ID to be used instead
  - Alternatively, the last octet can be explicitly defined for each host using the `last_octet` host_var. Example inventory:
```
[servers]
hostname1.domain.com last_octet=12
hostname2.domain.com last_octet=13
```
  - The first three octets of each IP address of each VLAN, can be specified in `group_vars/all.yml`:
```
rocev2_vlans:
  - id: 31
    ip_prefix: 201.0.0
    netmask: 255.0.0.0
  - id: 32
    ip_prefix: 203.0.0
    netmask: 255.0.0.0
tcp_vlans:
  - id: 41
    ip_prefix: 202.0.0
    netmask: 255.0.0.0
  - id: 42
    ip_prefix: 204.0.0
    netmask: 255.0.0.0
```

* All ConnectX adapters intended to be used in the cluster must be connected to Onyx Switch (Status: `Up`):
```
# ibdev2netdev -v
0000:01:00.0 mlx5_0 (MT4123 - MCX653105A-HDAT) ConnectX-6 VPI adapter card, HDR IB (200Gb/s) and 200GbE, single-port QSFP56 fw 20.28.1002 port 1 (ACTIVE) ==> p5p1 (Up)
0000:41:00.0 mlx5_1 (MT4123 - MCX653105A-HDAT) ConnectX-6 VPI adapter card, HDR IB (200Gb/s) and 200GbE, single-port QSFP56 fw 20.28.1002 port 1 (ACTIVE) ==> p4p1 (Up)
0000:8f:00.0 mlx5_2 (MT4123 - MCX653105A-HDAT) ConnectX-6 VPI adapter card, HDR IB (200Gb/s) and 200GbE, single-port QSFP56 fw 20.28.1002 port 1 (ACTIVE) ==> p2p1 (Up)
0000:c4:00.0 mlx5_3 (MT4123 - MCX653105A-HDAT) ConnectX-6 VPI adapter card, HDR IB (200Gb/s) and 200GbE, single-port QSFP56 fw 20.28.1002 port 1 (ACTIVE) ==> p3p1 (Up)
```
* There must be a direct correlation of the number of ConnectX ports to the number of VLANs defined in `group_vars/all.yml`
  * By default, `num_vlans_per_port` is `1`, as defined in `group_vars/servers.yml` and `group_vars/clients.yml`
    * This would mean that there must be an equal number of ConnectX ports to VLANs defined in `group_vars/all.yml`
  * If `num_vlans_per_port` is set to `2` for example, then 2 ConnectX ports can be mapped to 4 total VLANs (`tcp_vlans` + `rocev2_vlans`)
  * Alternatively, the number of VLANs listed under `tcp_vlans` and `rocev2_vlans` can be reduced or increased to match the number of ConnectX ports for each group.


  - This value can be optionally changed in `group_vars/all.yml`
* Number of `Up` ConnectX-6 adapters, times `num_vlans_per_port` must be an even number
* Number of `Up` ConnectX-6 adapters, times `num_vlans_per_port` must match combined number of `rocev2_vlans` and `tcp_vlans` defined in `group_vars/all.yml`
* Samsung PM983 SSD's installed (Model: `SAMSUNG MZ4LB3T8HALS-00003`)
  - KVSSD model can be user-defined in `group_vars/all.yml`

#### Client requirements

* Pre-deployed with any x86_64 linux OS (Prefered: CentOS 7.4 1708)
* Hostnames pre-configured
* Manangement NIC configured and accessible by the Ansible deployment host

#### Onyx Switch requirements

* Onyx version 3.8.2306 preferred
* Administrator credentials for switch required
  - Note: Since ssh keys cannot be copied to Onyx switch, passkey will need to be used
  - Either provide `ansible_ssh_pass` var for `onyx` group in `hosts` (insecure) or use Ansible Vault <https://docs.ansible.com/ansible/latest/user_guide/vault.html>
* Note: Onyx ansible modules are not idempotent, and will report `changed` even if no changes are made

## Deploy

To deploy the cluster, use: `ansible-playbook deploy_all.yml`

Note that priviledged credentials are required. By default, `sudo` is used. If a password is required for `sudo`, it can be provided from the command line using the `-K` or `--ask-become-pass` flag. See <https://docs.ansible.com/ansible/latest/user_guide/become.html> for additional details.

## Reset

To remove VLANs, use `ansible-playbook reset_vlans.yml`

This will remove all VLAN configuration for all ConnectX adapters on all servers (including IP address assignment), as well as remove all allowed VLANs for each switchport each adapter is connected to. This is useful, for example, if you wish to alter your VLAN configuration if it has already been set.