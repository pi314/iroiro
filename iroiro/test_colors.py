from .lib_test_utils import *

from iroiro import *


class TestColorFacade(TestCase):
    def test_color_facade(self):
        # no argument unpack
        with self.raises(TypeError):
            color((208,))

        with self.raises(TypeError):
            color([208])

        with self.raises(TypeError):
            color((0xC0, 0xFF, 0xEE))

        with self.raises(TypeError):
            color([0xC0, 0xFF, 0xEE])

        with self.raises(TypeError):
            color(0xC0, 0xFF)

        # copy_ctor
        self.eq(color(color(208)), color(208))

        # subclass
        self.true(issubclass(Color256, Color))
        self.true(issubclass(ColorRGB, Color))

        # Color256
        orange = color(208)
        self.true(isinstance(orange, Color256))
        self.true(isinstance(orange, Color))

        # ColorRGB
        coffee = color(0xC0, 0xFF, 0xEE)
        self.true(isinstance(coffee, ColorRGB))
        self.true(isinstance(coffee, Color))

        # ColorRGB
        coffee = color('#C0FFEE')
        self.true(isinstance(coffee, ColorRGB))
        self.true(isinstance(coffee, Color))

        # ColorHSV
        lime = color('@120,100,100')
        self.true(isinstance(lime, ColorHSV))
        self.true(isinstance(lime, Color))

    def test_color_invalid_value(self):
        with self.raises(TypeError):
            color(True)

        with self.raises(TypeError):
            Color256(True)

        with self.raises(TypeError):
            ColorRGB(True)


class TestColorTraits(TestCase):
    def setUp(self):
        self.orange = color(214)
        self.coffee = color('#C0FFEE')
        self.purple = color('@300,100,50')

    def test_repr(self):
        self.eq(repr(self.orange), 'Color256(214)')
        self.eq(' '.join(repr(self.coffee).split()), 'ColorRGB(192, 255, 238)')
        self.eq(' '.join(repr(self.purple).split()), 'ColorHSV(300deg, 100%, 50%)')

    def test_int(self):
        self.eq(int(self.orange), 214)
        self.eq(int(self.coffee), 0xC0FFEE)
        self.eq(int(self.purple), 300100050)

    def test_fg(self):
        self.eq(self.orange('text'), '\033[38;5;214mtext\033[m')
        self.eq(self.coffee('text'), '\033[38;2;192;255;238mtext\033[m')
        self.eq(self.purple('text'), '\033[38;2;128;0;128mtext\033[m')
        self.eq(self.orange.fg('text'), '\033[38;5;214mtext\033[m')
        self.eq(self.coffee.fg('text'), '\033[38;2;192;255;238mtext\033[m')
        self.eq(self.purple.fg('text'), '\033[38;2;128;0;128mtext\033[m')

    def test_bg(self):
        self.eq(self.orange.bg('text'), '\033[48;5;214mtext\033[m')
        self.eq(self.coffee.bg('text'), '\033[48;2;192;255;238mtext\033[m')
        self.eq(self.purple.bg('text'), '\033[48;2;128;0;128mtext\033[m')

    def test_str(self):
        self.eq(str(self.orange), '\033[38;5;214m')
        self.eq(str(self.coffee), '\033[38;2;192;255;238m')
        self.eq(str(self.purple), '\033[38;2;128;0;128m')
        self.eq('{}'.format(self.orange), str(self.orange))
        self.eq('{}'.format(self.coffee), str(self.coffee))
        self.eq('{}'.format(self.purple), str(self.purple))

    def test_invert(self):
        self.eq(str(~self.orange), '\033[48;5;214m')
        self.eq(str(~self.coffee), '\033[48;2;192;255;238m')
        self.eq(str(~self.purple), '\033[48;2;128;0;128m')
        self.true(isinstance(~self.orange, ColorCompound))
        self.true(isinstance(~self.coffee, ColorCompound))
        self.true(isinstance(~self.purple, ColorCompound))

    def test_div(self):
        colors_under_test = (self.orange, self.coffee, self.purple)
        for A in colors_under_test:
            for B in colors_under_test:
                self.eq(A / B, paint(fg=A, bg=B))

        for A in colors_under_test:
            with self.raises(TypeError):
                A / 1

    def test_or(self):
        colors_under_test = (self.orange, self.coffee, self.purple)
        for A in colors_under_test:
            self.eq(nocolor | A, A)
            self.eq(A | nocolor, A)

        for A in colors_under_test:
            for B in colors_under_test:
                self.eq(A | B, B)


