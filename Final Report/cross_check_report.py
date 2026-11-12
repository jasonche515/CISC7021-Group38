"""Independent numeric review of GitHub report at 894aab6 (no model inference)."""
import csv
import hashlib
import json
import math
import statistics as st
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from shared.metrics import score

OUT = Path(__file__).resolve().parent / 'review_20261112'
OUT.mkdir(exist_ok=True)
samples = {r['id']: r for r in json.loads((ROOT/'shared/samples.json').read_text())['samples']}
audit = {'reviewed_commit': '894aab6b428c3664125fd77ded90101e153390ac',
         'numeric_checks': [], 'settings': {}, 'paired': [], 'position_groups': []}
def read(p):
    return json.loads((ROOT/p).read_text())
def check(ok, detail):
    if not ok:
        raise AssertionError(detail)
    audit['numeric_checks'].append(detail)
def summarize(label, rows, path, summary=None):
    check(len(rows)==150 and {r['id'] for r in rows}==samples.keys(), label+': 150 unique shared ids')
    for r in rows:
        source=samples[r['id']]
        check(r['question']==source['question'] and r['answers']==source['answers'], label+': source '+r['id'])
        expected=score(r['answer'],source['answers'])
        check(all(math.isclose(r[k],expected[k],abs_tol=1e-12) for k in expected), label+': score '+r['id'])
    result={'n':150,'em':st.mean(r['em'] for r in rows),'f1':st.mean(r['f1'] for r in rows),
            'f1_sd':st.stdev(r['f1'] for r in rows),'prompt_tokens':st.mean(r['prompt_tokens'] for r in rows),
            'empty_docs':sum(not r.get('docs') for r in rows),'file':path}
    for k in ('compression_latency','generation_latency','total_latency'):
        vals=[r[k] for r in rows if r.get(k) is not None]
        if vals: result[k]=st.mean(vals)
    if summary:
        for k in ('em','f1','prompt_tokens','compression_latency','generation_latency','total_latency'):
            if summary.get('mean_'+k) is not None and k in result:
                check(math.isclose(summary['mean_'+k],result[k],abs_tol=1e-10),label+': stored mean '+k)
    audit['settings'][label]=result
    return {r['id']:r for r in rows}
groups={}
for label,path in [('P1','part1_uncompressed/results_member1.json'),('HT2','part2_truncation/results_member2_2x.json'),('HT4','part2_truncation/results_member2_4x.json')]:
    d=read(path); groups[label]=summarize(label,d['results'],path,d['summary'])
for prefix,path in [('LL','part3_llmlingua/results_member3.json'),('Enh','part4_llmlingua_enhanced/results_member4.json'),('Alpaca','part3_llmlingua/author_full150_results.json'),('Matched','part3_llmlingua/author_full150_matched_headtail.json')]:
    d=read(path)
    for ratio in (2,4):
        label=prefix+str(ratio)
        groups[label]=summarize(label,[r for r in d['results'] if r['target_compression_ratio']==ratio],path,d['summary'][f'{ratio}x'])
for label,path in [('SameP1','results_same_machine/results_member1.json'),('SameHT2','results_same_machine/results_member2_2x.json'),('SameHT4','results_same_machine/results_member2_4x.json'),('SameLL','results_same_machine/results_member3.json')]:
    d=read(path)
    if label=='SameLL':
        for ratio in (2,4):
            groups[label+str(ratio)]=summarize(label+str(ratio),[r for r in d['results'] if r['target_compression_ratio']==ratio],path,d['summary'][f'{ratio}x'])
    else: groups[label]=summarize(label,d['results'],path,d['summary'])
