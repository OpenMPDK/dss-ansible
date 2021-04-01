"""

   BSD LICENSE

   Copyright (c) 2021 Samsung Electronics Co., Ltd.
   All rights reserved.

   Redistribution and use in source and binary forms, with or without
   modification, are permitted provided that the following conditions
   are met:

     * Redistributions of source code must retain the above copyright
       notice, this list of conditions and the following disclaimer.
     * Redistributions in binary form must reproduce the above copyright
       notice, this list of conditions and the following disclaimer in
       the documentation and/or other materials provided with the
       distribution.
     * Neither the name of Samsung Electronics Co., Ltd. nor the names of
       its contributors may be used to endorse or promote products derived
       from this software without specific prior written permission.

   THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
   "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
   LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
   A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
   OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
   SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
   LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
   DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
   THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
   (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
   OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

import argparse
import json
import os
from subprocess import Popen, PIPE
import sys

dss_conf_file = 'conf.json'
minio_alias = "dssalias"


def exec_cmd(cmd):
    """
    Execute any given command on shell
    @return: Return code, output, error if any.
    """
    print("Executing cmd %s..." % cmd)
    p = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
    try:
        out, err = p.communicate()
        out = out.decode()
        out = out.strip()
        err = err.decode()
    except Exception as e:
        print('Error in running the command (%s) - %s '.format(cmd, str(e)))
        out = None
        err = None
    retval = p.returncode

    return retval, out, err


def setup_client_conf_for_dss(endpoints):
    endpoints = endpoints.split(',')
    conf = dict()
    conf['version'] = 0.1
    conf['clusters'] = []
    entry = dict()
    entry['id'] = 0
    entry['endpoints'] = []
    for ep in endpoints:
        endpoint = ep.replace('http://', '')
        ipaddr, port = endpoint.split(':')
        endpoint_entry = dict()
        endpoint_entry['ipv4'] = ipaddr
        endpoint_entry['port'] = int(port)
        entry['endpoints'].append(endpoint_entry)

    conf['clusters'].append(entry)

    with open(dss_conf_file, 'w') as f:
        json.dump(conf, f, indent=4)


def setup_client_conf_for_stock(endpoints):
    endpoints = endpoints.split(',')
    conf = dict()
    conf['version'] = 0.1
    conf['clusters'] = []
    entry_id = 0
    for ep in endpoints:
        entry = dict()
        entry['id'] = entry_id
        entry['endpoints'] = []
        endpoint = ep.replace('http://', '')
        ipaddr, port = endpoint.split(':')
        endpoint_entry = dict()
        endpoint_entry['ipv4'] = ipaddr
        endpoint_entry['port'] = int(port)
        entry['endpoints'].append(endpoint_entry)
        entry_id += 1
        conf['clusters'].append(entry)

    with open(dss_conf_file, 'w') as f:
        json.dump(conf, f, indent=4)


def initialize_config_file_for_dss_client(endpoints, mc_cmd, access_key, secret_key):
    endpoints = endpoints.split(',')
    ep = endpoints[0].replace('http://', '')
    cmd = "MC_HOST_" + minio_alias + "=http://" + access_key + ":" + secret_key + "@" + ep + " "
    cmd += mc_cmd + " mb " + minio_alias + "/dss"
    retval, out, err = exec_cmd(cmd)
    if retval or 'ERROR' in err:
        if 'you already own it' in err:
            print("Bucket already present. Ignoring the error")
        else:
            print('Error in creating bucket - ret %s - err %s' % (retval, err))
            return -1

    cmd = "MC_HOST_" + minio_alias + "=http://" + access_key + ":" + secret_key + "@" + ep + " "
    cmd += mc_cmd + " cp " + dss_conf_file + " " + minio_alias + "/dss"
    retval, out, err = exec_cmd(cmd)
    if retval or 'ERROR' in err:
        print('Error in copying configuration file - ret %s - err %s' % (retval, err))
        return -1

    return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-e', '--endpoints', dest='endpoints', help='comma separated endpoints of minio instances',
                        required=True)
    parser.add_argument('-m', '--mode', dest='minio_mode', help='Minio mode (dss/stock) - default: dss',
                        required=False, default='dss')
    parser.add_argument('-p', '--mc_path', dest='mc_path', help='Minio mc command path (default /usr/bin)',
                        required=False, default='/usr/bin/')
    parser.add_argument('-a', '--access-key', dest='access_key', help='Access Key of the Minio server', required=True)
    parser.add_argument('-s', '--secret-key', dest='secret_key', help='Secret Key of the Minio server', required=True)

    args = parser.parse_args()
    mode = args.minio_mode

    if not args.mc_path.endswith('mc'):
        mc_cmd = os.path.join(args.mc_path, 'mc')
    else:
        mc_cmd = args.mc_path

    if mode == 'dss':
        try:
            setup_client_conf_for_dss(args.endpoints)
        except:
            print('Failed to create conf.json in DSS MINIO mode')
            sys.exit(-1)
    elif mode == 'stock':
        try:
            setup_client_conf_for_stock(args.endpoints)
        except:
            print('Failed to create conf.json for Stock MINIO mode')
            sys.exit(-1)
    else:
        print('Invalid mode given')
        sys.exit(-1)

    ret = initialize_config_file_for_dss_client(args.endpoints, mc_cmd, args.access_key, args.secret_key)
    if ret:
        print('Error in setting up the dss_client configuration')
        sys.exit(-1)

    sys.exit(0)
