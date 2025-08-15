import sys

from collections import UserList

from .lib_itertools import zip_longest

from .internal_utils import exporter
export, __all__ = exporter()


@export
def charwidth(c):
    import unicodedata
    return 1 + (unicodedata.east_asian_width(c) in 'WF')


@export
def strwidth(s):
    from .lib_colors import decolor
    return sum(charwidth(c) for c in decolor(s))


@export
def wrap(s, width, clip=None):
    if clip is None:
        pass
    elif not isinstance(clip, str) or (len(clip) != 1) or (charwidth(clip) != 1):
        raise ValueError('clip should be a single width char')

    w = 0
    for idx, char in enumerate(s):
        cw = charwidth(char)
        if w + cw > width:
            if clip and w + 1 <= width:
                return (s[:idx] + clip, s[idx:])
            return (s[:idx], s[idx:])
        w += cw
    return (s, '')


def lpad(text, padding):
    return text + padding


def rpad(text, padding):
    return padding + text


def just_elem(func):
    def wrapper(elem, width, fillchar):
        row, col, text = elem
        padding = (width - strwidth(text)) * fillchar(row=row, col=col, text=text)
        return func(text, padding)
    return wrapper


def just_generator(just_func, data, width, fillchar):
    for row, vector in enumerate(data):
        if isinstance(width, int):
            width = (width,) * len(vector)
        yield tuple(
                just_func((row, col, text), w, fillchar)
                for col, (text, w) in enumerate(zip_longest(vector, width[:len(vector)], fillvalues=('', 0)))
                )


def just(just_func, data, width, fillchar):
    if not callable(fillchar):
        _fillchar = fillchar
        fillchar = lambda row, col, text: _fillchar

    if isinstance(data, str):
        return just_func((0, 0, data), width, fillchar)

    if width:
        if isinstance(data, (tuple, list)):
            t = type(data)
        else:
            t = lambda x: x
        return t(just_generator(just_func, data, width, fillchar))

    maxwidth = []
    for vector in data:
        maxwidth = [
                max(w, strwidth(text))
                for text, w in zip_longest(vector, maxwidth, fillvalues=('', 0))
                ]

    return [
            tuple(
                just_func((row, col, text), w, fillchar)
                for col, (text, w) in enumerate(zip_longest(vector, maxwidth, fillvalues=('', 0)))
                )
            for row, vector in enumerate(data)
            ]


@export
def ljust(data, width=None, fillchar=' '):
    return just(just_elem(lpad), data, width, fillchar)


@export
def rjust(data, width=None, fillchar=' '):
    return just(just_elem(rpad), data, width, fillchar)


@export
class ThreadedSpinner:
    def __init__(self, *icon, delay=0.1):
        if not icon:
            self.icon_entry = '⠉⠛⠿⣿⠿⠛⠉⠙'
            self.icon_loop = '⠹⢸⣰⣤⣆⡇⠏⠛'
            self.icon_leave = '⣿'
        elif len(icon) == 1:
            self.icon_entry = tuple()
            self.icon_loop = icon
            self.icon_leave = '.'
        elif len(icon) == 2:
            self.icon_entry = icon[0]
            self.icon_loop = icon[1]
            self.icon_leave = '.'
        elif len(icon) == 3:
            self.icon_entry = icon[0]
            self.icon_loop = icon[1]
            self.icon_leave = icon[2]
        else:
            raise ValueError('Invalid value: ' + repr(icon))

        ok = True
        for name, icon in (('entry', self.icon_entry), ('loop', self.icon_loop), ('leave', self.icon_leave)):
            if isinstance(icon, str):
                ok = True
            elif isinstance(icon, (tuple, list)) and all(isinstance(c, str) for c in icon):
                ok = True
            else:
                raise ValueError('Invalid value of icon[{}]: {}'.format(name, icon))

        self.delay = delay
        self.is_end = False
        self.thread = None
        self._text = ''

        import itertools
        self.icon_iter = (
                itertools.chain(
                    self.icon_entry,
                    itertools.cycle(self.icon_loop)
                    ),
                iter(self.icon_leave)
                )
        self.icon_head = [None, None]

        import builtins
        self.print = builtins.print

    def __enter__(self):
        if self.thread:
            return self

        self.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.end()

    @property
    def icon(self):
        idx = self.is_end
        if self.icon_head[idx] is None:
            self.icon_head[idx] = next(self.icon_iter[idx])
        return self.icon_head[idx]

    def text(self, *args):
        if not args:
            return self._text

        self._text = ' '.join(str(a) for a in args)
        if self.thread:
            self.refresh()

    def refresh(self):
        self.print('\r' + self.icon + '\033[K ' + self._text, end='')

    def animate(self):
        import time

        while not self.is_end:
            self.refresh()
            time.sleep(self.delay)
            self.icon_head[0] = next(self.icon_iter[0])

        try:
            while True:
                self.refresh()
                self.icon_head[1] = next(self.icon_iter[1])
                time.sleep(self.delay)
        except StopIteration:
            pass

        self.print()

    def start(self):
        if self.thread:
            return

        import threading
        self.thread = threading.Thread(target=self.animate)
        self.thread.daemon = True
        self.thread.start()

    def end(self, wait=True):
        self.is_end = True
        if wait:
            self.join()

    def join(self):
        self.thread.join()


