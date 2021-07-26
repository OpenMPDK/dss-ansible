# TESS on VM Tutorial

## Overview

Ansible automation for configuring systems and orchestrating deployment of TESS software.

## Pre-deployment

### VM Setup and Configuration

* ESXi 7.0.0 with Enterprise Plus or Evaluation license
* vCenter Server Appliance with Standard or Evaluation license

Suggested ESXi specifications:

        CPU: Intel(R) Xeon(R) CPU E5-2696 v4 @ 2.20GHz
        Cores: 22 cores per socket,
        CPU sockets: 2
        HyperThreading: Enabled
        Memory: 512G (DDR4)

Suggested ESXi storage:

        Minimum 1TB SSD for local datastore

Guest VM Specification:

        VM Hardware version: 17
        OS guest: CentOS 7.9
        CPU: 6 cores
        mem: 32 GB
        boot / OS disk: default
        boot disk controller: paravirtual
        management NIC (TCP): VMXnet3
        RDMA back-end NIC: PVRDMA
        data disk: 50GB+ thick provisioned
        data disk controller: Virtual NVMe

In guest OS:

* Configure IPs for management network (TCP) and back-end traffic (RDMA)
* Set MTU for PVRDMA interface to 9000
* Kernel 5.1 must have PVRDMA driver compiled (included in the bundle, automatically installed by Ansible)

For complete documentation for PVRDMA vSphere and guest VM configuration, please refer to VMware and Mellenox documentation.

<https://docs.vmware.com/en/VMware-vSphere/7.0/com.vmware.vsphere.networking.doc/GUID-4A5EBD44-FB1E-4A83-BB47-BBC65181E1C2.html>

<https://docs.mellanox.com/pages/releaseview.action?pageId=15055422>

### Ansible Host Setup

#### *Linux Packages*

On a linux host, install Ansible version 2.9.12 using python3. Do not use a package-manager version of Ansible.

     yum install -y python3
     curl <https://bootstrap.pypa.io/get-pip.py> -o get-pip.py
     python3 get-pip.py
     python3 -m pip install ansible==2.9.12

### Download Deployment Bundle

Download the deployment bundle to the Ansible host.

## VM Cluster Setup

Clusters with 4 and 10 VM nodes are supported, and have been tested.

### Enable Ansible SSH to Cluster

Ensure Ansible can access all VMs in the cluster.

#### *Add Ansible user*

A user should be provisioned on all hosts in the cluster with "NOPASSWD" sudo access.
Ansible will use this account for all automated configuration.
Alternatively, the root user can be used instead.

#### *Generate SSH key*

Generate SSH key on Ansible host, unless already generated.

        #ssh-keygen
        Generating public/private rsa key pair.
        Enter file in which to save the key (/home/ylo/.ssh/id_rsa):
        Enter passphrase (empty for no passphrase):
        Enter same passphrase again:
        Your identification has been saved in id_rsa.
        Your public key has been saved in id_rsa.pub.
        The key fingerprint is:
        SHA256:GKW7yzA1J1qkr1Cr9MhUwAbHbF2NrIPEgZXeOUOz3Us user@host
        The key's randomart image is:
        +---[RSA 2048]----+
        |.*++ o.o.        |
        |.+B + oo.        |
        | +++ *+.         |
        | .o.Oo.+E        |
        |    ++B.S.       |
        |   o * =.        |
        |  + = o          |
        | + = = .         |
        |  + o o          |
        +----[SHA256]-----+

#### *Copy key for ansible login*

Copy ssh key to each of the hosts using the shh-copy-id command.

        ssh-copy-id ansible@testhost01.domain.com

To copy keys to 10 hosts automatically:

        for i in {01..10}; do sshpass -p "ansible" ssh-copy-id -o StrictHostKeyChecking=no ansible@testhost${i}.domain.com; done

#### *Test cluster nodes for ansible login*

To confirm the ssh key copy, test if you can login to the hosts using ssh without the password.

### Prepare Inventory File

