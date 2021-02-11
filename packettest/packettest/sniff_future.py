from concurrent.futures import wait

class SniffFuture:
    def __init__(self, sniffer, future):
        self._future = future

    def result(self):
        exception = self._future.exception()
        if exception is not None:
            raise exception
        return self._future.result()

    def __repr__(self):
        if self._future.done():
            return f'SniffFuture(done={self._future.done()}, result={self._result})'