def alt_if_none(A, B):
    if A is None:
        return B
    return A


class UserSelection:
    def __init__(self, options, accept_empty=None, abbr=None, sep=None, ignorecase=None):
        if not options:
            accept_empty = True
            abbr = False
            ignorecase = False

        self.accept_empty = alt_if_none(accept_empty, True)
        self.abbr = alt_if_none(abbr, True)
        self.ignorecase = alt_if_none(ignorecase, self.abbr)
        self.sep = alt_if_none(sep, ' / ')

        self.mapping = dict()
        self.options = [o for o in options]

        if self.options:
            if self.accept_empty:
                self.mapping[''] = self.options[0]

            for opt in self.options:
                for o in (opt,) + ((opt[0],) if self.abbr else tuple()):
                    self.mapping[o.lower() if self.ignorecase else o] = opt

        self.selected = None

    def select(self, o=''):
        if self.ignorecase:
            o = o.lower()

        if not self.options:
            self.selected = o
            return

        if o not in self.mapping:
            raise ValueError('Invalid option: ' + o)

        self.selected = o

    @property
    def prompt(self):
        if not self.options:
            return ''

        opts = [o for o in self.options]
        if self.accept_empty and self.ignorecase:
            opts[0] = opts[0].capitalize()

        if self.abbr:
            return ' [' + self.sep.join('({}){}'.format(o[0], o[1:]) for o in opts) + ']'
        else:
            return ' [' + self.sep.join(opts) + ']'

    def __eq__(self, other):
        if self.ignorecase and other is not None:
            other = other.lower()

        if self.selected == other:
            return True

        if self.selected in self.mapping:
            return self.mapping[self.selected] == self.mapping.get(other)

        return False

    def __str__(self):
        return str(self.selected)

    def __repr__(self):
        return '<warawara.tui.UserSelection selected=[{}]>'.format(self.selected)


class HijackStdio:
    def __init__(self, replace_with='/dev/tty'):
        self.replace_with = replace_with

    def __enter__(self):
        self.stdin_backup = sys.stdin
        self.stdout_backup = sys.stdout
        self.stderr_backup = sys.stderr

        sys.stdin = open(self.replace_with)
        sys.stdout = open(self.replace_with, 'w')
        sys.stderr = open(self.replace_with, 'w')

    def __exit__(self, exc_type, exc_value, traceback):
        sys.stdin.close()
        sys.stdout.close()
        sys.stderr.close()

        sys.stdin = self.stdin_backup
        sys.stdout = self.stdout_backup
        sys.stderr = self.stderr_backup


class ExceptionSuppressor:
    def __init__(self, *exc_group):
        if isinstance(exc_group[0], tuple):
            self.exc_group = exc_group[0]
        else:
            self.exc_group = exc_group

    def __enter__(self, *exc_group):
        pass

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type in (EOFError, KeyboardInterrupt):
            print()
        return exc_type in self.exc_group


@export
def prompt(question, options=tuple(),
           accept_empty=True,
           abbr=True,
           ignorecase=None,
           sep=' / ',
           suppress=(EOFError, KeyboardInterrupt)):

    if isinstance(options, str) and ' ' in options:
        options = options.split()

    user_selection = UserSelection(options, accept_empty=accept_empty, abbr=abbr, sep=sep, ignorecase=ignorecase)

    with HijackStdio():
        with ExceptionSuppressor(suppress):
            while user_selection.selected is None:
                print((question + (user_selection.prompt)), end=' ')

                import contextlib
                with contextlib.suppress(ValueError):
                    i = input().strip()
                    user_selection.select(i)

    return user_selection


class Key:
    def __init__(self, seq, *aliases):
        if isinstance(seq, str):
            seq = seq.encode('utf8')

        if not isinstance(seq, bytes):
            raise TypeError('seq should be in type bytes, not {}'.format(type(seq)))

        if not all(isinstance(a, str) for a in aliases):
            raise TypeError('Aliases should be in type str')

        self.seq = seq
        self.aliases = []
        for name in aliases:
            self.nameit(str(name))

    def __hash__(self):
        return hash(self.seq)

    def __repr__(self):
        fmt = type(self).__name__ + '({})'
        if self.aliases:
            return fmt.format(self.aliases[0])
        try:
            return fmt.format(repr(self.seq.decode('utf8')))
        except UnicodeError:
            return fmt.format(repr(self.seq))

    def nameit(self, name):
        if name not in self.aliases:
            self.aliases.append(name)

    def __eq__(self, other):
        if type(self) == type(other):
            return self.seq == other.seq
        elif isinstance(other, bytes) and self.seq == other:
            return True
        elif isinstance(other, str) and self.seq == other.encode('utf8'):
            return True
        else:
            return other in self.aliases


