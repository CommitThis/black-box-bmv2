import pytest
import time

from scapy.all import Ether, IP, TCP, Dot1Q, get_if_hwaddr, sendp
from packettest.test_context import make_test_context
from packettest.predicates import received_packet
from packettest.predicates import timed_out
from packettest.predicates import saw_src_mac
from packettest.predicates import saw_dst_mac
from packettest.predicates import did_not_see_src_mac
from packettest.predicates import did_not_see_dst_mac
from packettest.predicates import saw_vlan_tag
from packettest.predicates import did_not_see_vlan
from packettest.predicates import saw_packet_equals_sent
from packettest.predicates import packet_count_was
from packettest.predicates import packet_count

iface = 'dummy0'

src_mac = get_if_hwaddr(iface)
dst_mac = 'ff:ff:ff:ff:ff:ff'
tcp_pkt = Ether(src=src_mac, dst=dst_mac) / \
	IP(src='221.221.221.221', dst='17.17.17.17') / TCP(sport=3456, dport=43)

vlan_102_pkt = Ether(src=src_mac, dst=dst_mac) / Dot1Q(vlan=102) / \
	IP(src='221.221.221.221', dst='17.17.17.17') / TCP(sport=3456, dport=43)

vlan_202_pkt = Ether(src=src_mac, dst=dst_mac) / Dot1Q(vlan=202) / \
	IP(src='221.221.221.221', dst='17.17.17.17') / TCP(sport=3456, dport=43)

context = make_test_context()





def test_received_packet_returns_true_when_packet_sent(context):
	future = context.expect(iface, received_packet)
	sendp(tcp_pkt, iface=iface)
	assert(future.result() == True)


''' This may fail -- packets may be flying around the interface for any number
	of reasons '''
def test_received_packet_returns_false_when_packet_not_sent(context):
	future = context.expect(iface, received_packet)
	assert(future.result() == False)


''' This may fail -- packets may be flying around the interface for any number
	of reasons '''
def test_timed_out_returns_true_when_no_packet_sent(context):
	future = context.expect(iface, timed_out)
	assert(future.result() == True)


def test_timed_out_returns_false_when_packet_sent(context):
	future = context.expect(iface, timed_out)
	sendp(tcp_pkt, iface=iface)
	assert(future.result() == False)


def test_should_saw_src_mac_returns_true_when_mac_present(context):
	future = context.expect(iface, saw_src_mac(src_mac))
	sendp(tcp_pkt, iface=iface)
	assert(future.result() == True)


def test_should_saw_src_mac_returns_false_when_mac_not_present(context):
	future = context.expect(iface, saw_src_mac('ab:ab:ab:ab:ab:ab'))
	sendp(tcp_pkt, iface=iface)
	assert(future.result() == False)


def test_did_not_see_src_mac_returns_true_when_mac_not_present(context):
	future = context.expect(iface, did_not_see_src_mac('ab:ab:ab:ab:ab:ab'))
	sendp(tcp_pkt, iface=iface)
	assert(future.result() == True)


def test_did_not_see_src_mac_returns_false_when_mac_present(context):
	future = context.expect(iface, did_not_see_src_mac(src_mac))
	sendp(tcp_pkt, iface=iface)
	assert(future.result() == False)


def test_should_saw_dst_mac_returns_true_when_mac_present(context):
	future = context.expect(iface, saw_dst_mac(dst_mac))
	sendp(tcp_pkt, iface=iface)
	assert(future.result() == True)


def test_should_saw_dst_mac_returns_false_when_mac_not_present(context):
	future = context.expect(iface, saw_dst_mac('ab:ab:ab:ab:ab:ab'))
	sendp(tcp_pkt, iface=iface)
	assert(future.result() == False)


def test_did_not_see_dst_mac_returns_true_when_mac_not_present(context):
	future = context.expect(iface, did_not_see_dst_mac('ab:ab:ab:ab:ab:ab'))
	sendp(tcp_pkt, iface=iface)
	assert(future.result() == True)