Configure an Ansible inventory file for the cluster.
Below is an example inventory file defining a cluster of 10 TESS servers, with one also used as a client.

        [servers]
        msl-ssg-vm11.msl.lab tcp_ip_list="['10.1.51.35']" rocev2_ip_list="['192.168.199.11']"
        msl-ssg-vm12.msl.lab tcp_ip_list="['10.1.51.38']" rocev2_ip_list="['192.168.199.12']"
        msl-ssg-vm13.msl.lab tcp_ip_list="['10.1.51.58']" rocev2_ip_list="['192.168.199.13']"
        msl-ssg-vm14.msl.lab tcp_ip_list="['10.1.51.24']" rocev2_ip_list="['192.168.199.14']"
        msl-ssg-vm15.msl.lab tcp_ip_list="['10.1.50.230']" rocev2_ip_list="['192.168.199.15']"
        msl-ssg-vm16.msl.lab tcp_ip_list="['10.1.50.235']" rocev2_ip_list="['192.168.199.16']"
        msl-ssg-vm17.msl.lab tcp_ip_list="['10.1.50.226']" rocev2_ip_list="['192.168.199.17']"
        msl-ssg-vm18.msl.lab tcp_ip_list="['10.1.50.227']" rocev2_ip_list="['192.168.199.18']"
        msl-ssg-vm19.msl.lab tcp_ip_list="['10.1.50.234']" rocev2_ip_list="['192.168.199.19']"
        msl-ssg-vm20.msl.lab tcp_ip_list="['10.1.50.232']" rocev2_ip_list="['192.168.199.20']"
        [clients]
        msl-ssg-vm11.msl.lab
        [all:vars]
        ansible_user=ansible
        target_fw_version=1.0
        dss_target_mode=kv_block_vm
        minio_ec_block_size=524288

## Install and Start DSS Software Stack

### First time Deployment

* Configure VMs

    ```ansible-playbook -i your_inventory playbooks/configure_vms.yml```

* Deploy TESS:  Deploy and start TESS software stack

    ```ansible-playbook -i your_inventory playbooks/deploy_dss_software.yml```

### Complete Playbook documentation

#### playbooks/cleanup_dss_ai_benchmark.yml

NOTE: For internal Samsung / DSS use! Unsupported!

Execute this playbook in the event that "start_dss_ai_benchmark" has failed.
This playbook will terminate stuck warp processes.
Additionally, kernel packet pacing will be removed from each server.

#### playbooks/cleanup_dss_minio.yml

Execute this playbook to cleanup minio object store metadata.
This playbook will stop minio, and execute cleanup from a single node of each cluster in your inventory.
This will effectively remove any metadata at the root level of the object store.

Note that this will create the appearance of a reformated object store, but space will not be reclaimed.
Note that if a bucket is re-created after executing cleanup, its child objects will become accessible again.

#### playbooks/configure_hosts.yml

Execute this playbook to configure hosts prior to deploying DSS / TESS software.
This playbook will deploy custom kernel, install YUM / python dependencies, and configure OFED.
Note that presently, only versions of CentOS between 7.4 and 7.8 are supported

#### playbooks/configure_inbox_infiniband.yml

Execute this playbook to deploy the in-box Infiniband Support group.
This playbook is intended to be used to configure VMs or hosts where OFED is not desired.
Note that if configuring a host with inbox Infiniband Support, OFED must be removed from the system first.
Note that hosts configured with inbox Infiniband Support must be configured in your inventory with
"tcp_ip_list" and "rocev2_ip_list" lists populated. See README.md for additional details on inventory configuration.

#### playbooks/configure_vlans.yml

NOTE: For internal Samsung / DSS use! Unsupported!

Execute this playbook to automatically configure VLANs in Mellanox / Onyx environment.

Hosts that are configured with this playbook do not need to have "tcp_ip_list" and "rocev2_ip_list" lists defined in inventory.
If these vars are not defined, Ansible will attempt to automatically discover IP / VLAN configuration, as configured by this playbook.

