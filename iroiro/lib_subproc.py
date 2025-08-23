import queue
import subprocess as sub
import threading

from signal import SIGKILL

from .lib_itertools import is_iterable

from .internal_utils import exporter
export, __all__ = exporter()


export('TimeoutExpired')
TimeoutExpired = sub.TimeoutExpired


@export
class AlreadyRunningError(Exception):
    def __init__(self, cmd):
        if callable(cmd.cmd[0]):
            prog = cmd.cmd[0].__name__ + '()'
        else:
            prog = cmd.cmd[0]

        super().__init__(' '.join(
            [prog] + cmd.cmd[1:]))


class EventBroadcaster:
    def __init__(self):
        self.handlers = []

    def __iadd__(self, handler):
        self.handlers.append(handler)
        return self

    def __isub__(self, handler):
        self.handlers.remove(handler)
        return self

    def broadcast(self, *args, **kwargs):
        for handler in self.handlers:
            handler(*args, **kwargs)


class QueueEventAdapter:
    def __init__(self, Q):
        self.Q = Q

    def __call__(self, line):
        self.Q.put(line)


class stream:
    def __init__(self):
        self.queue = queue.Queue()
        self.keep = False
        self.lines = []
        self.eof = threading.Event()
        self.hub = EventBroadcaster()

        self.pipe_count_lock = threading.Lock()
        self.pipe_count = 0

    def welcome(self, subscriber):
        if isinstance(subscriber, (list, tuple)):
            for s in subscriber:
                self.welcome_one(s)
        else:
            self.welcome_one(subscriber)

    def welcome_one(self, subscriber):
        if subscriber is True:
            self.keep = True

        else:
            handler = None
            if hasattr(subscriber, 'put'):
                handler = QueueEventAdapter(subscriber)
            elif callable(subscriber):
                handler = subscriber

            if handler:
                self.hub += handler
            else:
                raise TypeError('Invalid subscriber value: {}'.format(repr(subscriber)))

    def pipe_attached(self):
        self.pipe_count_lock.acquire()
        try:
            self.pipe_count += 1
        finally:
            self.pipe_count_lock.release()

    def pipe_detached(self):
        self.pipe_count_lock.acquire()
        try:
            self.pipe_count -= 1
            if self.pipe_count <= 0:
                self.close()
        finally:
            self.pipe_count_lock.release()

    def read(self):
        data = self.queue.get()
        return data

    def readline(self):
        return self.read()

    def write(self, data, *, suppress=True):
        if self.closed:
            if suppress:
                return
            raise BrokenPipeError('stream already closed')

        if self.keep:
            self.lines.append(data)

        self.queue.put(data)
        self.hub.broadcast(data)

    def writeline(self, line, *, suppress=True):
        self.write(line, suppress=suppress)

    def writelines(self, lines):
        for line in lines:
            self.writeline(line)

    def close(self):
        self.eof.set()
        self.queue.put(None)

    @property
    def closed(self):
        return self.eof.is_set()

    @property
    def empty(self):
        return not self.lines and self.queue.empty()

    def __bool__(self):
        return not self.empty

    def __len__(self):
        return len(self.lines)

    def __iter__(self):
        if self.closed:
            yield from self.lines

        else:
            while True:
                line = self.readline()
                if line is None:
                    break
                yield line


class IntegerEvent(threading.Event):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.value = None

    def set(self, value=None):
        self.value = value
        super().set()

    def clear(self):
        self.value = None
        super().clear()

    def __eq__(self, other):
        if not self.is_set():
            return other is False or other is None
        return self.value == other


