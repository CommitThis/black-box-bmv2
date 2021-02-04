from scapy.all import Ether, IP, UDP, TCP, ICMP, Dot1Q, Packet
import enum


class TimedOut:
	pass



class Predicate:
	def on_packet(self, pkt):
		pass

	def stop_condition(self, pkt) -> bool:
		pass

	def on_finish(self, timed_out):
		pass

'''
It is quicker to find something than not find something!
'''

class received_packet(Predicate):
	''' Will only get called if a packet is received '''
	def stop_condition(self, pkt):
		return True

	def on_finish(self, timed_out):
		return not timed_out



class timed_out(Predicate):
	def stop_condition(self, pkt):
		return True

	def on_finish(self, timed_out):
		return timed_out



class saw_src_mac(Predicate):
	def __init__(self, mac):
		self._mac = mac

	''' Need to do result setting and stop condition here as the stop filter is
		called before the packet function '''
	def stop_condition(self, pkt):
		return pkt.haslayer(Ether) and pkt[Ether].src == self._mac

	def on_finish(self, timed_out):
		return not timed_out



class did_not_see_src_mac(Predicate):
	def __init__(self, mac):
		super().__init__()
		self._mac = mac
		self._results = []

	def on_packet(self, pkt):
		if pkt.haslayer(Ether):
			self._results.append(pkt[Ether].src)

	def on_finish(self, timed_out):
		return self._mac not in self._results



class saw_dst_mac(Predicate):
	def __init__(self, mac):
		self._mac = mac

	''' Need to do result setting and stop condition here as the stop filter is
		called before the packet function '''
	def stop_condition(self, pkt):
		return pkt.haslayer(Ether) and pkt[Ether].dst == self._mac

	def on_finish(self, timed_out):
		return not timed_out



class did_not_see_dst_mac(Predicate):
	def __init__(self, mac):
		super().__init__()
		self._mac = mac
		self._results = []

	def on_packet(self, pkt):
		if pkt.haslayer(Ether):
			self._results.append(pkt[Ether].dst)

	def on_finish(self, timed_out):
		return self._mac not in self._results



class saw_vlan_tag(Predicate):
	def __init__(self, tag):
		self._tag = tag

	def stop_condition(self, pkt):
		return pkt.haslayer(Dot1Q) and pkt[Dot1Q].vlan == self._tag

	def on_finish(self, timed_out):
		return not timed_out



class did_not_see_vlan(Predicate):

	def stop_condition(self, pkt):
		return pkt.haslayer(Dot1Q)

	def on_finish(self, timed_out):
		return timed_out



class saw_packet_equals_sent(Predicate):
	def __init__(self, pkt):
		super().__init__()
        # Reload packet to generate CRC
		tmp = pkt.__class__(bytes(pkt))

		self._pkt = tmp

	def stop_condition(self, pkt):
		return self._pkt == pkt

	def on_finish(self, timed_out):
		return not timed_out


class did_not_see_packet_equals_sent(Predicate):
	def __init__(self, pkt):
		super().__init__()
		tmp = pkt.__class__(bytes(pkt))
		self._pkt = tmp
		self._saw_pkt = False

	# def stop_condition(self, pkt):
	# 	return self._pkt == pkt

	def on_packet(self, pkt):
		if pkt == self._pkt:
			self._saw_pkt = True

	def on_finish(self, timed_out):
		return not self._saw_pkt




class packet_count_was(Predicate):

	def __init__(self, count):
		self._expected_count = count
		self._received_count = 0

	def on_packet(self, pkt):
		self._received_count += 1

	def on_finish(self, timed_out):
		return self._received_count == self._expected_count
		


class packet_count(Predicate):

	def __init__(self):
		self._received_count = 0

	def on_packet(self, pkt):
		self._received_count += 1

	def on_finish(self, timed_out):
		return self._received_count