KEY_ESCAPE = Key(b'\033', 'esc', 'escape')
KEY_BACKSPACE = Key(b'\x7f', 'backspace')
KEY_TAB = Key(b'\t', 'tab', 'ctrl-i', 'ctrl+i', '^I')
KEY_ENTER = Key(b'\r', 'enter', 'ctrl-m', 'ctrl+m', '^M')
KEY_SPACE = Key(b' ', 'space')

KEY_FS = Key(b'\x1c', 'fs', 'ctrl-\\', 'ctrl+\\', '^\\')

KEY_UP = Key(b'\033[A', 'up')
KEY_DOWN = Key(b'\033[B', 'down')
KEY_RIGHT = Key(b'\033[C', 'right')
KEY_LEFT = Key(b'\033[D', 'left')

KEY_HOME = Key(b'\033[1~', 'home')
KEY_END = Key(b'\033[4~', 'end')
KEY_PGUP = Key(b'\033[5~', 'pgup', 'pageup')
KEY_PGDN = Key(b'\033[6~', 'pgdn', 'pagedown')

KEY_F1 = Key(b'\033OP', 'F1')
KEY_F2 = Key(b'\033OQ', 'F2')
KEY_F3 = Key(b'\033OR', 'F3')
KEY_F4 = Key(b'\033OS', 'F4')
KEY_F5 = Key(b'\033[15~', 'F5')
KEY_F6 = Key(b'\033[17~', 'F6')
KEY_F7 = Key(b'\033[18~', 'F7')
KEY_F8 = Key(b'\033[19~', 'F8')
KEY_F9 = Key(b'\033[20~', 'F9')
KEY_F10 = Key(b'\033[21~', 'F10')
KEY_F11 = Key(b'\033[23~', 'F11')
KEY_F12 = Key(b'\033[24~', 'F12')

def _register_ctrl_n_keys():
    for c in 'abcdefghjklnopqrstuvwxyz':
        C = c.upper()
        idx = ord(c) - ord('a') + 1
        aliases = ('ctrl-' + c, 'ctrl+' + c, '^' + C)
        globals()['KEY_CTRL_' + C] = Key(chr(idx), *aliases)

_register_ctrl_n_keys()
del _register_ctrl_n_keys


def _export_all_keys():
    for key in globals().keys():
        if key.startswith('KEY_'):
            export(key)

_export_all_keys()
del _export_all_keys


key_seq_table = {}
key_alias_table = {}

def _init_key_table():
    for k, v in globals().items():
        if not k.startswith('KEY_'):
            continue
        key_seq_table[v.seq] = v

        for alias in v.aliases:
            key_alias_table[alias] = v

_init_key_table()
del _init_key_table


@export
def register_key(seq, *aliases):
    if isinstance(seq, Key):
        new_key = seq
        seq = new_key.seq
        aliases = new_key.aliases + list(aliases)

    elif isinstance(seq, str):
        seq = seq.encode('utf8')

    if not seq:
        raise ValueError('huh?')

    if seq not in key_seq_table:
        key_seq_table[seq] = Key(seq, *aliases)
        return key_seq_table[seq]

    key = key_seq_table[seq]
    for name in aliases:
        key.nameit(name)

    return key


@export
def deregister_key(seq):
    if isinstance(seq, Key):
        seq = seq.seq
    elif isinstance(seq, str):
        seq = seq.encode('utf8')

    key = key_seq_table.pop(seq, None)
    for alias in key.aliases:
        key_alias_table.pop(alias, None)
    return key


