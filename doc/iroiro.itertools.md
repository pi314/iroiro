# iroiro.itertools

This document describes the API set provided by `iroiro.itertools`.

For the index of this package, see [iroiro.md](iroiro.md).


## `is_iterable(obj)`

Returns `True` if `obj` is iterable and `False` otherwise.

__Examples__
```python
assert is_iterable([])
assert is_iterable("iroiro")
assert not is_iterable(3)
```


## `unwrap(obj=None)`

Try to unpack `obj` as much as possible.

`str` stay as-is and doesn't unpacked to characters.

__Examples__
```python
assert unwrap([[[1, 2, 3]]]) == [1, 2, 3]
assert unwrap([[True]]) == True
assert unwrap(3) == 3
assert unwrap('iroiro') == 'iroiro'
```


## `flatten(tree)`

Flattens every nested list/tuple and merge them into one.

__Examples__
```python
assert flatten([[1, 2, 3], [4, 5, 6], [7], [8, 9]]) == [1, 2, 3, 4, 5, 6, 7, 8, 9]
```


## `lookahead(iterable)`

Returns a generator object that generate boolean values to indicate the last element.

Like `enumerate()` that generate `index` values for each element,
`lookahead()` generate `is_last`.

__Examples__
```python
assert list(lookahead([1, 2, 3, 4, 5])) == [
   (1, False),
   (2, False),
   (3, False),
   (4, False),
   (5, True),
   ]
```


## `zip_longest(*iterables, fillvalues=None)`

Similar to standard `itertools.zip_longest()`, but iroiro version supports
setting `fillvalue` for each iterable.

If `fillvalues` is not a `tuple` or a `list`, the value is duplicated for each iterable.

__Examples__
```python
# Same as itertools.zip_longest()
A = list(zip_longest('ABCD', [1, 2], fillvalues='#')),
B = [
   ('A', 1),
   ('B', 2),
   ('C', '#'),
   ('D', '#'),
   ]
assert A == B

A = list(zip_longest('ABCD', [1, 2], fillvalues=('#', 0))),
B = [
   ('A', 1),
   ('B', 2),
   ('C', 0),
   ('D', 0),
   ]
assert A == B

A = list(zip_longest('AB', [1, 2, 3, 4], fillvalues=('#', 0))),
B = [
   ('A', 1),
   ('B', 2),
   ('#', 3),
   ('#', 4),
   ]
assert A == B
```
