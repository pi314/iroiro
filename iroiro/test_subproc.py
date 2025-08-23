import threading
import queue

from .lib_test_utils import *

from iroiro import *

import iroiro
stream = iroiro.subproc.stream


def queue_to_list(Q):
    ret = []
    while not Q.empty():
        ret.append(Q.get())
    return ret


class TestEventBroadcaster(TestCase):
    def test_all(self):
        data1 = []
        def handler1(arg):
            data1.append(arg)

        data2 = []
        def handler2(arg):
            data2.append(arg)

        import iroiro
        hub = iroiro.subproc.EventBroadcaster()
        hub.broadcast('...')

        hub += handler1
        hub.broadcast('wah')

        hub += handler2
        hub.broadcast('Wah')

        hub += handler2
        hub.broadcast('WAAAAAH')

        hub -= handler1
        hub.broadcast('wah?')

        hub -= handler2
        hub.broadcast('wow')

        hub -= handler2
        hub.broadcast('bye')

        self.eq(data1, ['wah', 'Wah', 'WAAAAAH'])
        self.eq(data2, ['Wah', 'WAAAAAH', 'WAAAAAH', 'wah?', 'wah?', 'wow'])


class TestStream(TestCase):
    def test_stream_basic_io(self):
        s = stream()
        self.eq(s.keep, False)

        s.writeline('line1')
        s.writeline('line2')
        s.writeline('line3')
        self.false(s.closed)

        s.close()
        self.true(s.closed)

        self.eq(s.lines, [])
        self.eq(s.readline(), 'line1')
        self.eq(s.readline(), 'line2')
        self.eq(s.readline(), 'line3')

    def test_stream_iter(self):
        s = stream()
        self.eq(s.keep, False)
        s.writelines(['line1', 'line2', 'line3'])

        i = iter(s)
        self.eq(next(i), 'line1')
        self.eq(next(i), 'line2')
        self.eq(next(i), 'line3')

        s.close()

        with self.raises(StopIteration):
            next(iter(s))

    def test_stream_keep(self):
        s = stream()
        s.keep = True

        lines = ['line1', 'line2', 'line3']
        for line in lines:
            s.writeline(line)

        self.eq(s.lines, lines)
        self.eq(len(s), 3)

        self.false(s.empty)
        self.true(bool(s))

        self.eq(s.readline(), 'line1')
        self.eq(s.readline(), 'line2')
        self.eq(s.readline(), 'line3')

        self.eq(s.lines, lines)
        self.eq(len(s), 3)

    def test_stream_subscribers(self):
        data1 = []
        def handler1(line):
            data1.append(line)

        data2 = []
        def handler2(line):
            data2.append(line)

        Q = queue.Queue()

        s = stream()
        s.welcome([handler1, handler2])
        s.welcome(Q)
        s.welcome(True)

        with self.raises(TypeError):
            s.welcome(s)

        lines = ['line1', 'line2', 'line3']
        s.writelines(lines)

        self.eq(data1, lines)
        self.eq(data2, lines)

    def test_stream_write_after_close(self):
        def should_not_be_called_handler(line):
            self.fail()

        # test in test
        with self.raises(AssertionError):
            should_not_be_called_handler('wah')

        s = stream()
        s.welcome(should_not_be_called_handler)
        s.close()

        s.writeline('line1')

        with self.raises(BrokenPipeError):
            s.writeline('line2', suppress=False)