@export
def getch(*, timeout=None, encoding='utf8', capture=('ctrl+c', 'ctrl+z', 'fs')):
    import termios, tty
    import os
    import select
    import signal

    fd = sys.stdin.fileno()
    orig_term_attr = termios.tcgetattr(fd)
    when = termios.TCSADRAIN

    term_attr_cc = termios.tcgetattr(fd)[6]

    capture_table = [
            [KEY_CTRL_C, term_attr_cc[termios.VINTR], signal.SIGINT],
            [KEY_CTRL_Z, term_attr_cc[termios.VSUSP], signal.SIGTSTP],
            [KEY_FS,     term_attr_cc[termios.VQUIT], signal.SIGQUIT],
            ]

    if isinstance(capture, str):
        capture = [capture]

    for cap in capture or []:
        for entry in capture_table:
            if entry[0] == cap:
                entry[2] = None

    def has_data(t=0):
        return select.select([fd], [], [], t)[0]

    def read_one_byte():
        return os.read(sys.stdin.fileno(), 1)

    try:
        tty.setraw(fd, when=when)

        # Wait for input until timeout
        if not has_data(timeout):
            return None

        acc = b''
        candidate_matches = set(key_seq_table.keys())
        while True:
            acc += read_one_byte()

            # Check special sequences that correspond to signals
            for entry in capture_table:
                key, seq, sig = entry
                if acc[-len(seq):] == seq:
                    if sig is not None:
                        os.kill(os.getpid(), sig)
                    else:
                        break

            if not has_data():
                break

            # Still have chance to match in key table
            if candidate_matches:
                # eliminate potential matches
                candidate_matches = set(key_seq for key_seq in candidate_matches if key_seq.startswith(acc))

                # Perfect match, return
                if candidate_matches == {acc}:
                    break

                # multiple prefix matchs: collect more byte
                if candidate_matches:
                    continue

            # Input sequence does not match anything in key table
            # Collect enough bytes to decode at least one unicode char
            try:
                acc.decode(encoding)
                break
            except UnicodeError:
                continue

        if acc in key_seq_table:
            return key_seq_table[acc]

        try:
            return acc.decode(encoding)
        except UnicodeError:
            return acc

    finally:
        termios.tcsetattr(fd, when, orig_term_attr)


class Pagee:
    def __init__(self, text, section, offset, visible):
        self.text = str(text)
        self.section = section
        self.offset = offset
        self.visible = visible


class Subpager:
    def __init__(self, parent, section):
        self.lines = []
        self.parent = parent
        self.section = section

    def __len__(self):
        return len(self.lines)

    def __iter__(self):
        for pagee in self.parent.data:
            if pagee.section == self.section:
                yield pagee

    def __getitem__(self, idx):
        return self.lines[idx]

    def __setitem__(self, idx, line):
        self.lines[idx] = line

    @property
    def empty(self):
        return not self.lines

    def append(self, line=''):
        self.lines.append(line)

    def extend(self, lines=[]):
        for line in lines:
            self.append(line)

    def insert(self, index, line):
        return self.lines.insert(index, line)

    def pop(self, index=-1):
        return self.lines.pop(index)

    def clear(self):
        self.lines.clear()


@export
class Pager:
    def __init__(self, max_height=None, max_width=None, flex=False):
        self._max_height = max_height
        self._max_width = max_width
        self.flex = flex
        self._scroll = 0

        self.header = Subpager(parent=self, section='header')
        self.body = Subpager(parent=self, section='body')
        self.footer = Subpager(parent=self, section='footer')

        import builtins
        self.print = builtins.print
        self._display = []

    @property
    def term_size(self):
        import shutil
        return shutil.get_terminal_size()

    @property
    def term_height(self):
        return self.term_size.lines

    @property
    def term_width(self):
        return self.term_size.columns

    @property
    def max_height(self):
        return self._max_height

    @max_height.setter
    def max_height(self, value):
        self._max_height = max(value or 0, 0)

    @property
    def max_width(self):
        return self._max_width

    @max_width.setter
    def max_width(self, value):
        self._max_width = max(value, 0)

    @property
    def height(self):
        if self.flex and self.max_height:
            content_total_height = self.max_height
        else:
            content_total_height = len(self.header) + len(self.body) + len(self.footer)

        return min(
                self.max_height or self.term_height,
                self.term_height,
                content_total_height,
                )

    @property
    def width(self):
        return min(self.max_width or self.term_width, self.term_width)

    def __len__(self):
        return len(self.body)

    def __iter__(self):
        return iter(self.body)

    def __getitem__(self, idx):
        content_height = max(0, self.height - len(self.header) - len(self.footer))
        return Pagee(
                text=self.body[idx],
                section='body',
                offset=len(self.header) - self.scroll,
                visible=(self.scroll) <= idx <= (self.scroll + content_height - 1)
                )

    def __setitem__(self, idx, line):
        if isinstance(idx, slice):
            start = idx.start or 0
        else:
            start = idx

        for i in range(len(self), start + 1):
            self.append()

        self.body[idx] = line

    @property
    def data(self):
        from .lib_collections import namablelist
        alloc = namablelist(header=0, body=0, padding=0, footer=0)

        for i in range(self.height):
            if not self.header.empty and alloc.header == 0:
                section = 'header'
            elif not self.footer.empty and alloc.footer == 0:
                section = 'footer'
            elif alloc.header < len(self.header):
                section = 'header'
            elif alloc.footer < len(self.footer):
                section = 'footer'
            elif alloc.body < len(self.body):
                section = 'body'
            else:
                section = 'padding'

            alloc[section] += 1

        at_line = 0
        for section, lines, base in [
                ('header',  self.header.lines,    0),
                ('body',    self.body.lines,      len(self.header) - self.scroll),
                ('padding', [''] * alloc.padding, alloc.header + alloc.body),
                ('footer',  self.footer.lines,    alloc.header + alloc.body + alloc.padding),
                ]:
            for idx, line in enumerate(lines):
                pagee = Pagee(text=line,
                            section=section,
                            offset=idx + base,
                            visible=idx + base >= at_line and getattr(alloc, section) > 0,)
                yield pagee
                if pagee.visible:
                    alloc[section] -= 1
                    at_line += 1

    @property
    def lines(self):
        return tuple(item.text for item in self.data)

    @property
    def preview(self):
        return tuple(item.text for item in self.data if item.visible)

    @property
    def display(self):
        return tuple(self._display)

    @property
    def empty(self):
        for line in self.lines:
            return False
        return True

    def append(self, line=''):
        self.body.append(line)

    def extend(self, lines=[]):
        for line in lines:
            self.append(line)

    def insert(self, index, line):
        return self.body.insert(index, line)

    def pop(self, index=-1):
        return self.body.pop(index)

    def clear(self):
        self.header.clear()
        self.body.clear()
        self.footer.clear()

    @property
    def home(self):
        return 0

    @property
    def end(self):
        return len(self.body) - 1

    @property
    def scroll(self):
        self.scroll = self._scroll
        return self._scroll

    @scroll.setter
    def scroll(self, value):
        self._scroll = value

        content_height = max(0, self.height - len(self.header) - len(self.footer))
        from .lib_math import clamp
        self._scroll = clamp(0, self._scroll, max(0, len(self.body)-content_height))

    def render(self, *, all=None):
        # Skip out-of-screen lines, i.e. canvas size-- if terminal size--
        self._display = self._display[-self.term_height:] or [None]

        visible_lines = list(self.preview)

        cursor = len(self._display) - 1

        for i in range(cursor, max(len(visible_lines) - 1, 0), -1):
            self.print('\r\033[K\033[A', end='')
            self._display.pop()
            cursor -= 1

        if not visible_lines:
            self.print('\r\033[K', end='')
            self._display.pop()
            return

        # Assumed that cursor is always at the end of last line
        from .lib_itertools import lookahead
        for (idx, line), is_last in lookahead(enumerate(visible_lines)):
            # Append empty lines, i.e. canvas size++ if terminal size++
            for i in range(len(self._display), idx + 1):
                self._display.append(None)

            # Skip non-dirty lines, but always redraw the last line
            # for keeping cursor at end of the last line
            if not all and not is_last and self._display[idx] == line:
                continue

            # Align cursor position
            if cursor != idx:
                dist = min(abs(cursor - idx), len(self._display) - 1)
                self.print('\r\033[{}{}'.format(dist, 'A' if cursor > idx else 'B'), end='')

            wline = wrap(line, self.width)[0]
            self._display[idx] = wline

            # Print content onto screen
            self.print('\r{}\033[K'.format(wline),
                  end='' if is_last else '\n')

            # Estimate cursor position
            cursor = idx + (not is_last)


