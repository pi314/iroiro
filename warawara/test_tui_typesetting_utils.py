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
