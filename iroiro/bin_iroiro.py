import os
import sys

from os.path import basename

from . import bin


def main():
    prog = basename(sys.argv[0])
    sys.argv = sys.argv[1:]

    arg_idx = None
    for idx, arg in enumerate(sys.argv):
        if arg != 'iro':
            arg_idx = idx
            break

    if arg_idx is None and len(sys.argv) > 2:
        print(
r'''
        ╭────────────────────────────────╮
        │       ╭──────────────────────╮ │
        │       │   ╭────────────────╮ │ │
        │       │   │ RecursionError │ │ │
        │       │   ╰──────┬─────────╯ │ │
        │       │     ,__, ╯           │ │
        │       │   __(..)             │ │
        │       │ ~(  (__)             │ │
        │       │  ||-||               │ │
        │       ╰────┬─────────────────╯ │
        │       ,__, ╯                   │
        │    ___(..)                     │
        │  /(   (__)                     │
        │ ' ||--||                       │
        ╰────────┬───────────────────────╯
            (__) ╯
    _______/(..)
  /(       /(__)
 * | w----||
   ||     ||
''', file=sys.stderr)
        sys.exit(1)

    sys.argv = sys.argv[(arg_idx or 0):]

    if not sys.argv:
        for f in sorted(os.listdir(os.path.dirname(__file__))):
            if f.startswith('bin_') and f.endswith('.py'):
                m = os.path.splitext(f[4:])[0]
                print(m)
        sys.exit(1)

    subcmd = sys.argv[0]

    try:
        getattr(bin, subcmd).main()
    except (AttributeError, ModuleNotFoundError):
        print(f'Unknown subcommand: {subcmd}', file=sys.stderr)
        sys.exit(1)
