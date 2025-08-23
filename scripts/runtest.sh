#!/usr/bin/env sh

COVERAGE_JSON='coverage.json'

'true' '''shell start'

if [ "$1" != '' ]; then
    verbose_flag=--full-trace
fi

if command -v pytest >/dev/null 2>&1 ; then
    rm -f "${COVERAGE_JSON}"
    pytest --cov=iroiro --cov-report=json:"${COVERAGE_JSON}" --cov-report=html ${verbose_flag}
    succ=$?
    if [ ${succ} -eq 0 ]; then
        python3 "$0"
    fi
    rm -f "${COVERAGE_JSON}"
else
    python3 -m unittest --verbose
    succ=$?
fi

exit ${succ}

'true' 'shell end'''

import sys
import json
from os.path import exists

print()

table = [('Name', 'Stmts', 'Miss', 'Branch', 'BrPart', 'Cover')]
def add_entry(name, entry):
    table.append((name,
                  str(entry['num_statements']),
                  str(entry['missing_lines']),
                  str(entry['num_branches']),
                  str(entry['num_partial_branches']),
                  entry['percent_covered_display'] + '%'))

with open(COVERAGE_JSON) as f:
    data = json.load(f)
    for file in sorted(data['files']):
        add_entry(file, data['files'][file]['summary'])
    add_entry('TOTAL', data['totals'])

widths = [0 for col in table[0]]
for entry in table:
    widths = [max(widths[idx], len(text)) for idx, text in enumerate(entry)]

lines = []

for entry in table:
    lines.append('  '.join(
        getattr(text, 'ljust' if idx == 0 else 'rjust')(widths[idx])
        for idx,text in enumerate(entry)
        ))

sepline = '-' * len(lines[0])
lines.insert(1, sepline)
lines.insert(-1, sepline)

for line in lines:
    print(line)

# Name                       Stmts   Miss Branch BrPart  Cover
# ------------------------------------------------------------
# iroiro/bin_ntfy.py            32     24      6      0    21%
# iroiro/bin_palette.py          3      1      0      0    67%
# iroiro/bin_rainbow.py        353    211    202     29    36%
# iroiro/bin_sponge.py          52     43     22      0    12%
# iroiro/bin_iro.py             28      0     12      0   100%
# iroiro/internal_utils.py      13      0      6      0   100%
# iroiro/lib_colors.py         358      0    104      0   100%
# iroiro/lib_fs.py              49      0      8      0   100%
# iroiro/lib_itertools.py       65      0     16      0   100%
# iroiro/lib_math.py           110      0     48      0   100%
# iroiro/lib_regex.py           24      0      2      0   100%
# iroiro/lib_sh.py              40      0      6      0   100%
# iroiro/lib_subproc.py        304      0    130      0   100%
# iroiro/lib_tui.py            229      0     80      0   100%
# ------------------------------------------------------------
# TOTAL                       1660    279    642     29    80%
