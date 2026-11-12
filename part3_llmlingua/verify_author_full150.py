"""Verify the released result bundle and recompute its report values (stdlib only)."""
import hashlib
import json
import math
import statistics as st
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from shared.metrics import score

def read(path):
    return json.loads((ROOT/path).read_text(encoding='utf-8'))

def require(condition, message):
    if not condition:
        raise ValueError(message)

def main():
    manifest_path=ROOT/'ALPACA_MANIFEST.json'
    if manifest_path.exists():
        for name, expected in read('ALPACA_MANIFEST.json')['sha256'].items():
            require(hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==expected, 'Bundle digest mismatch: '+name)
    status=read('part3_llmlingua/author_full150_status.json')
    require(status['state']=='complete','Experiment is incomplete')
    for name,expected in status['frozen_code_sha256'].items():
        require(hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==expected,'Frozen digest mismatch: '+name)
    samples={r['id']:r for r in read('shared/samples.json')['samples']}
    require(len(samples)==150,'Expected 150 unique sources')
    expected={(i,r) for i in samples for r in (2,4)}
    stages={}
    payloads={}
    for stage in ('compressed','results','matched_headtail'):
        payload=read('part3_llmlingua/author_full150_'+stage+'.json')
        rows=payload['results']
        keyed={(r['id'],r['target_compression_ratio']):r for r in rows}
        require(len(rows)==300 and keyed.keys()==expected,'Stage coverage: '+stage)
        stages[stage]=keyed
        payloads[stage]=payload
    gaps=Counter()
    for key in sorted(expected):
        c,a,b=(stages[s][key] for s in ('compressed','results','matched_headtail'))
        for row in (c,a,b):
            source=samples[key[0]]
            require(row['question']==source['question'] and row['answers']==source['answers'],'Changed source/reference: '+str(key))
        for row in (a,b):
            for metric,value in score(row['answer'],samples[key[0]]['answers']).items():
                require(math.isclose(row[metric],value,abs_tol=1e-12),'Score mismatch: '+str(key))
        require(c['compressed_docs']==a['docs'] and c['prompt_tokens']==a['prompt_tokens'],'Compression/evaluation mismatch')
        settings={'compressor_loading_verified':True,'source_text_preserved':True,'compressor_lm_head_key_remapped':True,
                  'recipe':'author_release','compressor_revision':'c98caccd9a60bc04b92c07e93966a72ee5173a95',
                  'iterative_size':100,'context_budget':'*2','rank_method':'llmlingua',
                  'use_sentence_level_filter':False,'use_token_level_filter':True}
        require(all(c.get(k)==v for k,v in settings.items()),'Frozen recipe mismatch: '+str(key))
        gap=a['prompt_tokens']-b['prompt_tokens']
        require(gap in (0,1) and gap==b['budget_gap_tokens'],'Budget mismatch: '+str(key))
        gaps[gap]+=1
    print('PASS: source/data hashes, 300 rows per stage, 600 answer scores and actual budgets')
    print('Requested | LL F1 | HT F1 | LL EM | LL tokens | HT tokens | actual ratio | LL-HT [approx 95% CI]')
    for ratio in (2,4):
        aa=[stages['results'][(i,ratio)] for i in samples]
        bb=[stages['matched_headtail'][(i,ratio)] for i in samples]
        dif=[a['f1']-b['f1'] for a,b in zip(aa,bb)]
        avg=st.mean(dif); margin=1.96*st.stdev(dif)/math.sqrt(150)
        for stage,rows in [('results',aa),('matched_headtail',bb)]:
            summary=payloads[stage]['summary'][f'{ratio}x']
            for metric in ('f1','em','prompt_tokens'):
                require(math.isclose(summary['mean_'+metric],st.mean(r[metric] for r in rows),abs_tol=1e-12),'Stored summary mismatch')
        print(f"{ratio}x | {st.mean(a['f1'] for a in aa):.4f} | {st.mean(b['f1'] for b in bb):.4f} | "
              f"{st.mean(a['em'] for a in aa):.4f} | {st.mean(a['prompt_tokens'] for a in aa):.1f} | "
              f"{st.mean(b['prompt_tokens'] for b in bb):.1f} | "
              f"{st.mean(a['original_prompt_tokens']/a['prompt_tokens'] for a in aa):.4f} | "
              f"{avg:+.4f} [{avg-margin:+.4f}, {avg+margin:+.4f}]")
    print('Token gap counts:',dict(sorted(gaps.items())))
    print('Token counts and source-preservation flags are audited recorded values; tokenizer/weight execution is not rerun.')

if __name__=='__main__':
    main()
