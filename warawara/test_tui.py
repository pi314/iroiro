import queue

import functools
import threading
import unittest.mock

from .lib_test_utils import *

from warawara import *


class TestTypesettingUtils(TestCase):
    def test_charwidth(self):
        self.eq(charwidth('t'), 1)
        self.eq(charwidth('哇'), 2)
        self.eq(charwidth('嗚'), 2)
        self.eq(charwidth('😂'), 2)

        with self.raises(TypeError):
            charwidth('test')

    def test_strwidth(self):
        self.eq(strwidth('test'), 4)
        self.eq(strwidth(orange('test')), 4)
        self.eq(strwidth('哇嗚'), 4)

    def test_wrap(self):
        self.eq(wrap('嗚啦呀哈', 1), ('', '嗚啦呀哈'))
        self.eq(wrap('嗚啦呀哈', 2), ('嗚', '啦呀哈'))
        self.eq(wrap('嗚啦呀哈', 3), ('嗚', '啦呀哈'))
        self.eq(wrap('嗚啦呀哈', 4), ('嗚啦', '呀哈'))
        self.eq(wrap('嗚啦呀哈', 5), ('嗚啦', '呀哈'))
        self.eq(wrap('嗚啦呀哈', 6), ('嗚啦呀', '哈'))
        self.eq(wrap('嗚啦呀哈', 7), ('嗚啦呀', '哈'))
        self.eq(wrap('嗚啦呀哈', 8), ('嗚啦呀哈', ''))
        self.eq(wrap('嗚啦呀哈', 9), ('嗚啦呀哈', ''))

        self.eq(wrap('嗚啦呀哈', 1, clip='>'), ('>', '嗚啦呀哈'))
        self.eq(wrap('嗚啦呀哈', 2, clip='>'), ('嗚', '啦呀哈'))
        self.eq(wrap('嗚啦呀哈', 3, clip='>'), ('嗚>', '啦呀哈'))
        self.eq(wrap('嗚啦呀哈', 4, clip='>'), ('嗚啦', '呀哈'))
        self.eq(wrap('嗚啦呀哈', 5, clip='>'), ('嗚啦>', '呀哈'))
        self.eq(wrap('嗚啦呀哈', 6, clip='>'), ('嗚啦呀', '哈'))
        self.eq(wrap('嗚啦呀哈', 7, clip='>'), ('嗚啦呀>', '哈'))
        self.eq(wrap('嗚啦呀哈', 8, clip='>'), ('嗚啦呀哈', ''))
        self.eq(wrap('嗚啦呀哈', 9, clip='>'), ('嗚啦呀哈', ''))

        with self.raises(ValueError):
            wrap('whatever', 1, clip=1)

        with self.raises(ValueError):
            wrap('whatever', 1, clip='wa')

        with self.raises(ValueError):
            wrap('whatever', 1, clip='蛤')

    def test_ljust_str(self):
        self.eq(ljust('test', 10), 'test      ')
        self.eq(rjust('test', 10), '      test')

        padding = ' ' * 6
        self.eq(ljust(orange('test'), 10), orange('test') + padding)
        self.eq(rjust(orange('test'), 10), padding + orange('test'))

        padding = '#' * 6
        self.eq(ljust(orange('test'), 10, '#'), orange('test') + padding)
        self.eq(rjust(orange('test'), 10, '#'), padding + orange('test'))

    def test_just_rect(self):
        data = [
                ('column1', 'col2'),
                ('word1', 'word2'),
                ('word3', 'word4 long words'),
                ]

        self.eq(ljust(data), [
            ('column1', 'col2            '),
            ('word1  ', 'word2           '),
            ('word3  ', 'word4 long words'),
            ])

        self.eq(rjust(data), [
            ('column1', '            col2'),
            ('  word1', '           word2'),
            ('  word3', 'word4 long words'),
            ])

    def test_just_with_fillchar(self):
        data = [
                ('column1', 'col2'),
                ('word1', 'word2'),
                ('word3', 'word4 long words'),
                ]

        self.eq(ljust(data, fillchar='#'), [
            ('column1', 'col2############'),
            ('word1##', 'word2###########'),
            ('word3##', 'word4 long words'),
            ])

    def test_just_with_fillchar_func(self):
        data = [
                ('up left',   'up',   'up right'),
                ('left',      '',     'right'),
                ('down left', 'down', 'down r'),
                ]

        def fillchar(row, col, text):
            if row + col == 2:
                return '%'
            if text == 'right':
                return '$'
            return '#' if (row % 2) else '@'

        self.eq(ljust(data, fillchar=fillchar, width=10), [
            ('up left@@@', 'up@@@@@@@@', 'up right%%'),
            ('left######', '%%%%%%%%%%', 'right$$$$$'),
            ('down left%', 'down@@@@@@', 'down r@@@@'),
            ])

        self.eq(rjust(data, fillchar=fillchar, width=10), [
            ('@@@up left', '@@@@@@@@up', '%%up right'),
            ('######left', '%%%%%%%%%%', '$$$$$right'),
            ('%down left', '@@@@@@down', '@@@@down r'),
            ])

    def test_just_with_width(self):
        data = [
                ('column1', 'col2'),
                ('word1', 'word2'),
                ('word3', 'word4 long words'),
                ]

        self.eq(ljust(data, width=20), [
            ('column1             ', 'col2                '),
            ('word1               ', 'word2               '),
            ('word3               ', 'word4 long words    '),
            ])

        self.eq(ljust(data, width=(10, 20)), [
            ('column1   ', 'col2                '),
            ('word1     ', 'word2               '),
            ('word3     ', 'word4 long words    '),
            ])

    def test_just_with_generator(self):
        data = [
                ('column1', 'col2'),
                ('word1', 'word2'),
                ('word3', 'word4 long words'),
                ]

        ret = ljust((vector for vector in data), width=(10, 20))
        self.false(isinstance(ret, (tuple, list)))

        self.eq(list(ret), [
            ('column1   ', 'col2                '),
            ('word1     ', 'word2               '),
            ('word3     ', 'word4 long words    '),
            ])

    def test_just_rect_lack_columns(self):
        self.eq(
                ljust([
                    ('column1', 'col2'),
                    ('word1',),
                    tuple(),
                    ('', 'multiple words'),
                    tuple(),
                    ]),
                [
                    ('column1', 'col2          '),
                    ('word1  ', '              '),
                    ('       ', '              '),
                    ('       ', 'multiple words'),
                    ('       ', '              '),
                    ])

    def test_just_rect_more_columns(self):
        self.eq(
                ljust([
                    ('column1', 'col2'),
                    tuple(),
                    ('word1', 'word2', 'word4'),
                    ('word3', 'multiple words'),
                    ]),
                [
                    ('column1', 'col2          ', '     '),
                    ('       ', '              ', '     '),
                    ('word1  ', 'word2         ', 'word4'),
                    ('word3  ', 'multiple words', '     '),
                    ])