@export
class command:
    def __init__(self, cmd=None, *,
                 stdin=None, stdout=True, stderr=True,
                 encoding='utf8', rstrip='\r\n',
                 bufsize=-1,
                 env=None):

        if cmd and isinstance(cmd, str):
            cmd = [cmd]
        elif callable(cmd):
            cmd = [cmd]
        elif isinstance(cmd, (tuple, list)):
            pass
        else:
            raise ValueError('Invalid command:' + repr(cmd))

        if not cmd:
            raise ValueError('command is empty')

        if callable(cmd[0]):
            self.cmd = [token for token in cmd]
        else:
            self.cmd = [str(token) for token in cmd]

        self.encoding = encoding
        self.bufsize = bufsize
        self.rstrip = rstrip

        self.env = env
        self.proc = None
        self.thread = None
        self.exception = None
        self.signaled = IntegerEvent()
        self.returncode = None

        if isinstance(stdin, (str, bytes, bytearray)):
            stdin = [stdin]

        # Initialize stdin stream
        self.stdin = stream()
        self.stdin.keep = True
        self.stdin_queue = None
        self.stdin_autoclose = False
        if stdin is None or stdin is False:
            self.proc_stdin = None
            self.stdin.close()
        else:
            self.proc_stdin = sub.PIPE
            if isinstance(stdin, queue.Queue):
                self.stdin_queue = stdin
            elif is_iterable(stdin):
                for line in stdin:
                    self.stdin.write(line)
                self.stdin_autoclose = True

        # Initialize stdout stream
        self.stdout = stream()
        if stdout is None:
            self.proc_stdout = None
            self.stdout.close()
        elif stdout is False:
            self.proc_stdout = sub.DEVNULL
            self.stdout.close()
        else:
            self.proc_stdout = sub.PIPE
            self.stdout.keep = False
            self.stdout.welcome(stdout)

        # Initialize stderr stream
        self.stderr = stream()
        if stderr is None:
            self.proc_stderr = None
            self.stderr.close()
        elif stderr is False:
            self.proc_stderr = sub.DEVNULL
            self.stderr.close()
        else:
            self.proc_stderr = sub.PIPE
            self.stderr.keep = False
            self.stderr.welcome(stderr)

        self.io_threads = []

    @property
    def killed(self):
        return self.signaled

    def __getitem__(self, idx):
        return [self.stdin, self.stdout, self.stderr][idx]

    def __enter__(self):
        return self.run(wait=False)

    def __exit__(self, exc_type, exc_value, traceback):
        self.stdin.close()
        self.stdout.close()
        self.stderr.close()
        self.wait()

    def run(self, wait=None):
        if wait is not None and not isinstance(wait, (int, bool, float)):
            raise TypeError('The type of "wait" should be NoneType, int, bool, or float')

        if self.proc or self.thread:
            raise AlreadyRunningError(self)

        if callable(self.cmd[0]):
            def worker():
                try:
                    self.returncode = self.cmd[0](self, *self.cmd[1:])
                except Exception as e:
                    self.exception = e

                self.stdin.close()
                self.stdout.close()
                self.stderr.close()

            self.thread = threading.Thread(target=worker)
            self.thread.daemon = True
            self.thread.start()

        else:
            if self.encoding == False:
                # binary mode
                kwargs = {
                        'bufsize': 2 if self.bufsize == 1 else self.bufsize,
                        'text': False,
                        }
            else:
                kwargs = {
                        'bufsize': 1,
                        'encoding': self.encoding,
                        'errors': 'backslashreplace',
                        }

            self.proc = sub.Popen(
                    self.cmd,
                    stdin=self.proc_stdin,
                    stdout=self.proc_stdout,
                    stderr=self.proc_stderr,
                    env=self.env, **kwargs)

            def writer(self_stream, proc_stream):
                for line in self_stream:
                    if self.encoding == False:
                        proc_stream.write(line)
                    elif isinstance(line, (bytes, bytearray)):
                        proc_stream.buffer.write(line)
                    else:
                        proc_stream.write(line + '\n')
                    proc_stream.flush()
                proc_stream.close()

            def reader(self_stream, proc_stream):
                if self.encoding != False:
                    # text
                    for line in proc_stream:
                        line = line.rstrip(self.rstrip)
                        self_stream.writeline(line)

                else:
                    # binary
                    while self.poll() is None:
                        data = proc_stream.read(
                                -1
                                if self.bufsize < 0
                                else (self.bufsize or 1)
                                )

                        if not data:
                            continue

                        self_stream.write(data)

                    # Read all remaining data left in stream
                    data = proc_stream.read()
                    if data:
                        self_stream.writeline(data)

                self_stream.close()
                proc_stream.close()

            for (worker, self_stream, proc_stream) in (
                    (writer, self.stdin, self.proc.stdin),
                    (reader, self.stdout, self.proc.stdout),
                    (reader, self.stderr, self.proc.stderr),
                    ):
                if self_stream is not None and proc_stream is not None:
                    t = threading.Thread(target=worker, args=(self_stream, proc_stream))
                    t.daemon = True
                    t.start()
                    self.io_threads.append(t)

        # Pull data from stdin_queue and feed into stdin stream
        if self.stdin_queue:
            def feeder():
                while True:
                    self.stdin.writeline(self.stdin_queue.get())
                    self.stdin_queue.task_done()

            t = threading.Thread(target=feeder)
            t.daemon = True
            t.start()

        elif self.stdin_autoclose:
            self.stdin.close()

        self.wait(wait)

        return self

    def poll(self):
        if self.proc:
            return self.proc.poll()
        if self.thread:
            return self.returncode
        return False

    def wait(self, timeout=None):
        if timeout is True:
            timeout = None
        elif timeout is False:
            return

        # Wait for child process to finish
        if self.proc:
            self.proc.wait(timeout)
            self.returncode = self.proc.returncode

        if self.thread:
            self.thread.join(timeout)

        # Wait too early
        if self.proc is None and self.thread is None:
            return

        if self.exception:
            raise self.exception

        # Wait for all streams to close
        self.stdin.eof.wait()
        self.stdout.eof.wait()
        self.stderr.eof.wait()

        # Gracefully wait for threads to finish
        for t in self.io_threads:
            t.join()

    def signal(self, signal):
        if self.proc:
            self.proc.send_signal(signal)

        self.signaled.set(signal)

    def kill(self, signal=SIGKILL):
        self.signal(signal)

        if self.proc:
            self.proc.wait()
            for proc_stream in (
                    self.proc.stdin,
                    self.proc.stdout,
                    self.proc.stderr
                    ):
                if proc_stream:
                    proc_stream.close()

            self.returncode = self.proc.returncode

        if self.thread:
            self.thread.join()


