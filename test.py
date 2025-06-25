import warawara


def main():
    import os
    def format(menu, cursor, item, check, box):
        if menu.data.grabbing and menu.cursor == item:
            return f'{cursor}{box[0]}{check}{box[1]} {item.text}'
        return f'{cursor} {box[0]}{check}{box[1]} {item.text}'
    menu = warawara.Menu('title', warawara.natsorted(os.listdir()), checkbox='[*]', format=format, max_height=10)

    def pager_info(key):
        menu.message = 'key={} cursor={} grab={} text=[{}] visible={} scroll={} height={}'.format(
                key, repr(menu.cursor), menu.data.grabbing, menu.cursor.text,
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

    def grab(menu, key):
        menu.data.grabbing = True
    def ungrab(menu, key):
        menu.data.grabbing = False
    def up(menu, key):
        if menu.data.grabbing and menu.cursor > 0:
            menu.swap(menu.cursor, menu.cursor - 1)
        menu.cursor.up()
    def down(menu, key):
        if menu.data.grabbing and menu.cursor < len(menu) - 1:
            menu.swap(menu.cursor, menu.cursor + 1)
        menu.cursor.down()
    menu.onkey(warawara.KEY_UP, up)
    menu.onkey('down', down)
    menu.onkey(warawara.KEY_LEFT, grab)
    menu.onkey(warawara.KEY_RIGHT, ungrab)

    menu.onkey(onkey, onkey_vim, onkey_resize)
    menu.onkey('q', menu.quit)

    def enter(item, key):
        item.menu.message = 'enter'
        item.menu.done()
    done = menu.append('[done]', meta=True)
    done.onkey(warawara.KEY_ENTER, enter)

    def index(item, key):
        if key == 'i':
            menu.message = f'index={item.index}'
            return False
        elif key == 'space':
            item.toggle()
    for item in menu:
        item.onkey('i', 'space', index)

    select_all = menu.append('Select all', meta=True, checkbox='{*}')
    select_all.onkey(warawara.KEY_SPACE, menu.select_all)

    select_all = menu.append('Unselect all', meta=True)
    select_all.onkey(warawara.KEY_SPACE, menu.unselect_all)

    ret = menu.interact()
    print(ret)


if __name__ == '__main__':
    main()