def queue_to_list(Q):
    ret = []
    while not Q.empty():
        ret.append(Q.get())
    return ret


class TestThreadedSpinner(TestCase):
    from collections import namedtuple
    Event = namedtuple('Event',
                       ('timestamp', 'tag', 'args', 'callback'),
                       defaults=(None, None, None, None))

    def setUp(self):
        self.sys_time = 0
        self.behavior_queue = queue.Queue()
        self.events_upon_sleep = queue.Queue()

    def mock_print(self, *args, **kwargs):
        if not args and not kwargs:
            self.behavior_queue.put((self.sys_time, 'print', None))
        else:
            self.behavior_queue.put((
                self.sys_time, 'print',
                tuple(' '.join(args).lstrip('\r').split('\x1b[K ')),
                ))

    def mock_sleep(self, secs):
        self.behavior_queue.put((self.sys_time, 'sleep', secs))

        if not self.events_upon_sleep.empty():
            callback = self.events_upon_sleep.get()
            if callable(callback):
                callback()

            self.events_upon_sleep.task_done()

        self.sys_time += secs

    def test_default_values(self):
        self.patch('builtins.print', RuntimeError('Should not print() at all'))
        self.patch('time.sleep', RuntimeError('Should not sleep() at all'))

        spinner = ThreadedSpinner()
        self.eq(spinner.delay, 0.1)
        self.eq(spinner.icon_entry, '⠉⠛⠿⣿⠿⠛⠉⠙')
        self.eq(spinner.icon_loop, '⠹⢸⣰⣤⣆⡇⠏⠛')
        self.eq(spinner.icon_leave, '⣿')
        self.eq(spinner.text(), '')
        spinner.text('wah')
        self.eq(spinner.text(), 'wah')

    def test_icon_set_loop(self):
        spinner = ThreadedSpinner('LOOP')
        self.eq(spinner.icon_entry, tuple())
        self.eq(spinner.icon_loop, ('LOOP',))
        self.eq(spinner.icon_leave, '.')

    def test_icon_set_entry_loop(self):
        spinner = ThreadedSpinner('ENTRY', 'LOOP')
        self.eq(spinner.icon_entry, 'ENTRY')
        self.eq(spinner.icon_loop, 'LOOP')
        self.eq(spinner.icon_leave, '.')

    def test_icon_set_entry_loop_leave(self):
        spinner = ThreadedSpinner('ENTRY', 'LOOP', 'LEAVE')
        self.eq(spinner.icon_entry, 'ENTRY')
        self.eq(spinner.icon_loop, 'LOOP')
        self.eq(spinner.icon_leave, 'LEAVE')

    def test_icon_set_invalid(self):
        with self.raises(ValueError):
            spinner = ThreadedSpinner('ENTRY', 'LOOP', 'LEAVE', 'WHAT')

        with self.raises(ValueError):
            spinner = ThreadedSpinner(True)

    def test_context_manager(self):
        spinner = ThreadedSpinner()
        spinner.print = lambda *args, **kwarags: None
        with spinner:
            with spinner:
                spinner.start()

    def test_run(self):
        self.patch('time.sleep', self.mock_sleep)
        Event = self.__class__.Event

        delay = 1
        spinner = ThreadedSpinner('ENTRY', 'LOOP', 'OUT', delay=delay)
        spinner.print = self.mock_print

        event_list = [
                Event( 0, 'print', ('E', 'meow')),
                Event( 0, 'sleep', delay),
                Event( 1, 'print', ('N', 'meow')),
                Event( 1, 'sleep', delay),
                Event( 2, 'print', ('T', 'meow')),
                Event( 2, 'sleep', delay),
                Event( 3, 'print', ('R', 'meow')),
                Event( 3, 'sleep', delay),
                Event( 4, 'print', ('Y', 'meow')),
                Event( 4, 'sleep', delay),
                Event( 5, 'print', ('L', 'meow')),
                Event( 5, 'sleep', delay),
                Event( 6, 'print', ('O', 'meow')),
                Event( 6, 'sleep', delay),
                Event( 7, 'print', ('O', 'meow')),
                Event( 7, 'sleep', delay),
                Event( 8, 'print', ('P', 'meow')),
                Event( 8, 'sleep', delay),
                Event( 9, 'print', ('L', 'meow')),
                Event( 9, 'sleep', delay, functools.partial(spinner.text, 'woof')),
                Event( 9, 'print', ('L', 'woof')),
                Event(10, 'print', ('O', 'woof')),
                Event(10, 'sleep', delay),
                Event(11, 'print', ('O', 'woof')),
                Event(11, 'sleep', delay),
                Event(12, 'print', ('P', 'woof')),
                Event(12, 'sleep', delay),
                Event(13, 'print', ('L', 'woof')),
                Event(13, 'sleep', delay),
                Event(14, 'print', ('O', 'woof')),
                Event(14, 'sleep', delay),
                Event(15, 'print', ('O', 'woof')),
                Event(15, 'sleep', delay),
                Event(16, 'print', ('P', 'woof')),
                Event(16, 'sleep', delay, functools.partial(spinner.end, wait=False)),
                Event(17, 'print', ('O', 'woof')),
                Event(17, 'sleep', delay),
                Event(18, 'print', ('U', 'woof')),
                Event(18, 'sleep', delay),
                Event(19, 'print', ('T', 'woof')),
                Event(19, 'print'),
                ]

        for event in filter(lambda e: e.tag == 'sleep', event_list):
            self.events_upon_sleep.put(event.callback)

        spinner.text('meow')
        spinner.start()
        spinner.join()

        from itertools import zip_longest
        for e, behavior in zip_longest(event_list, queue_to_list(self.behavior_queue)):
            expected = (e.timestamp, e.tag, e.args)
            self.eq(expected, behavior)


