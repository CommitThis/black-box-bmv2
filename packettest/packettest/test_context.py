from packettest.sniff_future import SniffFuture

from concurrent.futures import ThreadPoolExecutor
from threading import Lock, Event, Thread

from scapy.all import AsyncSniffer

import pytest

class TestContext:
	''' '''

	__test__ = False # So pytest doesn't collect this class as a test

	DEFAULT_TIMEOUT = 5

	def __init__(self):
		self._executor = ThreadPoolExecutor(max_workers=4)
		self._monitors = []
		self._monitor_lock = Lock()

	def monitor(self, 
			iface: str,
			prn: callable=lambda p: print(p.summary()),
			count: int=0,
			session=None,
			filter: str=None,
			lfilter: callable=None):
		
		ready_event = Event()

		if isinstance(iface, veth.Interface):
			iface = iface.name

		def notify_started():
			''' Callback used by sniffer to event when it's actually started '''
			nonlocal ready_event
			ready_event.set()

		sniffer = AsyncSniffer(iface=iface, 
			session=session,
			count=count,
			prn=prn,
			monitor=True,
			filter=filter,
			lfilter=lfilter,
			started_callback=notify_started)

		sniffer.start()


		def join():
			''' Start task to join sniffer, this will return as soon as the
			sniffer has finished, or until it's timeout has been reached.
			returns result which will be available through the future
			returned by the thread executor. '''
			nonlocal sniffer
			print(f'sniffer {str(sniffer)} joining')
			sniffer.join()
			print(f'sniffer {str(sniffer)} joined')



		''' Wait until sniffer has actually started '''
		if not ready_event.wait(timeout=5):
			raise Exception('Sniffer did not start!')

		with self._monitor_lock:
			self._monitors.append(sniffer)

		# return SniffFuture(f'monitor {iface}', self._executor.submit(join))
		return self._executor.submit(join)


	def stop(self):
		print('Stopping monitors')
		with self._monitor_lock:
			for monitor in self._monitors:
				if monitor.running:
					monitor.stop()
			for monitor in self._monitors:
				monitor.join()
		print('Monitors stopped')


	def expect(self, 
			iface: str,
			expect_function, #: BasePredicate,
			timeout: float=DEFAULT_TIMEOUT,
			count: int=0):
		''' Sniff interface and check packets with callable

		Function supplied must either return a boolean or nothing (None).
		If the function doesn't return anything, for example because it is only
		printing, return True. This enables use of utility functions to print
		out information without affecting tests.
		'''

		# result = default_result
		ready_event = Event()
		timed_out = True

		if isinstance(expect_function, type):
			expect_function = expect_function()


		def wrapped(pkt):
			''' Wrapper for stop condition. '''
			# nonlocal result, expect, timed_out
			nonlocal expect_function, timed_out
			should_stop: bool = expect_function.stop_condition(pkt) 
			if should_stop == True:
				timed_out = False
			return should_stop


		def notify_started():
			''' Callback used by sniffer to event when it's actually started '''
			nonlocal ready_event
			ready_event.set()


		sniffer = AsyncSniffer(iface=iface, 
			count=count,
			stop_filter=wrapped,
			timeout=timeout,
			prn=expect_function.on_packet,
			started_callback=notify_started)


		''' Need the sniffer to start immediately '''
		sniffer.start()


		def join():
			''' Start task to join sniffer, this will return as soon as the
			sniffer has finished, or until it's timeout has been reached.
			returns result which will be available through the future
			returned by the thread executor. '''
			nonlocal sniffer, timed_out, expect_function
			sniffer.join()
			result = expect_function.on_finish(timed_out)
			return result


		''' Wait until sniffer has actually started '''
		if not ready_event.wait(timeout=5):
			raise Exception('Sniffer did not start!')

		with self._monitor_lock:
			self._monitors.append(sniffer)

		return SniffFuture(
			sniffer, 
			self._monitor_lock, 
			self._executor.submit(join))



def make_test_context():
    @pytest.fixture(scope='module')
    def context_fixture():
        yield TestContext()
    return context_fixture