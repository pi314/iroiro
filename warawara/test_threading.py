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


class TestTimer(TestCase):
    def test_timer_start_expire(self):
        fake_time = FakeTime()
        for name, func in fake_time.patch():
            self.patch(name, func)

        checkpoint = self.checkpoint()

        def foo(*args, **kwargs):
            checkpoint.set()

        timer = wara.Timer(foo, 10)
        self.false(timer.active)
        self.false(timer.expired)
        self.true(timer.idle)
        self.false(timer.canceled)

        timer.start(args=['wah'], kwargs={'kw': 'args'})
        self.true(timer.active)
        self.false(timer.expired)
        self.false(timer.idle)
        self.false(timer.canceled)
        checkpoint.check(False)

        import time
        time.sleep(10)
        checkpoint.wait()
        self.false(timer.active)
        self.true(timer.expired)
        self.true(timer.idle)
        self.false(timer.canceled)

    def test_timer_start_cancel(self):
        fake_time = FakeTime()
        for name, func in fake_time.patch():
            self.patch(name, func)

        checkpoint = self.checkpoint()

        def foo(*args, **kwargs):
            checkpoint.set()

        timer = wara.Timer(foo, 10)
        self.false(timer.active)
        self.false(timer.expired)
        self.true(timer.idle)
        self.false(timer.canceled)

        timer.start(args=['wah'], kwargs={'kw': 'args'})
        self.true(timer.active)
        self.false(timer.expired)
        self.false(timer.idle)
        self.false(timer.canceled)
        checkpoint.check(False)

        self.true(timer.cancel())
        checkpoint.check(False)
        self.false(timer.active)
        self.false(timer.expired)
        self.true(timer.idle)
        self.true(timer.canceled)

    def test_timer_start_expire_cancel(self):
        fake_time = FakeTime()
        for name, func in fake_time.patch():
            self.patch(name, func)

        checkpoint = self.checkpoint()

        def foo(*args, **kwargs):
            checkpoint.set()

        timer = wara.Timer(foo, 10)
        self.false(timer.active)
        self.false(timer.expired)
        self.true(timer.idle)
        self.false(timer.canceled)

        timer.start(args=['wah'], kwargs={'kw': 'args'})
        self.true(timer.active)
        self.false(timer.expired)
        self.false(timer.idle)
        self.false(timer.canceled)
        checkpoint.check(False)

        import time
        time.sleep(10)
        checkpoint.wait()
        self.false(timer.active)
        self.true(timer.expired)
        self.true(timer.idle)
        self.false(timer.canceled)

        self.false(timer.cancel())
        self.false(timer.active)
        self.true(timer.expired)
        self.true(timer.idle)
        self.false(timer.canceled)

    def test_timer_start_twice(self):
        fake_time = FakeTime()
        for name, func in fake_time.patch():
            self.patch(name, func)

        checkpoint = self.checkpoint()

        def foo(*args, **kwargs):
            checkpoint.set()

        timer = wara.Timer(foo, 10)
        self.false(timer.active)
        self.false(timer.expired)
        self.true(timer.idle)
        self.false(timer.canceled)

        timer.start(args=['wah'], kwargs={'kw': 'args'})
        self.true(timer.active)
        self.false(timer.expired)
        self.false(timer.idle)
        self.false(timer.canceled)
        checkpoint.check(False)

        res = timer.start(args=['wah'], kwargs={'kw': 'args'})
        self.false(res)
        self.true(timer.active)
        self.false(timer.expired)
        self.false(timer.idle)
        self.false(timer.canceled)

    def test_timer_idle_cancel(self):
        fake_time = FakeTime()
        for name, func in fake_time.patch():
            self.patch(name, func)

        def foo(*args, **kwargs):
            pass

        timer = wara.Timer(foo, 10)
        self.false(timer.active)
        self.false(timer.expired)
        self.true(timer.idle)
        self.false(timer.canceled)

        self.false(timer.cancel())
        self.false(timer.active)
        self.false(timer.expired)
        self.true(timer.idle)
        self.false(timer.canceled)

    def test_timer_join(self):
        fake_time = FakeTime()
        for name, func in fake_time.patch():
            self.patch(name, func)

        checkpoint = self.checkpoint()

        def foo(*args, **kwargs):
            checkpoint.set()

        timer = wara.Timer(foo, 10)
        self.false(timer.active)
        self.false(timer.expired)
        self.true(timer.idle)
        self.false(timer.canceled)

        timer.start(args=['wah'], kwargs={'kw': 'args'})
        self.true(timer.active)
        self.false(timer.expired)
        self.false(timer.idle)
        self.false(timer.canceled)
        checkpoint.check(False)

        e = threading.Event()
        def move_time():
            e.wait()
            import time
            for i in range(10):
                time.sleep(i)

        t = threading.Thread(target=move_time, daemon=True)
        t.start()

        e.set()
        timer.join()
        t.join()
        checkpoint.wait()
        self.false(timer.active)
        self.true(timer.expired)
        self.true(timer.idle)
        self.false(timer.canceled)
