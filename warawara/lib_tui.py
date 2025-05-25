import sys

from .lib_itertools import zip_longest, flatten

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


key_table = {}
key_table_reverse = {}

def _init_key_table():
    for k, v in globals().items():
        if not k.startswith('KEY_'):
            continue
        key_table[v.seq] = v

        for alias in v.aliases:
            key_table_reverse[alias] = v

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

    if seq not in key_table:
        key_table[seq] = Key(seq, *aliases)
        return key_table[seq]

    key = key_table[seq]
    for name in aliases:
        key.nameit(name)

    return key


@export
def deregister_key(seq):
    if isinstance(seq, Key):
        seq = seq.seq
    elif isinstance(seq, str):
        seq = seq.encode('utf8')
    return key_table.pop(seq, None)


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
        candidate_matches = set(key_table.keys())
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

        if acc in key_table:
            return key_table[acc]

        try:
            return acc.decode(encoding)
        except UnicodeError:
            return acc

    finally:
        termios.tcsetattr(fd, when, orig_term_attr)


class Pagee:
    def __init__(self, text, offset, visible):
        self.text = str(text)
        self.offset = offset
        self.visible = visible


class PageeGroup:
    def __init__(self):
        self.lines = []

    def __len__(self):
        return len(self.lines)

    def __iter__(self):
        return iter(self.lines)

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
    def __init__(self, lines=None, columns=None, flex=False):
        self.height_limit = lines
        self.width_limit = columns
        self.height = lines
        self.width = columns
        self.flex = flex
        self._scroll = 0

        self.top = PageeGroup()
        self.middle = PageeGroup()
        self.bottom = PageeGroup()

        import builtins
        self.print = builtins.print
        self.display = []

    def __len__(self):
        return len(self.middle)

    def __iter__(self):
        return iter(self.middle)

    def __getitem__(self, idx):
        content_height = max(0, self.height - len(self.top) - len(self.bottom))
        return Pagee(
                text=self.middle[idx],
                offset=len(self.top) - self.scroll,
                visible=(self.scroll) <= idx <= (self.scroll + content_height - 1))

    def __setitem__(self, idx, line):
        if isinstance(idx, slice):
            start = idx.start or 0
        else:
            start = idx

        for i in range(len(self), start + 1):
            self.append()

        self.middle[idx] = line

    @property
    def lines(self):
        return tuple(self.top.lines + self.middle.lines + self.bottom.lines)

    @property
    def empty(self):
        return not self.lines

    def append(self, line=''):
        self.middle.append(line)

    def extend(self, lines=[]):
        for line in lines:
            self.append(line)

    def insert(self, index, line):
        return self.middle.insert(index, line)

    def pop(self, index=-1):
        return self.middle.pop(index)

    def clear(self):
        self.top.clear()
        self.middle.clear()
        self.bottom.clear()

    @property
    def scroll(self):
        return self._scroll

    @scroll.setter
    def scroll(self, value):
        self._scroll = value

        content_height = max(0, self.height - len(self.top) - len(self.bottom))
        from .lib_math import clamp
        self._scroll = clamp(0, self.scroll, max(0, len(self.middle)-content_height))

    def render(self, *, all=None):
        # Get effective canvas size
        import shutil
        term_size = shutil.get_terminal_size()
        canvas_width = self.width_limit or term_size.columns
        canvas_height = self.height_limit or term_size.lines
        canvas_width = min(canvas_width, term_size.columns)
        canvas_height = min(canvas_height, term_size.lines)

        self.width = canvas_width
        self.height = canvas_height

        # Skip out-of-screen lines, i.e. canvas size-- if terminal size--
        self.display = self.display[-self.height:] or [None]

        content_height = max(0, self.height - len(self.top) - len(self.bottom))
        content_lines = self.middle[self.scroll:(self.scroll + content_height)]

        lines = ((list(self.top) + content_lines + list(self.bottom)))[-self.height:] or ['']

        cursor = len(self.display) - 1

        for i in range(cursor, max(len(lines) - 1, 0), -1):
            self.print('\r\033[K\033[A', end='')
            self.display.pop()
            cursor -= 1

        # Assumed that cursor is always at the end of last line
        from .lib_itertools import lookahead
        for (idx, line), is_last in lookahead(enumerate(lines)):
            # Append empty lines, i.e. canvas size++ if terminal size++
            for i in range(len(self.display), idx + 1):
                self.display.append(None)

            # Skip non-dirty lines, but always redraw the last line
            # for keeping cursor at end of the last line
            if not all and not is_last and self.display[idx] == line:
                continue

            # Align cursor position
            if cursor != idx:
                dist = min(abs(cursor - idx), len(self.display) - 1)
                self.print('\r\033[{}{}'.format(dist, 'A' if cursor > idx else 'B'), end='')

            wline = wrap(line, self.width)[0]
            self.display[idx] = wline

            # Print content onto screen
            self.print('\r{}\033[K'.format(wline),
                  end='' if is_last else '\n')

            # Estimate cursor position
            cursor = idx + (not is_last)


@export
class Menu:
    def __init__(self, title, options, *,
                 format=None, arrow='>', type=None, onkey=None, wrap=False):
        self.pager = Pager(lines=4)
        self.title = title
        self.options = options
        self.message = ''

        self.idx = 0

    def render(self):
        self.pager.clear()

        self.pager.top.clear()
        if self.title:
            self.pager.top.append(self.title)

        for idx, opt in enumerate(self.options):
            self.pager[idx] = ('  ' if idx != self.idx else '> ') + opt

        self.pager.bottom.clear()
        self.pager.bottom.append(self.message)

        self.pager.render()

    def interact(self, *, suppress=(EOFError, KeyboardInterrupt, BlockingIOError)):
        # with HijackStdio():
            # with ExceptionSuppressor(suppress):

        self.message = 'scroll=' + str(self.pager.scroll)
        while True:
            self.render()
            ch = getch(capture='fs')

            if ch == 'up':
                self.idx = (self.idx + len(self.options) - 1) % len(self.options)
            elif ch == 'down':
                self.idx = (self.idx + 1) % len(self.options)
            elif ch in ('q', 'ctrl+c', KEY_FS):
                self.message = repr(ch)
                self.render()
                break
            elif ch == 't':
                if self.title == 'new title':
                    self.title = 'new multiline\ntitle'
                elif self.title:
                    self.title = None
                else:
                    self.title = 'new title'
            elif ch == 's':
                self.message = 'scroll=' + str(self.pager.scroll)
            elif ch == 'j':
                self.pager.scroll += 1
                self.message = 'scroll=' + str(self.pager.scroll)
            elif ch == 'k':
                self.pager.scroll -= 1
                self.message = 'scroll=' + str(self.pager.scroll)
            elif ch == 'c':
                self.message = 'cursor={} visible={}'.format(self.idx, self.pager[self.idx].visible)
            else:
                self.message = repr(ch)

        print()
