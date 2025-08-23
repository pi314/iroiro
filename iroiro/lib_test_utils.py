import unittest
import threading


from .internal_utils import exporter
export, __all__ = exporter()


@export
class Checkpoint:
    def __init__(self, testcase):
        self.testcase = testcase
        self.checkpoint = threading.Event()

    def set(self):
        self.checkpoint.set()

    def clear(self):
        self.checkpoint.clear()

    def wait(self):
        self.checkpoint.wait()

    def is_set(self):
        return self.checkpoint.is_set()

    def check(self, is_set=True):
        self.testcase.eq(
                self.checkpoint.is_set(),
                is_set,
                'Checkpoint was' + (' ' if self.checkpoint.is_set() else ' not ') + 'set')

    def __bool__(self):
        return self.is_set()


@export
class TestCase(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.eq = self.assertEqual
        self.ne = self.assertNotEqual
        self.le = self.assertLessEqual
        self.lt = self.assertLess
        self.ge = self.assertGreaterEqual
        self.gt = self.assertGreater
        self.true = self.assertTrue
        self.false = self.assertFalse
        self.raises = self.assertRaises

    def checkpoint(self):
        return Checkpoint(self)

    class run_in_thread:
        def __init__(self, func, args=tuple(), kwargs=dict()):
            self.func = func
            self.args = args
            self.kwargs = kwargs
            self.thread = None

        def __enter__(self, *args):
            if self.thread is not None:
                raise RuntimeError('Thread objects cannot be reused')
            self.thread = threading.Thread(target=self.func, args=self.args, kwargs=self.kwargs)
            self.thread.daemon = True
            self.thread.start()

        def __exit__(self, exc_type, exc_value, traceback):
            self.thread.join()

    def patch(self, name, side_effect):
        patcher = unittest.mock.patch(name, side_effect=side_effect)
        thing = patcher.start()
        self.addCleanup(patcher.stop)
        return thing


@export
class RunMocker:
    def __init__(self):
        self.rules = {}

    def register(self, cmd, callback=None, *, stdout=None, stderr=None, returncode=None):
        if not isinstance(cmd, str):
            raise ValueError('cmd must be a str')

        if callback is not None and not isinstance(callback, Exception) and not callable(callback):
            raise TypeError('callback should be an Exception or a callable')

        by_callback = callback
        by_output = (stdout, stderr, returncode)

        if by_callback is None and by_output == (None, None, None):
            raise ValueError('Meaningless behavior')

        if by_callback is not None and by_output != (None, None, None):
            raise ValueError('Ambiguous behavior')

        if cmd not in self.rules:
            self.rules[cmd] = []

        if by_callback:
            if isinstance(by_callback, Exception):
                behavior = by_callback
            else:
                def behavior(proc, *args):
                    proc.cmd = (cmd, *args)
                    return by_callback(proc, *args)

        else:
            def behavior(proc, *args):
                proc.cmd = (cmd, *args)
                if by_output[0]:
                    proc.stdout.writelines(by_output[0])
                if by_output[1]:
                    proc.stderr.writelines(by_output[1])
                return by_output[2]

        self.rules[cmd].append(behavior)
        return self

    def __call__(self, cmd, *,
                 stdin=None, stdout=True, stderr=True,
                 encoding='utf8', rstrip='\r\n',
                 bufsize=-1,
                 env=None,
                 wait=True):
        if not cmd:
            raise ValueError('command is empty')

        if isinstance(cmd, str):
            cmd = [cmd]

        matched_callbacks = None

        if cmd[0] in self.rules:
            matched_callbacks = self.rules[cmd[0]]
        elif '*' in self.rules:
            matched_callbacks = self.rules['*']
        else:
            raise ValueError('Unregistered command: {}'.format(cmd))

        behavior = matched_callbacks[0]
        if len(matched_callbacks) > 1:
            matched_callbacks.pop(0)

        if isinstance(behavior, Exception):
            raise behavior

        from .lib_subproc import command
        p = command([behavior] + cmd[1:],
                    stdin=stdin, stdout=stdout, stderr=stderr,
                    encoding=encoding, rstrip=rstrip,
                    bufsize=bufsize,
                    env=env)
        p.run(wait=wait)
        return p
