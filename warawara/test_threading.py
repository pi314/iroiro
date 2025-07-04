import threading

from .lib_test_utils import *

import warawara as wara


class TestLock(TestCase):
    def test_lock(self):
        my_lock = wara.Lock()
        py_lock = threading.Lock()
        self.eq(type(my_lock.lock), type(py_lock))

        self.false(my_lock.locked)

        with my_lock:
            self.true(my_lock.locked)

        self.false(my_lock.locked)

        with my_lock.acquire() as ac:
            self.true(ac)
            self.true(my_lock.locked)

            with my_lock.acquire(blocking=False) as ac2:
                self.false(ac2)
                self.true(ac2.locked)

            self.true(ac)
            self.true(my_lock.locked)

        self.false(my_lock.locked)

    def test_rlock(self):
        my_lock = wara.RLock()
        py_lock = threading.RLock()
        self.eq(type(my_lock.lock), type(py_lock))

        self.eq(my_lock.locked, 0)
        with my_lock:
            self.eq(my_lock.locked, 1)
            with my_lock:
                self.eq(my_lock.locked, 2)
            self.eq(my_lock.locked, 1)
        self.eq(my_lock.locked, 0)
