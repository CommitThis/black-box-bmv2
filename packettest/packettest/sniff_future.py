from concurrent.futures import wait

class SniffFuture:
    def __init__(self, predicate, future):
        self._future = future
        self._result = None
        self._predicate = predicate

    def result(self):
        exception = self._future.exception()
        if exception is not None:
            raise exception
        self._result = self._future.result()
        return self._result


    def assert_result(self):
        result_ = self.result()
        assert(result_ == True), f'{self._predicate._detail()}'


    def __repr__(self):
        if self._future.done():
            return f'SniffFuture(done={self._future.done()}, result={self._result})'