class TestColor256(TestCase):
    def test_color256_code(self):
        for i in range(256):
            self.eq(color(i).code, i)

    def test_color256_to_rgb(self):
        self.eq(color(0).to_rgb(), ColorRGB(0x00, 0x00, 0x00))
        self.eq(color(1).to_rgb(), ColorRGB(0x80, 0x00, 0x00))
        self.eq(color(2).to_rgb(), ColorRGB(0x00, 0x80, 0x00))
        self.eq(color(3).to_rgb(), ColorRGB(0x80, 0x80, 0x00))
        self.eq(color(4).to_rgb(), ColorRGB(0x00, 0x00, 0x80))
        self.eq(color(5).to_rgb(), ColorRGB(0x80, 0x00, 0x80))
        self.eq(color(6).to_rgb(), ColorRGB(0x00, 0x80, 0x80))
        self.eq(color(7).to_rgb(), ColorRGB(0xC0, 0xC0, 0xC0))
        self.eq(color(8).to_rgb(), ColorRGB(0x80, 0x80, 0x80))
        self.eq(color(9).to_rgb(), ColorRGB(0xFF, 0x00, 0x00))
        self.eq(color(10).to_rgb(), ColorRGB(0x00, 0xFF, 0x00))
        self.eq(color(11).to_rgb(), ColorRGB(0xFF, 0xFF, 0x00))
        self.eq(color(12).to_rgb(), ColorRGB(0x00, 0x00, 0xFF))
        self.eq(color(13).to_rgb(), ColorRGB(0xFF, 0x00, 0xFF))
        self.eq(color(14).to_rgb(), ColorRGB(0x00, 0xFF, 0xFF))
        self.eq(color(15).to_rgb(), ColorRGB(0xFF, 0xFF, 0xFF))
        self.eq(color(208).to_rgb(), ColorRGB(0xFF, 0x87, 0x00))
        self.eq(color(232).to_rgb(), ColorRGB(0x08, 0x08, 0x08))
        self.eq(color(237).to_rgb(), ColorRGB(0x3A, 0x3A, 0x3A))

    def test_color256_to_hsv(self):
        self.eq(color(0).to_hsv(), color(0).to_rgb().to_hsv())
        self.eq(color(1).to_hsv(), color(1).to_rgb().to_hsv())
        self.eq(color(2).to_hsv(), color(2).to_rgb().to_hsv())
        self.eq(color(3).to_hsv(), color(3).to_rgb().to_hsv())
        self.eq(color(4).to_hsv(), color(4).to_rgb().to_hsv())
        self.eq(color(5).to_hsv(), color(5).to_rgb().to_hsv())
        self.eq(color(6).to_hsv(), color(6).to_rgb().to_hsv())
        self.eq(color(7).to_hsv(), color(7).to_rgb().to_hsv())
        self.eq(color(8).to_hsv(), color(8).to_rgb().to_hsv())
        self.eq(color(9).to_hsv(), color(9).to_rgb().to_hsv())
        self.eq(color(10).to_hsv(), color(10).to_rgb().to_hsv())
        self.eq(color(11).to_hsv(), color(11).to_rgb().to_hsv())
        self.eq(color(12).to_hsv(), color(12).to_rgb().to_hsv())
        self.eq(color(13).to_hsv(), color(13).to_rgb().to_hsv())
        self.eq(color(14).to_hsv(), color(14).to_rgb().to_hsv())
        self.eq(color(15).to_hsv(), color(15).to_rgb().to_hsv())
        self.eq(color(208).to_hsv(), color(208).to_rgb().to_hsv())
        self.eq(color(232).to_hsv(), color(232).to_rgb().to_hsv())
        self.eq(color(237).to_hsv(), color(237).to_rgb().to_hsv())


