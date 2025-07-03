import warawara


def main():
    import os
    def format(menu, cursor, item, check, box):
        ind = ''
        if item.data.ind:
            ind = ' ' + item.data.ind

        if menu.data.grabbing and menu.cursor == item:
            return f'{cursor}{box[0]}{check}{box[1]} {item.text}{ind}'
        return f'{cursor} {box[0]}{check}{box[1]} {item.text}{ind}'
    menu = warawara.Menu('title', warawara.natsorted(os.listdir()), checkbox='[*]', format=format, max_height=20)

    def pager_info(key):
        menu.message = 'key={} cursor={} grab={} text=[{}] visible={} scroll={} height={}'.format(
                key, repr(menu.cursor), menu.data.grabbing, menu.cursor.text,
                menu.pager[int(menu.cursor)].visible, menu.pager.scroll, menu.pager.height)

    def onkey_vim(menu, key):
        if key == 'k':
            return menu.feedkey(warawara.KEY_UP)
        elif key == 'j':
            return menu.feedkey(warawara.KEY_DOWN)
        if key == 'h':
            return menu.feedkey(warawara.KEY_LEFT)
        elif key == 'l':
            return menu.feedkey(warawara.KEY_RIGHT)
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

        if menu.data.grabbing:
            menu.data.grabbing.moveto(menu.cursor)

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
            menu.message = '[' + repr(key) + ']'

    def grab(menu, key):
        menu.data.grabbing = menu[menu.cursor]
    def ungrab(menu, key):
        menu.data.grabbing = None
    def up(menu, key):
        menu.cursor.up()
        if menu.data.grabbing:
            menu.data.grabbing.moveto(menu.cursor)
    def down(menu, key):
        menu.cursor.down()
        if menu.data.grabbing:
            menu.data.grabbing.moveto(menu.cursor)
    menu.onkey(warawara.KEY_UP, up)
    menu.onkey('down', down)
    menu.onkey(warawara.KEY_LEFT, grab)
    menu.onkey(warawara.KEY_RIGHT, ungrab)

    menu.onkey(onkey, onkey_vim, onkey_resize)
    menu.onkey('q', menu.quit)

    def index(item, key):
        if key == 'i':
            menu.message = f'index={item.index}'
            return False
        elif key == 'space':
            item.toggle()
            import time
            if not item.data.thread:
                def task():
                    limit = 5
                    item.data.start = time.time()
                    while (time.time() - item.data.start) < limit:
                        item.data.ind = f'({int((limit + item.data.start - time.time()) * 1000) / 1000})'
                        time.sleep(0.0005)
                        item.menu.refresh()
                        if not menu.active:
                            break
                    del item.data.thread
                    del item.data.ind
                    item.menu.refresh()
                item.data.thread = menu.Thread(target=task)
                item.data.thread.start()
            else:
                item.data.start = time.time()

    for item in menu:
        item.onkey('i', 'space', index)

    select_all = menu.append('Select all', meta=True)
    def check(*args, **kwargs):
        if all(item.selected for item in menu if not item.meta):
            return '*'
        elif all(not item.selected for item in menu if not item.meta):
            return ' '
        else:
            return '+'
    select_all.check = check
    def select_and_trigger_all(item, key):
        item.menu.select_all()
        for item in menu:
           if not item.meta:
                item.feedkey(warawara.KEY_SPACE)
    select_all.onkey(warawara.KEY_SPACE, select_and_trigger_all)

    unselect_all = menu.append('Unselect all', meta=True)
    def check(item):
        if all(item.selected for item in menu if not item.meta):
            return ' '
        elif all(not item.selected for item in menu if not item.meta):
            return '*'
        else:
            return '-'
    unselect_all.check = check
    unselect_all.onkey(warawara.KEY_SPACE, menu.unselect_all)

    def enter(item, key):
        item.menu.message = 'enter'
        item.menu.done()
    done = menu.append('Done', meta=True)
    def format_done(menu, cursor, item, check, box):
        if menu.data.grabbing and menu.cursor == item:
            return f'{cursor}{item.text}'
        return f'{cursor} {item.text}'
    done.format = format_done
    done.onkey(warawara.KEY_ENTER, enter)

    def menu_enter(menu, key):
        if menu.cursor.meta:
            return menu.cursor.feedkey(warawara.KEY_SPACE)
        elif menu.cursor.selected:
            menu.done()
        else:
            menu.cursor.select()
    menu.onkey(warawara.KEY_ENTER, menu_enter)

    ret = menu.interact()
    print(ret)


if __name__ == '__main__':
    main()
