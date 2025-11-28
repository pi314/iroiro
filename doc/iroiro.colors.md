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
color('...')
```

__Examples__
```python
color()                 # Color256: empty
color(214)              # Color256: darkorange
color(255, 175, 0)      # ColorRGB: orange
color('#FFAF00')        # ColorRGB: orange
color('@41,100,100')    # ColorHSV: orange
color('\033[38;5;214m') # paint(fg=Color256(214))
```

If the argument does not in correct data type, `TypeError` is raised.

See [Color256](#class-color256), [ColorRGB](#class-colorrgb),
and [ColorHSV](#class-colorhsv) for more details.


## Class `Emphasis`

Represent special attributes (bold, underline, blink, etc.)

__Parameters__
```python
Emphasis()
Emphasis(*codes, **attrs)
# codes: 1 | 2 | 4 | 5 | 7 | 8
# attrs: bold | lowint | underline | blink | reverse | invisible
```

__Examples__
```python
Emphasis(1)
Emphasis(1, 2, 4, 5, 7, 8)
Emphasis(bold=True)
Emphasis(bold=True, lowint=True, underline=True, blink=True, reverse=True, invisible=True)
```


## Class `Color`

An abstract base class that is inherited by other Color types.

It's intended to be used for type checking. For example, `isinstance(obj, Color)`.

Two `Color` objects are defined equal if their escape sequences are equal.


## Class `Color8`

Represents a VT100 8 color.

The actual color displayed in your terminal might look different
depends on your palette settings.

__Parameters__
```python
Color8()
Color8(index) # index: int, 0 ~ 7
```

__Examples__
```python
# Magenta
c = Color8(5)
assert str(c) == '\033[35m'
assert c.to_256() == Color256(5)
```

Color8 is kind of a subset of Color256.
See [Color256](#class-color256) for more examples.


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
paint(em=None, fg=None, bg=None)
```


## Class ``ColorCompound``

Binds two Color object together, one for foreground and one for background.

`ColorCompound` objects are created when doing operations on `Color` objects.

__Parameters__
```python
ColorCompound(em=None, fg=None, bg=None)
```

__Examples__
```python
orange = Color256(208)
darkorange = ColorRGB(255, 175, 0)

# Make orange background
assert (~orange)('ORANGE') == '\033[48;5;208mORANGE\033[m'

# Pair a foreground and a background
od = orange / darkorange
assert od('ORANGE') == '\033[38;5;208;48;2;255;175;0mORANGE\033[m'
```

In addition, `ColorCompound` objects supports ``__or__`` operation.
*   Foreground remains foreground, background remains background
*   The later color overrides the former