class TestColorRGB(TestCase):
    def test_rgb_empty(self):
        self.eq(ColorRGB().seq, '')

    def test_rgb(self):
        some_color = ColorRGB(160.2, 90, 0)

        self.eq(some_color.r, 160.2)
        self.eq(some_color.g, 90)
        self.eq(some_color.b, 0)
        self.eq(some_color.rgb, (160.2, 90, 0))

        self.eq(some_color.R, 160)
        self.eq(some_color.G, 90)
        self.eq(some_color.B, 0)
        self.eq(some_color.RGB, (160, 90, 0))

        self.eq(int(some_color), 0xA05A00)

    def test_value_range_check(self):
        with self.raises(TypeError):
            ColorRGB(300, 300, 300)

    def test_rgb_mul(self):
        some_color = ColorRGB(160, 90, 0) * 2
        self.eq(some_color.r, 320)
        self.eq(some_color.g, 180)
        self.eq(some_color.b, 0)

        self.eq(some_color.R, 255)
        self.eq(some_color.G, 180)
        self.eq(some_color.B, 0)

        some_color = ColorRGB(160, 90, 0) * 0.8
        self.eq(str(some_color), '\033[38;2;128;72;0m')

    def test_rgb_div(self):
        some_color = ColorRGB(160, 90, 0) // 2
        self.eq(some_color, ColorRGB(80, 45, 0))

    def test_rgb_overflow(self):
        some_color = ColorRGB(160, 90, 0) * 2
        self.eq(str(some_color), '\033[38;2;255;180;0m')
        self.eq(int(some_color), 0xFFB400)

    def test_rgb_average(self):
        d_red = ColorRGB(255, 0, 0) * 2
        self.eq(d_red.r, 255 * 2)
        self.eq(d_red.g, 0)
        self.eq(d_red.b, 0)

        d_green = ColorRGB(0, 255, 0) * 2
        self.eq(d_green.r, 0)
        self.eq(d_green.g, 255 * 2)
        self.eq(d_green.b, 0)

        d_yellow = d_red + d_green
        self.eq(d_yellow.r, 255 * 2)
        self.eq(d_yellow.g, 255 * 2)
        self.eq(d_yellow.b, 0)

        yellow = d_yellow // 2
        self.eq(yellow, ColorRGB(255, 255, 0))

    def test_rgb_to_rgb(self):
        red = ColorRGB(255, 0, 0)
        self.true(red.to_rgb() is red)

    def test_rgb_to_hsv(self):
        red = ColorRGB(255, 0, 0)
        self.eq(red.to_hsv(), ColorHSV(0, 100, 100))

    def test_rgb_format(self):
        red = ColorRGB(255, 0, 0)
        self.eq('{:#x}'.format(red), '#ff0000')
        self.eq('{:#X}'.format(red), '#FF0000')
        with self.raises(TypeError):
            self.eq('{:d}'.format(red), str(red))


