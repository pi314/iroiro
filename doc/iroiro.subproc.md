# iroiro.subproc

This document describes the API set provided by `iroiro.subproc`.

For the index of this package, see [iroiro.md](iroiro.md).


## Class `command()`

A line-oriented object for interacing with the specified command.

The command is not started after creation.  
You could prepare data for stdin, or create pipes from stdout/stderr before running.

A `command` object holds an external command, or a `callable` with parameters.  
They could be mixed together in a pipeline in order to complete complex tasks.

For example, you could get stdout from `ls -1` line by line,
add prefix to all of them with a small lambda,
and pipe the results into `nl` to number them.

It's like writing a pipeline with a lot of `awk`, `sed`, `grep`, etc, without leaving Python.


### Parameters

```python
command(self, cmd=None, *,
        stdin=None, stdout=True, stderr=True,
        encoding='utf8', rstrip='\r\n',
        bufsize=-1,
        env=None)
```

*   `cmd`
    -   If `cmd` is a `tuple` or a `list`, it's converted into `[cmd]` and goes to the following cases.
    -   If `cmd` is a `[str, ...]`, the first item is taken as the command,
        and the remaining items are taken as arguments.
    -   If `cmd` is a `[callable, ...]`, the first item is taken as the command,
        and the remaining items are taken as arguments.
        +   The callable should take `len(cmd)` parameters.
        +   The first parameter of the callable is `proc`, which is the command object itself.
        +   The remaining parameters are assigned with the remaining arguments.
    -   Otherwise, `ValueError` is raised.

    -   Examples
        +   `'true'`
        +   `['ls', '-a', '-1']`
        +   Callable
            *   `lambda proc: ...`
            *   `[(lambda proc, *args: ...), 'bar', 'baz']` (a callable with arguments)

*   `stdin` (default: `None`)
    -   If `stdin` is `None` or `False`, the stream is closed.
    -   If `stdin` is a `str`, `bytes`, or a `bytearray`, it's converted into `[stdin]` and goes to the following cases.
    -   If `stdin` is a `tuple` or a `list`, each item is treated as one line of text input.
        +   The stream is left open and accepts more input, and it's closed upon `run()`.
    -   If `stdin` is `True`, the stream is left open and wait for data input.
    -   If `stdin` is a `queue.Queue`, the stream is left open
        and the process pulls data from the given `Queue` object and feed into `stdin`.

*   `stdout` (default: `True`)
    -   If `stdout` is `None`, the stream is forwarded to the tty.
    -   If `stdout` is `False`, the stream is closed and outputs are silently dropped.
    -   If `stdout` is `True`, the output data is kept in the stream object.
    -   If `stdout` is a `callable`, the callable is called for each line as argument.
    -   If `stdout` is a `queue.Queue`, each line of output is put into the `Queue` object.
    -   If `stdout` is a `tuple` or a `list`, output is duplicated to each object.
    -   Examples
        +   `stdout=lambda line: ...`
        +   `stdout=tuple(print, queue.Queue())`

*   `stderr` (default: `True`)
    -   See `stdout`.

*   `encoding` (default: `'utf8'`)
    -   If `encoding` is `False`, the process is opened in binary mode.

*   `rstrip` (default: `'\r\n'`)
    -   In text mode (`encoding != False`), each line will be `rstrip()`ed with `rstrip` value

*   `bufsize` (default: `-1`)
    -   `bufsize` is only meaningful when encoding is `False`.
    -   This value controls the rough size of underlying buffer.

*   `env` (default: None)
    -   Environment variables.
    -   By default, child processs inherits environment variables from parent proess.


### Methods and Properties

#### `command.run(wait=True)`

Run the command and return the command object itself.  
The `wait` argument is passed to `wait()` method, see below.


#### `command.poll()`

Check the process status and return the status code.


#### `command.wait(timeout=None)`

Wait the process to finish for `timeout` seconds.

*   If `timeout` is `True` or `None`, it waits for the command to finish.
*   If `timeout` is `False`, it returns immediately.
*   If `timeout` is an `int` or a `float`, it waits for the specified seconds.
*   Otherwise, `TypeError` is raised.


#### `command.signal(signal)`

Send `signal` to the process.


#### `command.kill(signal=SIGKILL)`

Send `signal`, wait for the process to stop, and close all streams.


#### `command.signaled`

Stores the received signal.

It's a subclass of `threading.Event` thus can be `.wait()`.


#### `command.killed`

An alias to `signaled`.


### Stream object methods and properties

Each stream object (i.e. `command.stdin`, `command.stdout`, and `command.stderr`)
has the following methods and properties:

*   `read()`: read one line or a block of data from the stream.
*   `readline()`: an alias to `read()`.
*   `write(data)`: write one line or a block of data to the stream.
*   `writeline(line)`: an alias to `write()`.
*   `writelines(lines)`: write each line in `lines` with `writeline()`.
*   `close()`: close the stream.
*   `closed`: indicate if the stream is already closed.
*   `empty`: indicate if the stream is empty.
*   `lines`: all lines or data blocks flowed through the stream.
*   `__len__()`
*   `__iter__()`


## `run()`

Creates a `command` object and runs it.

__Parameters__
```python
run(cmd=None, *,
    stdin=None, stdout=True, stderr=True,
    encoding='utf8', rstrip='\r\n',
    bufsize=-1,
    env=None,
    wait=True)
```

Conceptually equals to:
```python
def run(..., wait=True):
    p = command(...)
    p.run(wait=wait)
    return p
```


## `pipe()`

Connect input/output streams together.

__Parameters__
```python
pipe(istream, *ostreams, *, start=True)
```

A daemon thread is created and returned, that pulls data from istream and duplicate to ostreams.

*   When a `pipe` is created, it notifies `ostreams` objects and cause their reference count increase by 1.

*   When the `istream` closes, the `Pipe` object notifies each `ostreams` for its leaving
    and cause their reference count decrease by 1.  
    -   A `ostream` object closes itself on this event when its reference count is less than or equals to 0.

__Examples__
```python
p1 = command(...)
p2 = command(...)
p3 = command(...)
pipe1 = pipe(p1.stdout, p2.stdin)
pipe2 = pipe(p2.stdout, p3.stdin)
pipe1.join()
pipe2.join()
```
