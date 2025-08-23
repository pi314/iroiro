import queue

import functools
import threading
import unittest.mock

from collections import namedtuple

from .lib_test_utils import *

from iroiro import *


class TestTypesettingUtils(TestCase):
    def test_strwidth(self):
        self.eq(strwidth('test'), 4)
        self.eq(strwidth(orange('test')), 4)
        self.eq(strwidth('哇嗚'), 4)

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
        spinner.print_function = lambda *args, **kirogs: None
        with spinner:
            with spinner:
                spinner.start()

    def test_run(self):
        self.patch('time.sleep', self.mock_sleep)
        Event = self.__class__.Event

        delay = 1
        spinner = ThreadedSpinner('ENTRY', 'LOOP', 'OUT', delay=delay)
        spinner.print_function = self.mock_print

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
        self.patch('tty.setraw', self.mock_setraw)
        self.patch('termios.tcgetattr', self.mock_tcgetattr)
        self.patch('termios.tcsetattr', self.mock_tcsetattr)
        self.buffer = bytearray()
        self.default_term_attr = [
                'iflag', 'oflag', 'cflag', 'lflag',
                'ispeed', 'ospeed',
                'cc']

        self.term_attr = list(self.default_term_attr)

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
        self.eq(getch(), '\33A')
        self.eq(getch(), 'B')
        self.eq(getch(), 'C')
        self.eq(getch(), 'D')
        self.eq(getch(), None)

        MY_HOME = register_key(KEY_HOME.seq, 'MY_HOME')
        self.eq(MY_HOME, KEY_HOME)
        self.press(KEY_HOME.seq)
        self.eq(getch(), MY_HOME)
