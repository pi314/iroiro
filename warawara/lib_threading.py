import threading
import time

from .internal_utils import exporter
export, __all__ = exporter()


@export
class Timer:
    def __init__(self, func, interval=None):
        self.func = func
        self.interval = interval
        self.args = None
        self.kwargs = None
        self.ret = None

        self.rlock = threading.RLock()
        self.timer = None
        self._expired = threading.Event()
        self._canceled = threading.Event()

    def callback(self, *args, **kwargs):
        self._expired.set()
        with self.rlock:
            self.timer = None
        self.ret = self.func(*args, **kwargs)

    def start(self, interval=None, args=None, kwargs=None):
        with self.rlock:
            if self.timer:
                return False

            self.args = args
            self.kwargs = kwargs

            self._expired.clear()
            self._canceled.clear()
            self.timer = threading.Timer(
                    interval or self.interval, self.callback,
                    self.args or [], self.kwargs or {})
            self.timer.start()
            return True

    def cancel(self):
        with self.rlock:
            if not self.timer:
                return False

            self.timer.cancel()
            self.timer = None
            if not self.expired:
                self._canceled.set()
            return self.canceled

    def join(self):
        return self.timer.join()

    @property
    def active(self):
        with self.rlock:
            return self.timer is not None

    @property
    def expired(self):
        with self.rlock:
            return self._expired.is_set()

    @property
    def idle(self):
        with self.rlock:
            return not self.active or self.expired

    @property
    def canceled(self):
        with self.rlock:
            return not self.active and not self.expired


class Throttler:
    def __init__(self, func, interval):
        self.func = func
        self.interval = interval

        self.timestamp = 0
        self.timer = Timer(self.lopri)

        self.trtl_lock = threading.Lock()
        self.main_lock = threading.Lock()

    def callback(self, *args, **kwargs):
        ret = self.func(*args, **kwargs)
        self.timestamp = time.time()
        return ret

    def lopri(self, *args, **kwargs):
        try:
            # throttling: block simultaneous callers
            ll = self.trtl_lock.acquire(blocking=False)
            if not ll:
                return False

            # throttling: block simultaneous callers
            if self.timer.active:
                return False

            # throttling: defer fast callers
            delta = time.time() - self.timestamp
            if delta < self.interval:
                return self.timer.start(self.interval - delta, args, kwargs)

            try:
                aq = self.main_lock.acquire(blocking=False)
                if not aq:
                    return False

                self.callback(*args, **kwargs)
                return True
            finally:
                if aq:
                    self.main_lock.release()

        finally:
            if ll:
                self.trtl_lock.release()

    def hipri(self, *args, **kwargs):
        with self.main_lock:
            self.timer.cancel()
            return self.callback(*args, **kwargs)