Environment MUST have Mellanox Onyx switch configured in inventory.
Onyx Switch(es) must be included under the [onyx] group in your inventory file.
Switch credentials must be provided using "ansible_user" and "ansible_ssh_pass" vars for each Onyx host or the entire [onyx] group.
Key-based authentication is not possible with Onyx.

It is critical to review the "rocev2_vlans" and "tcp_vlans" vars under "group_vars/all.yml" to auto-configure VLANs on Onyx.
To make changes to the default values, uncomment these vars and make changes to "group_vars/all.yml" or add them to your inventory file.
There must be an even number of physical interface ports available, with each pair of ports corresponding to one TCP and one RoCEv2 VLAN/IP.
IPV4 last octet / IPV6 last hextet are automatically derived based on the presence of a digit appended to each hostname in your inventory.
If a unique number cannot be automatically derived from each hostname in your inventory, a number will automatically be assigned to each host
in your inventory, starting with "1".
You can specify a static last octet to each host by assigning the variable, "last_octet" for each host in your inventory file.
Additionally, you can offset the automatically derived last octet for a host, or a group, by assigning a "last_octet_offset" var for each host or group.
For example, given two hosts in your inventory: "server_01" and "client_01"
You can assign "last_octet_offset=100" to "client_01", which will result in "client_01" having a derived last octet of "101"

VLAN IDs for all Onyx switches, clients, and servers must be assigned in your inventory file using "tcp_vlan_id_list" and "rocev2_vlan_id_list" vars.
The VLAN IDs provided in these list must correspond to the VLAN IDs provided in "rocev2_vlans" and "tcp_vlans" lists, as mentioned above.
If using multiple Onyx switches, it is thus possible to spread your VLANs across multiple switches.
Note that if a host and switch both are tagged with a VLAN ID, it is expected that there is a physical link between this switch and host.
If no link is detected, the playbook fail on this assertion.

Note that it is possible to assign multiple VLANs to a single physical link using the "num_vlans_per_port" var as a host / group var.
For example, a host with "num_vlans_per_port=2" and 2 physical ports will allow the use of 4 VLANs (2 TCP and 2 RoCEv2)

#### playbooks/configure_vms.yml

Execute this playbook to configure VMs, or other hosts using the in-box Infiniband Support group.
This playbook is intended to be used to configure VMs or hosts where OFED is not desired.

Note that if configuring a host with inbox Infiniband Support, OFED must be removed from the system first.
Note that hosts configured with inbox Infiniband Support must be configured in your inventory with
"tcp_ip_list" and "rocev2_ip_list" lists populated. See README.md for additional details on inventory configuration.

#### playbooks/debug_dss_software.yml

Execute this playbook to run a series of basic status debug tests .
This playbook will perform the following actions:

* Get a count of running minio instances on each host
* Get a count of running target instances on each host
* Search for errors in all minio logs across all hosts
* Search for errors in all target logs across all hosts

#### playbooks/deploy_datamover.yml

Execute this playbook to deploy the datamover, client library, and their dependencies.
Artifacts are deployed to hosts under the [clients] group.
Note that it is possible for hosts to appear under both the [clients] and [servers] groups.
Hosts under the [clients] group will be used for datamover distributed operations.
This playbook will also create configuration files for client library and datamover, based on hosts that appear in your inventory.
Please review "Datamover Settings" under "group_vars/all.yml" if you wish to adjust the default settings of the datamover.
Uncomment vars with new values, or add them to your inventory file.

Re-running this playbook will update the datamover configuration across all hosts in your inventory.

#### playbooks/deploy_dss_ai_benchmark.yml

NOTE: For internal Samsung / DSS use! Unsupported!

Execute this playbook to deploy the DSS AI Benchmark software.
This playbook will also create configuration files for client library and datamover, based on hosts that appear in your inventory.
Please review "Datamover Settings" under "group_vars/all.yml" if you wish to adjust the default settings of the datamover.
Uncomment vars with new values, or add them to your inventory file.

Re-running this playbook will update the datamover configuration across all hosts in your inventory.

#### playbooks/deploy_dss_software.yml