class TestColorHSV(TestCase):
    def test_copy_ctor(self):
        red = ColorHSV('@0,100,100')
        other = ColorHSV(red)
        self.eq(red, other)

    def test_hsv_empty(self):
        self.eq(ColorHSV().seq, '')

    def test_hsv_parse_str(self):
        self.eq(ColorHSV('@0,100,100'), ColorHSV(0, 100, 100))
        self.eq(ColorHSV('@41,100,100'), ColorHSV(41, 100, 100))
        self.eq(ColorHSV('@401,100,100'), ColorHSV(41, 100, 100))
        self.eq(repr(ColorHSV('@0,100,100')), 'ColorHSV(0deg, 100%, 100%)')
        self.eq(repr(ColorHSV('@360,100,100')), 'ColorHSV(0deg, 100%, 100%)')

    def test_to_rgb(self):
        self.eq(ColorHSV('@0,100,100').to_rgb(), ColorRGB(255, 0, 0))

    def test_to_hsv(self):
        red = ColorHSV('@0,100,100')
        self.true(red.to_hsv() is red)

    def test_hsv(self):
        some_color = ColorHSV(60, 90, 0)
        self.eq(some_color.h, 60)
        self.eq(some_color.s, 90)
        self.eq(some_color.v, 0)
        self.eq(int(some_color), 60090000)

    def test_value_range_check(self):
        with self.raises(TypeError):
            ColorHSV(0, 101, 0)

        with self.raises(TypeError):
            ColorHSV(0, 0, 101)

        with self.raises(TypeError):
            ColorHSV(0, 0, 101, 0)

    def test_hsv_mul(self):
        some_color = ColorHSV(180, 100, 100) * 2
        self.eq(some_color.h, 0)
        self.eq(some_color.s, 200)
        self.eq(some_color.v, 200)
        self.eq(str(some_color), '\033[38;2;255;0;0m')

        some_color = ColorHSV(0, 100, 100) * 0.8
        self.eq(str(some_color), '\033[38;2;204;41;41m')

    def test_hsv_div(self):
        some_color = ColorHSV(160, 90, 0) // 2
        self.eq(some_color, ColorHSV(80, 45, 0))

    def test_hsv_overflow(self):
        some_color = ColorHSV(160, 90, 100) * 2
        self.eq(str(some_color), '\033[38;2;255;0;170m')
        self.eq(int(some_color), 320100100)

    def test_hsv_average(self):
        red = ColorHSV(360, 100, 100)
        yellow = ColorHSV(60, 100, 100)

        d_orange = red + yellow
        self.eq(d_orange.h, 60)
        self.eq(d_orange.s, 200)
        self.eq(d_orange.v, 200)

        orange = d_orange // 2
        self.eq(orange, ColorHSV(30, 100, 100))

    def test_hsv_format(self):
        lime = ColorHSV(120, 100, 100)
        self.eq('{}'.format(lime), str(ColorRGB(0, 255, 0)))
        self.eq('{:#}'.format(lime), '(@120, 100%, 100%)')

        with self.raises(TypeError):
            '{:d}'.format(lime)


class TestBuiltInColors(TestCase):
    def test_nocolor(self):
        self.eq(nocolor(), '')
        self.eq(nocolor('text'), 'text')
        self.eq(str(nocolor), '\033[m')
        self.eq('{}'.format(nocolor), '\033[m')

    def test_str(self):
        self.eq(str(black),     '\033[38;5;0m')
        self.eq(str(maroon),    '\033[38;5;1m')
        self.eq(str(green),     '\033[38;5;2m')
        self.eq(str(olive),     '\033[38;5;3m')
        self.eq(str(navy),      '\033[38;5;4m')
        self.eq(str(purple),    '\033[38;5;5m')
        self.eq(str(teal),      '\033[38;5;6m')
        self.eq(str(silver),    '\033[38;5;7m')
        self.eq(str(grey),      '\033[38;5;8m')
        self.eq(str(red),       '\033[38;5;9m')
        self.eq(str(lime),      '\033[38;5;10m')
        self.eq(str(yellow),    '\033[38;5;11m')
        self.eq(str(blue),      '\033[38;5;12m')
        self.eq(str(fuchsia),   '\033[38;5;13m')
        self.eq(str(magenta),   '\033[38;5;13m')
        self.eq(str(cyan),      '\033[38;5;14m')
        self.eq(str(aqua),      '\033[38;5;14m')
        self.eq(str(white),     '\033[38;5;15m')
        self.eq(str(darkorange),'\033[38;5;208m')
        self.eq(str(murasaki),  '\033[38;5;135m')

    def test_invert(self):
        self.eq(~red,      paint(bg=red))
        self.eq(~green,    paint(bg=green))
        self.eq(~yellow,   paint(bg=yellow))
        self.eq(~blue,     paint(bg=blue))
        self.eq(~magenta,  paint(bg=magenta))
        self.eq(~cyan,     paint(bg=cyan))
        self.eq(~white,    paint(bg=white))
        self.eq(~orange,   paint(bg=orange))

    def test_call(self):
        self.eq(black('text'),     '\033[38;5;0mtext\033[m')
        self.eq(maroon('text'),    '\033[38;5;1mtext\033[m')
        self.eq(green('text'),     '\033[38;5;2mtext\033[m')
        self.eq(olive('text'),     '\033[38;5;3mtext\033[m')
        self.eq(navy('text'),      '\033[38;5;4mtext\033[m')
        self.eq(purple('text'),    '\033[38;5;5mtext\033[m')
        self.eq(teal('text'),      '\033[38;5;6mtext\033[m')
        self.eq(silver('text'),    '\033[38;5;7mtext\033[m')
        self.eq(grey('text'),      '\033[38;5;8mtext\033[m')
        self.eq(red('text'),       '\033[38;5;9mtext\033[m')
        self.eq(lime('text'),      '\033[38;5;10mtext\033[m')
        self.eq(yellow('text'),    '\033[38;5;11mtext\033[m')
        self.eq(blue('text'),      '\033[38;5;12mtext\033[m')
        self.eq(fuchsia('text'),   '\033[38;5;13mtext\033[m')
        self.eq(magenta('text'),   '\033[38;5;13mtext\033[m')
        self.eq(cyan('text'),      '\033[38;5;14mtext\033[m')
        self.eq(aqua('text'),      '\033[38;5;14mtext\033[m')
        self.eq(white('text'),     '\033[38;5;15mtext\033[m')
        self.eq(darkorange('text'),'\033[38;5;208mtext\033[m')
        self.eq(murasaki('text'),  '\033[38;5;135mtext\033[m')


