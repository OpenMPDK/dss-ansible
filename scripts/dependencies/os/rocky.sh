#! /usr/bin/env bash
set -e

# Build Dependencies
BUILD_DEPS=()
BUILD_DEPS+=('python3.11')
BUILD_DEPS+=('git')
BUILD_DEPS+=('sshpass')

# Optimizations for Docker build
if [[ -f /.dockerenv ]]
then
    BUILD_DEPS+=('--nodocs')
    BUILD_DEPS+=('--noplugins')
    BUILD_DEPS+=('--setopt=install_weak_deps=0')
fi

# Detect package installer
INSTALLER_BIN=""

if [[ -f '/usr/bin/dnf' ]]
then
    echo "using dnf"
    INSTALLER_BIN='dnf'
elif [[ -f '/usr/bin/microdnf' ]]
then
    echo "using microdnf"
    INSTALLER_BIN='microdnf'
else
    # Can't find an appropriate installer
    echo "can't find a valid installer"
    exit 1
fi

INSTALL_STRING="$INSTALLER_BIN install -y ${BUILD_DEPS[*]}"
echo "executing command: $INSTALL_STRING"
eval "$INSTALL_STRING"

# Farther cleanup if Docker environment
if [[ -f /.dockerenv ]]
then
    CLEANUP_STRING="$INSTALLER_BIN clean all"
    echo "executing command: $CLEANUP_STRING"
    eval "$CLEANUP_STRING"
    rm -rf /var/lib/dnf/history*
    rm -rf /var/lib/dnf/repos/*
    rm -rf /var/lib/rpm/__db*
    rm -rf /usr/share/man /usr/share/doc /usr/share/licenses /tmp/*
    rm -f /var/log/dnf*
fi