Execute this playbook to deploy DSS software to all hosts in your inventory.
This playbook will perform the following:

* Deploy, configure, and start target on all [servers]
* Deploy, configure, and start nkv-sdpk host driver to all [servers]
* Deploy, configure, and start minio instances to all [servers]
* Optionally deploy, configure, and start UFM to all [ufm_hosts]
* Deploy and configure datamover and client library to all [clients]

#### playbooks/format_redeploy_dss_software.yml

Execute this playbook to re-deploy DSS software to all hosts in your inventory.
This playbook is effectively identical to running "remove_dss_software", then "deploy_dss_software".
Additionally, KVSSDs (with KV firmware) will be formated cleanly.

#### playbooks/format_restart_dss_software.yml

Execute this playbook to restart DSS software to all hosts in your inventory.
This playbook is effectively identical to running "stop_dss_software", then "start_dss_software".
Additionally, KVSSDs (with KV firmware) will be formated cleanly.
SSDs (with block firmware) will be re-formated with mkfs_blobfs.

#### playbooks/redeploy_dss_ai_benchmark.yml

NOTE: For internal Samsung / DSS use! Unsupported!

Execute this playbook to redeploy the DSS AI Benchmark software.
This is effectively the same as executing "remove_dss_ai_benchmark" then "deploy_dss_ai_benchmark" playbooks.

#### playbooks/redeploy_dss_software.yml

Execute this playbook to redeploy DSS software to all hosts in your inventory.
This playbook is effective the same as executing "stop_dss_software", "remove_dss_software", then "deploy_dss_software".
Data present across back-end storage will persist after redeploy.

#### playbooks/remove_dss_ai_benchmark.yml

NOTE: For internal Samsung / DSS use! Unsupported!

Execute this playbook to remove the DSS AI Benchmark software.

#### playbooks/remove_dss_software.yml

Execute this playbook to remove DSS software to all hosts in your inventory.
This playbook is effective the same as executing "stop_dss_software" and "remove_dss_software"
Data present across back-end storage will persist after removing DSS software.

#### playbooks/remove_packet_pacing.yml

NOTE: For internal Samsung / DSS use! Unsupported!

Execute this playbook to remove packet pacing from servers.
This can be used to cleanup DSS AI Benchmark.

#### playbooks/remove_vlans.yml

NOTE: For internal Samsung / DSS use! Unsupported!

Execute this playbook to remove VLAN / IP configuration, which was previously configured with "configure_vlans" playbook.

#### playbooks/restart_dss_software.yml

Execute this playbook to restart DSS software to all hosts in your inventory.
This playbook is effective the same as executing "stop_dss_software" then "start_dss_software".

#### playbooks/start_compaction.yml

Execute this playbook to start the compaction process across all [servers].
Compaction is useful to reclaim space on backing storage devices after WRITE or DELETE operations.
Note that this playbook will wait and retry until compaction has completed across all hosts.
Compaction may take a very long time with very large datasets.
The default timeout is 12,000 seconds (200 hours)
The timeout may be changed by setting the "start_compaction_timeout" var.
For example, to start compaction with a 400 hour timeout:
    ansible-playbook -i <your_inventory> playbooks/start_compaction -e 'start_compaction_timeout=24000'

Compaction status is checked every 15 seconds by default. This value can be user-defined with the "start_compaction_delay" var.

#### playbooks/start_datamover.yml

Execute this playbook to start the datamover accross all [clients].

By default, "start_datamover" will execute a PUT operation, uploading all files from your configured NFS shares to the minio object store.
Please review the "Datamover Settings" section of "group_vars/all.yml"
It is critical to set the "datamover_nfs_shares" to match your environment.
IPV4, IPV6, or resolvable hostnames are accepted for the "ip" key.

Additional operations supported by "start_datamover: PUT, GET, DEL, LIST, TEST

