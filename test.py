import warawara


def main():
    import os
    menu = warawara.Menu('title', warawara.natsorted(os.listdir()), max_height=10)

    def pager_info(key):
        menu.message = 'key={} cursor={} visible={} scroll={} height={}'.format(
                key, repr(menu.cursor), menu.pager[int(menu.cursor)].visible, menu.pager.scroll, menu.pager.height)

    def onkey_vim(menu, key):
        if key == 'k':
            return warawara.KEY_UP
        elif key == 'j':
            return warawara.KEY_DOWN
        elif key == 'ctrl-e':
            menu.pager.scroll += 1
            if not menu.pager[int(menu.cursor)].visible:
                menu.cursor += 1
        elif key == 'ctrl-y':
            menu.pager.scroll -= 1
            if not menu.pager[int(menu.cursor)].visible:
                menu.cursor -= 1
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
        if key == 'up':
            menu.cursor -= 1
            if not menu.pager[int(menu.cursor)].visible:
                menu.pager.scroll -= 1
                if not menu.pager[int(menu.cursor)].visible:
                    menu.pager.scroll = '$'
        elif key == 'down':
            menu.cursor += 1
            if not menu.pager[int(menu.cursor)].visible:
                menu.pager.scroll += 1
                if not menu.pager[int(menu.cursor)].visible:
                    menu.pager.scroll = 0
        elif key in ('q', 'ctrl+c', warawara.KEY_FS):
            menu.message = repr(key)
            menu.render()
            menu.quit()
        elif key == 'w':
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

    menu.onkey(onkey)
    menu.onkey(onkey_vim)
    menu.onkey(onkey_resize)
    ret = menu.interact()
    print(ret)


if __name__ == '__main__':
    main()
