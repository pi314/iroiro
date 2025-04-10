# warawara.tui

This document describes the API set provided by `warawara.tui`.

For the index of this package, see [warawara.md](warawara.md).


## `strwidth()`

Return the "display width" of the string.

__Parameters__
```python
strwidth(s)
```

Printable ASCII characters are counted as width 1, and CJK characters are counted as width 2.

Color escape sequences are ignored.

__Examples__
```python
assert strwidth('test') == 4
assert strwidth('\033[38;5;214mtest\033[m') == 4
assert strwidth('哇嗚') == 4
```


## `ljust()` / `rjust()`

`ljust` and `rjust` `data` based on `strwidth()`.

__Parameters__
```python
ljust(data, width=None, fillchar=' ')
rjust(data, width=None, fillchar=' ')
```

If `data` is a `str`, the behavior is similar to `str.ljust` and `str.rjust`.

```python
assert ljust('test', 10) == 'test      '
assert rjust('test', 10) == '      test'
```

If `data` is a 2-dimensional list of `str`, each columns are aligned separately.

```python
data = [
    ('column1', 'col2'),
    ('word1', 'word2'),
    ('word3', 'word4 long words'),
    ]

assert ljust(data) == [
    ('column1', 'col2            '),
    ('word1  ', 'word2           '),
    ('word3  ', 'word4 long words'),
    ]
```


## Class `ThreadedSpinner`

Display a pipx-inspired spinner on screen in a daemon thread.

__Parameters__
```python
ThreadedSpinner(*icon, delay=0.1)
```

Three sequences of icons are defined for different displaying phase:

*   Entry
*   Loop
*   Leave

The "entry" sequence is displayed once, and the "loop" sequence is repeated.  
Before the animation finishes, the "leave" sequence is displayed.

*   If `icon` is not specified:

    -   Entry sequence is set to `⠉ ⠛ ⠿ ⣿ ⠿ ⠛ ⠉ ⠙` (without the white spaces)
    -   Loop sequence is set to `⠹ ⢸ ⣰ ⣤ ⣆ ⡇ ⠏ ⠛` (without the white spaces)
    -   Leave sequence is set to `⣿`

*   If `icon` is a single string, it's used as the loop sequence

    -   Entry sequence is set to `''`
    -   Leave sequence is set to `.`

*   If `icon` contains two strings, they are used as entry and loop sequences, respectively.

    -   Leave sequence is set to `.`

*   If `icon` contains three strings, they are used as entry, loop, and leave sequences, respectively.

__Examples__
```python
spinner = ThreadedSpinner()

with spinner:
    # do some work that takes time
    spinner.text('new content')
    spinner.text('newer content')

spinner.start()
spinner.text('some text')
spinner.end()
spinner.join()
```

Note that `ThreadedSpinner` uses control sequences to redraw its content in terminal.

If other threads also print contents on to screen, the output could be messed up.


## `prompt()`

Prompt a message and wait for user input.

__Parameters__
```python
prompt(question, options=tuple(),
       accept_empty=True,
       abbr=True,
       ignorecase=None,
       sep=' / ',
       suppress=(EOFError, KeyboardInterrupt))
```

*   `question`: the message printed on screen
*   `accept_empty`: accept empty string, otherwise keep asking
*   `abbr`: show abbreviations of the options
*   `ignorecase`: ignorecase
*   `sep`: set the separator between options
*   `suppress`: exception type list that being suppressed

In the simplest form, it could be used like `input()`:
```python
user_input = prompt('Input anything to continue>')
```

If `options` is specified, user is prompted to choose one from it:
```python
yn = prompt('Do you like warawara, or do you not like it?', ('yes', 'no'))
print("You've replied:", yn)
```
User is prompted with a message like this (`_` represents the cursor):
```
Do you like warawara, or do you not like it? [(Y)es / (n)o] _
```
In this case, `yes`, `no`, `y`, `n`, and empty string are accepted and returned.

All other inputs are ignored and the prompt repeats:
```
Do you like warawara, or do you not like it? [(Y)es / (n)o] what
Do you like warawara, or do you not like it? [(Y)es / (n)o] why
Do you like warawara, or do you not like it? [(Y)es / (n)o] #
Do you like warawara, or do you not like it? [(Y)es / (n)o] yes
You've replied: yes
```

The returned object contains the `rstrip()` user input.

It overloads `__eq__()` and allows you to compare it with equivalent values:

```python
assert yn == 'yes'
assert yn == 'Yes'
assert yn == 'YES'
assert yn == ''
assert yn != 'no'
```

In this example, `accept_empty=True`, so empty string is treated as equal
to the first option specified, i.e. `'yes'`.

Similarly, if user input an empty string, both `yn == 'yes'` and `yn == ''` evaluates to `True`.

If user triggers `EOFError` or `KeyboardInterrupt`,
it will be suppressed and make `yn` stores `None`.

`yn.selected` stores the user input, so you could distinguish `yes` and `''`.


## `getch()`

Get a "character" from stdin without waiting for carriage return.