* PUT: Upload files from NFS shares to object store
* GET: Download files from object store to a shared mountpoint on all [clients]
* LIST: List objects on object store. Produces a count of objects on object store, and saves a list of objects to a default location.
* DEL: Delete all objects on object store, previously uploaded by datamover.
* TEST: Perform a checksum validation test of all objects on object store, compared to files on NFS shares.

This playbook has a number of user-definable variables that can be set from the command line to run the operation you choose:

* datamover_operation: PUT
* datamover_dryrun: false
* datamover_compaction: true
* datamover_prefix: ''
* datamover_get_path: "{{ ansible_env.HOME }}/datamover"

For example, to execute datamover GET operation to a writable, shared mount point across all [clients]:
    ansible-playbook -i <your_inventory> playbooks/start_datamover -e 'datamover_operation=GET,datamover_get_path=/path/to/share/'

For additional documentation, please consult the datamover README.md file, located on all [clients]:
> /usr/dss/nkv-datamover/README.md

#### playbooks/start_dss_ai_benchmark.yml

NOTE: For internal Samsung / DSS use! Unsupported!

Execute this playbook to destartploy the DSS AI Benchmark software.
This playbook will also create configuration files for client library and datamover, based on hosts that appear in your inventory.
Please review "Datamover Settings" under "group_vars/all.yml" if you wish to adjust the default settings of the datamover.
Uncomment vars with new values, or add them to your inventory file.

#### playbooks/start_dss_software.yml

Execute this playbook to start DSS software to all hosts in your inventory.
This playbook is idempotent, and will only start DSS processes if they are not already running.

#### playbooks/stop_dss_software.yml

Execute this playbook to stop DSS software on all hosts in your inventory.
This playbook is idempotent, and will only stop DSS processes if they are not already stopped.
The following actions will be performed on all servers:

1. Stop MinIO
2. Unmount NVMeOF targets / remove kernel driver
3. Stop Target

Note: Disks will remain in user space (SPDK)

#### playbooks/stop_reset_dss_software.yml

Execute this playbook to stop DSS software to all hosts in your inventory.
Additionally, once DSS software is stopped, disks will be returned back to kernel mode (SPDK reset).

#### playbooks/support_bundle.yml

Execute this playbook to collect a basic support bundle on all hosts.
This playbook will search all hosts for core dumps (by default, under /var/crash/).
A support bundle will be generated, including the core dump as well as:

* target logs
* minio logs
* dmesg logs

Support bundle will be downloaded to a local path, defined by "local_coredump_dir" var.
For example, to download support bundles from all hosts to your local home directory:

    ansible-playbook -i <your_inventory> playbooks/support_bundle.yml -e 'local_coredump_dir=~/tess_support/'

By default, a support bundle will always be downloaded. To only generate a support bundle if a coredump is detected,
set the "coredump_only" var to 'true'. Example:

    ansible-playbook -i <your_inventory> playbooks/support_bundle.yml -e 'local_coredump_dir=~/tess_support/,coredump_only=true'

#### playbooks/test_network.yml

Execute this playbook to perform a basic set of network tests across all hosts.
All hosts will ping each other across TCP IP's, and RoCEv2 IPs.
An ib_read_bw test will then run, and assert that measured throughput is at least 90% of link speed.

#### playbooks/test_nkv_test_cli.yml

NOTE: For internal Samsung / DSS use! Unsupported!

Perform a basic nkv_test_cli test and report observed bandwidth.

#### playbooks/upgrade_dss_software.yml

Execute this playbook to upgrade DSS software to all hosts in your inventory.
This playbook is equivelent to executing "stop_dss_software" then "deploy_dss_software"
Note that software will only be upgraded if new binaries are placed under the "artifacts" directory.

#### playbooks/upgrade_kvssd_firmware.yml

NOTE: For internal Samsung / DSS use! Unsupported!

This playbook can be used to upgrade the firmware of PM983 SSDs. All other models not supported.
In order to upgrade firmware, a valid firmware binary must be copied to the "artifacts" directory.
Then the "target_fw_version" must be commented out in all vars / defaults files.

## Testing DSS Software Stack

### AI benchmark

