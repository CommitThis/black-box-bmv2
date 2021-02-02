class SniffFuture:
	def __init__(self, sniffer, monitor_lock, future):
		self._future = future
		self._sniffer = sniffer
		self._monitor_lock = monitor_lock
		self._result = None
	
	def result(self):
		if self._result == None:
			self._result = self._future.result()
		return self._result

	def notify(self):
		with self._monitor_lock:
			self._sniffer.stop()

	def __repr__(self):
		if self._future.done():
			return f'SniffFuture(done={self._future.done()}, result={self._result})'