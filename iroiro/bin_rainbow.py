import sys
import shutil
import argparse
import textwrap

from os.path import basename

from . import lib_colors

from .lib_colors import paint
from .lib_colors import color
from .lib_regex import rere
from .lib_math import resample
from .lib_math import is_uint8
from .lib_math import lerp
from .lib_itertools import lookahead
from .lib_tui import getch


errors = []
def pend_error(*errmsg):
    errors.append(errmsg)


def judge_errors():
    if errors:
        for error in errors:
            print(*error)
        sys.exit(1)


def high_contrast_fg(c):
    if isinstance(c, lib_colors.Color256):
        c = c.index

    if c == 0:
        return None

    if c < 16:
        return 0

    elif c < 232:
        base = c - 16
        r = (base // 36)
        g = ((base % 36) // 6)
        b = (base % 6)

        if r < 2 and g < 2:
            return None

        if r < 3 and g < 1:
            return None

    elif c in range(232, 240):
        return None

    return 0


def parse_target(arg):
    if not isinstance(arg, str):
        return

    ret = None

    to = []

    while True:
        m = rere(arg)

        if m.fullmatch(r'^(.+)\.(rgb|RGB|hsv|HSV)$'):
            to.append(m.group(2))
            arg = m.group(1)
            continue

        break

    if arg in lib_colors.names:
        ret = getattr(lib_colors, arg)

    # #RRGGBB format
    elif m.fullmatch(r'#?([0-9a-fA-Z]{6})'):
        ret = color('#' + m.group(1))

    # #RRR,GGG,BBB format
    elif m.fullmatch(r'#([0-9]+),([0-9]+),([0-9]+)'):
        r, g, b = map(lambda x: int(x, 10), arg[1:].split(','))
        ret = lib_colors.ColorRGB(r, g, b)

    # @HHH,SSS,VVV format
    elif m.fullmatch(r'@([0-9]+),([0-9]+),([0-9]+)'):
        ret = lib_colors.ColorHSV(arg)

    # int
    elif m.fullmatch(r'[0-9]+'):
        try:
            i = int(arg, 10)
            if is_uint8(i):
                ret = color(i)
        except:
            ret = None

    tr_path = arg
    for t in to[::-1]:
        try:
            if t.lower() == 'rgb':
                ret = ret.to_rgb()
                tr_path += '.rgb'
            elif t.lower() == 'hsv':
                ret = ret.to_hsv()
                tr_path += '.hsv'
        except AttributeError:
            pend_error('Error: Cannot transform color', tr_path, 'to', t)

    return ret


def spell_suggestions(word):
    import difflib
    return difflib.get_close_matches(word, lib_colors.names, cutoff=0)


def spell_suggestion_err_msg(word):
    err_msg = 'Unknown color name "{}"'.format(word)
    suggestions = spell_suggestions(word)[:3]
    if suggestions:
        err_msg += ', did you mean '
        if len(suggestions) == 1:
            err_msg += '"{}"'.format(suggestions[0])
        elif len(suggestions) == 2:
            err_msg += '"{}", or "{}"'.format(suggestions[0], suggestions[1])
        elif len(suggestions) == 3:
            err_msg += '"{}", "{}", or "{}"'.format(*suggestions)
        err_msg += '?'
    pend_error(err_msg)


def expand_macro_all():
    ret = []
    for i in range(256):
        ret.append((parse_target(str(i)), []))

    for name in lib_colors.names:
        c = parse_target(name)
        if hasattr(c, 'index'):
            ret[c.index][1].append(name)
        else:
            ret.append((c, [name]))

    return ret


def expand_macro_named():
    ret = []
    for name in lib_colors.names:
        ret.append((parse_target(name), [name]))
    return ret


def main_256cube():
    # Print color cube palette
    print('Format: ESC[30;48;5;{}m')
    for c in range(0, 256):
        color_rgb = color(c).to_rgb()
        print(paint(fg=high_contrast_fg(c), bg=c)(' ' + str(c).rjust(3)), end='')

        if c < 16 and (c + 1) % 8 == 0:
            print()
        if c >= 16 and (c - 16 + 1) % 36 == 0:
            print()
        if c in (15, 231):
            print()

    print()
    sys.exit()


def main():
    prog = basename(sys.argv[0])
    argv = sys.argv[1:]

    if not argv:
        main_256cube()

    if '-h' in argv or '--help' in argv:
        subcmd = None
    elif argv[0] in ('tile', 'gradient'):
        subcmd = argv.pop(0)
    elif argv[0] == 'hsv':
        subcmd = argv.pop(0)
    else:
        subcmd = 'list'

    colorful = ''.join(
            map(
                lambda x: lib_colors.color(x[0])(x[1]),
                zip(
                    ['#FF2222', '#FFC000', '#FFFF00',
                     '#C0FF00', '#00FF00', '#00FFC0',
                     '#00FFFF', '#00C0FF', '#3333FF', '#C000FF', '#FF00FF'],
                    'coooolorful'
                    )
                )
            )

    class YesNoToBoolOption(argparse.Action):
        def __call__(self, parser, namespace, values, option_string=None):
            setattr(namespace, self.dest, values == 'yes')

    parser = argparse.ArgumentParser(
            prog=prog,
            description=('Query pre-defined colors from iroiro, ' +
                         'or produce ' + colorful + ' strips/tiles to fill the screen.'),
            epilog=textwrap.dedent('''
                    Example usages:
                    {s} {prog}
                    {s} {prog} all
                    {s} {prog} all --sort svh
                    {s} {prog} named --grep orange --hex
                    {s} {prog} FFD700 --rgb
                    {s} {prog} tile --lines=2 --cols=8 salmon white
                    {s} {prog} gradient 00AFFF FFAF00
                    '''.strip('\n')).format(prog=prog, s=lib_colors.murasaki('$')),
            allow_abbrev=False, add_help=False,
            formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument('-h', '--help', action='help', help='Show this help message and exit')

    if not subcmd or subcmd in ('list', 'gradient'):
        parser.add_argument('--grep',
                            action='append',
                            help='''Filter out colors that does not contain the specified sub-string
    This argument can be specified multiple times for multiple keywords''')

    if not subcmd or subcmd in ('list', 'gradient'):
        parser.add_argument('-a', '--aliases',
                            action='store_true',
                            help='Show aliases of specified colors')

    if not subcmd or subcmd in ('list', 'gradient'):
        parser.add_argument('--hex', dest='val_fmt',
                            action='append_const', const='hex',
                            help='Show RGB value in hex number')

        parser.add_argument('--rgb', dest='val_fmt',
                            action='append_const', const='rgb',
                            help='Show RGB value in 3-tuple')

        parser.add_argument('--hsv', dest='val_fmt',
                            action='append_const', const='hsv',
                            help='Show HSV value in 3-tuple')

    if not subcmd or subcmd in ('list', 'gradient'):
        def SortKey(arg):
            if arg in ('index', 'name', 'rgb', 'hsv'):
                return arg
            if all(ch in 'rgbRGBhsvHSVni' for ch in arg):
                return arg
            raise ValueError(arg)
        parser.add_argument('--sort',
                            nargs='?', type=SortKey, const='index', metavar='key',
                            default='',
                            help='Sort output by the specified attribute.\nAvailable keys: index, name, rgb, hue, [rgbRGBhsvHSVni]')

    if not subcmd or subcmd in ('list', 'gradient'):
        parser.add_argument('-r', '--reverse',
                            action='store_true',
                            help='Reverse output sequence')

    if not subcmd or subcmd in ('list', 'gradient'):
        parser.add_argument('-m', '--merge',
                            action=YesNoToBoolOption, nargs='?', choices=['yes', 'no'], const='yes',
                            help='Merge colors that have same index')

        parser.add_argument('-M', '--no-merge',
                            action='store_false', dest='merge',
                            help='Dont merge colors that have same index')

    if not subcmd or subcmd == 'gradient':
        parser.add_argument('-c', '--clockwise',
                            action=YesNoToBoolOption, nargs='?', choices=['yes', 'no'], const='yes',
                            help='''Calculate clockwise color gradient for HSV''')

    if not subcmd or subcmd == 'tile':
        parser.add_argument('--cols', '--columns',
                            type=int,
                            help='Specify terminal columns')

        parser.add_argument('--lines',
                            type=int,
                            help='Specify terminal height')

    parser.add_argument('targets', nargs='*', help='''Names / indexs / RGB hex values / HSV values to query
"all" and "named" macros could be used in "list" mode''')

    parser.set_defaults(val_fmt=[])

    args = parser.parse_intermixed_args(argv)

    if subcmd == 'tile':
        main_tile(args)
    elif subcmd == 'gradient':
        main_list(args, gradient=True)
    elif subcmd == 'hsv':
        main_hsv(args)
    else:
        main_list(args)


def main_list(args, gradient=False):
    if gradient:
        # argument handling for gradient
        if not args.targets:
            pend_error('No colors to gradient')

        judge_errors()

        targets = list(args.targets)
        path = []
        import re
        while targets:
            if not path:
                path.append([None, None, None])

            arg = targets.pop(0)
            if re.fullmatch(r'\+\d+', arg):
                path[-1][2] = arg

            elif path[-1][0] is None:
                path[-1][0] = arg

            elif path[-1][1] is None:
                path[-1][1] = arg

            else:
                path.append([path[-1][1], arg, None])

        def color_text(this_color):
            if isinstance(this_color, lib_colors.Color256):
                return str(this_color.index)
            elif isinstance(this_color, lib_colors.ColorRGB):
                return '{:#X}'.format(this_color)
            elif isinstance(this_color, lib_colors.ColorHSV):
                return '@{:},{:},{:}'.format(this_color.H, this_color.S, this_color.V)
            else:
                line.append('(?)')

        src = parse_target(path[0][0])
        if not src:
            spell_suggestion_err_msg(src)

        expanded = [(src, color_text(src))]
        for step in path:
            src = step[0]
            dst = step[1]

            if dst is None:
                continue

            arg_n = step[2]

            src = parse_target(src)
            if not src:
                spell_suggestion_err_msg(src)

            dst = parse_target(dst)
            if not dst:
                spell_suggestion_err_msg(dst)

            try:
                n = int(arg_n, 10) if arg_n else None
            except:
                pend_error('Invalid number: {}'.format(arg_n))

            judge_errors()

            expanded += [(g, color_text(g)) for g in lib_colors.gradient(src, dst, n, clockwise=args.clockwise)[1:]]

    else:
        # argument handling for list
        if args.merge is None:
            if 'all' in args.targets or 'named' in args.targets:
                args.merge = True
            elif args.aliases:
                args.merge = True
            else:
                args.merge = False

        if args.grep and not args.targets:
            args.targets = ['all']

        expanded = []
        for arg in args.targets:
            if arg in ('all', 'named'):
                if arg == 'all':
                    expansion = expand_macro_all()
                elif arg == 'named':
                    expansion = expand_macro_named()

                for entry in expansion:
                    if not entry[1]:
                        expanded.append((entry[0], None))
                    else:
                        for name in entry[1]:
                            expanded.append((entry[0], name))
                continue

            t = parse_target(arg)
            if t:
                expanded.append((t, arg))
            else:
                spell_suggestion_err_msg(arg)

        judge_errors()

    # Grep
    if args.grep:
        for keyword in args.grep:
            tmp, expanded = expanded, []
            for C, name in tmp:
                if keyword == '':
                    if not name:
                        expanded.append((C, name))
                else:
                    if name and keyword in name:
                        expanded.append((C, name))
            del tmp

    # Sort
    if args.sort == 'index':
        expanded.sort(key=lambda x: int(x[0]) + (isinstance(x[0], lib_colors.ColorRGB) << 8))
    elif args.sort == 'name':
        expanded.sort(key=lambda x: ((isinstance(x[0], lib_colors.ColorRGB)), x[1]))
    elif args.sort == 'rgb':
        expanded.sort(key=lambda x: (x[0].to_rgb() if isinstance(x[0], lib_colors.Color256) else x[0]).rgb)
    elif args.sort == 'hue':
        def to_hsv(x):
            if isinstance(x, lib_colors.ColorHSV):
                return x
            if isinstance(x, lib_colors.ColorRGB):
                return x.to_hsv()
            if isinstance(x, lib_colors.Color256):
                return x.to_rgb().to_hsv()
        expanded.sort(key=lambda x: to_hsv(x[0]).h)
    elif all(ch in 'rgbRGBhsvHSVni' for ch in args.sort):
        def key(x):
            ret = []
            for ch in args.sort:
                try:
                    if ch == 'n':
                        ret.append(x.name)
                    elif ch == 'i':
                        ret.append(x.index)
                    else:
                        ret.append(getattr(x, ch))
                except AttributeError:
                    if ch in 'rgbRGB':
                        ret.append(getattr(x.to_rgb(), ch))
                    if ch in 'hsvHSV':
                        ret.append(getattr(x.to_hsv(), ch))
                    if ch == 'i':
                        ret.append(int(x))
            return ret
        expanded.sort(key=lambda x: key(x[0]))

    inventory = []
    def stage(color, name):
        if name is None:
            name = ''

        m = rere(name)
        if not gradient and m.fullmatch(r'[0-9]+') and not m.fullmatch(r'#?[0-9a-fA-F]{6}'):
            name = ''

        if not args.merge:
            inventory.append((color, [name] if name else []))
            return

        entries = filter(lambda entry: entry[0] == color, inventory)

        try:
            entry = next(entries)
            append = False
            if not entry[1]:
                append = True
            if name and args.merge and name not in entry[1]:
                append = True

            if append:
                entry[1].append(name)

            return

        except StopIteration:
            pass

        inventory.append((color, [name] if name else []))

    for entry in expanded:
        stage(entry[0], entry[1])

    if not inventory:
        print('No colors to query')
        sys.exit(1)

    unmentioned_names = set(lib_colors.names)
    for _, names in inventory:
        unmentioned_names -= set(names)

    aliases = [[] for i in range(256)]
    if args.aliases:
        for name in unmentioned_names:
            c = getattr(lib_colors, name).index
            aliases[c].append(name)

    for this_color, names in inventory[::(-1 if args.reverse else 1)]:
        line = []
        rgb = this_color if isinstance(this_color, lib_colors.ColorRGB) else this_color.to_rgb()
        hsv = rgb.to_hsv()

        if isinstance(this_color, lib_colors.Color256):
            line.append('{:>3}'.format(this_color.index))
        elif isinstance(this_color, lib_colors.ColorRGB):
            line.append('(#)')
        elif isinstance(this_color, lib_colors.ColorHSV):
            line.append('(@)')
        else:
            line.append('(?)')

        for val_fmt in args.val_fmt:
            if val_fmt == 'rgb':
                line.append('({:>3}, {:>3}, {:>3})'.format(*rgb.RGB))

            elif val_fmt == 'hex':
                line.append('{:#X}'.format(rgb))

            elif val_fmt == 'hsv':
                line.append('(@{:>3}, {:>3}%, {:>3}%)'.format(*hsv.HSV))

        line.append(paint(fg=this_color, bg=this_color)('iroiro'))

        line.append(', '.join(names))

        if isinstance(this_color, lib_colors.Color256):
            aliases[this_color.index] = [name
                                         for name in aliases[this_color.index]
                                         if name not in names]
            if aliases[this_color.index]:
                a = ('(' + ', '.join(aliases[this_color.index]) + ')')
                line[-1] = line[-1] + (' ' if line[-1] else '') + a
                aliases[this_color.index] = []

        print(' '.join(line))


def main_hsv(args):
    import shutil
    term_size = shutil.get_terminal_size()
    term_width = term_size.columns
    term_height = term_size.lines

    height = 5
    if term_width < 80:
        width = term_width
    elif term_width > 120:
        width = 120
    else:
        width = 80

    for y in range(0, height):
        line = ''
        for x in range(width):
            hue = (x / width) * 360
            sat = 100
            val1 = lerp(30, 100, (y * 2) / (height*2))
            val2 = lerp(30, 100, (y * 2 + 1) / (height*2))

            bgcolor = lib_colors.ColorHSV(hue, sat, val1)
            color = lib_colors.ColorHSV(hue, sat, val2)
            line += (color / bgcolor)('▄')

        print(line)


def main_tile(args):
    if not args.targets:
        pend_error('No colors to tile')

    judge_errors()

    tiles = [[]]
    for arg in args.targets:
        for token in arg.split('/'):
            if token in ('all', 'named'):
                pend_error('"{}" cannot be used in tile mode'.format(token))
                continue

            t = parse_target(token)
            if not t:
                spell_suggestion_err_msg(token)
                continue

            tiles[-1].append((token, t))

        tiles.append([])

    judge_errors()

    if not tiles[-1]:
        tiles.pop()

    cols, lines = shutil.get_terminal_size()
    cols = args.cols or cols
    lines = args.lines or lines

    if lines < 0:
        lines = len(tiles)

    for idx, is_last in lookahead(resample(range(len(tiles)), lines)):
        colors = tiles[idx]
        widths = []
        quo, rem = divmod(cols, len(colors))
        widths = [quo + (i < rem) for i, elem in enumerate(colors)]
        line = ''
        for idx, textcolor in enumerate(colors):
            text, c = textcolor
            text = text[:widths[idx]]
            line += paint(fg=c, bg=c)(text) + (~c)(' ' * (widths[idx] - len(text)))

        if args.lines:
            print(line)
        else:
            print(line, end='\n' if not is_last else '')

    sys.stdout.flush()

    getch()
