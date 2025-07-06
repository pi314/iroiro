import threading
import time

from .internal_utils import exporter
export, __all__ = exporter()


class LockWrapper:
    def __init__(self, lock_type):
        self.lock = lock_type()
        self._locked = 0

    def acquire(self, blocking=True, timeout=-1):
        acquired = self.lock.acquire(blocking=blocking, timeout=timeout)
        if acquired:
            self._locked += 1
        return Locked(self.lock, acquired)

    def release(self):
        self._locked -= 1
        return self.lock.release()

    def __enter__(self):
        return self.acquire()

    def __exit__(self, exc_type, exc_value, traceback):
        return self.release()

    @property
    def locked(self):
        if not hasattr(self.lock, 'locked'):
            return self._locked
        return self.lock.locked()


@export
class Lock(LockWrapper):
    def __init__(self):
        super().__init__(threading.Lock)


@export
class RLock(LockWrapper):
    def __init__(self):
        super().__init__(threading.RLock)


class Locked:
    def __init__(self, lock, acquired):
        self.lock = lock
        self.acquired = acquired

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.acquired:
            return self.lock.release()

    def __getattr__(self, attr):
        return getattr(self.lock, attr)

    def __bool__(self):
        return self.acquired


@export
class Timer:
    def __init__(self, func, interval=None):
        self.func = func
        self.interval = interval
        self.args = None
        self.kwargs = None
        self.ret = None

        self.rlock = RLock()
        self.timer = None
        self._expired = threading.Event()
        self._canceled = threading.Event()

    def callback(self, *args, **kwargs):
        with self.rlock:
            self._expired.set()
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
            self._canceled.set()
            return True

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
            return self._canceled.is_set()


class Throttler:
    def __init__(self, func, interval):
        self.func = func
        self.interval = interval

        self.timestamp = 0
        self.timer = Timer(self.lopri)

        self.trtl_lock = Lock()
        self.main_lock = Lock()

    def callback(self, *args, **kwargs):
        ret = self.func(*args, **kwargs)
        self.timestamp = time.time()
        return ret

    def lopri(self, *args, **kwargs):
        # throttling: block simultaneous callers
        with self.trtl_lock.acquire(blocking=False) as tl:
            if not tl:
                return False

            # throttling: block simultaneous callers
            if self.timer.active:
                return False

            # throttling: defer fast callers
            delta = time.time() - self.timestamp
            if delta < self.interval:
                return self.timer.start(self.interval - delta, args, kwargs)

            with self.main_lock.acquire(blocking=False) as ml:
                if not ml:
                    return False

                self.callback(*args, **kwargs)
                return True

    def hipri(self, *args, **kwargs):
        with self.main_lock:
            self.timer.cancel()
            return self.callback(*args, **kwargs)

    def __call__(self, blocking=False, args=None, kwargs=None):
        if blocking:
            return self.hipri(*args, **kwargs)
        else:
            return self.lopri(*args, **kwargs)