```python
ry = red / yellow
ig = ~green
ryig = ry | ig
assert ryig == red / green
assert ryig('text') == '\033[38;5;9;48;5;2mtext\033[m'

# Emphasize with bold and underline
buryig = bold | underline | ryig
assert buryig('text') == '\033[1;4;38;5;9;48;5;2mtext\033[m'
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

A list of named colors, that are built-in by iroiro and could be accessed
with `iroiro.<name>`.

The list was taken from
[W3C CSS Color Module Level 3, 4.3. Extended color keywords](https://www.w3.org/TR/css-color-3/#svg-color),
with a few extensions.

The 256-color index or the RGB value of the colors are listed as following:

| Color                  | Index or RGB Value |
|------------------------+--------------------|
| `black`                | 0                  |
| `maroon`               | 1                  |
| `green`                | 2                  |
| `olive`                | 3                  |
| `navy`                 | 4                  |
| `purple`               | 5                  |
| `teal`                 | 6                  |
| `silver`               | 7                  |
| `gray` / `grey`        | 8                  |
| `red`                  | 9                  |
| `lime`                 | 10                 |
| `yellow`               | 11                 |
| `blue`                 | 12                 |
| `fuchsia` / `magenta`  | 13                 |
| `aqua` / `cyan`        | 14                 |
| `white`                | 15                 |
| `murasaki`             | 135                |
| `aliceblue`            | (240, 248, 255)    |
| `antiquewhite`         | (250, 235, 215)    |
| `aquamarine`           | (127, 255, 212)    |
| `azure`                | (240, 255, 255)    |
| `beige`                | (245, 245, 220)    |
| `bisque`               | (255, 228, 196)    |
| `blanchedalmond`       | (255, 235, 205)    |
| `blueviolet`           | (138, 43, 226)     |
| `brown`                | (165, 42, 42)      |
| `burlywood`            | (222, 184, 135)    |
| `cadetblue`            | (95, 158, 160)     |
| `chartreuse`           | (127, 255, 0)      |
| `chocolate`            | (210, 105, 30)     |
| `clementine`           | (233, 110, 0)      |
| `coral`                | (255, 127, 80)     |
| `cornflowerblue`       | (100, 149, 237)    |
| `cornsilk`             | (255, 248, 220)    |
| `crimson`              | (220, 20, 60)      |
| `darkblue`             | (0, 0, 139)        |
| `darkcyan`             | (0, 139, 139)      |
| `darkgoldenrod`        | (184, 134, 11)     |
| `darkgray`             | (169, 169, 169)    |
| `darkgreen`            | (0, 100, 0)        |
| `darkgrey`             | (169, 169, 169)    |
| `darkkhaki`            | (189, 183, 107)    |
| `darkmagenta`          | (139, 0, 139)      |
| `darkolivegreen`       | (85, 107, 47)      |
| `darkorange`           | (255, 140, 0)      |
| `darkorchid`           | (153, 50, 204)     |
| `darkred`              | (139, 0, 0)        |
| `darksalmon`           | (233, 150, 122)    |
| `darkseagreen`         | (143, 188, 143)    |
| `darkslateblue`        | (72, 61, 139)      |
| `darkslategray`        | (47, 79, 79)       |
| `darkslategrey`        | (47, 79, 79)       |
| `darkturquoise`        | (0, 206, 209)      |
| `darkviolet`           | (148, 0, 211)      |
| `deeppink`             | (255, 20, 147)     |
| `deepskyblue`          | (0, 191, 255)      |
| `dimgray`              | (105, 105, 105)    |
| `dimgrey`              | (105, 105, 105)    |
| `dodgerblue`           | (30, 144, 255)     |
| `firebrick`            | (178, 34, 34)      |
| `floralwhite`          | (255, 250, 240)    |
| `forestgreen`          | (34, 139, 34)      |
| `gainsboro`            | (220, 220, 220)    |
| `ghostwhite`           | (248, 248, 255)    |
| `gold`                 | (255, 215, 0)      |
| `goldenrod`            | (218, 165, 32)     |
| `greenyellow`          | (173, 255, 47)     |
| `honeydew`             | (240, 255, 240)    |
| `hotpink`              | (255, 105, 180)    |
| `indianred`            | (205, 92, 92)      |
| `indigo`               | (75, 0, 130)       |
| `ivory`                | (255, 255, 240)    |
| `khaki`                | (240, 230, 140)    |
| `lavender`             | (230, 230, 250)    |
| `lavenderblush`        | (255, 240, 245)    |
| `lawngreen`            | (124, 252, 0)      |
| `lemonchiffon`         | (255, 250, 205)    |
| `lightblue`            | (173, 216, 230)    |
| `lightcoral`           | (240, 128, 128)    |
| `lightcyan`            | (224, 255, 255)    |
| `lightgoldenrodyellow` | (250, 250, 210)    |
| `lightgray`            | (211, 211, 211)    |
| `lightgreen`           | (144, 238, 144)    |
| `lightgrey`            | (211, 211, 211)    |
| `lightpink`            | (255, 182, 193)    |
| `lightsalmon`          | (255, 160, 122)    |
| `lightseagreen`        | (32, 178, 170)     |
| `lightskyblue`         | (135, 206, 250)    |
| `lightslategray`       | (119, 136, 153)    |
| `lightslategrey`       | (119, 136, 153)    |
| `lightsteelblue`       | (176, 196, 222)    |
| `lightyellow`          | (255, 255, 224)    |
| `limegreen`            | (50, 205, 50)      |
| `linen`                | (250, 240, 230)    |
| `mediumaquamarine`     | (102, 205, 170)    |
| `mediumblue`           | (0, 0, 205)        |
| `mediumorchid`         | (186, 85, 211)     |
| `mediumpurple`         | (147, 112, 219)    |
| `mediumseagreen`       | (60, 179, 113)     |
| `mediumslateblue`      | (123, 104, 238)    |
| `mediumspringgreen`    | (0, 250, 154)      |
| `mediumturquoise`      | (72, 209, 204)     |
| `mediumvioletred`      | (199, 21, 133)     |
| `midnightblue`         | (25, 25, 112)      |
| `mintcream`            | (245, 255, 250)    |
| `mistyrose`            | (255, 228, 225)    |
| `moccasin`             | (255, 228, 181)    |
| `navajowhite`          | (255, 222, 173)    |
| `oldlace`              | (253, 245, 230)    |
| `olivedrab`            | (107, 142, 35)     |
| `orange`               | (255, 165, 0)      |
| `orangered`            | (255, 69, 0)       |
| `orchid`               | (218, 112, 214)    |
| `palegoldenrod`        | (238, 232, 170)    |
| `palegreen`            | (152, 251, 152)    |
| `paleturquoise`        | (175, 238, 238)    |
| `palevioletred`        | (219, 112, 147)    |
| `papayawhip`           | (255, 239, 213)    |
| `peachpuff`            | (255, 218, 185)    |
| `peru`                 | (205, 133, 63)     |
| `pink`                 | (255, 192, 203)    |
| `plum`                 | (221, 160, 221)    |
| `powderblue`           | (176, 224, 230)    |
| `rosybrown`            | (188, 143, 143)    |
| `royalblue`            | (65, 105, 225)     |
| `saddlebrown`          | (139, 69, 19)      |
| `salmon`               | (250, 128, 114)    |
| `sandybrown`           | (244, 164, 96)     |
| `seagreen`             | (46, 139, 87)      |
| `seashell`             | (255, 245, 238)    |
| `sienna`               | (160, 82, 45)      |
| `skyblue`              | (135, 206, 235)    |
| `slateblue`            | (106, 90, 205)     |
| `slategray`            | (112, 128, 144)    |
| `slategrey`            | (112, 128, 144)    |
| `snow`                 | (255, 250, 250)    |
| `springgreen`          | (0, 255, 127)      |
| `steelblue`            | (70, 130, 180)     |
| `tan`                  | (210, 180, 140)    |
| `thistle`              | (216, 191, 216)    |
| `tomato`               | (255, 99, 71)      |
| `turquoise`            | (64, 224, 208)     |
| `violet`               | (238, 130, 238)    |
| `wheat`                | (245, 222, 179)    |
| `whitesmoke`           | (245, 245, 245)    |
| `yellowgreen`          | (154, 205, 50)     |


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
