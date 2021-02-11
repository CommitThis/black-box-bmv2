from scapy.all import Ether, IP, UDP, TCP, ICMP, Dot1Q, Packet
import enum


class TimedOut:
    pass


class Write:
    def __init__(self, file, predicate):
        self._file = file
        self._pred = predicate

    def on_packet(self, pkt):
        self._pred.on_packet(pkt)

    def stop_condition(self, pkt) -> bool:
        self._file.write(pkt)
        return self._pred.stop_condition(pkt)

    def on_finish(self, timed_out):
        self._pred.on_finish(timed_out)




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
    def __init__(self, packet):
        # Reload packet to generate CRC
        self._packet = packet.__class__(bytes(packet))
        self._saw_pkt = False

    def stop_condition(self, packet):
        self._saw_pkt = packet == self._packet
        return self._saw_pkt

    def on_finish(self, timed_out):
        return self._saw_pkt



class did_not_see_packet_equals_sent(Predicate):
    def __init__(self, packet):
        self._packet = packet.__class__(bytes(packet))
        self._saw_pkt = False

    def stop_condition(self, packet):
        self._saw_pkt = packet == self._packet
        return self._saw_pkt
        
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


class only_saw(Predicate):
    def __init__(self, packet):
        self._packet = packet.__class__(bytes(packet))
        self._seen_count = None
        self._expected = None
        self._method = None

    def on_packet(self, packet):
        if self._packet == packet:
            self._seen_count += 1
    
    def on_finish(self):
        return self._seen_count == self._expected

    def once(self):
        self._count = 1
        return self

    def count(self, n):
        self._count = n
        return self


