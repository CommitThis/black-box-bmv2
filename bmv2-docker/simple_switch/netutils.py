from subprocess import run
from subprocess import PIPE

import os



def _run_command(command):
    command = 'sudo ' + command
    output = run(command.split(), stdout=PIPE, stderr=PIPE)
    out = output.stdout.decode('utf-8').strip()
    err = output.stderr.decode('utf-8').strip()
    if output.returncode != 0:
        raise Exception(err + f' ({command})')
    return out, err


def __rnetlink_ignore_file_exists(command, exists_ok):
    print(command)
    command = 'sudo ' + command
    output = run(command.split(), stdout=PIPE, stderr=PIPE)
    if output.returncode != 0:
        errout = output.stderr.decode('utf-8').strip()
        if not ('File exists' in errout and exists_ok):
            raise Exception(errout)


# https://stackoverflow.com/questions/39086/search-and-replace-a-line-in-a-file-in-python
from tempfile import mkstemp
from shutil import move, copymode
from os import fdopen, remove


# catch if avahi not present
def avahi_deny(iface):
    try:
        FILE = '/etc/avahi/avahi-daemon.conf'
        fh, abs_path = mkstemp()
        with fdopen(fh,'w') as new_file:
            with open(FILE) as old_file:
                for line in old_file:
                    if 'deny-interfaces' in line:
                        line = line[:-1] #remove cr
                        if line.startswith('#'):
                            line = line[1:]
                        if iface not in line:
                            line = line + f',{iface}'
                        line = line + '\n'
                    new_file.write(line)
        copymode(FILE, abs_path)
        remove(FILE)
        move(abs_path, FILE)
    except:
        pass # this is crap


# catch if avahi not present
def restart_avahi():
    try:
        _run_command('systemctl restart avahi-daemon')
    except:
        pass # more crap


def __get_namespace_comand(command, namespace=None):
    if namespace is not None:
        command = f'ip netns exec {namespace} {command}'
    return command

def add_veth_pair(host, peer, exists_ok=False):
    command =f'ip link add name {host} type veth peer name {peer}'
    __rnetlink_ignore_file_exists(f'{command}', exists_ok)


def configure_mtu(iface, mtu, namespace=None):
    command = f'ip link set {iface} mtu {mtu}'
    _run_command(__get_namespace_comand(f'{command}', namespace))


def iface_up(iface, namespace=None):
    command = f'ip link set dev {iface} up'
    _run_command(__get_namespace_comand(f'{command}', namespace))


def configure_ip(iface, ip, namespace=None):
    command = f'ip addr add {ip} dev {iface}'
    __rnetlink_ignore_file_exists(__get_namespace_comand(f'{command}', namespace), True)


def configure_mac(iface, mac, namespace=None):
    command = f'ip link set {iface} address {mac}'
    _run_command(__get_namespace_comand(f'{command}', namespace))


def disable_ipv6(iface, disable): #, enable=False):
    disable = '1' if disable else '0' 
    _run_command(f'sysctl -w net.ipv6.conf.{iface}.disable_ipv6={disable}')


def multicast_enabled(iface, enable=False, namespace=None):
    enable = 'on' if enable else 'off'
    command =  f'ip link set {iface} multicast {enable}'
    _run_command(__get_namespace_comand(f'{command}', namespace))


def stop_mdns_ssdp(iface, stop):
    avahi_deny(iface) # Need to create symmetric command

    action = ''
    if not stop:
        action = 'delete '
    _run_command(f'ufw {action}deny out on {iface} to 224.0.0.22') # IGMP
    _run_command(f'ufw {action}deny out on {iface} to 224.0.0.251')
    _run_command(f'ufw {action}deny out on {iface} to 239.255.255.250')



def create_bridge(bridge_name, exists_ok=False):
    __rnetlink_ignore_file_exists(f'ip link add name {bridge_name} type bridge', exists_ok)
    set_up(bridge_name)


def set_iface_namespace(iface, namespace):
    _run_command(f'ip link set {iface} netns {namespace}')
    _run_command(f'ip netns exec {namespace} ip link set {iface} up')


def delete_device(dev):
    _run_command(f'ip link del {dev}')


# Need to cover rest of keys in config dict
def configure_interface(config, namespace=None):
    iface = config['name']

    # Default commands
    # stop_mdns_ssdp(iface, config.get('stop_mdns_ssdp', True))

    # Need to work on sysctl settings for namespaced interfaces
    if namespace is None:
        disable_ipv6(iface, config.get('disable_ipv6', True))
    
    multicast_enabled(iface, config.get('disable_multicast', True), namespace)

    # Optional Commands
    if 'mtu' in config.keys(): configure_mtu(iface, config['mtu'], namespace)
    if 'mac' in config.keys(): configure_mac(iface, config['mac'], namespace)
    if 'ip' in config.keys(): configure_ip(iface, config['ip'], namespace)
    
    iface_up(iface, namespace)

