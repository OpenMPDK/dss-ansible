#!/usr/bin/env bash
# The Clear BSD License
#
# Copyright (c) 2022 Samsung Electronics Co., Ltd.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted (subject to the limitations in the disclaimer
# below) provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, 
#   this list of conditions and the following disclaimer.
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
# * Neither the name of Samsung Electronics Co., Ltd. nor the names of its
#   contributors may be used to endorse or promote products derived from this
#   software without specific prior written permission.
# NO EXPRESS OR IMPLIED LICENSES TO ANY PARTY'S PATENT RIGHTS ARE GRANTED BY
# THIS LICENSE. THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND
# CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT
# NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
# OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
# OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
# ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

gid_count=0
ib_path=/sys/class/infiniband

# Iterate over infiniband devices
find_devs()
{
    for dev in "$ib_path"/*
    do
        find_ports "$dev"
    done
}

# Iterate over ports for each infiniband device
find_ports()
{
    dev=$(basename "$1")
    for port in "$ib_path/$dev"/ports/*
    do
        find_gids "$dev" "$port"
    done
}

# Iterate over gids for each port
find_gids()
{
    dev=$1
    portpath=$2
    port=$(basename "$2")
    for gidpath in "$ib_path/$dev/ports/$port"/gids/*
    do
        gidnum=$(basename "$gidpath")
        gid=$(cat "$gidpath")
        if [ "$gid" = 0000:0000:0000:0000:0000:0000:0000:0000 ] || [ "$gid" = fe80:0000:0000:0000:0000:0000:0000:0000 ]
        then
            continue
        fi
        ndev=$(cat "$portpath"/gid_attrs/ndevs/"$gidnum" 2>/dev/null)
        type=$(cat "$portpath"/gid_attrs/types/"$gidnum" 2>/dev/null)
        ver=$(echo "$type"| grep -o "[Vv].*")
        if [ "$(echo "$gid" | cut -d ":" -f -1)" = "0000" ]
        then
            ipv4=$(printf "%d.%d.%d.%d" 0x"${gid:30:2}" 0x"${gid:32:2}" 0x"${gid:35:2}" 0x"${gid:37:2}")
            echo -e "$dev\t$port\t$gidnum\t$gid\t$ipv4 \t$ver\t$ndev"
        else
            echo -e "$dev\t$port\t$gidnum\t$gid\t\t\t$ver\t$ndev"
        fi
        gid_count=$((1+gid_count))
    done
}

# # Print gids table header
echo -e "DEV\tPORT\tINDEX\tGID\t\t\t\t\tIPv4 \t\tVER\tDEV"
echo -e "---\t----\t-----\t---\t\t\t\t\t------------ \t---\t---"

# Find user-defined dev if specified from command line, otherwise find all devs
if [ -n "$1" ]
then
    find_ports "$ib_path/$1"
else
    find_devs
fi

# Print total number of gids counted
echo n_gids_found=$gid_count
