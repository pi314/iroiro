from .lib_test_utils import *

from warawara import NoColor, color, Emphasis
from warawara import paint
from warawara import nocolor


class TestNoColor(TestCase):
    def test_repr(self):
        self.eq(repr(NoColor()), 'NoColor()')

    def test_seq(self):
        nc = NoColor()
        self.eq(str(nc), '\033[m')
        self.eq(nc.seq, '\033[m')

    def test_or(self):
        nc = NoColor()
        self.eq(paint() | nc, nc)
        self.eq(color(135) | nc, nc)
        self.eq(Emphasis() | nc, nc)

        self.eq(nc | paint(fg=135), paint(fg=135))
        self.eq(nc | color(135), color(135))
        self.eq(nc | Emphasis(bold=True), Emphasis(bold=True))

    def test_color(self):
        self.eq(nocolor('wah'), 'wah')