class TestPromotAskUser(TestCase):
    def setUp(self):
        self.input_queue = None
        self.print_queue = queue.Queue()

        self.patch('builtins.print', self.mock_print)
        self.patch('builtins.input', self.mock_input)

        self.mock_open = unittest.mock.mock_open()
        self.patch('builtins.open', self.mock_open)
        self.assert_called_open = True

    def tearDown(self):
        if self.assert_called_open:
            self.mock_open.assert_has_calls([
                    unittest.mock.call('/dev/tty'),
                    unittest.mock.call('/dev/tty', 'w'),
                    unittest.mock.call('/dev/tty', 'w'),
                    ])

            handle = self.mock_open()
            handle.close.assert_has_calls([
                    unittest.mock.call(),
                    unittest.mock.call(),
                    unittest.mock.call(),
                ])
        else:
            self.mock_open.assert_not_called()

    def set_input(self, *lines):
        self.input_queue = queue.Queue()
        for line in lines:
            self.input_queue.put(line)

    def mock_print(self, *args, **kwargs):
        self.print_queue.put(' '.join(args) + kwargs.get('end', '\n'))

    def mock_input(self, prompt=None):
        if prompt:
            self.print_queue.put(prompt)

        if self.input_queue.empty():
            self.fail('Expected more test input')

        s = self.input_queue.get()
        if isinstance(s, BaseException):
            raise s
        return s + '\n'

    def expect_output(self, *args):
        self.eq(queue_to_list(self.print_queue), list(args))

    def test_empty(self):
        with self.raises(TypeError):
            s = prompt()

        self.assert_called_open = False

    def test_continue(self):
        self.set_input('wah')
        yn = prompt('Input anything to continue>')
        self.expect_output('Input anything to continue> ')

        repr(yn)
        self.eq(yn.selected, 'wah')
        self.eq(str(yn), 'wah')
        self.eq(yn, 'wah')
        self.ne(yn, 'WAH')

    def test_coffee_or_tea(self):
        self.set_input('')
        yn = prompt('Coffee or tea?', 'coffee tea')
        self.expect_output('Coffee or tea? [(C)offee / (t)ea] ')

        self.eq(yn.ignorecase, True)
        self.eq(yn.selected, '')
        self.eq(yn, '')
        self.eq(yn, 'coffee')
        self.eq(yn, 'Coffee')
        self.eq(yn, 'COFFEE')
        self.ne(yn, 'tea')

    def test_coffee_or_tea_yes(self):
        self.set_input(
                'what',
                'WHAT?',
                'tea',
                )
        yn = prompt('Coffee or tea?', 'coffee tea both')
        self.expect_output(
                'Coffee or tea? [(C)offee / (t)ea / (b)oth] ',
                'Coffee or tea? [(C)offee / (t)ea / (b)oth] ',
                'Coffee or tea? [(C)offee / (t)ea / (b)oth] ',
                )

        self.eq(yn.selected, 'tea')
        self.eq(yn, 'tea')
        self.ne(yn, 'coffee')

    def test_eoferror(self):
        self.set_input(EOFError())
        yn = prompt('Coffee or tea?', 'coffee tea')
        self.expect_output(
                'Coffee or tea? [(C)offee / (t)ea] ',
                '\n',
                )

        self.eq(yn.selected, None)
        self.eq(yn, None)
        self.ne(yn, 'coffee')
        self.ne(yn, 'tea')
        self.ne(yn, 'water')
        self.ne(yn, 'both')

    def test_keyboardinterrupt(self):
        self.set_input(KeyboardInterrupt())
        yn = prompt('Coffee or tea?', 'coffee tea')
        self.expect_output(
                'Coffee or tea? [(C)offee / (t)ea] ',
                '\n',
                )

        self.eq(yn.selected, None)
        self.eq(yn, None)
        self.ne(yn, 'coffee')
        self.ne(yn, 'tea')
        self.ne(yn, 'water')
        self.ne(yn, 'both')

    def test_suppress(self):
        self.set_input(RuntimeError('wah'), TimeoutError('waaaaah'))
        yn = prompt('Question', suppress=RuntimeError)
        self.eq(yn, None)

        with self.raises(TimeoutError):
            yn = prompt('Question', suppress=RuntimeError)
        self.eq(yn, None)

    def test_sep(self):
        self.set_input('')
        yn = prompt('Coffee or tea?', 'coffee tea', sep='|')
        self.expect_output('Coffee or tea? [(C)offee|(t)ea] ')

    def test_noignorecase(self):
        self.set_input('tea')
        yn = prompt('Coffee or tea?', 'coffee tea', ignorecase=False)
        self.expect_output('Coffee or tea? [(c)offee / (t)ea] ')

        self.eq(yn, 'tea')
        self.ne(yn, 'TEA')

        self.set_input('coFFee', 'coffEE', 'coffee')
        yn = prompt('Coffee or tea?', 'coffee tea', ignorecase=False)
        self.expect_output(
                'Coffee or tea? [(c)offee / (t)ea] ',
                'Coffee or tea? [(c)offee / (t)ea] ',
                'Coffee or tea? [(c)offee / (t)ea] ',
                )

        self.ne(yn, 'coFFee')
        self.ne(yn, 'coffEE')
        self.eq(yn, 'coffee')

    def test_noabbr(self):
        self.set_input('t', 'tea')
        yn = prompt('Coffee or tea?', 'coffee tea', abbr=False)
        self.expect_output(
                'Coffee or tea? [coffee / tea] ',
                'Coffee or tea? [coffee / tea] ',
                )

        self.ne(yn, 't')
        self.eq(yn, 'tea')
        self.ne(yn, 'TEA')

    def test_noaccept_empty(self):
        self.set_input('', 'c')
        yn = prompt('Coffee or tea?', 'coffee tea', accept_empty=False)
        self.expect_output(
                'Coffee or tea? [(c)offee / (t)ea] ',
                'Coffee or tea? [(c)offee / (t)ea] ',
                )

        self.eq(yn.ignorecase, True)
        self.eq(yn.selected, 'c')
        self.eq(yn, 'c')
        self.eq(yn, 'coffee')
        self.eq(yn, 'Coffee')
        self.eq(yn, 'COFFEE')
        self.ne(yn, 'tea')


