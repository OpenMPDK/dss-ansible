# deploy

Ansible automated deployment for DSS software

## Requirements

To deploy the cluster using Ansible, the host system must use Ansible version 2.9 or later.

To check the currently-installed version of Ansible:
```
ansible --version
```

To install the latest version of Ansible:
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
* There is a direct relationship of the number of ConnectX ports to the number of VLANs defined in `group_vars/all.yml`
  * By default, `num_vlans_per_port` is `1`, as defined in `group_vars/servers.yml` and `group_vars/clients.yml`
    * This would mean that there must be an equal number of `Up` ConnectX ports to VLANs defined in `group_vars/all.yml`
  * If `num_vlans_per_port` is set to `2` for example, then 2 ConnectX ports can be mapped to 4 total VLANs (`tcp_vlans` + `rocev2_vlans`)
  * Alternatively, the number of VLANs listed under `tcp_vlans` and `rocev2_vlans` can be reduced or increased to match the number of ConnectX ports for each group.
  * Number of VLANS listed under `rocev2_vlans` must match the number of VLANS listed under `tcp_vlans`, defined in `group_vars/all.yml`
  * Number of `Up` ConnectX adapters, times `num_vlans_per_port` must match combined number of `rocev2_vlans` and `tcp_vlans` defined in `group_vars/all.yml`
* Samsung PM983 SSD's installed (Model: `SAMSUNG MZ4LB3T8HALS-00003`)
  - KVSSD model can be user-defined in `group_vars/all.yml`

#### Client requirements

* The client requirements are identical to server requirements, with the exception that only TCP VLANs are configured on clients
  * Note that it is required to leave the `combined_vlans: "{{ tcp_vlans }}"` setting as-is in `group_vars/clients.yml`

#### Onyx Switch requirements

* Onyx version must be 3.6.8130 or later
* Administrator credentials for switch are required
  - Note: Since ssh keys cannot be copied to Onyx switch, passkey will need to be used
  - Either provide `ansible_ssh_pass` var for `onyx` group in `hosts` (insecure) or use Ansible Vault <https://docs.ansible.com/ansible/latest/user_guide/vault.html>
* Note: Onyx ansible modules are not idempotent, and will report `changed` even if no changes are made

## Configure hosts

`ansible-playbook playbooks/configure_hosts.yml`

This playbook will automatically configure all hosts (clients + servers) and execute a number of roles including:
* validate_centos
* deploy_kernel
* configure_firewalld
* configure_tuned
* deploy_utils
* deploy_nvme_cli
* deploy_ofed
* load_mlnx_drivers
* configure_lldpad
* configure_dcqcn
* configure_irq
* upgrade_connectx_firmware

## Configure VLANs

`ansible-playbook playbooks/configure_vlans.yml`

This playbook will automatically configure the high-speed ConnectX adapters, as well as the Mellanox Onyx switch.
It will automatically assign IP addresses, VLANs, as well as a number of other performance configurations.

## Remove VLANS

`ansible-playbook playbooks/configure_vlans.yml`

This playbook will remove all VLAN configuration from the high-speed ConnectX adapters on all hosts (clients + servers) as well as the switch.
This is useful if you wish to change the VLAN configuration (change number of VLANs, change VLAN ID's, add or remove ConnectX ports, etc)

## Validate network

`ansible-playbook playbooks/test_network.yml`

This playbook will automatically validate the network configuration by performing the following tests:
* Ping all RoCEv2 endpoints between all servers
* Ping all TCP endpoitns between all servers and clients
* Perform ib_read_bw test between all servers and validate bandwidth is >= 90% of link speed

## Deploy DSS Software

`ansible-playbook playbooks/deploy_dss_software.yml`

This playbook will deploy the DSS target, host, and minio stack on all servers, as well as DSS benchmark software to all clients.
Upon successful deployment, the target, host, and minio services will be started and ready to test.

## Remove DSS Software

This playbook will stop and remove all DSS software from all hosts.

## Re-deploy DSS Software

`ansible-playbook playbooks/redeploy_dss_software.yml`

This playbook will stop and remove all DSS software from all hosts. Then DSS software will be deployed and started again.
This is useful to upgrade DSS software in place, or if you would like to re-deploy the software with new configuration settings.

## Restart DSS Software

`ansible-playbook playbooks/restart_dss_software.yml`

This playbook will stop all running DSS software in the target/host/minio stack, and restart all services, without making configuration changes.

## Reset DSS Software

`ansible-playbook playbooks/redeploy_dss_software.yml`

This playbook is the same as the above `redeploy_dss_software` playbook, with the exception that all KV SSD's on all servers will also be formated prior to re-deploying DSS software.
This is useful if the cluster storage subsystems are in a bad state, or you wish to re-deploy the cluster from a clean state.

## Cleanup DSS Minio

`ansible-playbook playbooks/redeploy_dss_minio.yml`

While the DSS software is up-and-running, this playbook will remove all objects from all Minio instances without the need to re-deploy or format the KVSSDs.

## Start DSS Benchmark

`ansible-playbook playbooks/start_dss_benchmark.yml`

This playbook will execute the DSS Benchmark from all clients against all servers in the cluster.

Benchmark results can be found on the client "master node" in `/var/logs/dss`

The client "master node" is the first client in the `hosts` inventory file
