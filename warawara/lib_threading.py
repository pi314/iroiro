import threading

from .internal_utils import exporter
export, __all__ = exporter()


@export
class Timer:
    def __init__(self, interval, func):
        self.interval = interval
        self.func = func
        self.args = None
        self.kwargs = None

        self.rlock = threading.RLock()
        self.timer = None
        self._expired = threading.Event()

    def start(self, args=None, kwargs=None):
        with self.rlock:
            if self.timer:
                return False

            self.args = args
            self.kwargs = kwargs

            def func(*args, **kwargs):
                self._expired.set()
                self.func(*args, **kwargs)

            self._expired.clear()
            self.timer = threading.Timer(
                    self.interval, func,
                    self.args or [], self.kwargs or {})
            self.timer.start()
            return True

    def cancel(self):
        with self.rlock:
            self.timer.cancel()
            self.timer = None
            self.args = None
            self.kwargs = None
            return not self.expired

    @property
    def active(self):
        with self.rlock:
            return self.timer is not None

    @property
    def expired(self):
        with self.rlock:
            return self._expired.is_set()
