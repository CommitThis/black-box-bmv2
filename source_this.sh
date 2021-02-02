#! /bin/bash

python3 -m venv .venv --copies

# RAW for creating sockets (scapy)
# DAC for file operations (linking/unlinking)
# ADMIN not sure yet
sudo setcap CAP_NET_RAW,CAP_DAC_OVERRIDE+eip .venv/bin/python
sudo setcap CAP_NET_RAW,CAP_DAC_OVERRIDE+eip .venv/bin/pytest



source .venv/bin/activate
pip install --upgrade setuptools
pip install wheel
pip install -e packettest
pip install -e bmv2-docker
pip install -e simplep4client