class TestSubproc(TestCase):
    def test_default_properties(self):
        def prog(proc):
            self.eq(proc[0].readline(), 'line')

        p = run(prog, stdin='line', stdout=False, stderr=False)

    def test_stdout(self):
        p = run('seq 5'.split())
        self.eq(p.stdout.lines, '1 2 3 4 5'.split())

    def test_disable_stdout_and_stderr(self):
        p = command('seq 5'.split(), stdout=None, stderr=None)
        self.true(p.stdout.closed)
        self.true(p.stderr.closed)

    def test_wait_early(self):
        p = command('seq 5'.split())
        p.wait()
        p.run(wait=False)
        p.wait()
        self.eq(p.stdout.lines, '1 2 3 4 5'.split())

    def test_already_running_error(self):
        checkpoint = self.checkpoint()

        def prog(proc, *args):
            checkpoint.wait()

        p = command(prog)
        p.run(wait=False)

        with self.raises(AlreadyRunningError):
            p.run()

        checkpoint.set()
        p.wait()

        p = command(['sleep', 1])
        p.run(wait=False)
        with self.raises(AlreadyRunningError):
            p.run(wait=False)
        p.kill()

    def test_word(self):
        p = run('true')
        self.eq(p.returncode, 0)

        p = run('false')
        self.eq(p.returncode, 1)

    def test_invalid_cmd(self):
        with self.raises(ValueError):
            p = command()
        with self.raises(ValueError):
            p = run()

        for i in ([], True, 3, None, queue.Queue()):
            with self.raises(ValueError):
                command(i)
            with self.raises(ValueError):
                run(i)

    def test_run_with_context_manager(self):
        barrier = threading.Barrier(2)

        def prog(proc, *args):
            barrier.wait()

        with command(prog) as p:
            barrier.wait()

    def test_stdout_nokeep(self):
        p = command('seq 5'.split(), stdout=False)
        p.run()
        self.eq(p.stdout.lines, [])

    def test_keep_trailing_whitespaces(self):
        p = run(['echo', 'a b c '])
        self.eq(p.stdout.lines, ['a b c '])

    def test_callable(self):
        def prog(proc, *args):
            self.eq(args, ('arg1', 'arg2'))
            for idx, line in enumerate(proc[0]):
                proc[(idx % 2) + 1].writeline(line)
            return 2024

        p = run([prog, 'arg1', 'arg2'], stdin=['hello ', 'how are you ', 'im fine ', 'thank you '])
        self.eq(p.stdout.lines, ['hello ', 'im fine '])
        self.eq(p.stderr.lines, ['how are you ', 'thank you '])
        self.eq(p.returncode, 2024)

    def test_stdout_callback(self):
        lines = []
        def callback(line):
            lines.append(line)
        p = command('seq 5'.split(), stdout=callback)
        p.run()
        self.eq(lines, ['1', '2', '3', '4', '5'])

    def test_stdout_queue(self):
        Q = queue.Queue()
        p = command('seq 5'.split(), stdout=Q)
        self.false(p.stdout.keep)
        p.run()
        self.eq(p.stdout.lines, [])
        self.eq(queue_to_list(Q), ['1', '2', '3', '4', '5'])

    def test_multi_ouptut_merge(self):
        def prog(proc, *args):
            for i in range(5):
                proc[1].write(i)
                proc[2].write(i)

        Q = queue.Queue()

        lines = []
        def callback(line):
            lines.append(line)

        self.true(hasattr(Q, 'put'))

        p = command(prog, stdout=(Q, callback, True), stderr=(Q, True))
        p.run()
        self.eq(p.stdout.lines, [0, 1, 2, 3, 4])
        self.eq(p.stderr.lines, [0, 1, 2, 3, 4])
        self.eq(lines, [0, 1, 2, 3, 4])

        self.eq(queue_to_list(Q), [0, 0, 1, 1, 2, 2, 3, 3, 4, 4])

    def test_stdin(self):
        p = command('nl -w 1 -s :'.split(), stdin=['hello', 'world'])
        p.run()
        self.eq(p.stdout.lines, ['1:hello', '2:world'])

    def test_stdin_delayed_write(self):
        data = ['hello', 'world']
        p = command('nl -w 1 -s :'.split(), stdin=data)

        data += ['wow', 'haha']     # ignored
        p.stdin.writeline('wah')    # allow write before run
        p.run(wait=False).wait()

        self.eq(p.stdout.lines, ['1:hello', '2:world', '3:wah'])

    def test_stdin_queue(self):
        Q = queue.Queue()
        p = command('nl -w 1 -s :'.split(), stdin=Q)

        Q.put('pre')

        p.run(wait=False)

        Q.join()
        Q.put('hello')
        Q.put('world')
        Q.join()
        Q.put('wah')
        Q.join()

        p.stdin.close()

        p.wait()
        self.eq(p.stdout.lines, ['1:pre', '2:hello', '3:world', '4:wah'])

    def test_callable_with_pipe(self):
        def prog(proc, *args):
            for line in proc[0]:
                proc[1].writeline(line)
                proc[2].writeline(line)
            return 2024

        p1 = command(prog, stdin=['hello', 'world'])
        p2 = command('nl -w 1 -s :'.split(), stdin=True)
        p3 = command('nl -w 1 -s /'.split(), stdin=True)
        pipe(p1.stdout, p2.stdin)
        pipe(p1.stderr, p3.stdin)

        p1.run()
        p2.run()
        p3.run()

        self.eq(p1.returncode, 2024)
        self.eq(p2.stdout.lines, ['1:hello', '2:world'])
        self.eq(p3.stdout.lines, ['1/hello', '2/world'])

    def test_callable_raises_exception(self):
        def prog(proc, *args):
            # NameError
            n + 1

        with self.raises(NameError):
            p = run(prog)

    def test_loopback(self):
        # Collatz function
        def collatz_function(x):
            return (x // 2) if (x % 2 == 0) else (3 * x + 1)

        def prog(proc, *args):
            for line in proc[0]:
                x = line
                if x == 1:
                    break
                else:
                    proc[1].write(collatz_function(x))

        p = command(prog, stdin=True)

        # loopback
        pipe(p.stdout, p.stdin)

        import time
        t = int(time.time())
        p.stdin.write(t)
        p.run()

        # If this test fails, make sure to check the initial input
        self.eq(p.stdout.lines[-1], 1, p.stdin.lines[0])

    def test_wait_false(self):
        checkpoint = self.checkpoint()

        def prog(proc, *args):
            checkpoint.wait()

        p = command(prog)
        p.run(wait=False)
        checkpoint.check(False)
        p.wait(False)
        checkpoint.check(False)
        checkpoint.set()

    def test_wait_invalid_types(self):
        def prog(proc, *args): # pragma: no cover
            pass

        p = command(prog)
        with self.raises(TypeError):
            p.run(wait='wah')
        self.eq(p.proc, None)
        self.eq(p.thread, None)

    def test_timeout(self):
        import time

        p = command(['sleep', 3])
        t1 = time.time()
        try:
            p.run(wait=0.1)
        except TimeoutExpired:
            pass
        t2 = time.time()
        self.le(t2 - t1, 1)
        p.kill()

    def test_poll(self):
        p = command('true')
        self.eq(p.poll(), False)
        p.run()
        self.eq(p.poll(), 0)

        checkpoint = self.checkpoint()
        def prog(proc, *args):
            checkpoint.wait()
            return 1
        p = command(prog)
        self.eq(p.poll(), False)
        p.run(wait=False)
        self.eq(p.poll(), None)
        checkpoint.set()
        p.wait()
        self.eq(p.poll(), 1)

    def test_signal(self):
        p = run(['cat'], wait=False)
        import signal
        p.signal(signal.SIGINT)
        p.wait()
        self.eq(p.signaled, signal.SIGINT)

    def test_kill_callable(self):
        checkpoint = self.checkpoint()

        def prog(proc, *args):
            proc.killed.wait()
            checkpoint.set()

        p = run(prog, wait=False)
        self.eq(p.signaled, False)
        self.eq(p.signaled, None)
        p.kill()
        p.wait()

        import signal
        checkpoint.check()
        self.eq(p.signaled, signal.SIGKILL)

        p.signaled.clear()
        self.eq(p.signaled, False)
        self.eq(p.signaled, None)

        p.kill(signal.SIGTERM)
        self.eq(p.signaled, signal.SIGTERM)

    def test_read_stdout_twice(self):
        ans = '1 2 3 4 5'.split()
        p = run('seq 5'.split())

        lines = []
        for line in p.stdout:
            lines.append(line)
        self.eq(lines, ans)

        checkpoint = self.checkpoint()
        lines = []
        def may_stuck():
            for line in p.stdout:
                lines.append(line)
            checkpoint.set()

        with self.run_in_thread(may_stuck):
            checkpoint.check()
            self.eq(lines, ans)

    def test_encoding_false(self):
        pi = b''
        pi += b'\x31\x41\x59\x26\x53\x58\x97\x93\x23\x84\x62\x64\x33\x83\x27\x95'
        pi += b'\x02\x88\x41\x97\x16\x93\x99\x37\x51\x05\x82\x09\x74\x94\x45\x92'
        pi += b'\x30\x78\x16\x40\x62\x86\x20\x89\x98\x62\x80\x34\x82\x53\x42\x11'
        pi += b'\x70\x67\x90'
        p = run(['xxd'], encoding=False, stdin=pi)
        self.eq(p.returncode, 0)
        self.eq(p.stdin.lines, [pi])
        self.eq(len(p.stdout.lines), 1)
        hex_pi = p.stdout.lines[0].decode('utf-8')
        self.eq(hex_pi, '''
00000000: 3141 5926 5358 9793 2384 6264 3383 2795  1AY&SX..#.bd3.'.
00000010: 0288 4197 1693 9937 5105 8209 7494 4592  ..A....7Q...t.E.
00000020: 3078 1640 6286 2089 9862 8034 8253 4211  0x.@b. ..b.4.SB.
00000030: 7067 90                                  pg.
'''.lstrip())

    def test_encoding_true_but_write_binary(self):
        pi = b''
        pi += b'\x31\x41\x59\x26\x53\x58\x97\x93\x23\x84\x62\x64\x33\x83\x27\x95'
        pi += b'\x02\x88\x41\x97\x16\x93\x99\x37\x51\x05\x82\x09\x74\x94\x45\x92'
        pi += b'\x30\x78\x16\x40\x62\x86\x20\x89\x98\x62\x80\x34\x82\x53\x42\x11'
        pi += b'\x70\x67\x90'
        p = run(['xxd'], stdin=pi)
        self.eq(p.returncode, 0)
        self.eq(p.stdin.lines, [pi])
        self.eq(len(p.stdout.lines), 4)
        self.eq(p.stdout.lines, [
            "00000000: 3141 5926 5358 9793 2384 6264 3383 2795  1AY&SX..#.bd3.'.",
            "00000010: 0288 4197 1693 9937 5105 8209 7494 4592  ..A....7Q...t.E.",
            "00000020: 3078 1640 6286 2089 9862 8034 8253 4211  0x.@b. ..b.4.SB.",
            "00000030: 7067 90                                  pg.",
            ])

    def test_large_amount_of_retention_data(self):
        p = command(['echo', 'a lot of data'], encoding=False)
        def mock_poll():
            # block p.poll() until the p.proc writes all stdout and exits
            while p.proc.poll() is None:
                pass
            return p.proc.poll()

        p.poll = mock_poll
        p.run()
        self.eq(p.stdout.lines, [b'a lot of data\n'])


class TestPipe(TestCase):
    def test_pipe(self):
        p1 = command('nl -w 1 -s :'.split(), stdin=['hello', 'world'])
        p2 = command('nl -w 1 -s /'.split(), stdin=True)
        pp = pipe(p1.stdout, p2.stdin)

        p1.run()
        self.eq(p1.stdout.lines, ['1:hello', '2:world'])
        p2.run(wait=False)

        p2.wait()
        self.eq(p2.stdin.lines, ['1:hello', '2:world'])
        self.eq(p2.stdout.lines, ['1/1:hello', '2/2:world'])

        pp.join()

    def test_pipe_dont_start(self):
        p1 = command(lambda prog: prog.stdout.writeline('wah'))

        def cat(prog):
            for line in prog.stdin:
                prog.stdout.writeline(line)
        p2 = command(cat, stdin=True)

        pp = pipe(p1.stdout, p2.stdin, start=False)

        p1.run(wait=False)
        p2.run(wait=False)
        p1.wait()

        self.false(p2.stdout.lines)
        self.eq(p2.returncode, None)

        pp.start()
        p2.wait()
        pp.join()

        self.eq(p2.stdout.lines, ['wah'])

    def test_pipe_istream_already_closed(self):
        i = stream()
        o = stream()
        i.close()

        with self.raises(EOFError):
            pipe(i, o)

    def test_pipe_ostream_already_closed(self):
        i = stream()
        o = stream()
        o.close()

        with self.raises(BrokenPipeError):
            pipe(i, o)

    def test_pipe_exception(self):
        i = stream()
        o = stream()
        o.queue = None
        o.close = lambda: None

        p = pipe(i, o)
        i.writeline('wah')

        with self.raises(Exception):
            p.join()

        self.ne(p.exception, None)

    def test_pipe_merge_to_same_stream(self):
        i1 = stream()
        i2 = stream()
        o = stream()
        o.keep = True

        pp1 = pipe(i1, o)
        e1 = threading.Event()
        pp1.post_write = e1.set
        pp2 = pipe(i2, o)
        e2 = threading.Event()
        pp2.post_write = e2.set

        i1.writeline('wah1')
        e1.wait()
        e1.clear()
        self.eq(o.lines, ['wah1'])

        i2.writeline('wow1')
        e2.wait()
        e2.clear()
        self.eq(o.lines, ['wah1', 'wow1'])

        i1.writeline('wah2')
        e1.wait()
        e1.clear()
        self.eq(o.lines, ['wah1', 'wow1', 'wah2'])

        i1.close()
        pp1.join()
        self.false(o.closed)

        i2.writeline('wow2')
        e2.wait()
        e2.clear()
        self.eq(o.lines, ['wah1', 'wow1', 'wah2', 'wow2'])

        i2.close()
        pp2.join()

        self.true(o.closed)