class MenuData:
    def __init__(self):
        super().__setattr__('dataset', {})

    def __repr__(self):
        return f'MenuData({repr(self.dataset)})'

    def __setitem__(self, key, value):
        self.dataset[key] = value
        if value is None:
            del self.dataset[key]

    def __getitem__(self, key):
        return self.dataset.get(key)

    def __delitem__(self, key):
        if key in self.dataset:
            del self.dataset[key]

    def __getattr__(self, attr):
        return self[attr]

    def __setattr__(self, attr, value):
        self[attr] = value

    def __delattr__(self, attr):
        del self[attr]


class MenuThread:
    def __init__(self, menu, target=None, name=None, args=(), kwargs={}):
        self.menu = menu
        self.target = target
        self.name = name
        self.args = args
        self.kwargs = kwargs
        self.thread = None

    def start(self):
        import threading
        self.thread = threading.Thread(
                target=self.target, name=self.name,
                args=self.args, kwargs=self.kwargs,
                daemon=True)

        # register self to self.menu
        self.menu.notify_start(self.thread)

        self.thread.start()
        return self

    def is_alive(self):
        return self.thread and self.thread.is_alive()

    def join(self):
        self.thread.join()


@export
class Menu:
    class DoneSelection(Exception):
        pass

    class GiveUpSelection(Exception):
        pass

    class StdoutIsNotAtty(Exception):
        def __init__(self):
            super().__init__('Stdout should be a tty for using interactive menu')

    @staticmethod
    def parse_checkbox(checkbox):
        if not checkbox:
            check = None
            box = None
        elif checkbox in ('()', 'single', 'radio'):
            check = '*'
            box = checkbox
        elif checkbox.startswith('(') and checkbox.endswith(')'):
            check = checkbox[1:-1]
            box = '()'
        elif checkbox in ('[]', 'multi', 'multiple', 'checkbox'):
            check = '*'
            box = checkbox
        elif checkbox.startswith('[') and checkbox.endswith(']'):
            check = checkbox[1:-1]
            box = '[]'
        else:
            check = None
            box = None

        return check, box

    def __init__(self, title, options, *,
                 max_height=None, wrap=False,
                 format=None, cursor='>', checkbox=None,
                 onkey=None):
        self.pager = Pager(max_height=max_height)

        self.title = title
        self.options = [MenuItem(self, False, opt, None, None) for opt in options]
        self.message = ''
        self.data = MenuData()

        self.check, self.box = self.parse_checkbox(checkbox)

        if format:
            self.format = format
        elif self.box:
            self.format = '{cursor} {box[0]}{check}{box[1]} {item.text}'
        else:
            self.format = '{cursor} {item.text}'

        self._onkey = MenuKeyHandler(self)
        if onkey:
            self._onkey += onkey

        self.cursor_symbol = cursor
        self._cursor = MenuCursor(self, wrap=wrap)

        self._active = False

        import threading

        from .lib_threading import Throttler
        self._refresh_throttler = Throttler(self.do_render, 1/60)

        self._threads = []

    def __iter__(self):
        return iter(self.options)

    def __len__(self):
        return len(self.options)

    def __getitem__(self, idx):
        if isinstance(idx, (MenuItem, MenuCursor)):
            if idx.menu is self:
                idx = idx.index
        return self.options[idx]

    def Thread(self, target=None, name=None, args=(), kwargs={}):
        return MenuThread(menu=self, target=target, name=name, args=args, kwargs=kwargs)

    def notify_start(self, thread):
        self._threads.append(thread)

    @property
    def active(self):
        return self._active

    @property
    def wrap(self):
        return self.cursor.wrap

    @wrap.setter
    def wrap(self, value):
        self.cursor.wrap = value

    @property
    def max_height(self):
        return self.pager.max_height

    @max_height.setter
    def max_height(self, value):
        self.pager.max_height = value

    @property
    def cursor(self):
        return self._cursor

    @cursor.setter
    def cursor(self, value):
        self._cursor.to(value)

    @property
    def onkey(self):
        return self._onkey

    @onkey.setter
    def onkey(self, value):
        self._onkey.clear()
        self._onkey += value

    @property
    def first(self):
        return self.options[0]

    @property
    def last(self):
        return self.options[-1]

    @property
    def top(self):
        for idx, pagee in enumerate(self.pager):
            if pagee.visible:
                return self.options[idx]

    @property
    def bottom(self):
        ret = None
        for idx, pagee in enumerate(self.pager):
            if pagee.visible:
                ret = self.options[idx]
            elif ret is not None:
                break
        return ret

    @property
    def selected(self):
        selected_items = [item for item in self if item.selected and not item.meta]
        if self.box == '[]':
            return selected_items
        elif self.box == '()' or not self.box:
            if selected_items:
                return selected_items[0]

    def index(self, item):
        for index, i in enumerate(self.options):
            if item is i:
                return index
        return -1

    def insert(self, index, text='', cursor=None, checkbox=None, meta=False, onkey=None):
        ret = MenuItem(self, meta, text, cursor, checkbox)
        self.options.insert(index, ret)
        if onkey:
            ret.onkey(onkey)
        return ret

    def append(self, text='', cursor=None, checkbox=None, meta=False, onkey=None):
        ret = MenuItem(self, meta, text, cursor, checkbox)
        self.options.append(ret)
        if onkey:
            ret.onkey(onkey)
        return ret

    def extend(self, options, cursor=None, checkbox=None, meta=False, onkey=None):
        ret = [MenuItem(self, meta, text, cursor, checkbox) for text in options]
        self.options.extend(ret)
        if onkey:
            for i in ret:
                i.onkey(onkey)
        return ret

    def swap(self, a, b):
        if isinstance(a, (MenuItem, MenuCursor)):
            a = a.index
        if isinstance(b, (MenuItem, MenuCursor)):
            b = b.index
        self.options[a], self.options[b] = self.options[b], self.options[a]

    def moveto(self, item, to):
        if not isinstance(item, MenuItem):
            raise TypeError('item should be a MenuItem')

        if isinstance(item, (MenuItem, MenuCursor)):
            item = item.index
        if isinstance(to, (MenuItem, MenuCursor)):
            to = to.index

        if item < to: # move down
            self.options = (
                    self.options[:item] +
                    self.options[item+1:to] +
                    [self.options[to]] +
                    [self.options[item]] +
                    self.options[to+1:]
                    )
            return

        if item > to: # move up
            self.options = (
                    self.options[:to] +
                    [self.options[item]] +
                    [self.options[to]] +
                    self.options[to+1:item] +
                    self.options[item+1:]
                    )
            return

    def bind(self, *args, **kwargs):
        return self._onkey.bind(*args, **kwargs)

    def unbind(self, *args, **kwargs):
        return self._onkey.unbind(*args, **kwargs)

    def done(self, **kwargs):
        if not self.box:
            self.cursor.select()
        raise Menu.DoneSelection()

    def quit(self, **kwargs):
        raise Menu.GiveUpSelection()

    def select(self, item):
        if self.box == '()':
            self.unselect_all()
        item.selected = True

    def select_all(self):
        if self.box == '[]':
            for item in self.options:
                item.selected = True

    def unselect(self, item):
        item.selected = False

    def unselect_all(self):
        for item in self.options:
            item.selected = False

    def toggle(self, item):
        if item.selected:
            item.unselect()
        else:
            item.select()

    def feedkey(self, key):
        ret = self[self.cursor].onkey.handle(key)
        if ret:
            return ret
        return self.onkey.handle(key)

    def scroll_to_contain(self, index):
        if isinstance(index, (MenuItem, MenuCursor)):
            index = index.index
        else:
            index = index

        try:
            if self.pager[int(self.cursor)].visible:
                return

            if self.cursor < self.pager.scroll:
                self.pager.scroll = int(self.cursor)
                return

            for i in range(int(self.cursor), 0, -1):
                if self.pager[i].visible:
                    self.pager.scroll += int(self.cursor) - i
                    break
        except IndexError:
            return

    def pull_cursor(self):
        if self.pager[int(self.cursor)].visible:
            return

        if self.cursor < self.pager.scroll:
            self.cursor = self.pager.scroll
            return

        for i in range(int(self.cursor), 0, -1):
            if self.pager[i].visible:
                self.cursor = i
                break

    def scroll(self, count=1):
        self.pager.scroll += count
        self.pull_cursor()

    def do_render(self, force=False):
        if not self.active and not force:
            return

        self.pager.clear()

        # import time
        # time.sleep(0.1)

        if self.title:
            self.pager.header.extend(self.title.split('\n'))

        def pad(s):
            if not s:
                return ''
            return strwidth(str(s)) * ' '

        for idx, item in enumerate(self.options):
            cursor = self.cursor
            check = item.check or self.check
            box = item.box or self.box
            fmt = item.format or self.format

            check = '' if check is None else check
            check = check(item) if callable(check) else check
            fmt = fmt if callable(fmt) else fmt.format
            self.pager[idx] = fmt(
                    menu=self,
                    cursor=cursor if self.cursor == idx else pad(cursor),
                    item=item,
                    check=check if item.selected or item.meta else pad(check),
                    box=box or ('', ''),
                    )

        self.pager.footer.append(self.message)

        self.pager.render()

    def refresh(self, force=False):
        self._refresh_throttler(blocking=force, args=[], kwargs={'force': force})

    def interact_loop(self):
        try:
            self._active = True
            while True:
                self.refresh(force=True)
                ch = getch(capture='fs')
                try:
                    with self._refresh_throttler.main_lock:
                        self.feedkey(ch)
                except Menu.GiveUpSelection:
                    return None
                except Menu.DoneSelection:
                    return self.selected
        finally:
            # self.join()
            self._active = False
            self.refresh(force=True)
            print()

    def interact(self, *, suppress=(EOFError, KeyboardInterrupt, BlockingIOError)):
        if not sys.stdout.isatty():
            raise Menu.StdoutIsNotAtty()

        with HijackStdio():
            with ExceptionSuppressor(suppress):
                return self.interact_loop()

    def join(self):
        while self._threads:
            self._threads[0].join()
            self._threads.pop(0)