class TestKey(TestCase):
    def test_builtin_key(self):
        self.eq(KEY_ESCAPE, b'\033')
        self.eq(KEY_ESCAPE, '\033')
        self.eq(KEY_ESCAPE, 'esc')
        self.eq(KEY_ESCAPE, 'escape')

        self.eq(KEY_BACKSPACE, b'\x7f')
        self.eq(KEY_BACKSPACE, 'backspace')

        self.eq(KEY_TAB, b'\t')
        self.eq(KEY_TAB, 'tab')
        self.eq(KEY_TAB, 'ctrl-i')
        self.eq(KEY_TAB, 'ctrl+i')
        self.eq(KEY_TAB, '^I')

        self.eq(KEY_ENTER, b'\r')
        self.eq(KEY_ENTER, '\r')
        self.eq(KEY_ENTER, 'enter')
        self.eq(KEY_ENTER, 'ctrl-m')
        self.eq(KEY_ENTER, 'ctrl+m')
        self.eq(KEY_ENTER, '^M')

        self.eq(KEY_SPACE, b' ')
        self.eq(KEY_SPACE, ' ')
        self.eq(KEY_SPACE, 'space')

        self.eq(KEY_UP, b'\033[A')
        self.eq(KEY_UP, '\033[A')
        self.eq(KEY_UP, 'up')

        self.eq(KEY_DOWN, b'\033[B')
        self.eq(KEY_DOWN, '\033[B')
        self.eq(KEY_DOWN, 'down')

        self.eq(KEY_RIGHT, b'\033[C')
        self.eq(KEY_RIGHT, '\033[C')
        self.eq(KEY_RIGHT, 'right')

        self.eq(KEY_LEFT, b'\033[D')
        self.eq(KEY_LEFT, '\033[D')
        self.eq(KEY_LEFT, 'left')

        self.eq(KEY_HOME, b'\033[1~')
        self.eq(KEY_HOME, '\033[1~')
        self.eq(KEY_HOME, 'home')

        self.eq(KEY_END, b'\033[4~')
        self.eq(KEY_END, '\033[4~')
        self.eq(KEY_END, 'end')

        self.eq(KEY_PGUP, b'\033[5~')
        self.eq(KEY_PGUP, '\033[5~')
        self.eq(KEY_PGUP, 'pgup')
        self.eq(KEY_PGUP, 'pageup')

        self.eq(KEY_PGDN, b'\033[6~')
        self.eq(KEY_PGDN, '\033[6~')
        self.eq(KEY_PGDN, 'pgdn')
        self.eq(KEY_PGDN, 'pagedown')

        self.eq(KEY_F1, b'\033OP')
        self.eq(KEY_F1, 'F1')

        self.eq(KEY_F2, b'\033OQ')
        self.eq(KEY_F2, 'F2')

        self.eq(KEY_F3, b'\033OR')
        self.eq(KEY_F3, 'F3')

        self.eq(KEY_F4, b'\033OS')
        self.eq(KEY_F4, 'F4')

        self.eq(KEY_F5, b'\033[15~')
        self.eq(KEY_F5, 'F5')

        self.eq(KEY_F6, b'\033[17~')
        self.eq(KEY_F6, 'F6')

        self.eq(KEY_F7, b'\033[18~')
        self.eq(KEY_F7, 'F7')

        self.eq(KEY_F8, b'\033[19~')
        self.eq(KEY_F8, 'F8')

        self.eq(KEY_F9, b'\033[20~')
        self.eq(KEY_F9, 'F9')

        self.eq(KEY_F10, b'\033[21~')
        self.eq(KEY_F10, 'F10')

        self.eq(KEY_F11, b'\033[23~')
        self.eq(KEY_F11, 'F11')

        self.eq(KEY_F12, b'\033[24~')
        self.eq(KEY_F12, 'F12')

        for c in 'abcdefghjklnopqrstuvwxyz':
            key = globals()['KEY_CTRL_' + c.upper()]
            self.eq(key, chr(ord(c) - ord('a') + 1))
            self.eq(key, 'ctrl-' + c)
            self.eq(key, 'ctrl+' + c)
            self.eq(key, '^' + c.upper())

    def test_key_invalid_seq_and_alias(self):
        Key = type(KEY_UP)
        with self.raises(TypeError):
            Key(['wah'], 'WAH')

        with self.raises(TypeError):
            Key('wah', ['WAH'])

    def test_key_hash(self):
        self.eq(hash(KEY_UP), hash(KEY_UP.seq))

    def test_key_nameit(self):
        Key = type(KEY_UP)
        TEST_KEY = Key('test_key')
        self.ne(TEST_KEY, 'wah')
        TEST_KEY.nameit('wah')
        self.eq(TEST_KEY, 'wah')
        TEST_KEY.nameit('wah')
        self.eq(TEST_KEY, 'wah')

    def test_key_repr(self):
        self.eq(repr(KEY_UP), 'Key(up)')

        Key = type(KEY_UP)
        new_key = Key('測')
        self.eq(repr(new_key), r"Key('測')")

        seq = '測'.encode('utf8')[:-2]
        new_key2 = Key(seq)
        self.eq(repr(new_key2), r'Key(' + repr(seq) + ')')