class TestPaint(TestCase):
    def test_repr(self):
        self.true(repr(paint()).startswith('ColorCompound'))

    def test_or(self):
        self.eq(black | (~yellow), paint(fg=0, bg=11))

        ry = red / yellow
        ig = ~green
        ryig = ry | ig
        self.eq(ryig, paint(fg=red, bg=green))

    def test_div(self):
        ry = red / yellow
        bg = blue / green
        rybg = ry / bg
        self.eq(rybg, paint(fg=red, bg=blue))
        self.eq(rybg('text'), '\033[38;5;9;48;5;12mtext\033[m')

    def test_invert(self):
        ry = red / yellow
        bg = blue / green
        rybg = ry / bg
        self.eq(~rybg, paint(fg=blue, bg=red))
        self.eq((~rybg)('text'), '\033[38;5;12;48;5;9mtext\033[m')


class TestDecolor(TestCase):
    def test_decolor(self):
        self.eq(decolor(orange('test')), 'test')
        self.eq(decolor('\033[1;31mred\033[m'), 'red')


class TestGradient(TestCase):
    def test_invalid_values(self):
        with self.raises(TypeError):
            gradient(True, False)

        A = color()
        B = color()

        with self.raises(TypeError):
            gradient(A, B, 1.5)

        with self.raises(ValueError):
            gradient(A, B, 1)

    def test_trivial(self):
        # N=2 trivial case
        A = color(39)
        B = color(214)
        self.eq(gradient(A, B, 2), (A, B))

        # Color256() and ColorRGB() case
        A = color(39)
        B = color('#C0FFEE')
        self.eq(gradient(A, B), (A, B))

        # Color256() rgb6 and gray case
        A = color(39)
        B = color(255)
        self.eq(gradient(A, B), (A, B))

    def test_color256_gray(self):
        A = color(235)
        B = color(245)

        # default length
        res = gradient(A, B)
        ans = tuple(range(235, 246))
        self.eq(res, tuple(map(color, ans)))

        # shorter length
        res = gradient(A, B, N=5)
        ans = (235, 238, 241, 243, 245)
        self.eq(res, tuple(map(color, ans)))

        # longer length
        res = gradient(A, B, N=15)
        ans = (235, 235, 236, 236, 237, 237, 238, 238, 239, 240, 241, 242, 243, 244, 245)
        self.eq(res, tuple(map(color, ans)))


    def test_color256_rgb(self):
        A = color(39)
        B = color(214)

        # default length
        res = gradient(A, B)
        ans = (39 ,74 ,109 ,144 ,179 ,214)
        self.eq(res, tuple(map(color, ans)))

        # shorter length
        res = gradient(A, B, N=4)
        ans = (39, 109, 179, 214)
        self.eq(res, tuple(map(color, ans)))

        # longer length
        res = gradient(A, B, N=15)
        ans = (39, 39, 39, 74, 74, 74, 109, 109, 109, 144, 144, 179, 179, 214, 214)
        self.eq(res, tuple(map(color, ans)))

    def test_rgb(self):
        A = color(242, 5, 148)
        B = color(146, 219, 189)

        # default length
        res = gradient(A, B)
        ans = (ColorRGB(242, 5, 148),
               ColorRGB(218, 58, 158),
               ColorRGB(194, 112, 168),
               ColorRGB(170, 166, 179),
               ColorRGB(146, 219, 189))
        for i in range(len(res)):
            self.eq(res[i], ans[i])

        # shorter length
        res = gradient(A, B, N=4)
        ans = (ColorRGB(242, 5, 148),
               ColorRGB(210, 76, 162),
               ColorRGB(178, 148, 175),
               ColorRGB(146, 219, 189))
        for i in range(len(res)):
            self.eq(res[i], ans[i])

        # longer length
        res = gradient(A, B, N=15)
        ans = (ColorRGB(242, 5, 148),
               ColorRGB(235, 20, 151),
               ColorRGB(228, 36, 154),
               ColorRGB(221, 51, 157),
               ColorRGB(215, 66, 160),
               ColorRGB(208, 81, 163),
               ColorRGB(201, 97, 166),
               ColorRGB(194, 112, 168),
               ColorRGB(187, 127, 171),
               ColorRGB(180, 143, 174),
               ColorRGB(173, 158, 177),
               ColorRGB(167, 173, 180),
               ColorRGB(160, 188, 183),
               ColorRGB(153, 204, 186),
               ColorRGB(146, 219, 189))
        for i in range(len(res)):
            self.eq(res[i], ans[i])

        A = color('#FF1100')
        B = color('#FF0011')
        res = gradient(A, B, N=3)
        self.eq(res, (A, color('#FF0808'), B))

    def test_hsv(self):
        A = ColorHSV(0, 100, 100)
        B = ColorHSV(300, 50, 100)

        # clockwise
        res = gradient(A, B, clockwise=True)
        res2 = gradient(A, B)
        ans = (ColorHSV(0, 100, 100),
               ColorHSV(33, 94, 100),
               ColorHSV(66, 88, 100),
               ColorHSV(100, 83, 100),
               ColorHSV(133, 77, 100),
               ColorHSV(166, 72, 100),
               ColorHSV(200, 66, 100),
               ColorHSV(233, 61, 100),
               ColorHSV(266, 55, 100),
               ColorHSV(300, 50, 100),)

        self.eq(len(res), len(ans))
        for a, b, c in zip(res, res2, ans):
            # Check if the colors are close enough
            self.le(abs(sum(a.hsv) - sum(b.hsv)), 2)
            self.le(abs(sum(a.hsv) - sum(c.hsv)), 2)

        res = gradient(A, B, clockwise=True, N=5)
        res2 = gradient(A, B)
        ans = (ColorHSV(0, 100, 100),
               ColorHSV(75, 88, 100),
               ColorHSV(150, 75, 100),
               ColorHSV(225, 62, 100),
               ColorHSV(300, 50, 100),)

        for a, b in zip(res, ans):
            # Check if the colors are close enough
            self.le(abs(sum(a.hsv) - sum(b.hsv)), 2)

        # counter-clockwise
        res = gradient(A, B, clockwise=False)
        ans = (ColorHSV(0, 100, 100),
               ColorHSV(345, 87, 100),
               ColorHSV(330, 75, 100),
               ColorHSV(315, 62, 100),
               ColorHSV(300, 50, 100),)

        self.eq(len(res), len(ans))
        for a, b in zip(res, ans):
            # Check if the colors are close enough
            self.le(abs(sum(a.hsv) - sum(b.hsv)), 2)

        # reverse
        res = gradient(A, B, clockwise=True)
        rev = gradient(A, B, clockwise=True, reverse=True)

        for a, b in zip(res, rev[::-1]):
            # Check if the colors are close enough
            self.le(abs(sum(a.hsv) - sum(b.hsv)), 2)

        # reverse
        res = gradient(A, B, clockwise=False)
        rev = gradient(A, B, clockwise=False, reverse=True)

        for a, b in zip(res, rev[::-1]):
            # Check if the colors are close enough
            self.le(abs(sum(a.hsv) - sum(b.hsv)), 2)
