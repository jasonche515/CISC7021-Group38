"""Check the canonical revised report against independently recomputed data.

Run cross_check_report.py first. No model inference or PDF compilation is done.
The position-bootstrap bounds are checked only against the committed summary;
this does not independently reproduce the unavailable bootstrap procedure.
"""
import hashlib
import json
import math
import re
import statistics
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'report/final_report_revised.tex'
s = SOURCE.read_text()
audit = json.loads((ROOT / 'Final Report/review_20261112/numeric_audit.json').read_text())
passed = []


def check(condition, detail):
    assert condition, detail
    passed.append(detail)


def table(label):
    found = [t for t in re.findall(r'\\begin\{table\*?\}.*?\\end\{table\*?\}', s, re.S)
             if '\\label{' + label + '}' in t]
    assert len(found) == 1, label
    return found[0]


def rows(label, ampersands):
    return [line.split('&') for line in table(label).splitlines()
            if line.count('&') == ampersands and line.rstrip().endswith('\\\\')][1:]


def number(cell):
    return float(re.sub(r'[^0-9.+-]', '', cell.replace('{,}', '').replace('\\,', '')))


def close(cell, expected, places):
    check(math.isclose(number(cell), float(f'{expected:.{places}f}'), abs_tol=1e-9),
          f'{cell.strip()} matches {expected:.{places}f}')


check(Counter(re.findall(r'\\begin\{([^}]+)\}', s)) ==
      Counter(re.findall(r'\\end\{([^}]+)\}', s)), 'balanced environments')
labels = re.findall(r'\\label\{([^}]+)\}', s)
check(len(labels) == len(set(labels)), 'unique labels')
check(not set(re.findall(r'\\(?:eqref|ref)\{([^}]+)\}', s)) - set(labels), 'all references resolve')
cites = {c for group in re.findall(r'\\cite\w*\{([^}]+)\}', s) for c in group.split(',')}
bib = set(re.findall(r'\\bibitem(?:\[[^]]*\])?\{([^}]+)\}', s))
check(not cites - bib, 'all citations resolve')
for asset in re.findall(r'\\includegraphics(?:\[[^]]*\])?\{([^}]+)\}', s):
    check(any((folder / asset).is_file() for folder in [SOURCE.parent, ROOT / 'figures']),
          'figure exists: ' + asset)

names = ['P1', 'HT2', 'HT4', 'LL2', 'LL4', 'Enh2', 'Enh4']
main = rows('tab:main', 8)
check(len(main) == 7, 'seven historical rows preserved')
for cells, name in zip(main, names):
    a = audit['settings'][name]
    for col, key, places in [(1, 'n', 0), (2, 'em', 4), (3, 'f1', 4),
                             (4, 'f1_sd', 4), (5, 'prompt_tokens', 1),
                             (6, 'token_reduction_pct', 1), (7, 'compression_latency', 3),
                             (8, 'total_latency', 2)]:
        if name == 'P1' and col == 6:
            continue
        close(cells[col], a[key], places)

rerun = rows('tab:rerun', 6)
check(len(rerun) == 5, 'five common-environment rows')
for cells, name in zip(rerun, ['SameP1', 'SameHT2', 'SameHT4', 'SameLL2', 'SameLL4']):
    a = audit['settings'][name]
    for col, key, places in [(1, 'n', 0), (2, 'f1', 4), (3, 'prompt_tokens', 1),
                             (4, 'generation_latency', 3), (6, 'total_latency', 2)]:
        close(cells[col], a[key], places)
    if name != 'SameP1':
        close(cells[5], a['compression_latency'], 3)

remaining = [p for p in audit['paired'] if not p['after'].startswith('Alpaca')]
paired = rows('tab:paired', 3)
check(len(paired) == 12, 'twelve historical paired contrasts')
for cells in paired:
    values = [number(cells[1])] + [float(v) for v in re.findall(r'[+-]?\d+\.\d+', cells[2])]
    matches = [p for p in remaining if values == [float(f"{p['delta']:.4f}"),
               float(f"{p['low']:.3f}"), float(f"{p['high']:.3f}")]]
    check(len(matches) == 1, 'paired contrast ' + cells[0].strip())
    p = matches[0]
    check(('n.s.' in cells[3]) == (p['low'] <= 0 <= p['high']), 'paired verdict')
    remaining.remove(p)
check(not remaining, 'all historical contrasts checked')


def result_rows(name):
    data = json.loads((ROOT / audit['settings'][name]['file']).read_text())['results']
    ratio = int(name[-1]) if name.startswith(('LL', 'Enh', 'Alpaca', 'Matched')) else None
    return {r['id']: r for r in data if ratio is None or r['target_compression_ratio'] == ratio}


