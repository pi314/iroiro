from .lib_test_utils import *


class TestMenuData(TestCase):
    def test_basic(self):
        import warawara
        data = warawara.tui.MenuData()
        data['key'] = 'value'
        self.eq(data.key, 'value')

        data.key = 42
        self.eq(data['key'], 42)
        self.eq(repr(data), "MenuData({'key': 42})")

        del data.what
        self.eq(repr(data), "MenuData({'key': 42})")

        del data.key
        self.eq(repr(data), 'MenuData({})')

        data.key = 52
        self.eq(repr(data), "MenuData({'key': 52})")

        data.key = None
        self.eq(repr(data), 'MenuData({})')

        del m.key
        self.eq(repr(m), 'MenuData({})')

        m.key = 52
        self.eq(repr(m), "MenuData({'key': 52})")

        m.key = None
        self.eq(repr(m), 'MenuData({})')
