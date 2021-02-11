''''
    Operations
    ==========

    Initialisation
    --------------
    - Create veth pairs
    - Create /var/run/netns
    - Write ports file
    - Run container with ${name}
    - Run read thread
    - Bind container process pid to namespace ${name}_ns
    - Move peer ports to namespace
    - Send trap
    - Wait

    Cleanup
    -------
    - Kill container
    - Remove container
    - Remove namespace ${name}_ns
    - Join read thread
    - Profit

'''

# def setup_veth(config):

from simple_switch.netutils import add_veth_pair
from simple_switch.netutils import configure_mtu
from simple_switch.netutils import iface_up
from simple_switch.netutils import configure_ip
from simple_switch.netutils import configure_mac
from simple_switch.netutils import multicast_enabled
from simple_switch.netutils import set_iface_namespace
from simple_switch.netutils import delete_device
from simple_switch.netutils import configure_interface
from simple_switch.netutils import restart_avahi


from docker import DockerClient
from docker import APIClient as DockerAPIClient
from docker.utils import create_host_config
from pyroute2 import netns

import os
import signal

NETNS_DIR = '/var/run/netns'

BMV_DEFAULT_GRPC_PORT = 9559

if os.environ.get('https_proxy'):
    del os.environ['https_proxy']
if os.environ.get('http_proxy'):
    del os.environ['http_proxy']

class SimpleSwitchDocker:
    CONTAINER = 'bmv2'
    LAUNCH_SCRIPT = '/opt/wait.sh'

    def __init__(self, name, network, grpc_port):

        self._read_thread = None
        self._container = None
        self._name = name
        self._network = network
        self._id = None
        self._pid = None
        self._namespace = None
        self._switch_ports = {}
        self._grpc_port = grpc_port

        self._docker_client = DockerClient(base_url="unix://var/run/docker.sock", version='auto')
        self._docker_api = DockerAPIClient(base_url="unix://var/run/docker.sock", version='auto')


    def launch(self, log_level='info'):
        # self._create_network()

        # network_exists = True
        # try:
        #      self._docker_client.networks.get(self._network)
        # except:
        #     network_exists = False
        # if not network_exists: self._docker_api.create_network(self._network, driver="bridge")

        port_file = f'/tmp/ports_{self._name}'
        with open(port_file, 'w+') as ports_file:
            command = f'simple_switch_grpc --log-level={log_level} --log-console --no-p4 '
            command += ' '.join([f'-i {idx}@{peer}' for idx, peer in enumerate(self._switch_ports)])
            ports_file.write(command)

        restart_avahi()

        self._id = self._docker_client.containers.run(
                SimpleSwitchDocker.CONTAINER,
                SimpleSwitchDocker.LAUNCH_SCRIPT,
                volumes={port_file: {'bind': '/ports', 'mode': 'ro'}},
                name=self._name,
                network_mode='bridge',
                # network=self._network,
                detach=True,
                ports={
                        9559: self._grpc_port,
                    },
                )

        self._pid = self._docker_api.inspect_container(self._name)['State']['Pid']
        self._container = self._docker_client.containers.get(self._name)
        self._namespace = f'{self._name}_ns'

        try:
            from simple_switch.netutils import _run_command
            _run_command(f'sudo ln -s /proc/{self._pid}/ns/net /var/run/netns/{self._namespace}')
        except FileExistsError as err:
            # Might need to handle this
            pass
        for port, config in self._switch_ports.items():
            set_iface_namespace(port, self._namespace)
            configure_interface(config, self._namespace)

        self.signal_ready()


    def add_port(self, port, config):
        self._switch_ports[port] = config


    def signal_ready(self):
        """Signal port readiness.
        Send SIGUSR1 signal to container, which the startup script is waiting
        on, to indicate that the veth ports have been created and recorded in 
        the file it needs to read so that the behavioral model can be started.
        Also maybe because the virtual ethernet ports have been moved into the 
        containers namespace, but I'm not sure right now. """
        self._container.kill(signal.SIGUSR1)


    def kill(self):
        print(self._container.status)
        if self._container.status == 'running':
            try:
                self._container.kill()
            except:
                # Race condition on container exiting normally after a noop
                pass
        try:
            self._container.remove()
        except:
            pass
        print(f'Removing namespace {self._namespace}')
        netns.remove(self._namespace)
        


    def stream(self):
        return self._container.logs(stream=True)


    def get_container(self):
        return self._container


    def join(self):
        if self._read_thread:
            self._read_thread.join()



def make_switch(config, switch_name, network_name, grpc_port=BMV_DEFAULT_GRPC_PORT):
    peer_ports = {}
    defaults = config.get('defaults', {})
    for idx, veth_config in enumerate(config.get('pairs', {})):
        host_config = veth_config['host']
        peer_config = veth_config['peer']
        host_config.update(defaults)
        peer_config.update(defaults)
        add_veth_pair(host_config['name'], peer_config['name'], exists_ok=True)
        # configure_interface(peer_config)
        configure_interface(host_config)
        peer_ports[peer_config['name']] = peer_config

    
    switch = SimpleSwitchDocker(switch_name, network_name, grpc_port)
    for port, peer_config in peer_ports.items():
        switch.add_port(port, peer_config)

    return switch