A character (represents by [`Key`](#key) class described below) could be

*   A printable ASCII character (e.g. a-z, A-Z, comma, underscore, etc)
*   A multi-byte control sequence (e.g. arrow keys)
*   A unicode character (e.g. '😂')
*   Any sequences that does not prefix-match others that are recognized as a key

This function is probably very platform dependent.

__Parameters__
```python
getch(timeout=None, encoding='utf8')
```

`getch()` use a heuristic logic to decide whether to get another byte from stdin.

Roughly speaking, it tries to match the longest sequence that is registered through [`register_key()`](#register_key).

If none of them perfectly matches, it tries to get enough bytes that are decodable in `encoding`.

*   `timeout` specifies the waiting time if stdin is empty
    -   If stdin keep being empty during timeout, `None` is returned

`timeout` only applies to the first check, not in between every byte reads.


## Class `Key`

A class representing a key ("character".)

`Key.seq` stores the byte sequence of the key.

`Key.alises` stores the aliases of the key in `list[str]`.

When comparing a `Key` object (say `self`) with the other object, say `rhs`,

*   If `rhs` is also a `Key`, `self.seq` and `rhs.seq` are compared.
*   If `rhs` is a `bytes`, `self.seq` and `rhs` are compared.
*   If `rhs` is a `str`, `self.seq` and `rhs.encode('utf8')` are compared.
*   Otherwise, `rhs in self.aliases` is returned.

__Examples__
```python
KEY_ESCAPE = Key(b'\033', 'esc', 'escape')
assert KEY_ESCAPE == b'\033'
assert KEY_ESCAPE == 'esc'
assert KEY_ESCAPE == 'escape'
```

The following keys are pre-defined by warawara:

| Name                                        | Sequence              | Aliases                                   |
|---------------------------------------------|-----------------------|-------------------------------------------|
| `KEY_ESCAPE`                                | `b'\033'`             | `'esc'`, `'escape'`                       |
| `KEY_BACKSPACE`                             | `b'\x7f'`             | `'backspace'`                             |
| `KEY_TAB`                                   | `b'\t'`               | `'tab'`, `'ctrl-i'`, `'ctrl+i'`, `'^I'`   |
| `KEY_ENTER`                                 | `b'\r'`               | `'enter'`, `'ctrl-m'`, `'ctrl+m'`, `'^M'` |
| `KEY_SPACE`                                 | `b' '`                | `'space'`                                 |
| `KEY_UP`                                    | `b'\033[A'`           | `'up'`                                    |
| `KEY_DOWN`                                  | `b'\033[B'`           | `'down'`                                  |
| `KEY_RIGHT`                                 | `b'\033[C'`           | `'right'`                                 |
| `KEY_LEFT`                                  | `b'\033[D'`           | `'left'`                                  |
| `KEY_HOME`                                  | `b'\033[1~'`          | `'home'`                                  |
| `KEY_END`                                   | `b'\033[4~'`          | `'end'`                                   |
| `KEY_PGUP`                                  | `b'\033[5~'`          | `'pgup'`, `'pageup'`                      |
| `KEY_PGDN`                                  | `b'\033[6~'`          | `'pgdn'`, `'pagedown'`                    |
| `KEY_CTRL_#` (`a` ~ `z` except `i` and `m`) | `b'\x01'` ~ `b'\x1a'` | `'ctrl-#'`, `'ctrl+#'`, `'^#'`            |
| `KEY_F1`                                    | `b'\033OP'`           | `'F1'`                                    |
| `KEY_F2`                                    | `b'\033OQ'`           | `'F2'`                                    |
| `KEY_F3`                                    | `b'\033OR'`           | `'F3'`                                    |
| `KEY_F4`                                    | `b'\033OS'`           | `'F4'`                                    |
| `KEY_F5`                                    | `b'\033[15~'`         | `'F5'`                                    |
| `KEY_F6`                                    | `b'\033[17~'`         | `'F6'`                                    |
| `KEY_F7`                                    | `b'\033[18~'`         | `'F7'`                                    |
| `KEY_F8`                                    | `b'\033[19~'`         | `'F8'`                                    |
| `KEY_F9`                                    | `b'\033[20~'`         | `'F9'`                                    |
| `KEY_F10`                                   | `b'\033[21~'`         | `'F10'`                                   |
| `KEY_F11`                                   | `b'\033[23~'`         | `'F11'`                                   |
| `KEY_F12`                                   | `b'\033[24~'`         | `'F12'`                                   |


## `register_key()`

Register a sequence with specified aliases.

__Parameters__
```python
register_key(seq, *aliases)
```

`seq` could be in `bytes` or `str`; If it's `str`, `seq.encode('utf8')` is used.

`aliases` are names in `str`, see [Key](#class-key) about how Key object treat them.

The corresponding `Key` object, either newly created or a existing one, is returned.

__Examples__
```python
key = register_key('abcd', 'ABCD')
user_input = getch()
```
In the above example, you have to input `'abcd'` extremely fast for it to be detected.
Or just paste `'abcd'` and hope it would work.


## `deregister_key()`

Deregister a sequene from key table.

The deregistered key object is returned.

__Parameters__
```python
deregister_key(seq)
```

__Examples__
```python
key = deregister_key(seq)
assert key.seq == seq
```
