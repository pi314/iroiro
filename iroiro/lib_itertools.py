import itertools

from .internal_utils import exporter
export, __all__ = exporter()


@export
def is_iterable(obj):
    try:
        iter(obj)
        return True
    except TypeError:
        return False


@export
def unwrap_one(obj):
    try:
        while True:
            if len(obj) == 1 and iter(obj[0]) and not isinstance(obj[0], str):
                obj = obj[0]
            else:
                return obj
    except TypeError:
        pass

    return obj


@export
def unwrap(obj=None):
    try:
        while True:
            if isinstance(obj, str):
                return obj

            if len(obj) == 1:
                obj = obj[0]
                continue

            return obj
    except TypeError:
        pass

    return obj


@export
def flatten(tree):
    if not is_iterable(tree) or isinstance(tree, str):
        return tree

    wrapper_type = type(tree)
    return wrapper_type(itertools.chain.from_iterable(
        flatten(i) if is_iterable(i) and not isinstance(i, str) else [i]
        for i in tree
        ))


@export
def lookahead(iterable):
    it = iter(iterable)
    lookahead = next(it)

    for val in it:
        yield lookahead, False
        lookahead = val

    yield lookahead, True


@export
def zip_longest(*iterables, fillvalues=None):
    if not isinstance(fillvalues, (tuple, list)):
        fillvalues = (fillvalues,) * len(iterables)

    iterators = list(map(iter, iterables))

    while True:
        values = []
        cont = False
        for idx, iterator in enumerate(iterators):
            try:
                value = next(iterator)
                cont = True
            except:
                value = fillvalues[idx]

            values.append(value)

        if not cont:
            break

        yield tuple(values)