class TestGetch(TestCase):
    def setUp(self):
        self.patch('sys.stdin.fileno', self.mock_stdin_fileno)
        self.patch('select.select', self.mock_select)
        self.patch('os.read', self.mock_read)
        self.patch('os.getpid', self.mock_getpid)
        self.patch('os.kill', self.mock_kill)
        self.patch('tty.setraw', self.mock_setraw)
        self.patch('termios.tcgetattr', self.mock_tcgetattr)
        self.patch('termios.tcsetattr', self.mock_tcsetattr)
        self.buffer = bytearray()
        self.default_term_attr = [
                'iflag', 'oflag', 'cflag', 'lflag',
                'ispeed', 'ospeed',
                [b'cc'] * 20]

        import termios
        self.default_term_attr[6][termios.VINTR] = b'\x03'
        self.default_term_attr[6][termios.VSUSP] = b'\x1c'
        self.default_term_attr[6][termios.VQUIT] = b'\x1a'

        self.term_attr = list(self.default_term_attr)
        self.killed = None

    def tearDown(self):
        self.eq(self.term_attr, self.default_term_attr)

    def press(self, key):
        if isinstance(key, str):
            key = key.encode('utf8')
        self.buffer += key

    def mock_stdin_fileno(self):
        return 0

    def mock_select(self, rlist, wlist, xlist, timeout=None):
        self.eq(self.term_attr[0], 'raw')
        if self.buffer:
            return (rlist, [], [])
        return ([], [], [])

    def mock_read(self, fd, n):
        self.eq(self.term_attr[0], 'raw')
        ret = self.buffer[:n]
        del self.buffer[:n]
        return ret

    def mock_getpid(self):
        return self

    def mock_kill(self, pid, sig):
        assert pid is self
        self.killed = sig

    def mock_setraw(self, fd, when=None):
        import termios
        self.eq(when, termios.TCSADRAIN)
        self.term_attr = ['raw', 'raw', 'raw', 'raw', 'raw', 'raw', 'cc']

    def mock_tcgetattr(self, fd):
        return self.term_attr

    def mock_tcsetattr(self, fd, when, attributes):
        import termios
        self.eq(when, termios.TCSADRAIN)
        self.term_attr = attributes

    def test_getch_basic(self):
        self.eq(getch(), None)
        self.press(b'abc')
        self.eq(getch(), 'a')
        self.eq(getch(), 'b')
        self.eq(getch(), 'c')
        self.eq(getch(), None)

    def test_getch_unicode(self):
        self.eq(getch(), None)
        self.press('測試')
        self.eq(getch(), '測')
        self.eq(getch(), '試')
        self.eq(getch(), None)

    def test_getch_escape_keys(self):
        self.eq(getch(), None)
        self.press('\033[AA')
        self.eq(getch(), 'up')
        self.eq(getch(), 'A')
        self.eq(getch(), None)

    def test_getch_unicode_error(self):
        self.eq(getch(), None)
        test_data = '測'.encode('utf8')[:-1]
        self.press(test_data)
        self.eq(getch(), test_data)
        self.eq(getch(), None)

    def test_register_key_empty_seq(self):
        with self.raises(ValueError):
            register_key('')

    def test_register_key_with_key_object(self):
        new_key = type(KEY_UP)(r'\033[[[[[[', 'wow')
        nkey = register_key(new_key, 'wah', 'haha')
        self.eq(new_key.seq, nkey.seq)
        self.eq(new_key, 'wow')
        self.eq(nkey, 'wah')
        self.eq(nkey, 'haha')
        self.eq(deregister_key(new_key), new_key)

    def test_register_deregister_key(self):
        self.eq(getch(), None)
        self.press('測試')
        self.eq(getch(), '測')
        self.eq(getch(), '試')
        self.eq(getch(), None)

        # Resigter keys
        TE = register_key('測'.encode('utf8'), 'TE')
        ST = register_key('試'.encode('utf8'), 'ST')
        ABCD = register_key('\033ABCD', 'ABCD')
        self.eq(TE, '測')
        self.eq(TE, '測'.encode('utf8'))
        self.eq(ST, '試')
        self.eq(ST, '試'.encode('utf8'))
        self.eq(ABCD, 'ABCD')
        self.eq(ABCD, '\033ABCD')

        self.press('測試\033ABCD')
        self.eq(getch(), TE)
        self.eq(getch(), ST)
        self.eq(getch(), 'ABCD')
        self.eq(getch(), None)

        # Deresigter keys
        TE = deregister_key(TE)
        ST = deregister_key(ST.seq)
        ABCD = deregister_key('\033ABCD')

        self.press('測試\033ABCD')
        self.eq(getch(), TE)
        self.eq(getch(), ST)
        self.eq(getch(), '\033A')
        self.eq(getch(), 'B')
        self.eq(getch(), 'C')
        self.eq(getch(), 'D')
        self.eq(getch(), None)

        MY_HOME = register_key(KEY_HOME.seq, 'MY_HOME')
        self.eq(MY_HOME, KEY_HOME)
        self.press(KEY_HOME.seq)
        self.eq(getch(), MY_HOME)

    def test_capture(self):
        import signal

        self.press('\x03')
        getch()

        self.press('\x03')
        getch(capture='unknown key')
        self.eq(self.killed, signal.SIGINT)