for before,after in [('P1',x) for x in ('HT2','HT4','LL2','LL4','Enh2','Enh4')]+[(f'{a}{r}',f'{b}{r}') for r in (2,4) for a,b in [('HT','LL'),('LL','Enh'),('HT','Enh'),('Matched','Alpaca')]]:
    dif=[groups[after][i]['f1']-groups[before][i]['f1'] for i in samples]
    mean=st.mean(dif); margin=1.96*st.stdev(dif)/math.sqrt(150)
    audit['paired'].append({'before':before,'after':after,'delta':mean,'low':mean-margin,'high':mean+margin,
                            'wins':sum(d>1e-10 for d in dif),'ties':sum(abs(d)<=1e-10 for d in dif),'losses':sum(d < -1e-10 for d in dif)})
base_tokens=audit['settings']['P1']['prompt_tokens']
for label,v in audit['settings'].items():
    v['token_reduction_pct']=100*(1-v['prompt_tokens']/base_tokens)
    if label.startswith('Same'):
        v['total_latency_change_pct']=100*(v['total_latency']/audit['settings']['SameP1']['total_latency']-1)
for r in (2,4):
    gaps=Counter(groups[f'Alpaca{r}'][i]['prompt_tokens']-groups[f'Matched{r}'][i]['prompt_tokens'] for i in samples)
    check(set(gaps)<= {0,1},f'Alpaca{r}: all actual token budgets within one token')
    audit[f'matched_token_gaps_{r}']=dict(gaps)
positions=list(csv.DictReader((ROOT/'report/answer_position_analysis.csv').open()))
for ratio in ('2','4'):
    rows=[r for r in positions if r['ratio']==ratio]
    check(len(rows)==150 and {r['id'] for r in rows}==samples.keys(),'Position '+ratio+': complete ids')
    for r in rows:
        raw=groups['HT'+ratio][r['id']]
        check(all(math.isclose(float(r[k]),raw[k],abs_tol=1e-12) for k in ('f1','em','prompt_tokens')),'Position '+ratio+': raw values '+r['id'])
    audit['position_match_counts_'+ratio]=dict(Counter(r['match_type'] for r in rows))
    for zone in sorted({r['answer_zone'] for r in rows})+['pooled_kept']:
        rr=[r for r in rows if r['answer_zone'].startswith('kept')] if zone=='pooled_kept' else [r for r in rows if r['answer_zone']==zone]
        audit['position_groups'].append({'ratio':ratio,'zone':zone,'n':len(rr),
             'f1':st.mean(float(r['f1']) for r in rr),'em':st.mean(float(r['em']) for r in rr),
             'same_subset_uncompressed_f1':st.mean(groups['P1'][r['id']]['f1'] for r in rr)})
audit['literal_answer_matches']=sum(any(a in s['docs'] for a in s['answers']) for s in samples.values())
audit['case_insensitive_literal_answer_matches']=sum(any(a.lower() in s['docs'].lower() for a in s['answers']) for s in samples.values())
status=read('part3_llmlingua/author_full150_status.json')
for p,digest in status['frozen_code_sha256'].items():
    check(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==digest,'Frozen SHA256 '+p)
# Historical files used for the GitHub report must match the pinned remote blobs.
for p in sorted({v['file'] for k,v in audit['settings'].items() if not k.startswith(('Alpaca','Matched'))}):
    actual=subprocess.check_output(['git','hash-object',p],cwd=ROOT,text=True).strip()
    expected=subprocess.check_output(['git','rev-parse',audit['reviewed_commit']+':'+p],cwd=ROOT,text=True).strip()
    check(actual==expected,'Matches reviewed GitHub data blob: '+p)
audit['checks_passed']=len(audit['numeric_checks'])
(OUT/'numeric_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n')
print('PASS:',audit['checks_passed'],'checks; answer metrics recomputed for',len(groups)*150,'records')
for k,v in audit['settings'].items(): print(k, 'F1',f"{v['f1']:.4f}",'tokens',f"{v['prompt_tokens']:.1f}",'latency change',v.get('total_latency_change_pct'))
print('Literal answer matches:',audit['literal_answer_matches'])
