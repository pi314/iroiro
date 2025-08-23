# iroiro.colors

This document describes the API set provided by `iroiro.colors`.

For the index of this package, see [iroiro.md](iroiro.md).


## `color()`

A factory function that produces color objects based on input arguments.

__Parameters__
```python
color()
color(index)
color(R, G, B)
color('#RRGGBB')
color('@H,S,V')
```

__Examples__
```python
color()              # Color256: empty
color(214)           # Color256: darkorange
color(255, 175, 0)   # ColorRGB: orange
color('#FFAF00')     # ColorRGB: orange
color('@41,100,100') # ColorHSV: orange
```

If the argument does not have correct format, `TypeError` is raised.

See [Color256](#class-color256), [ColorRGB](#class-colorrgb),
and [ColorHSV](#class-colorhsv) for more details.


## Class `Color`

An abstract base class that is inherited by other Color types.

It's intended to be used for type checking. For example, `isinstance(obj, Color)`.

Two `Color` objects are defined equal if their escape sequences are equal.


## Class `Color256`

Represents a xterm 256 color.

The actual color displayed in your terminal might look different
depends on your palette settings.

__Parameters__
```python
Color256()
Color256(index) # index: int, 0 ~ 255
```

__Examples__
```python
# Orange
c = Color256(214)

# Attributes
assert c.index == 214

# int and str
assert int(c) == 214
assert str(c) == '\033[38;5;214m'

# Use it to color strings
assert c('text') == str(c) + 'text' + '\033[m'
assert '{}{}{}'.format(c, 'text', nocolor) == c('text')
```

A `Color256` object could be casted into a `ColorRGB` object or a `ColorHSV`
object through `.to_rgb()` or `.to_hsv()` methods:

```python
assert c.to_rgb() == ColorRGB(255, 175, 0)
assert c.to_hsv() == ColorHSV(41, 100, 100)
```

## Class ``ColorRGB``

Represents a RGB color.

__Parameters__
```python
ColorRGB(R, G, B)
# R, G, B: int, 0 ~ 255

ColorRGB('#RRGGBB')
# RR, GG, BB: 00 ~ FF
```

__Examples__
```python
# Orange
c = ColorRGB(255, 175, 0)

# Attributes
assert c.r == 255
assert c.g == 175
assert c.b == 0
assert c.rgb = (c.r, c.g, r.b)

# Regulated attributes, see below
assert c.R == 255
assert c.G == 175
assert c.B == 0
assert c.RGB = (c.R, c.G, r.B)

# int and str
assert int(c) == 0xFFAF00
assert str(c) == '\033[38;2;255;175;0m'

# Use it to color strings
assert c('text') == str(c) + 'text' + '\033[m'
assert '{}{}{}'.format(c, 'text', nocolor) == c('text')
```

`ColorRGB` objects could be mixed to produce new colors:

```python
red = ColorRGB('#FF0000')
green = ColorRGB('#00FF00')

# Add them together
assert red + green == ColorRGB('#FFFF00')

# Average them
assert (red + green) // 2 == ColorRGB('#7F7F00')

# Average with different weights
assert ((red * 2) + green) // 2 == ColorRGB('#FF7F00')
```

A `ColorRGB` object could be casted into a `ColorHSV` object:

```python
assert ColorRGB(255, 0, 0).to_rgb() == ColorRGB(255, 0, 0)
assert ColorRGB(255, 0, 0).to_hsv() == ColorHSV(0, 100, 100)
```

Two sets of RGB values are provided:

*   Lowercase `rgb` for real values
*   Uppercase `RGB` for regulated values that are
    `round()` and `clamp()` to `range(0, 256)`

```python
# Nearly orange
c = ColorRGB(255, 174.5, 0)

# Lowercase = real values
assert c.rgb == (255, 174.5, 0)

# Uppercase = regulated values
assert c.RGB == (255, 174, 0)
```

The escape sequence of a `ColorRGB` object is calculated based on `RGB`.


## Class ``ColorHSV``

Represents a HSV color.

__Parameters__
```python
ColorHSV(H, S, V)
# H: 0 ~ 360
# S: 0 ~ 100
# V: 0 ~ 100
```

__Examples__
```python
# Orange
c = ColorHSV(41, 100, 100)

# Attributes
assert c.h == 41
assert c.s == 100
assert c.v == 100
assert c.hsv == (c.h, c.s, c.v)

# Regulated attributes, see below
assert c.H == 41
assert c.S == 100
assert c.V == 100
assert c.HSV == (c.H, c.S, c.V)

# int and str
assert int(c) == 41100100
assert str(c) == '\033[38;2;255;174;0m'

# Use it to color strings
assert c('text') == str(c) + 'text' + '\033[m'
assert '{}{}{}'.format(c, 'text', nocolor) == c('text')
```

A `ColorHSV` object could be casted into a `ColorRGB` object:

```python
assert ColorHSV(41, 100, 100).to_rgb() == ColorRGB(255, 174, 0)
assert ColorHSV(41, 100, 100).to_hsv() == ColorHSV(41, 100, 100)
```

Two sets of HSV values are provided:
*   Lowercase ``hsv`` for real values
*   Uppercase ``HSV`` for regulated values that are
    ``round()`` and ``clamp()`` to proper range.

```python
# Similar to clementine
c = ColorHSV(21.5, 100, 100)

# An impossible color
cc = c * 2

# Lowercase = real values
assert cc.hsv == (43, 200, 200)

# Uppercase = regulated values
assert cc.HSV == (43, 100, 100)
```

The escape sequence of a `ColorHSV` object is calculated based on `HSV`.


## `paint()`

An alias function that returns `ColorCompound` object.

__Parameters__
```python
paint(fg=None, bg=None)
```


## Class ``ColorCompound``

Binds two Color object together, one for foreground and one for background.

`ColorCompound` objects are created when doing operations on `Color` objects.

__Parameters__
```python
ColorCompound(fg=None, bg=None)
```

__Examples__
```python
orange = Color256(208)
darkorange = ColorRGB(255, 175, 0)

# Make orange background
assert (~orange)('ORANGE') == '\033[48;5;208mORANGE\033[m'

# Pair a foreground and a background
od = orange / darkorange
assert od('ORANGE') == '\033[38;5;208;48;2;255;175;0mORANGE\033[m\n'
```

In addition, `ColorCompound` objects supports ``__or__`` operation.
*   Foreground remains foreground, background remains background
*   The later color overrides the former

```python
ry = red / yellow
ig = ~green
ryig = ry | ig
assert ryig == red / green
assert ryig('text') == '\033[38;5;9;48;5;12mtext\033[m'
```


## `decolor()`

Return a new string that has color escape sequences removed.

__Parameters__
```python
decolor(s)
```

__Examples__
```python
s = 'some string'
cs = color(214)('some string') # '\e[38;5;214msome string\e[m'
assert decolor(cs) == s
```


## `names`

A list of named colors, that are pre-defined by iroiro and could be accessed
with `iroiro.<name>`.

The list was taken from
[W3C CSS Color Module Level 3, 4.3. Extended color keywords](https://www.w3.org/TR/css-color-3/#svg-color),
with a few extensions.

Note that all these colors are mapped to the nearest xterm 256 color, which
makes their values duplicate **a lot**.
Their RGB values are likely **not** consistent with W3C's definition.

* `aliceblue` (15)
* `antiquewhite` (230)
* `aqua` (14)
* `aquamarine` (122)
* `azure` (15)
* `beige` (230)
* `bisque` (224)
* `black` (0 black)
* `blanchedalmond` (230)
* `blue` (12)
* `blueviolet` (92)
* `brown` (124)
* `burlywood` (180)
* `cadetblue` (73)
* `chartreuse` (118)
* `chocolate` (166)
* `clementine` (166)
* `coral` (209)
* `cornflowerblue` (69)
* `cornsilk` (230)
* `crimson` (161)
* `cyan` (14)
* `darkblue` (18)
* `darkcyan` (30)
* `darkgoldenrod` (136)
* `darkgray` / `darkgrey` (248)
* `darkgreen` (22)
* `darkkhaki` (143)
* `darkmagenta` (90)
* `darkolivegreen` (239)
* `darkorange` (208)
* `darkorchid` (98)
* `darkred` (88)
* `darksalmon` (174)
* `darkseagreen` (108)
* `darkslateblue` (60)
* `darkslategray` / `darkslategrey` (238)
* `darkturquoise` (44)
* `darkviolet` (92)
* `deeppink` (198)
* `deepskyblue` (39)
* `dimgray` / `dimgrey` (242)
* `dodgerblue` (33)
* `firebrick` (124)
* `floralwhite` (15)
* `forestgreen` (28)
* `fuchsia` (13)
* `gainsboro` (253)
* `ghostwhite` (15)
* `gold` (220)
* `goldenrod` (178)
* `gray` / `grey` (8 gray)
* `green` (2 green)
* `greenyellow` (154)
* `honeydew` (255)
* `hotpink` (205)
* `indianred` (167)
* `indigo` (54)
* `ivory` (15)
* `khaki` (222)
* `lavender` (255)
* `lavenderblush` (15)
* `lawngreen` (118)
* `lemonchiffon` (230)
* `lightblue` (152)
* `lightcoral` (210)
* `lightcyan` (195)
* `lightgoldenrodyellow` (230)
* `lightgray` / `lightgrey` (252)
* `lightgreen` (120)
* `lightpink` (217)
* `lightsalmon` (216)
* `lightseagreen` (37)
* `lightskyblue` (117)
* `lightslategray` / `lightslategrey` (102)
* `lightsteelblue` (152)
* `lightyellow` (230)
* `lime` (10)
* `limegreen` (77)
* `linen` (255)
* `magenta` (13)
* `maroon` (1 maroon)
* `mediumaquamarine` (79)
* `mediumblue` (20)
* `mediumorchid` (134)
* `mediumpurple` (98)
* `mediumseagreen` (71)
* `mediumslateblue` (99)
* `mediumspringgreen` (48)
* `mediumturquoise` (80)
* `mediumvioletred` (162)
* `midnightblue` (17)
* `mintcream` (15)
* `mistyrose` (224)
* `moccasin` (223)
* `murasaki` (135)
* `navajowhite` (223)
* `navy` (4 navy)
* `oldlace` (230)
* `olive` (3 olive)
* `olivedrab` (64)
* `orange` (214)
* `orangered` (202)
* `orchid` (170)
* `palegoldenrod` (223)
* `palegreen` (120)
* `paleturquoise` (159)
* `palevioletred` (168)
* `papayawhip` (230)
* `peachpuff` (223)
* `peru` (173)
* `pink` (218)
* `plum` (182)
* `powderblue` (152)
* `purple` (5 purple)
* `red` (9 red)
* `rosybrown` (138)
* `royalblue` (62)
* `saddlebrown` (94)
* `salmon` (209)
* `sandybrown` (215)
* `seagreen` (29)
* `seashell` (255)
* `sienna` (130)
* `silver` (7 silver)
* `skyblue` (117)
* `slateblue` (62)
* `slategray` / `slategrey` (66)
* `snow` (15)
* `springgreen` (48)
* `steelblue` (67)
* `tan` (180)
* `teal` (6 teal)
* `thistle` (182)
* `tomato` (203)
* `turquoise` (80)
* `violet` (213)
* `wheat` (223)
* `white` (15)
* `whitesmoke` (255)
* `yellow` (11)
* `yellowgreen` (113)


## `nocolor`

A special color name that has the following properties:

__Examples__
```python
# It's colorless
assert nocolor == color()

# It doesn't add color to strings
assert nocolor('anything') == 'anything'

# And it ends color when formated
assert str(nocolor) == '\033[m'
assert '{}'.format(nocolor) == '\033[m'
```


## `gradient()`

Produces a series of colors from ``A`` to ``B`` of length ``N >= 2``.

__Parameters__
```python
gradient(A, B, N=None, reverse=False, clockwise=None)
```

__Examples__
```python
salmon = color('#FF875F') # or iroiro.salmon
white = color('#FFFFFF')  # or iroiro.white
g = gradient(salmon, white, 4) # [#FF875F, #FFAF94, #FFD7CA, #FFFFFF]
```

__Trivia__

*   If `A` and `B` are different Color types, `(A, B)` is returned.

*   For [`Color256`](#class-color256) colors,
    a discrete gradient path is calculated on xterm 256 color cube

    -   RGB range (`range(16, 232)`) and Grayscale range (`range(232, 256)`)
        are not compatible with each other

        +   Use `.to_rgb()` or `.to_hsv()` to
            calculate the gradient in different system

*   For [`ColorHSV`](#class-colorhsv) colors,
    keyword argument `clockwise` could be specified to force the
    gradient sequence to be clockwise or counter-clockwise
    -   If not specified, a shorter gradient sequence is preferred
