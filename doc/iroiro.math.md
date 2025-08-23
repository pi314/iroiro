# iroiro.math

This document describes the API set provided by `iroiro.math`.

For the index of this package, see [iroiro.md](iroiro.md).


## `is_uint8(i)`

Checks if the argument `i` is an 8-bit unsigned integer.

Returns `True` if `i` fulfills all of the following condition:

* `isinstance(i, int)`
* `not isinstance(i, bool)`
* `0 <= i < 256`


## `sgn(i)`

Return the sign of parameter `i`.

* `-1` if `i < 0`
* `1` if `i > 0`
* `0` otherwise


## `lerp(a, b, t)`

Calculates the linear interpolation or extrapolation of argument `a`, `b` at ratio `t`.

* If `t = 0`, `a` is returned
* If `t = 1`, `b` is returned
* If `0 < t < 1`, the linear interpolation is returned
* Otherwise, the linear extrapolation is returned

The expression of interpolation/extrapolation is `a + t * (b - a)`,
any data types that supports involved operations works.

__Examples__
```python
assert lerp(-1, 9, 0) == -1
assert lerp(-1, 9, 0.5) == 4
assert lerp(-1, 9, 1) == 9
assert lerp(-1, 9, 2) == 19
```


## `clamp(A, x, B)`

clamps the value into the specified interval `[A, B]`.

* If `x` is less than `min(A, B)`, `min(A, B)` is returned
* If `x` is greater than `max(A, B)`, `max(A, B)` is returned
* Otherwise, `x` is returned

__Examples__
```python
assert clamp(3, 0, 7) == 3
assert clamp(3, 5, 7) == 5
assert clamp(3, 9, 7) == 7
```


## Class `vector(*args)`

A `tuple`-like object that supports numeric operations with `int` and `float`.

__Examples__
```python
v1 = vector(1, 2, 3)
v2 = vector(4, 5, 6)

# vectors could be added together
assert v1 + v2 == (5, 7, 9)
assert v1 - v2 == (-3, -3, -3)

# vector + number and number + vector applies to all coordinates
assert v1 + 2 == (3, 4, 5)
assert 2 + v1 == (3, 4, 5)

# vector - number applies to all coordinates
assert v1 - 2 == (-1, 0, 1)

# vector * number and number * vector
assert v1 * 2 == (2, 4, 6)
assert 2 * v1 == (2, 4, 6)

# vector / number and vector // number
assert (v1 / 2, (0.5, 1.0, 1.5))
assert (v1 // 2, (0, 1, 1))

# .map() might be handy if you need complex calculations
assert v1.map(lambda x: 3 * x + 1) == (4, 7, 10)
```


## `interval(a, b, close=True)`

Returns a `List[int]` that starts from `a` and ends with `b`.

If `close=False`, `a` and `b` are excluded from the result.

__Examples__
```python
assert interval(3, 1) == [3, 2, 1]
assert interval(3, -3) == [3, 2, 1, 0, -1, -2, -3]
assert interval(3, -3, close=False) == [2, 1, 0, -1, -2]

assert interval(3, 3) == [3]
assert interval(3, 3, close=False) == []
```


## `resample(samples, N)`

Returns a list that "distrubutes" `samples` into `N` items.

* If `N` is larger than `len(samples)`, some items are repeated in the result
* If `N` is less than `len(samples)`, some items are dropped from the result

__Examples__
```python
samples = (1, 2, 3, 4, 5)
assert resample(samples, 5) == samples
assert resample(samples, 3) == (1, 3, 5)
assert resample(samples, 10) == (1, 1, 2, 2, 3, 3, 4, 4, 5, 5)
```