class MenuItemRef:
    def __cmp__(self, other):
        a = self.index
        if isinstance(other, MenuItem) and other.menu is self.menu:
            b = other.index
        else:
            b = other
        return (a > b) - (a < b)

    def __lt__(self, other):
        return self.__cmp__(other) < 0

    def __le__(self, other):
        return self.__cmp__(other) <= 0

    def __eq__(self, other):
        return self.__cmp__(other) == 0

    def __ne__(self, other):
        return self.__cmp__(other) != 0

    def __gt__(self, other):
        return self.__cmp__(other) > 0

    def __ge__(self, other):
        return self.__cmp__(other) >= 0


class MenuItem(MenuItemRef):
    def __init__(self, menu, meta, text, cursor, checkbox):
        self.menu = menu
        self.meta = meta
        self.text = str(text)
        self.selected = False
        self.data = MenuData()
        self.format = None

        self.cursor_symbol = cursor
        self.check, self.box = Menu.parse_checkbox(checkbox)
        if self.meta:
            if not self.check:
                self.check = '*'
            if not self.box:
                self.box = '{}'

        self._onkey = MenuKeyHandler(self)

    def __repr__(self):
        return f'MenuItem(index={self.index}, text={self.text})'

    @property
    def onkey(self):
        return self._onkey

    @onkey.setter
    def onkey(self, value):
        self._onkey.clear()
        self._onkey += value

    @property
    def index(self):
        return self.menu.index(self)

    def bind(self, *args, **kwargs):
        return self._onkey.bind(*args, **kwargs)

    def unbind(self, *args, **kwargs):
        return self._onkey.unbind(*args, **kwargs)

    def select(self):
        self.menu.select(self)

    def unselect(self):
        self.menu.unselect(self)

    def toggle(self):
        self.menu.toggle(self)

    def moveto(self, where):
        self.menu.moveto(self, where)

    def feedkey(self, key):
        return self.onkey.handle(key)


