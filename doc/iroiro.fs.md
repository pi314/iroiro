# iroiro.fs

This document describes the API set provided by `iroiro.fs`.

For the index of this package, see [iroiro.md](iroiro.md).


## `open()`

A factory function that adds line-oriented methods to `builtin.open()`.

__Parameters__
```python
open(file, mode=None, rstrip='\r\n', newline='\n', **kwargs)
```

This function calls `builtin.open()`, with the following default values:

*   Sets default `encoding` to `'utf-8'`, if not specified
*   Sets default `errors` to `'backslashreplace'`, if not specifed
*   If `mode` does not contain `'b'`, returns a wrapper object

The returned wrapper object relays method calls to the underlying file object,
in addition it provides the following methods for convenience:

*   `writeline(*args)`: writes `' '.join(args) + newline` into file
*   `writelines(lines)`: write each elements in `lines` into file
*   `readline()`: read one line from file, and `rstrip` newline characters
*   `readlines()`: read all lines from file
*   `__iter__()`: yield lines from file


__Examples__
```python
import iroiro

with iroiro.open(path, 'w') as f:
    f.writelines(['a', 'b', 'c'])
    f.writeline('d')

with iroiro.open(path) as f:
    assert f.readlines() == ['a', 'b', 'c', 'd']
```

The built-in `open()` `.readline()` chose to keeps the newline character(s),
so when it returns a line without trailing newline, you know it's the last line of the file.

If you need built-in behavior, setting `rstrip=''` should work.


## `natsorted()`

A utility function that mimics the very basic functionality of [natsort](https://pypi.org/project/natsort/).

__Parameters__
```python
natsorted(iterable, key=None)
```

This function was made for sorting ``os.listdir()`` with a slightly better result.

__Examples__
```python
assert iro.natsorted([
        'apple1',
        'apple10',
        'banana10',
        'apple2',
        'banana1',
        'banana3',
    ]) == [
        'apple1',
        'apple2',
        'apple10',
        'banana1',
        'banana3',
        'banana10',
    ]
```
