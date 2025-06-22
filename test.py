import warawara


def main():
    import os
    menu = warawara.Menu('title', warawara.natsorted(os.listdir()), max_height=10)

    def pager_info(key):
        menu.message = 'key={} cursor={} text={} visible={} scroll={} height={}'.format(
                key, repr(menu.cursor),
                menu.pager[int(menu.cursor)].visible, menu.pager.scroll, menu.pager.height)

    def onkey_vim(menu, key):
        if key == 'k':
            return warawara.KEY_UP
        elif key == 'j':
            return warawara.KEY_DOWN
        elif key == 'ctrl-y':
            menu.scroll(-1)
        elif key == 'ctrl-e':
            menu.scroll(1)
        elif key == 'g':
            menu.cursor = menu.first
        elif key == 'G':
            menu.cursor = menu.last
        elif key == 'H':
            menu.cursor = menu.top
        elif key == 'M':
            menu.cursor = (menu.top.index + menu.bottom.index) // 2
        elif key == 'L':
            menu.cursor = menu.bottom
        pager_info(key)

    def onkey_resize(menu, key):
        if key == '-':
            if not menu.pager.max_height:
                menu.pager.max_height = menu.pager.height - 1
            else:
                menu.pager.max_height -= 1
        elif key == '+':
            if not menu.pager.max_height:
                menu.pager.max_height = menu.pager.height + 1
            else:
                menu.pager.max_height += 1
        elif key == '=':
            menu.pager.max_height = None
        pager_info(key)

    def onkey(menu, key):
        unknown_key = False
        if key == 'w':
            menu.wrap = not menu.wrap
        elif key == 't':
            if menu.title == 'new title':
                menu.title = 'new multiline\ntitle'
            elif menu.title:
                menu.title = None
            else:
                menu.title = 'new title'
        elif key == 's':
            menu.message = 'scroll=' + str(menu.pager.scroll)
        else:
            unknown_key = True

        if not unknown_key:
            pager_info(key)
        else:
            menu.message = repr(key)

    menu.onkey(warawara.KEY_UP, menu.cursor.up)
    menu.onkey('down', menu.cursor.down)
    menu.onkey(onkey, onkey_vim, onkey_resize)
    menu.onkey('q', menu.quit)

    def enter(item, key):
        item.menu.message = 'enter'
        item.menu.done()
    menu[-1].onkey(warawara.KEY_ENTER, enter)

    def index(item, key):
        if key == 'i':
            menu.message = f'index={item.index}'
            return False
    for item in menu:
        item.onkey('i', index)

    ret = menu.interact()
    print(ret)


if __name__ == '__main__':
    main()
