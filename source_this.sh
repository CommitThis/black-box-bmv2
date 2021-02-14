#! /bin/bash

SCRIPTPATH="$( cd "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"


# Create virtual environment, making copies of the python executables so that
# when the capabilities are set, firstly it actually works (you can't set
# against links), and if it did, we wouldn't want to modify system binaries
# anyway.
python3 -m venv .venv --copies

# RAW for creating sockets (scapy)
# DAC for file operations (linking/unlinking)
sudo setcap CAP_NET_RAW,CAP_DAC_OVERRIDE+eip .venv/bin/python
sudo setcap CAP_NET_RAW,CAP_DAC_OVERRIDE+eip .venv/bin/python3

source .venv/bin/activate
pip install --upgrade setuptools
pip install wheel
pip install -e ${SCRIPTPATH}/packettest
pip install -e ${SCRIPTPATH}/bmv2-docker
pip install -e ${SCRIPTPATH}/simplep4client

sudo setcap CAP_NET_RAW,CAP_DAC_OVERRIDE+eip .venv/bin/run_bmv2
