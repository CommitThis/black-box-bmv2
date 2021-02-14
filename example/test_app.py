from config import config

from packettest.packets import make_packet
# from packettest.test_context import make_context
from packettest.test_context import TestContext
from packettest.predicates import received_packet
from packettest.predicates import saw_packet_equals_sent

from simple_switch.simple_switch_runner import make_switch
from simple_switch.test_context import make_bmv_context
from simple_switch.compile import compile_p4


from p4client.p4grpc import P4RuntimeGRPC
from p4client.fields import MulticastGroup
from p4client.fields import MacAddress

from scapy.all import Ether, ICMP, IP, get_if_hwaddr, sendp
from threading import Thread, Event

import pytest
import os
import time

SWITCH_NAME = f'meow'
BRIDGE_NAME = f'simpleswitchbr0'
NETWORK_NAME = f'{SWITCH_NAME}_net'
GRPC_PORT = 9559




def configure_switch(controller):
    controller.master_arbitration_update()
    time.sleep(1)

    info_data = open(p4info, 'rb').read()
    bin_data = open(compiled, 'rb').read()
    controller._set_info(info_data)
    controller.configure_forwarding_pipeline(bin_data)

    print('Writing broadcast multicast group')
    controller.write_multicast(
        group_id=100,
        replicas=[
            {'egress_port': 0, 'instance': 42},
            {'egress_port': 1, 'instance': 42},
            {'egress_port': 2, 'instance': 42},
            {'egress_port': 3, 'instance': 42},
        ])
    controller.write_table(
        table_name='MyIngress.dmac_table',
        match_fields={
            'hdr.ethernet.dstAddr': MacAddress('ff:ff:ff:ff:ff:ff')
        },
        action_name='MyIngress.multicast_forward',
        action_params={
            'mcast_grp': MulticastGroup(100)
        }
    )



def control_thread(controller, shutdown_event):
    while not shutdown_event.is_set():
        msg = controller.get_message(0.1)
        if msg is None:
            continue
        print('received msg')
        if msg.WhichOneof('update') == 'digest':
            print('received digest')
            digests = msg.digest
            for entry in digests.data:
                mac = entry.struct.members[0]
                port = entry.struct.members[1]
                controller.write_table(
                    table_name='MyIngress.smac_table',
                    match_fields={
                        'hdr.ethernet.srcAddr': MacAddress.deserialise(mac.bitstring)
                    },
                    action_name='MyIngress.noop',
                )
                controller.write_table(
                    table_name='MyIngress.dmac_table',
                    match_fields={
                        'hdr.ethernet.dstAddr': MacAddress.deserialise(mac.bitstring)
                    },
                    action_name='MyIngress.mac_forward',
                    action_params={
                        'port': EgressSpec.deserialise(port.bitstring)
                    }
                )
            controller.acknowledge_digest_list(msg.digest.digest_id,
                    msg.digest.list_id)






dir_path = os.path.dirname(os.path.realpath(__file__))
compiled, p4info = compile_p4(dir_path, 'mac_learning.p4')

context = make_bmv_context(config,
        compiled,
        p4info,
        control_function=control_thread,
        configure=configure_switch)


def test_received_packet(context):
    pkt = Ether(src=get_if_hwaddr('h1eth0'), dst='ff:ff:ff:ff:ff:ff')/IP(
            src='10.0.0.1',
            dst='255.255.255.255')/ICMP()

    result1 = context.expect('h2eth0', saw_packet_equals_sent(pkt))
    result2 = context.expect('h3eth0', saw_packet_equals_sent(pkt))
    result3 = context.expect('h4eth0', saw_packet_equals_sent(pkt))

    sendp(pkt, iface='h2eth0')

    assert(result1.result() == True)
    print("received 1!")
    assert(result2.result() == True)
    print("received 2!")
    assert(result3.result() == True)
    print("received 3!")

def test_received_packet2(context):
    print('\n\n\n')
    # time.sleep(10)
    pkt = Ether(src=get_if_hwaddr('h1eth0'), dst='ff:ff:ff:ff:ff:ff')/IP(
            src='10.0.0.2',
            dst='255.255.255.255')/ICMP(type=8, code=0)/b'from h1h1eth0'

    result1a = context.expect('h2eth0', saw_packet_equals_sent(pkt))
    result2a = context.expect('h2h1eth0', saw_packet_equals_sent(pkt))
    result3a = context.expect('h4h1eth0', saw_packet_equals_sent(pkt))

    sendp(pkt, iface='h1eth0')
    assert(result1a.result() == True)
    print("received 1!")
    assert(result2a.result() == True)
    print("received 2!")
    assert(result3a.result() == True)
    print("received 3!")





