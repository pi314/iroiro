from .lib_test_utils import *

from iroiro import *


class TestItertools(TestCase):
    def test_unwrap_one(self):
        self.eq(unwrap_one(1), 1)
        self.eq(unwrap_one((1,)), (1,))
        self.eq(unwrap_one(False), False)
        self.eq(unwrap_one((False,)), (False,))
        self.eq(unwrap_one('text'), 'text')
        self.eq(unwrap_one([1, 2, 3]), [1, 2, 3])
        self.eq(unwrap_one([[1, 2, 3]]), [1, 2, 3])
        self.eq(unwrap_one([[[1, 2, 3]]]), [1, 2, 3])
        self.eq(unwrap_one([[[[1, 2, 3]]]]), [1, 2, 3])
        self.eq(unwrap_one([(1, 2, 3)]), (1, 2, 3))
        self.eq(unwrap_one(((1, 2, 3))), (1, 2, 3))
        self.eq(unwrap_one(([1, 2, 3])), [1, 2, 3])

    def test_unwrap(self):
        def wrap(obj, type=tuple):
            return type((obj,))

        self.eq(unwrap(), None)

        self.eq(unwrap(1), 1)
        self.eq(unwrap(False), False)
        self.eq(unwrap('text'), 'text')

        self.eq(unwrap(wrap(1)), 1)
        self.eq(unwrap(wrap(False)), False)
        self.eq(unwrap(wrap('text')), 'text')

        self.eq(unwrap([1, 2, 3]), [1, 2, 3])
        self.eq(unwrap([[1, 2, 3]]), [1, 2, 3])
        self.eq(unwrap([[[1, 2, 3]]]), [1, 2, 3])
        self.eq(unwrap([[[[1, 2, 3]]]]), [1, 2, 3])

        self.eq(unwrap([(1, 2, 3),]), (1, 2, 3))
        self.eq(unwrap(((1, 2, 3),)), (1, 2, 3))
        self.eq(unwrap(([1, 2, 3],)), [1, 2, 3])

    def test_flatten(self):
        self.eq(flatten(False), False)
        self.eq(flatten('text'), 'text')

        self.eq(
                flatten([[1, 2, 3], [4, 5, 6], [7], [8, 9]]),
                [1, 2, 3, 4, 5, 6, 7, 8, 9]
                )

        self.eq(
                flatten(([1, 2, 3], [4, 5, 6], [7], [8, 9])),
                (1, 2, 3, 4, 5, 6, 7, 8, 9)
                )

        self.eq(
                flatten(([[1, 2, [[]], 3], [4, ([5], 6)], 7, [8, 9]],)),
                (1, 2, 3, 4, 5, 6, 7, 8, 9)
                )

    def test_lookahead(self):
        data = []
        for val, is_last in lookahead([1, 2, 3, 4, 5]):
            data.append((val, is_last))

        self.eq(data, [
            (1, False),
            (2, False),
            (3, False),
            (4, False),
            (5, True),
            ])

    def test_zip_longest(self):
        self.eq(
                list(zip_longest('ABCD', [1, 2])),
                [
                    ('A', 1),
                    ('B', 2),
                    ('C', None),
                    ('D', None),
                    ]
                )

        self.eq(
                list(zip_longest('AB', [1, 2, 3, 4])),
                [
                    ('A', 1),
                    ('B', 2),
                    (None, 3),
                    (None, 4),
                    ]
                )

        self.eq(
                list(zip_longest('ABCD', [1, 2], fillvalues='#')),
                [
                    ('A', 1),
                    ('B', 2),
                    ('C', '#'),
                    ('D', '#'),
                    ]
                )

        self.eq(
                list(zip_longest('AB', [1, 2, 3, 4], fillvalues='#')),
                [
                    ('A', 1),
                    ('B', 2),
                    ('#', 3),
                    ('#', 4),
                    ]
                )

        self.eq(
                list(zip_longest('ABCD', [1, 2], fillvalues=('#', 0))),
                [
                    ('A', 1),
                    ('B', 2),
                    ('C', 0),
                    ('D', 0),
                    ]
                )

        self.eq(
                list(zip_longest('AB', [1, 2, 3, 4], fillvalues=('#', 0))),
                [
                    ('A', 1),
                    ('B', 2),
                    ('#', 3),
                    ('#', 4),
                    ]
                )
