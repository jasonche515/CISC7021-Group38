"""Check actual final.tex tables, cross-references and corrected statements."""
import hashlib
import json
import math
import re
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
source=ROOT/'report/final.tex'
s=source.read_text(encoding='utf-8-sig')
audit=json.loads((ROOT/'Final Report/review_20261112/numeric_audit.json').read_text())
assert Counter(re.findall(r'\\begin\{([^}]+)\}',s))==Counter(re.findall(r'\\end\{([^}]+)\}',s))
labels=re.findall(r'\\label\{([^}]+)\}',s)
assert len(labels)==len(set(labels))
assert not set(re.findall(r'\\(?:eqref|ref)\{([^}]+)\}',s))-set(labels)
cites={x for group in re.findall(r'\\cite\w*\{([^}]+)\}',s) for x in group.split(',')}
bib=set(re.findall(r'\\bibitem(?:\[[^]]*\])?\{([^}]+)\}',s))
assert not cites-bib
assert not re.findall(r'\\(?:input|include|includegraphics)\b',s)
def table(label):
    return next(t for t in re.findall(r'\\begin\{table\*?\}.*?\\end\{table\*?\}',s,re.S) if '\\label{'+label+'}' in t)
def numeric(cell):
    return float(re.sub(r'[^0-9.+-]','',cell.replace('\\,','').replace('{,}','')))
def close(cell,expected,places):
    assert math.isclose(numeric(cell),float(f'{expected:.{places}f}'),abs_tol=1e-9),(cell,expected)
rows=[line.split('&') for line in table('tab:main').splitlines() if line.count('&')==8 and not line.startswith('Method')]
assert len(rows)==7
for cells,name in zip(rows,['P1','HT2','HT4','LL2','LL4','Enh2','Enh4']):
    a=audit['settings'][name]
    for col,key,places in [(1,'n',0),(2,'em',4),(3,'f1',4),(4,'f1_sd',3),(5,'prompt_tokens',1),(8,'total_latency',2)]:close(cells[col],a[key],places)
rows=[line.split('&') for line in table('tab:latency').splitlines() if line.count('&')==5 and not line.startswith('Method')]
assert len(rows)==5
for cells,name in zip(rows,['SameP1','SameHT2','SameHT4','SameLL2','SameLL4']):
    a=audit['settings'][name]
    for col,key,places in [(1,'f1',4),(3,'generation_latency',3),(4,'total_latency',2)]:close(cells[col],a[key],places)
    if name!='SameP1':
        close(cells[2],a['compression_latency'],3)
        close(cells[5],a['total_latency_change_pct'],1)
historical=[p for p in audit['paired'] if not p['after'].startswith('Alpaca')]
rows=[line.split('&') for line in table('tab:paired').splitlines() if line.count('&')==3 and '95\\%' not in line]
assert len(rows)==12
remaining=list(historical)
for cells in rows:
    vals=[numeric(cells[1])]+[float(v) for v in re.findall(r'[+-]?\d+\.\d+',cells[2])]
    matches=[p for p in remaining if vals==[float(f"{p['delta']:.4f}"),float(f"{p['low']:.3f}"),float(f"{p['high']:.3f}")]]
    assert len(matches)==1,(cells,vals)
    remaining.remove(matches[0])
assert not remaining
assert r'7\,023' in table('tab:data')
for incorrect in ['43.6','0.0075','0.0054',r'7\,026','one process','Only the aggregated rerun table was preserved']:
    assert incorrect not in s,incorrect
assert 'sec:matched' in labels and 'tab:matched' in labels
out={'target':'report/final.tex','source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
     'passed':['seven historical rows','five same-environment rows','twelve paired contrast rows',
               'corrected prompt median','environment balance','unique labels','all references and citations',
               'self-contained TeX plots','supplement separately labelled'],
     'pdf_compiled':False}
(ROOT/'Final Report/review_finaltex_20261112/final_tex_verification.json').write_text(json.dumps(out,indent=2)+'\n')
print('PASS: report/final.tex numeric tables, source structure and references. PDF compilation not performed.')