class MenuCursor(MenuItemRef):
    def __init__(self, menu, *, wrap=False):
        self.menu = menu
        self.wrap = wrap
        self.index = 0

    def __repr__(self):
        return f'MenuCursor(index={self.index}, wrap={self.wrap})'

    def __str__(self):
        return self.menu[self].cursor_symbol or self.menu.cursor_symbol

    def __int__(self):
        return self.index

    def __add__(self, other):
        return self.cal_index(self.index + other)

    def __radd__(self, other):
        return self + other

    def __iadd__(self, other):
        self.to(self + other)
        return self

    def __sub__(self, other):
        return self.cal_index(self.index - other)

    def __rsub__(self, other):
        return other - self.index

    def __isub__(self, other):
        self.to(self - other)
        return self

    def __getattr__(self, attr):
        item = self.menu[self.index]
        if not attr.startswith('_') and hasattr(item, attr):
            return getattr(item, attr)
        raise AttributeError(attr)

    @property
    def text(self):
        return self.menu[self.index].text

    def cal_index(self, value):
        if isinstance(value, MenuItem):
            if value.menu is not self.menu:
                raise ValueError('MenuItem is in different Menu')
            return value.index

        value = int(value)
        N = len(self.menu)
        if self.wrap:
            return ((value % N) + N) % N
        else:
            from .lib_math import clamp
            return clamp(0, value, N - 1)

    def to(self, value):
        self.index = self.cal_index(value)
        self.menu.scroll_to_contain(self)

    def up(self, count=1):
        self -= count

    def down(self, count=1):
        self += count


