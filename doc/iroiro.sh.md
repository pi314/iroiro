# iroiro.sh

This document describes the API set provided by `iroiro.sh`.

For the index of this package, see [iroiro.md](iroiro.md).


## `cwd(path=None)`

If `path` is `None`, returns the current working directory path of `pathlib.Path`.

Otherwise, it `os.chdir()` to `path`, and returns the new working directory path.

If `path` is not a directory,
or any exception is raised during the process, `False` is returned.

__Examples__
```python
from iroiro import cwd
here = cwd()   # get CWD

there = cwd(here / 'tmp') # chdir
if not there:
    handle_chdir_failed()
```


## `pushd(path=None)` / `popd(all=False)`

`pushd()` pushes `cwd()` into dir stack, and then attempts to `os.chdir(path)`.

`popd()` pops a path from dir stack, and `os.chdir()` to it.

`popd(all=True)` jumps to the first path of dir stack and empty dir stack.

If `path` is `None`, `cwd()` is used instead.

If any operation fails, `False` or a falsy-object is returned.

__Examples__
```python
from os.path import expanduser
from iroiro import cwd, pushd, popd

here = cwd()
pushd(expanduser('~/Downloads'))
assert cwd() == expanduser('~/Downloads')
popd()
assert cwd() == here
```

`pushd()` could also be used as context manager:

```python
from os.path import expanduser
from iroiro import cwd, pushd

print(cwd())

with pushd(expanduser('~/Downloads')):
    print(cwd())

print(cwd())
assert popd() == False
```


## `dirs(clear=False)`

Returns a copy of the dir stack as a `list`. The top of the stack is at the end.

__Examples__
```python
from os.path import expanduser
from iroiro import cwd, pushd, dirs

here = cwd()

assert dirs() == [here]

with pushd(expanduser('~/Downloads')):
    assert dirs() == [here, expanduser('~/Downloads')]

assert dirs() == [here]
```

`clear=True` clears the dir stack, note that it keeps `cwd()` with current value.

To jump to the first item of dir stack, use `popd(all=True)` instead.


## `home()`

Returns `Path.home()`.

```python
from os.path import expanduser
from iroiro import home

assert home() == expanduser('~')
```


## `shrinkuser(path)`

Returns the opposite of `os.path.expanduser()`, i.e. replace `$HOME` with a `~` symbol.

The trailing slash is reserved if `path` ends with one.

```python
from os.path import expanduser
from iroiro import home

assert shrinkuser(home()) == '~'
HOME = str(home())
assert shrinkuser(HOME + '/') == '~/'
```