def test_did_not_see_dst_mac_returns_false_when_mac_present(context):
	future = context.expect(iface, did_not_see_dst_mac(dst_mac))
	sendp(tcp_pkt, iface=iface)
	assert(future.result() == False)


def test_saw_vlan_tag_returns_true_when_tag_sent(context):
	future = context.expect(iface, saw_vlan_tag(102))
	sendp(vlan_102_pkt, iface=iface)
	assert(future.result() == True)


def test_saw_vlan_tag_returns_false_when_tag_not_sent(context):
	future = context.expect(iface, saw_vlan_tag(202))
	sendp(vlan_102_pkt, iface=iface)
	assert(future.result() == False)


def test_saw_vlan_tag_returns_false_when_vlan_not_sent(context):
	future = context.expect(iface, saw_vlan_tag(102))
	sendp(tcp_pkt, iface=iface)
	assert(future.result() == False)


def test_did_not_see_vlan_returns_true_when_vlan_not_present(context):
	future = context.expect(iface, did_not_see_vlan)
	sendp(tcp_pkt, iface=iface)
	assert(future.result() == True)


def test_did_not_see_vlan_returns_false_when_vlan_present(context):
	future = context.expect(iface, did_not_see_vlan)
	sendp(vlan_102_pkt, iface=iface)
	assert(future.result() == False)


def test_received_packet_equals_sent_returns_true(context):
	tmp = tcp_pkt.__class__(bytes(tcp_pkt)) # Calculates checksum
	future = context.expect(iface, saw_packet_equals_sent(tmp))
	sendp(tcp_pkt, iface=iface)
	assert(future.result() == True)


def test_received_packet_equals_sent_returns_false(context):
	future = context.expect(iface, saw_packet_equals_sent(tcp_pkt))
	sendp(vlan_102_pkt, iface=iface)
	assert(future.result() == False)


''' This may fail -- packets may be flying around the interface for any number
	of reasons '''
def test_packet_count_was_returns_true_when_correct_count_received(context):
	''' If sending on loopback, sniffer will see packet twice '''
	future = context.expect(iface, packet_count_was(6))
	sendp(tcp_pkt, iface=iface)
	sendp(tcp_pkt, iface=iface)
	sendp(tcp_pkt, iface=iface)
	assert(future.result() == True)


''' This may fail -- packets may be flying around the interface for any number
	of reasons '''
def test_packet_count_was_returns_false_when_correct_count_not_received(context):
	future = context.expect(iface, packet_count_was(5))
	sendp(tcp_pkt, iface=iface)
	sendp(tcp_pkt, iface=iface)
	sendp(tcp_pkt, iface=iface)
	assert(future.result() == False)


''' This may fail -- packets may be flying around the interface for any number
	of reasons '''
def test_packet_count_returns_correct_number_of_packets(context):
	count = context.expect(iface, packet_count)
	sendp(tcp_pkt, iface=iface)
	sendp(tcp_pkt, iface=iface)
	sendp(tcp_pkt, iface=iface)
	assert(count.result() == 6)


'''
Testing timeouts
'''

def test_packet_count_with_timeout(context):
	count = context.expect(iface, packet_count, timeout=1.0)
	sendp(tcp_pkt, iface=iface)
	sendp(tcp_pkt, iface=iface)
	sendp(tcp_pkt, iface=iface)
	time.sleep(3)
	# Should have joined by this point
	sendp(tcp_pkt, iface=iface)
	sendp(tcp_pkt, iface=iface)
	sendp(tcp_pkt, iface=iface)
	assert(count.result() == 6)


def test_packet_count_with_notify(context):
	count = context.expect(iface, packet_count, timeout=10.0)
	start_time = time.time()
	count.notify()
	count.result()
	duration = time.time() - start_time
	assert(duration < 2)


def test_packet_count_without_notify(context):
	count = context.expect(iface, packet_count, timeout=5.0)
	start_time = time.time()
	time.sleep(1)
	count.result()
	duration = time.time() - start_time
	assert(duration >= 5)