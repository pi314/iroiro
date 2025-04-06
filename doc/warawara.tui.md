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

* Entry
* Loop
* Leave

The "entry" sequence is displayed once, and the "loop" sequence is repeated.

Before the animation finishes, the "leave" sequence is displayed.

* If `icon` is not specified:

  - Entry sequence is set to `⠉ ⠛ ⠿ ⣿ ⠿ ⠛ ⠉ ⠙` (without the white spaces)
  - Loop sequence is set to `⠹ ⢸ ⣰ ⣤ ⣆ ⡇ ⠏ ⠛` (without the white spaces)
  - Leave sequence is set to `⣿`

* If `icon` is a single string, it's used as the loop sequence

  - Entry sequence is set to `''`
  - Leave sequence is set to `.`

* If `icon` contains two strings, they are used as entry and loop sequences, respectively.

  - Leave sequence is set to `.`

* If `icon` contains three strings, they are used as entry, loop, and leave sequences, respectively.

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

If other threads also prints contents on to screen, the output could become a mess.


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

Get a "key" from stdin without waiting for carriage return.

This function is probably very platform dependent.

__Parameters__
```python
getch(timeout=None, encoding='utf8')
```


## `register_key()`
__Parameters__
```python
register_key(seq, *aliases)
```


## `deregister_key()`
__Parameters__
```python
deregister_key(seq)
```