class TestPager(TestCase):
    def setUp(self):
        from .lib_test_utils import FakeTerminal
        self.terminal = FakeTerminal()
        self.patch('shutil.get_terminal_size', lambda: self.terminal.get_terminal_size())

    def test_data_storing(self):
        pager = Pager()
        self.true(pager.empty)
        self.eq(pager.lines, tuple())

        pager.append('wah1')
        pager.append('wah2')
        pager.append('wah3')
        pager.extend(['wah4', 'wah5'])
        self.eq(len(pager), 5)
        self.eq(pager.lines, ('wah1', 'wah2', 'wah3', 'wah4', 'wah5'))
        self.false(pager.empty)

        self.eq(pager[1].text, 'wah2')

        pager[1] = 'wahwah'
        self.eq(pager[1].text, 'wahwah')

        pager[1:3] = ['slice1', 'slice2', 'slice3', 'slice4']
        self.eq(pager.lines,
                ('wah1', 'slice1', 'slice2', 'slice3', 'slice4', 'wah4', 'wah5')
                )

    def test_auto_append(self):
        pager = Pager()
        self.true(pager.empty)

        pager[2] = 'line3'
        pager[1] = 'line2'
        self.eq(len(pager), 3)

        pager[4] = 'line5'

        self.eq(pager.lines, (
            '',
            'line2',
            'line3',
            '',
            'line5',
            ))

    def test_render_basic(self):
        pager = Pager()
        pager.print = self.terminal.print

        self.eq(self.terminal.lines, [''])
        pager.render()
        self.eq(self.terminal.lines, [''])

        data = ['wah1', 'wah2', 'wah3']
        pager.extend(data)

        self.eq(self.terminal.lines, [''])
        pager.render()
        self.eq(self.terminal.lines, data)

        pager[1] = '哇啊'
        self.eq(self.terminal.lines, data)
        pager.render()
        self.eq(self.terminal.lines, ['wah1', '哇啊', 'wah3'])

    def test_render_horizontal_overflow(self):
        pager = Pager()
        pager.print = self.terminal.print
        self.eq(self.terminal.width, 80)
        self.eq(self.terminal.height, 24)

        pager.append('哇' * 50)
        pager.append('a' + '哇' * 50)
        pager.append('aa' + '哇' * 50)
        pager.render()
        self.eq(self.terminal.lines, [
            '哇' * 40,
            'a' + '哇' * 39,
            'aa' + '哇' * 39,
            ])

    def get_small_terminal_wah_pager(self, **kwargs):
        # Use a smaller terminal to make output less
        self.terminal = FakeTerminal(lines=5, columns=8)
        self.eq(self.terminal.width, 8)
        self.eq(self.terminal.height, 5)

        pager = Pager(**kwargs)
        pager.print = self.terminal.print

        for i in range(10):
            pager.append('哇 {}'.format(i))

        return pager

    def test_render_vertical_overflow(self):
        pager = self.get_small_terminal_wah_pager()

        self.terminal.recording = True
        pager.render()
        # Check output sequence
        self.eq(self.terminal.recording, [
            '\r哇 0\033[K\n',
            '\r哇 1\033[K\n',
            '\r哇 2\033[K\n',
            '\r哇 3\033[K\n',
            '\r哇 4\033[K',
            ])
        self.terminal.recording = False

        # Check terminal has 5 lines
        self.eq(len(self.terminal.lines), 5)
        for i in range(5):
            self.eq(self.terminal.lines[i], '哇 {}'.format(i))

        # Check cursor position
        self.eq(self.terminal.cursor.y, 4)

    def test_partial_re_render(self):
        pager = self.get_small_terminal_wah_pager()
        pager.render()

        # Update a visible line and an invisible line
        self.terminal.recording = True
        pager[2] = '哇 2 (new)'
        pager[17] = '哇 17 (new)'
        pager.render()

        # The last line is always updated in order to restore cursor position
        self.eq(self.terminal.recording, [
            '\r\033[2A',
            '\r哇 2 (ne\033[K\n',
            '\r\033[1B',
            '\r哇 4\033[K'])
        self.terminal.recording = False

    def test_hard_re_render(self):
        pager = self.get_small_terminal_wah_pager()
        pager.render()

        # A hard re-render
        self.terminal.recording = True
        pager[3] = '哇 3'
        pager.render(all=True)
        self.eq(self.terminal.recording, [
            '\r\033[4A',
            '\r哇 0\033[K\n',
            '\r哇 1\033[K\n',
            '\r哇 2\033[K\n',
            '\r哇 3\033[K\n',
            '\r哇 4\033[K'])
        self.terminal.recording = False

    def test_pop_insert(self):
        pager = self.get_small_terminal_wah_pager()
        pager.render()

        # pop line[0] and line[2] and then re-render
        self.terminal.recording = True
        pager.pop(0)
        pager.pop(2)
        pager.insert(3, '哇 new')
        pager.render()
        self.eq(self.terminal.recording, [
            '\r\033[4A',
            '\r哇 1\033[K\n',
            '\r哇 2\033[K\n',
            '\r哇 4\033[K\n',
            '\r哇 new\033[K\n',
            '\r哇 5\033[K'])
        self.terminal.recording = False

    def test_scrolling(self):
        pager = self.get_small_terminal_wah_pager()
        pager.render()

        self.terminal.recording = True
        pager[6] = '哇 6 (new)'
        pager.scroll += 2
        pager.render()
        self.eq(self.terminal.recording, [
            '\r\033[4A',
            '\r哇 2\033[K\n',
            '\r哇 3\033[K\n',
            '\r哇 4\033[K\n',
            '\r哇 5\033[K\n',
            '\r哇 6 (ne\033[K'])
        self.terminal.recording = False

    def test_clear(self):
        pager = self.get_small_terminal_wah_pager()
        pager.render()

        # Clear
        self.terminal.recording = True
        pager.clear()
        self.true(pager.empty)
        self.eq(pager.lines, tuple())
        pager.render()
        self.eq(self.terminal.recording, [
            '\r\033[K\033[A',
            '\r\033[K\033[A',
            '\r\033[K\033[A',
            '\r\033[K\033[A',
            '\r\033[K',
            ])
        self.eq(pager.display, tuple())
        self.terminal.recording = False

    def test_clear_by_slice_assignment(self):
        pager = self.get_small_terminal_wah_pager()
        pager.render()

        # Clear by slice assignment
        self.terminal.recording = True
        pager[:] = []
        self.eq(pager.lines, tuple())
        pager.render()
        self.eq(pager.display, tuple())
        self.eq(self.terminal.recording, [
            '\r\033[K\033[A',
            '\r\033[K\033[A',
            '\r\033[K\033[A',
            '\r\033[K\033[A',
            '\r\033[K',
            ])
        self.terminal.recording = False

    def test_size_limits(self):
        self.terminal = FakeTerminal()
        self.eq(self.terminal.width, 80)
        self.eq(self.terminal.height, 24)

        pager = Pager()
        pager.max_height = 5
        pager.max_width = 8
        pager.print = self.terminal.print

        self.lt(pager.max_height, self.terminal.height)
        self.lt(pager.max_width, self.terminal.width)

        self.terminal.recording = True
        pager[0] = 'line0line0'
        pager[1] = 'line1line1'
        pager[2] = 'line2line2'
        pager[3] = 'line3line3'
        pager[4] = 'line4line4'
        pager[5] = 'line5line5'
        pager[6] = 'line6line6'
        self.eq(len(pager), 7)
        pager.render()
        self.eq(len(pager.display), 5)

        self.eq(self.terminal.recording, [
            '\rline0lin\033[K\n',
            '\rline1lin\033[K\n',
            '\rline2lin\033[K\n',
            '\rline3lin\033[K\n',
            '\rline4lin\033[K',
            ])
        self.terminal.recording = False

    def test_header(self):
        pager = self.get_small_terminal_wah_pager()
        pager.render()

        pager.header.append('header')

        self.terminal.recording = True
        pager.render()
        self.eq(self.terminal.recording, [
            '\r\033[4A',
            '\rheader\033[K\n',
            '\r哇 0\033[K\n',
            '\r哇 1\033[K\n',
            '\r哇 2\033[K\n',
            '\r哇 3\033[K'])
        self.terminal.recording = False

    def test_footer(self):
        pager = self.get_small_terminal_wah_pager()
        pager.render()

        pager.footer.append('footer')

        self.terminal.recording = True
        pager.render()
        self.eq(self.terminal.recording, [
            '\rfooter\033[K'])
        self.terminal.recording = False

    def test_header_and_footer(self):
        pager = self.get_small_terminal_wah_pager()
        pager.render()

        pager.header.append('header')
        pager.footer.append('footer')

        self.terminal.recording = True

        # scroll down 1 line to test partial update
        pager.scroll += 1

        pager.render()
        self.eq(self.terminal.recording, [
            '\r\033[4A',
            '\rheader\033[K\n',
            '\r\033[3B',
            '\rfooter\033[K'])
        self.terminal.recording = False

    def test_flex(self):
        pager = self.get_small_terminal_wah_pager(flex=True, max_height=5)
        self.true(pager.flex)
        self.eq(pager.height, 5)
        self.eq(pager.max_height, 5)

        pager.clear()
        self.eq(pager.height, 5)

        pager.append('line0')
        pager.append('line1')
        pager.footer.append('footer')

        self.terminal.recording = True
        pager.render()
        self.eq(self.terminal.recording, [
            '\rline0\033[K\n',
            '\rline1\033[K\n',
            '\r\033[K\n',
            '\r\033[K\n',
            '\rfooter\033[K'])
        self.terminal.recording = False

    def test_thick_header_and_footer(self):
        pager = self.get_small_terminal_wah_pager()

        pager.header.extend(['header' + str(i) for i in range(5)])
        pager.footer.extend(['footer' + str(i) for i in range(5)])

        # Both header and footer are guarenteed to print at least one line
        # header has higher priority
        pager.render()
        self.eq(pager.preview, (
            'header0',
            'header1',
            'header2',
            'header3',
            'footer0',
            ))

        # footer fills the remaining space
        pager.header.clear()
        pager.header.extend(['header0', 'header1'])
        self.eq(pager.preview, (
            'header0',
            'header1',
            'footer0',
            'footer1',
            'footer2',
            ))

        # footer fills all the space
        pager.header.clear()
        self.eq(pager.preview, (
            'footer0',
            'footer1',
            'footer2',
            'footer3',
            'footer4',
            ))

        # body starts to have space to print
        pager.header.append('header0')
        pager.footer.pop(0)
        pager.footer.pop(0)
        pager.footer.pop(0)
        self.eq(pager.preview, (
            'header0',
            '哇 0',
            '哇 1',
            'footer3',
            'footer4',
            ))

        pager.header.append('header1')
        self.eq(pager.preview, (
            'header0',
            'header1',
            '哇 0',
            'footer3',
            'footer4',
            ))

        pager.header.pop(0)
        pager.footer.pop(0)
        self.eq(pager.preview, (
            'header1',
            '哇 0',
            '哇 1',
            '哇 2',
            'footer4',
            ))

        self.eq(list(pager.header), ['header1'])
        self.eq(list(pager), ['哇 0', '哇 1', '哇 2', '哇 3', '哇 4', '哇 5', '哇 6', '哇 7', '哇 8', '哇 9'])
        self.eq(list(pager.footer), ['footer4'])
