# iroiro.test_utils

This document describes the API set provided by `iroiro.test_utils`.

For the index of this package, see [iroiro.md](iroiro.md).


## class `TestCase`

A sub-class of `unittest.TestCase` with a few extensions.

### Parameters
```python
TestCase(*args, **kwargs)
```

### Methods and Properties

#### `TestCase.eq()` / `TestCase.ne()`
Alias to `self.assertEqual` and `self.assertNotEqual`, respectively.

#### `TestCase.le()` / `TestCase.lt()`
Alias to `self.assertLessEqual` and `self.assertLess`, respectively.

#### `TestCase.ge()` / `TestCase.gt()`
Alias to `self.assertGreaterEqual` and `self.assertGreater`, respectively.

#### `TestCase.true()` / `TestCase.false()`
Alias to `self.assertTrue` and `self.assertFalse`, respectively.

#### `TestCase.raises()`
Alias to `self.assertRaises`.

#### `TestCase.checkpoint()`
Create a [Checkpoint](#class-checkpoint) object, see below.

#### `TestCase.run_in_thread(func, args=tuple(), kwargs=dict())`
Run `func(*args, **kwargs)` in a daemon thread.

The return value is a context manager.  
It `start()` the thread on `__enter__`, and `join()` the thread on `__exit__`.
The object is not reusable.

__Examples__
```python
import iroiro
import threading

class TestRunInThread(TestCase):
    def test_run_in_thread(self):
        barrier = threading.Barrier(2)
        checkpoint = False

        def may_stuck():
            nonlocal checkpoint
            barrier.wait()
            checkpoint = True

        with self.run_in_thread(may_stuck):
            self.false(checkpoint)
            barrier.wait()

        self.true(checkpoint)
```

#### `TestCase.patch(name, side_effect)`

Patch out `name` with `side_effect`.

The patch is automatically cleaned up after each test case run.

__Examples__
```python
self.patch('builtins.open', mock_open)
```
After the aboved `patch()` call, any calls to `open()` will be forwared to `mock_open`.


## class `Checkpoint`

A wrapper to `threading.Event()` that links to a `Testcase`.

### Methods and Properties

#### `Checkpoint.set()` / `Checkpoint.clear()`
Set/Clear the checkpoint.

#### `Checkpoint.is_set()`
Return if the checkpoint was already set.

#### `Checkpoint.wait()`
Block the execution and wait for the checkpoint to be set.

#### `Checkpoint.check(is_set=True)`
Check if `checkpoint.is_set()` equals to argument `is_set`. If not, fail the testcase.

#### `Checkpoint.__bool__()`
Return `self.is_set()`.


## class `RunMocker`

A pre-configurable mocker for `subproc.run`.

Conceptually, the mocker's rule set is a dictionary of command and behavior(s):

```python
{
    'ls': (behavior),
    'rm': (behavior),
    'touch': (behavior),
}
```

When called, the command is searched from the rule set,
and the pre-configured behavior is used as the faked `run()` result.

### Methods and Properties

#### `RunMocker.__call__()`
```python
run_mocker = RunMocker()
run_mocker(cmd=None, *,
           stdin=None, stdout=True, stderr=True,
           encoding='utf8', rstrip='\r\n',
           bufsize=-1,
           env=None,
           wait=True)
```

Search `cmd` (if `str`) or `cmd[0]` (if `list`) from the rule set.

*   If it's found, the behavior is used as the result.
*   If it's not found, `ValueError` is raised.

#### `RunMocker.register()`

Register a command/behavior pair into the rule set.

__Parameters__
```python
run_mocker = RunMocker()
run_mocker.register(cmd, callback=None, *, stdout=None, stderr=None, returncode=None)
```

`cmd` is a `str` that specifies the mocked command,
and the remaining parameters defines the behavior.

*   When the behavior is defined by `stdout`, `stderr`, and `returncode`,
    the arguments are used as their name suggests.

*   When the behavior is defined by `callback`,
    -   If it's an `Exception`, it's raised when used.
    -   Otherwise, the callback is called with:
        +   A command object as the first parameter.
        +   Unpacked arguments as the remaining parameters.

__Examples__
```python
run_mocker = RunMocker()
run_mocker.register('ls', stdout=['ls stdout'], stderr=['ls stderr'], returncode=1)
run_mocker.register('rm', foo)

run_mocker('ls -a -l') # prints stdout & stderr, and returns 1

run_mocker('rm -r -f wah')
# calls foo(proc, '-r', '-f', 'wah')
# with proc.cmd == ('rm', '-r', '-f', 'wah')
```

A same command can be registered multiple times with different behaviors.  
In that case, a behavior is consumed by each call, and the last behavior is used indefinitely.

__Examples__
```python
run_mocker = RunMocker()
run_mocker.register('ls', returncode=1)
run_mocker.register('ls', foo)
run_mocker.register('ls', returncode=3)
run_mocker.register('ls', ValueError('wah'))

run_mocker('ls -a -l') # returncode=1

run_mocker('ls -a -l -l -l')
# calls foo(proc, '-a', '-l', '-l', '-l')

run_mocker('ls -a -l') # returncode=3

run_mocker('ls -a -l') # raises ValueError('wah')
```