@export
def run(cmd=None, *,
        stdin=None, stdout=True, stderr=True,
        encoding='utf8', rstrip='\r\n',
        bufsize=-1,
        env=None,
        wait=True):
    ret = command(cmd,
                  stdin=stdin, stdout=stdout, stderr=stderr,
                  encoding=encoding,
                  rstrip=rstrip, env=env)
    ret.run(wait=wait)
    return ret


class Pipe:
    def __init__(self, istream, *ostreams):
        if istream.closed:
            raise EOFError('istream already closed')

        for ostream in ostreams:
            if ostream.closed:
                raise BrokenPipeError('ostream already closed')

        self.exception = None
        self.thread = None
        self.istream = istream
        self.ostreams = ostreams
        self.post_write = None

    def main(self):
        try:
            for line in self.istream:
                for ostream in self.ostreams:
                    ostream.write(line)
                if self.post_write:
                    self.post_write()

        except Exception as e:
            self.exception = e
            self.istream.close()

        self.istream.eof.wait()
        for ostream in self.ostreams:
            ostream.pipe_detached()

    def start(self):
        self.thread = threading.Thread(target=self.main)
        self.thread.daemon = True
        self.thread.start()

    def join(self):
        self.thread.join()
        if self.exception:
            raise self.exception


@export
def pipe(istream, *ostreams, start=True):
    p = Pipe(istream, *ostreams)
    for ostream in ostreams:
        ostream.pipe_attached()

    if start:
        p.start()
    return p