#### *Execute AI Benchmark*

    cd ~/deploy
    ansible-playbook -i your_inventory playbooks/start_dss_benchamrk.yml

#### *View Benchmark Results*

From a web browser, navigate to the TCP IP of the first host in the `clients` group.
Benchmark results can be found under the dated directory corresponding with the benchmark run, under "graphs":

![image](image_AIBenchResult.png)

### S3-benchmark

s3-benchmark is a performance testing tool that can check the performing S3 operations (PUT, GET, and DELETE) for object storage.
s3-benchmark is automatically installed by Ansible to "/usr/dss/nkv-minio/s3-benchmark" on each VM node.

#### *Command Line Arguments*

Below is the command line arguments to use S3-Benchmark displayed using help:

        /usr/dss/nkv-minio/s3-benchmark -h
        Wasabi benchmark program v2.0
        Usage of myflag:
        -a string
            Access key
        -b string
            Bucket for testing (default "wasabi-benchmark-bucket")
        -c int
            Number of object per thread written earlier
        -d int
            Duration of each test in seconds (default 60)
        -l int
            Number of times to repeat test (default 1)
        -n int
            Number of IOS per thread to run
        -o int
            Type of op, 1 = put, 2 = get, 3 = del
        -p string
            Key prefix to be added during key generation (default "s3-bench-minio")
        -r string
            Region for testing (default "us-east-1")
        -s string
            Secret key
        -t int
            Number of threads to run (default 1)
        -u string
            URL for host with method prefix (default "http://s3.wasabisys.com")
        -z string
        Size of objects in bytes with postfix K, M, and G (default "1M")

#### *Example S3-Benchmark*

Here is an example run of the benchmark for 100 threads with the default 1MB object size. The benchmark reports each operation's PUT, GET and DELETE results in terms of data speed and operations per second. The program writes all results to the log file benchmark.log.
Note: Do not exceed 50% of the total subsystem capacity.
Note: Do not exceed 256 threads in VM Environment.

Note: After writing data in the storage and before reading the data, it is necessary to run compaction command. Compaction allows obtaining the software's accurate and optimal performance.  

* Put Data

        /usr/dss/nkv-minio/s3-benchmark -a minio -b testbucket -s minio123 -u <http://10.1.51.21:9000> -t 100 -z 1M -n 100 -o 1
        Wasabi benchmark program v2.0Parameters: url=<http://10.1.51.21:9000>, bucket=testbucket, region=us-east-1, duration=60, threads=100, num_ios=100, op_type=1, loops=1, size=1M
        2021/01/05 18:22:52 WARNING: createBucket testbucket error, ignoring BucketAlreadyOwnedByYou: Your previous request to create the named bucket succeeded and you already own it.
        status code: 409, request id: 1657835058733E40, host id:
        Loop 1: PUT time 38.9 secs, objects = 10000, speed = 2.5GB/sec, 257.1 operations/sec. Slowdowns = 0

* Run Compaction

        cd /root/deploy
        ansible-playbook playbooks/start_compaction.yml

* Get Data
  
        /usr/dss/nkv-minio/s3-benchmark -a minio -b testbucket -s minio123 -u http://10.1.51.21:9000 –t 100 -z 1M -n 100 -o 2
        Wasabi benchmark program v2.0Parameters: url=http://10.1.51.21:9000, bucket=testbucket, region=us-east-1, duration=60, threads=100, num_ios=100, op_type=2, loops=1, size=1M
        2021/01/05 18:23:39 WARNING: createBucket testbucket error, ignoring BucketAlreadyOwnedByYou: Your previous request to create the named bucket succeeded and you already own it.
        status code: 409, request id: 1657835B38D61A94, host id:
        Loop 1: GET time 14.9 secs, objects = 10000, speed = 6.6GB/sec, 672.1 operations/sec. Slowdowns = 0

