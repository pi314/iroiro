from .lib_test_utils import *


class TestMenuData(TestCase):
    def test_basic(self):
        import warawara
        m = warawara.tui.MenuData()
        m['key'] = 'value'
        self.eq(m.key, 'value')

        m.key = 42
        self.eq(m['key'], 42)
        self.eq(repr(m), "MenuData({'key': 42})")

        del m.what
        self.eq(repr(m), "MenuData({'key': 42})")

        del m.key
        self.eq(repr(m), 'MenuData({})')

        m.key = 52
        self.eq(repr(m), "MenuData({'key': 52})")

        m.key = None
        self.eq(repr(m), 'MenuData({})')
