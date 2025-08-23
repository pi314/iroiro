# iroiro.regex

This document describes the API set provided by `iroiro.regex`.

For the index of this package, see [iroiro.md](iroiro.md).


## Class `rere`

A proxy class that caches the last result of `search` / `match` / `fullmatch`.

__Parameters__
```python
rere(text)
```

__Examples__
```python
rr = rere('iro i ro')
rr.match(r'^(\w+) (\w+) (\w+)$')
assert rr.groups() == ('iro', 'i', 'ro')
```

`rere.sub()` and other methods are directly relayed to `re` module.

The purpose of this class is basically replaced by the "walrus operator" from Python 3.8.

But if for some reason you have to use Python 3.7 or below, this utility might still be helpful:

```python
rr = rere(...)

if rr.fullmatch(pattern1):
   # rr.groups()
   ...

elif rr.match(pattern2):
   # rr.groups()

...
```
