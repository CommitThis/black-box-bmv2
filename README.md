# Black Box BMv2 Testing

This set of python libraries is for testing and playing arounf with P4 programs
written for BMv2. The idea is that you can treat each program in a black box
scenario and that minimal setup is required to setup a behavioral model 
instance, a gRPC client, and a test application. Use cases include testing 
multicast distribution, VLAN tags, anything that involves receipt or altering of
a packet -- even using this to quickly test P4 ideas without having to worry 
about a significant number of dependencies.

For more information on P4, examples and guides, I would recommend 
https://github.com/jafingerhut/p4-guide

The project includes the following:

### Test Application (app)
Contains an MIT licensed basic implementation of a MAC learning P4 program, a 
test suite that installs and writes new multicast rules and a small test suite
(ok it's like one function!) to test the rule.

### [Behavioral Model Docker](bmv2-docker/README.md) (bmv2-docker)
Contains a docker file for creating a Ubuntu container that contains the 
behavioral model (with the help of github.com/jafingerhut/p4-guide), and an 
functions to run an instance of that container, setting up necessary virtual
ethernet ports, network/firewall rules and a test context helper for... testing.

### [Packet Test](packettest/README.md) (packettest)
Library for testing packets received on ports, using a future-bases async model.

### [Simple P4 Client](simplep4client/README.md) (simplep4client)
Wrapper for the P4 Runtime gRPC service, that provides helpers for writing
fields, tables, managing output streams


## Installation
Simply source `./source_this.sh`. This will set up a virtual environment and
install the packages.

*Note:* In order to create virtual interfaces, manage them and other manipulate
network and system settings, copies of the python executables are taken and the
following capabilities set:
* `CAP_NET_RAW`: Creating sockets for the sending packets, network management
  functions.
* `CAP_DAC_OVERRIDE`: Manipulating filesystem/sysfs
