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


class TestMenuCursor(TestCase):
    def setUp(self):
        import warawara
        self.menu = warawara.Menu('title', ['Option 1', 'Option 2', 'Option 3'])

    def test_repr(self):
        c = self.menu.cursor
        self.eq(repr(self.menu.cursor), f'MenuCursor(index={c.index}, wrap={c.wrap})')

    def test_str(self):
        self.eq(str(self.menu.cursor), '>')

    def test_add_sub_to(self):
        c = self.menu.cursor
        self.eq(c, 0)

        c += 1
        self.eq(c, 1)

        c += 1
        self.eq(c, 2)

        c += 10
        self.eq(c, 2)

        c -= 100
        self.eq(c, 0)

        c.to(1 + c)
        self.eq(c, 1)

        c.to(1 - c)
        self.eq(c, 0)

        c.to(1)
        self.ne(c, 0)
        self.gt(c, 0)
        self.ge(c, 0)
        self.ge(c, 1)
        self.eq(c, 1)
        self.le(c, 1)
        self.le(c, 2)
        self.lt(c, 2)
        self.ne(c, 2)

        c.up()
        self.eq(c, 0)

        c.down()
        c.down()
        self.eq(c, 2)

        c.to(self.menu[1])
        self.ne(c, self.menu[0])
        self.gt(c, self.menu[0])
        self.ge(c, self.menu[0])
        self.ge(c, self.menu[1])
        self.eq(c, self.menu[1])
        self.le(c, self.menu[1])
        self.le(c, self.menu[2])
        self.lt(c, self.menu[2])
        self.ne(c, self.menu[2])
        self.eq(c.text, 'Option 2')

    def test_up_down_wrap(self):
        c = self.menu.cursor

        c.wrap = True
        c.to(31)
        self.eq(c, 1)

        c.down()
        self.eq(c, 2)

        c.down()
        self.eq(c, 0)

        c.up()
        self.eq(c, 2)

    def test_to_diff_menu(self):
        import warawara
        other_menu = warawara.Menu('title', ['Option 1', 'Option 2', 'Option 3'])

        with self.raises(ValueError):
            self.menu.cursor.to(other_menu[1])

    def test_attr(self):
        c = self.menu.cursor

        c.to(1)
        self.eq(c.text, 'Option 2')

        with self.raises(AttributeError):
            c.bau


class TestMenuKeyHandler(TestCase):
    def setUp(self):
        import warawara
        self.menu = warawara.Menu('title', ['Option 1', 'Option 2'])

    def test_empty_handler(self):
        import warawara
        handler = warawara.tui.MenuKeyHandler(self.menu)

        ret = handler.handle('a')
        self.eq(ret, None)

    def test_bind_without_handler(self):
        import warawara
        handler = warawara.tui.MenuKeyHandler(self.menu)

        with self.raises(ValueError):
            handler.bind('a', 'b', 'c')

    def test_bind_unbind_handler(self):
        import warawara
        handler = warawara.tui.MenuKeyHandler(self.menu)

        def foo(menu, key):
            pass

        def bar(menu, key):
            pass

        def baz(menu, key):
            pass

        handler.bind(foo, bar)
        self.eq(handler[None], [foo, bar])

        handler(baz)
        self.eq(handler[None], [foo, bar, baz])

        handler.unbind(foo, bar, baz)
        self.eq(handler[None], [])

        handler += foo
        self.eq(handler[None], [foo])
        handler += (bar, baz)
        self.eq(handler[None], [foo, bar, baz])

        handler -= bar
        self.eq(handler[None], [foo, baz])
        handler -= (baz, foo)
        self.eq(handler[None], [])

        handler['k'] += foo
        self.eq(handler['k'], [foo])
        handler['w'] += (bar, baz)
        self.eq(handler['w'], [bar, baz])

        handler['k'] = None
        self.eq(handler['k'], [])
        handler -= (baz, foo)
        self.eq(handler['k'], [])
        self.eq(handler['w'], [bar])
        handler['w'] -= [bar]
        self.eq(handler['w'], [])

        handler['k'] = None
        self.eq(handler['k'], [])

        handler['k'] = foo
        self.eq(handler['k'], [foo])
        handler['k'] = bar
        self.eq(handler['k'], [bar])
        handler -= 'k'
        self.eq(handler['k'], [])

    def test_duplicated_bind(self):
        import warawara
        handler = warawara.tui.MenuKeyHandler(self.menu)

        def foo(menu, key):
            by.append(foo)

        handler.bind(foo)
        handler.bind(foo)

        by = []
        ret = handler.handle('f')
        self.eq(by, [foo])

    def test_key_bubbling(self):
        import warawara
        handler = warawara.tui.MenuKeyHandler(self.menu)

        def foo(menu, key):
            by.append(foo)
            if key == 'f':
                return foo

        def bar(menu, key):
            by.append(bar)
            if key == 'r':
                return bar

        def baz(menu, key):
            by.append(baz)
            if key == 'z':
                return baz

        handler.bind(foo)

        handler.bind('b', bar)
        handler.bind('b', baz)

        handler.bind('f', bar)
        handler.bind('f', baz)

        handler.bind('r', bar)

        handler.bind('z', bar)
        handler.bind('z', baz)

        by = []
        ret = handler.handle('w')
        self.eq(ret, None)
        self.eq(by, [foo])

        by = []
        ret = handler.handle('b')
        self.eq(ret, None)
        self.eq(by, [bar, baz, foo])

        by = []
        ret = handler.handle('f')
        self.eq(ret, foo)
        self.eq(by, [bar, baz, foo])

        by = []
        ret = handler.handle('r')
        self.eq(ret, bar)
        self.eq(by, [bar])

        by = []
        ret = handler.handle('z')
        self.eq(ret, baz)
        self.eq(by, [bar, baz])

    def test_attach_to_menu_item(self):
        import warawara
        handler = warawara.tui.MenuKeyHandler(self.menu[0])

        by = []
        def foo(item, key):
            by.append(foo)
        handler += foo

        handler.handle('f')
        self.eq(by, [foo])

    def test_attach_to_something_else(self):
        import warawara
        handler = warawara.tui.MenuKeyHandler(warawara)

        by = []
        def foo(key):
            by.append(foo)
            return key
        handler += foo

        ret = handler.handle('f')
        self.eq(ret, 'f')
        self.eq(by, [foo])

    def test_handler_without_args(self):
        import warawara
        handler = warawara.tui.MenuKeyHandler(self.menu)

        by = []
        def foo():
            by.append(foo)
        handler += foo

        handler.handle('f')
        self.eq(by, [foo])