class MenuKeyHandler:
    class MenuKeySubHandlerList(UserList):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

        def __add__(self, other):
            if isinstance(other, (list, tuple, UserList)):
                handler_list = other
            else:
                handler_list = [other]

            data = list(self.data)
            for handler in handler_list:
                if handler not in self.data:
                    data.append(handler)
            return type(self)(data)

        def __iadd__(self, other):
            self.data = (self + other).data
            return self

        def __sub__(self, other):
            if isinstance(other, (list, tuple, UserList)):
                handler_list = other
            else:
                handler_list = [other]

            data = list(self.data)
            for handler in handler_list:
                try:
                    data.remove(handler)
                except:
                    pass
            return type(self)(data)

        def __isub__(self, other):
            self.data = (self - other).data
            return self

    def __init__(self, parent):
        self.parent = parent
        self.clear()
        self.MenuKeySubHandlerList = self.__class__.MenuKeySubHandlerList

    def clear(self):
        self.handlers = {None: self.MenuKeySubHandlerList()}

    def __iadd__(self, other):
        if isinstance(other, (list, tuple, UserList)):
            return self.bind(*other)
        else:
            return self.bind(other)

    def __isub__(self, other):
        if isinstance(other, (list, tuple, UserList)):
            return self.unbind(*other)
        else:
            return self.unbind(other)

    def __getitem__(self, key):
        key = key_alias_table.get(key, key)
        return self.handlers.get(key, self.MenuKeySubHandlerList())

    def __setitem__(self, key, value):
        key = key_alias_table.get(key, key)
        try:
            if not value:
                del self.handlers[key]
            else:
                self.handlers[key] = self.MenuKeySubHandlerList() + value
        except KeyError:
            pass

    def __call__(self, *args):
        return self.bind(*args)

    def bind(self, *args):
        key_list = [arg for arg in args if not callable(arg)] or [None]
        handler_list = [arg for arg in args if callable(arg)]

        if not handler_list:
            raise ValueError('No handlers to bind')

        for key in key_list:
            key = key_alias_table.get(key, key)

            for handler in handler_list:
                if key not in self.handlers:
                    self.handlers[key] = self.MenuKeySubHandlerList()

                self.handlers[key] += handler

        return self

    def unbind(self, *args):
        key_list = [arg for arg in args if not callable(arg)] or self.handlers.keys()
        handler_list = [arg for arg in args if callable(arg)]

        for key in key_list:
            key = key_alias_table.get(key, key)

            if not handler_list:
                self.handlers.pop(key)

            if key not in self.handlers:
                continue

            for handler in handler_list:
                self.handlers[key] -= handler

        return self

    def handle(self, key):
        key = key_alias_table.get(key, key)
        for handler in self.handlers.get(key, []) + self.handlers[None]:
            try:
                param = {}
                if isinstance(self.parent, Menu):
                    param['menu'] = self.parent
                elif isinstance(self.parent, MenuItem):
                    param['item'] = self.parent
                ret = handler(key=key, **param)
            except TypeError:
                ret = handler()

            if ret:
                return ret
