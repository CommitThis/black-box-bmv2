# Behavioral Model Docker

Library and Dockerfile for building and running the Behavioral Model using
Python.

> **Note:** The docker image, because it is used for both running BMv2, and used
> for compiling programs, and we can't consequently clear a bunch of software,
> the image size comes out at ~10GB! This may be revisited in the future.

Requires Ubuntu, Docker, UFW (the Firewall).

## Installation

Build the docker container. The library requires it specifically be named/tagged
"bmv2"

    `cd docker && docker build -t bmv2 .`

## Compiling P4 Programs

```python
from simple_switch.compile import compile_p4

compiled, p4info = compile_p4(dir_path, 'mac_learning.p4')
```

The compiled program and P4 runtime files will be placed in a directory names
`out`, relative to the location of the supplied source code.


## Running BMv2


### Configuration

A configuration file, written in Python, is used to describe BMv2 settings.
It's format contains is centered around the configuration of linux "virtual
ethernet" port pairs, where the `host` is available to the host, and `peer` is
available to BMv2.

> Network name is not currently used.

```python
config = {
    'switch_name': 'example',
    'network_name': 'example_net',
    'defaults': {
        'disable_ipv6': True,
        'mtu': 9500,
        'state': 'up'
    },
    'pairs' : [{
        'host': {
            'name': 'h1eth0',
            'ip': '10.0.0.1',
        },
        'peer' : {
            'name': 'Ethernet0',
            'mac': '84:C7:8F:00:00:01',
            'ip': '10.0.2.1'
        }
    },
    ...
}
```

The top level contains basic switch information, and a key for defaults that are
to be applied to the ports.

For each virtual ethernet port, there is a host interface and a peer interface.

The available keys are:
* 'name': Interface name
* 'ip': IPv4 adddress
* 'mac': MAC address
* 'mtu': Maximum Transmission Unit
* 'diable_ipv6': Disable IPv6. This may not work on peer interfaces
* 'disable_multicast': Attempts to block SSDP, mDNS, etc.




### Running with Python

```python
from threading import Event
from threading import Thread

from simple_switch.simple_switch_runner import make_switch
from veth_config import config

SWITCH_NAME = "ExampleSwitch"
NETWORK_NAME = "ExampleNet"
GRPC_PORT = 9559 # Optional, default 9559

# Network name is not currently used
bmv2 = make_switch(config, SWITCH_NAME, NETWORK_NAME, GRPC_PORT)
bmv2.launch()

shutdown_event = Event()
continue_event = Event()

def wait_start_and_log_stream():
    ''' Start reading the logs and trigger an event when the switch
    application has started the thrift server to test for readiness.
    While not perfect as it isn't testing the gRPC interface, it is a
    good (read: only) proxy for doing so.'''
    for line in bmv2.stream():
        line = line.decode('utf-8').strip()
        if 'Thrift server was started' in line:
            continue_event.set()
        print(line)


logs = Thread(target=wait_start_and_log_stream)
logs.start()
continue_event.wait()

# Later ....
bmv2.kill()
```

### Technical Detail

Running the Behavioral Model in a Docker container is substantially more complex
than using a virtual machine or a native device because:

* We need to make the virtual ethernet ports used for the switch ports 
  available within the container but the container needs to be running before we
  can add the ports;
* And the `simple_switch` or `simple_switch_grpc` application can't be run until
  the ports are available.


The process is as follows:
1. Create virtual ethernet port pairs;
2. Port pairs are recorded and written to a file used by the simple switch to
   bind to;
3. Launch the container. The container is run in the first instance using the
   `wait.sh` script. This serves as a proxy for whatever executable that is to
   be run. It traps and waits for the SIGUSR1 signal. Once this is received the
   script will execute the contents of a file (it's called ports, but in
   practice) could be any command. It also traps SIGINT and SIGTERM to kill the
   executed process. The launch also binds the file created earlier to expose
   ports to the container.
4. The network namespace is made available to the host by linking the 
   container's PID in `/var/run/netns/${namespace}` where the namespace is the
   name of the container + `_ns`.
5. The peer interface of the veth pairs are moved to the containers namespace;
6. The peer interfaces are configured. When a interface moves namespaces, it
   appears to lose it's settings, so they must be applied again (or once here).
7. BMv2 is launched, using the ports file we generated at the begining.


> **Note:** I can't guarantee that the port pairs will be free of traffic. 
> Services such as Bonjour, Avahi, mDNS, SSDP and IPv6 router solicitation
> messages may be present. These services don't really care what interfaces they
> talk to. The best that I have done so far is to disable ipv6 (I actually 
> don't this is working anymore, I have no idea how `sysctl` plays with 
> namespaces), set deny interfaces for Avahi, and add firewall rules.