base = result_rows('P1')
setup = rows('tab:setup', 3)
check(len(setup) == 8, 'seven settings and rerun setup preserved')
for cells, name in zip(setup, names):
    data = result_rows(name)
    ratio = statistics.mean(base[i]['prompt_tokens'] / r['prompt_tokens'] for i, r in data.items())
    close(cells[2].split('$')[0], ratio, 3)
    path = re.search(r'\\texttt\{([^}]+)\}', cells[3]).group(1).replace('\\_', '_')
    check(path == audit['settings'][name]['file'], 'setup result path ' + name)

matched = rows('tab:matched', 4)
check(len(matched) == 2, 'additional Alpaca table kept separate')
for cells, ratio in zip(matched, (2, 4)):
    ll = audit['settings'][f'Alpaca{ratio}']
    ht = audit['settings'][f'Matched{ratio}']
    close(cells[1], ll['f1'], 4)
    close(cells[2], ht['f1'], 4)
    close(cells[3], ll['prompt_tokens'], 1)
    data = result_rows(f'Alpaca{ratio}')
    close(cells[4], statistics.mean(base[i]['prompt_tokens'] / r['prompt_tokens'] for i, r in data.items()), 4)
    p = next(p for p in audit['paired'] if p['after'] == f'Alpaca{ratio}')
    for key in ['delta', 'low', 'high']:
        check(f"{p[key]:.4f}" in s, 'Alpaca paired ' + key)

zones = rows('tab:zone', 4)
check(len(zones) == 10, 'ten position-zone rows')
for cells in zones:
    ratio = str(int(number(cells[0])))
    zone = cells[1].strip().replace('\\_', '_')
    a = next(a for a in audit['position_groups'] if a['ratio'] == ratio and a['zone'] == zone)
    close(cells[2], a['n'], 0)
    close(cells[3], a['f1'], 4)
    close(cells[4], a['em'], 4)
pooled = rows('tab:pooled', 4)
saved_bounds = (ROOT / 'report/answer_position_stats.tex').read_text()
for cells in pooled:
    ratio = str(int(number(cells[0])))
    zone = {'Kept (head+tail)': 'pooled_kept', 'Partial': 'partial', 'Dropped': 'dropped_middle'}[cells[1].strip()]
    a = next(a for a in audit['position_groups'] if a['ratio'] == ratio and a['zone'] == zone)
    close(cells[2], a['n'], 0)
    close(cells[3], a['f1'], 3)
    saved_line = next(line for line in saved_bounds.splitlines()
                      if line.startswith(ratio + 'x & ' + cells[1].strip().split()[0] + ' &'))
    saved_cells = saved_line.split('&')
    bounds = re.findall(r'\d+\.\d+', cells[4])
    if bounds:
        check([float(b) for b in bounds] == [number(b) for b in saved_cells[-2:]],
              'bootstrap bounds match saved summary only')
    else:
        check('NaN' in saved_line, 'singleton bootstrap interval omitted')

for a in audit['position_groups']:
    if a['zone'] in ['pooled_kept', 'dropped_middle']:
        check(f"{a['same_subset_uncompressed_f1']:.4f}" in s, 'same-id uncompressed subset comparison')
for obsolete in ['43.6', '0.0075', '0.0054', '7{,}026', 'at most 31--42',
                 'gain is an upper bound', 'At equal budget, every']:
    check(obsolete not in s, 'obsolete claim absent: ' + obsolete)
for disclosure in ['7{,}023', 'Coarse context filtering', 'sentence filtering are disabled',
                   '0.0076', '0.0053', '43.5\\%', 'separate stage subprocesses',
                   '288 match exactly', '12 differ', 'generating script, seed and replicate count',
                   'does not recreate the original datasets']:
    check(disclosure in re.sub(r'\s+', ' ', s), 'disclosure: ' + disclosure)

out = {'target': str(SOURCE.relative_to(ROOT)),
       'source_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
       'checks_passed': len(passed), 'checks': passed,
       'limits': ['No model or tokenizer inference rerun',
                  'Position bootstrap generation unavailable; bounds match saved summary only',
                  'Compilation and visual PDF review are separate checks']}
output = ROOT / 'Final Report/review_revised_20261113/source_verification.json'
output.parent.mkdir(exist_ok=True)
output.write_text(json.dumps(out, indent=2) + '\n')
print(f'PASS: {len(passed)} canonical-report checks; {output.relative_to(ROOT)}')