* Delete Data

        /usr/dss/nkv-minio/s3-benchmark -a minio -b testbucket -s minio123 -u <http://10.1.51.21:9000> –t 100 -z 1M -n 100 -o 3
        Wasabi benchmark program v2.0Parameters: url=<http://10.1.51.21:9000>, bucket=testbucket, region=us-east-1, duration=60, threads=100, num_ios=100, op_type=3, loops=1, size=1M
        2021/01/05 18:24:04 WARNING: createBucket testbucket error, ignoring BucketAlreadyOwnedByYou: Your previous request to create the named bucket succeeded and you already own it.
        status code: 409, request id: 16578360FD53602A, host id:
        Loop 1: DELETE time 4.3 secs, 2342.4 deletes/sec. Slowdowns = 0

### MinIO mc tool

The MinIO mc client is installed under "/usr/dss/nkv-minio/mc", and the DSS cluster is automatically registered with alias "autominio"

* Set of available command on mc tool

        /usr/dss/nkv-minio/mc -h

        COMMANDS:
        ls       list buckets and objects
        mb       make a bucket
        rb       remove a bucket
        cp       copy objects
        mirror   synchronize object(s) to a remote site
        cat      display object contents
        head     display first 'n' lines of an object
        pipe     stream STDIN to an object
        share    generate URL for temporary access to an object
        find     search for objects
        sql      run sql queries on objects
        stat     show object metadata
        tree     list buckets and objects in a tree format
        du       summarize disk usage folder prefixes recursively
        diff     list differences in object name, size, and date between two buckets
        rm       remove objects
        event    configure object notifications
        watch    listen for object notification events
        policy   manage anonymous access to buckets and objects
        admin    manage MinIO servers
        session  resume interrupted operations
        config   configure MinIO client
        update   update mc to latest release
        version  show version info
        
        GLOBAL FLAGS:
        --autocompletion              install auto-completion for your shell
        --config-dir value, -C value  path to configuration folder (default: "/opt/ansible/.mc")
        --quiet, -q                   disable progress bar display
        --no-color                    disable color theme
        --json                        enable JSON formatted output
        --debug                       enable debug output
        --insecure                    disable SSL certificate verification
        --help, -h                    show help
        --version, -v                 print the version

* To list objects on DSS cluster using mc:

        /usr/dss/nkv-minio/mc ls autominio
        [2021-02-05 12:19:18 PST] 0B benchmark-bucket-1/

### Client Components

The client library and data mover are provided to load data into the cluster from an NFS share.

* Client Library: please refer to its README file and the run example under dss_client directory.

* Data Mover: Installing the data mover is possible by executing the following playbook using Ansible.

```ansible-playbook -i your_inventory playbooks/deploy_datamover.yml```

* Data Mover configuration: Review `Datamover Settings` in `group_vars/all.yml`.
* Uncomment relevent changes as they apply to your specific environment, most imporantly `datamover_nfs_shares`:

        ```yaml
        ### Datamover Settings
        # datamover_master_workers: 1
        # datamover_master_max_index_size: 100
        # datamover_master_size: 1GB
        # datamover_client_workers: 25
        # datamover_client_max_index_size: 100
        # datamover_client_user_id: ansible
        # datamover_client_password: ansible
        # datamover_message_port_index: 4000
        # datamover_message_port_status: 4001
        # datamover_nfs_shares:
        #   - ip: 192.168.200.199
        #     shares:
        #       - /mnt/nfs_share/5gb
        #       - /mnt/nfs_share/10gb
        #       - /mnt/nfs_share/15gb
        #   - ip: 192.168.200.200
        #     shares: 
        #       - /mnt/nfs_share/5gb-B
        #       - /mnt/nfs_share/10gb-B
        #       - /mnt/nfs_share/15gb-B
        # datamover_bucket: bucket
        # datamover_client_lib: dss_client
        # datamover_logging_path: /var/log/dss
        ```

* Start datamover:

```ansible-playbook -i your_inventory playbooks/start_datamover.yml```

Complete documentation is available under the /usr/dss/nkv-datamover directory (deployed to each client in your cluster).

## Known Issues / Limitations

* Do not exceed 50% of total subsystem capacity
* Do not exceed 256 concurrent threads in VMware environment
