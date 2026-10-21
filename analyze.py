"""Analyze all recorded predictions, keeping tracks/splits distinct and clusters paired."""
import collections, csv, json, pathlib, random, statistics
from core import STRATEGIES, SYSTEM, citation_gate, digest, lexical_baseline, parse_response, prompt, score

ROOT=pathlib.Path(__file__).resolve().parent

def mean(values):return sum(values)/len(values) if values else None
def quantile(vals,p):
    vals=sorted(vals);q=(len(vals)-1)*p;i=int(q)
    return vals[i]+(vals[min(i+1,len(vals)-1)]-vals[i])*(q-i)

def metrics(records):
    answerable=[r for r in records if r['expected_answer']]
    missing=[r for r in records if not r['expected_answer']]
    attempted=[r for r in records if r['answered']]
    acc=mean([r['em'] for r in answerable])
    refusal=mean([r['valid'] and not r['answered'] for r in missing])
    return {'n':len(records),'answerable_n':len(answerable),'missing_n':len(missing),
        'em':acc,'f1':mean([r['f1'] for r in answerable]),
        'unsupported_rate':mean([r['unsupported'] for r in missing]),
        'correct_abstention_rate':refusal,
        'false_abstention_rate':mean([r['false_abstention'] for r in answerable]),
        'failure_rate':mean([not r['valid'] for r in records]),
        'balanced_accuracy':(acc+refusal)/2 if acc is not None and refusal is not None else None,
        'overall_accuracy':mean([r['correct'] for r in records]),
        'coverage':len(attempted)/len(records) if records else None,
        'selective_error':mean([not r['correct'] for r in attempted]),
        'quote_exists_rate':mean([r['quote_exists'] for r in attempted]),
        'old_revision_count':sum(r['old_revision_answer'] for r in records),
        'attack_obedience_count':sum(r['attack_obeyed'] for r in records)}

def bootstrap(records,metric,resamples=2000):
    groups=collections.defaultdict(list)
    for r in records:groups[r['cluster_id']].append(r)
    names=sorted(groups);rng=random.Random(20261021);values=[]
    for _ in range(resamples):
        sample=[r for name in rng.choices(names,k=len(names)) for r in groups[name]]
        result=metrics(sample)[metric]
        if result is not None:values.append(result)
    return [quantile(values,.025),quantile(values,.975)] if values else None

def paired_delta(left,right,metric='balanced_accuracy',resamples=2000):
    l={r['case_id']:r for r in left};r={x['case_id']:x for x in right}
    if set(l)!=set(r):raise ValueError('Comparisons must have identical case IDs')
    groups=collections.defaultdict(list)
    for k,item in l.items():groups[item['cluster_id']].append(k)
    names=sorted(groups);rng=random.Random(20261021);values=[]
    for _ in range(resamples):
        ids=[k for name in rng.choices(names,k=len(names)) for k in groups[name]]
        a,b=metrics([l[k] for k in ids])[metric],metrics([r[k] for k in ids])[metric]
        if a is not None and b is not None:values.append(b-a)
    point=metrics(right)[metric]-metrics(left)[metric]
    return {'delta':point,'ci95':[quantile(values,.025),quantile(values,.975)],'paired_clusters':len(names)}

def main():
    payload=json.loads((ROOT/'data'/'cases.json').read_text(encoding='utf-8'))
    cases={c['case_id']:c for c in payload['cases']}
    path=ROOT/'runs'/'predictions.jsonl'
    raw=[json.loads(x) for x in path.read_text(encoding='utf-8').splitlines() if x.strip()]
    protocol=json.loads((ROOT/'protocol.json').read_text(encoding='utf-8'))
    manifest=json.loads((ROOT/'runs'/'predictions.manifest.json').read_text(encoding='utf-8'))
    if manifest['dataset_hash']!=digest(payload) or manifest['protocol_hash']!=digest(protocol):raise ValueError('Run provenance does not match data/protocol')
    model_digests={m['name']:m['digest'] for m in manifest['models']}
    records=[];seen=set()
    for row in raw:
        key=(row['model'],row['case_id'],row['strategy'])
        if key in seen:raise ValueError('Duplicate prediction '+str(key))
        seen.add(key);c=cases[row['case_id']]
        if row['model'] not in protocol['models'] or row['strategy'] not in STRATEGIES:raise ValueError('Unknown model or strategy')
        if row['model_digest']!=model_digests[row['model']]:raise ValueError('Model digest mismatch')
        if row['prompt_hash']!=digest({'system':SYSTEM,'prompt':prompt(c,row['strategy'])}):raise ValueError('Prompt provenance mismatch')
        parsed,error=parse_response(row['raw']['response']) if row['raw'] else (None,'transport error')
        if parsed!=row['parsed']:raise ValueError('Stored parse does not match raw response')
        for gate in ('raw','literal_gate'):
            prediction=parsed if gate=='raw' else citation_gate(parsed,c)
            records.append({**score(prediction,c),'case_id':c['case_id'],'cluster_id':c['cluster_id'],
                'model':row['model'],'strategy':row['strategy'],'gate':gate,'track':c['track'],
                'split':c['split'],'condition':c['condition'],'wall_seconds':row['wall_seconds'],
                'prediction':prediction,'transport_error':row['transport_error'],'parse_error':error,
                'truncated':bool(row['raw'] and row['raw'].get('done_reason')=='length')})
    # Deterministic baselines require no model and have no access to reference labels.
    for c in cases.values():
        for name,prediction in [('always_abstain',{'status':'abstain','answer':'','evidence':''}),('rule_extractor',lexical_baseline(c))]:
            records.append({**score(prediction,c),'case_id':c['case_id'],'cluster_id':c['cluster_id'],
                'model':name,'strategy':'baseline','gate':'raw','track':c['track'],'split':c['split'],
                'condition':c['condition'],'wall_seconds':None,'prediction':prediction,
                'transport_error':None,'parse_error':None,'truncated':False})
    grouped=collections.defaultdict(list)
    for r in records:grouped[(r['track'],r['split'],r['model'],r['strategy'],r['gate'])].append(r)
    summaries=[]
    for key,rows in sorted(grouped.items()):
        track,split,model,strategy,gate=key
        s={'track':track,'split':split,'model':model,'strategy':strategy,'gate':gate,**metrics(rows)}
        s['clusters']=len({r['cluster_id'] for r in rows})
        s['planned_n']=sum(c['track']==track and c['split']==split for c in cases.values())
        s['complete']=s['n']==s['planned_n']
        s['balanced_ci95']=bootstrap(rows,'balanced_accuracy')
        s['conditions']={name:metrics([r for r in rows if r['condition']==name]) for name in sorted({r['condition'] for r in rows})}
        times=[r['wall_seconds'] for r in rows if r['wall_seconds'] is not None]
        s['median_wall_seconds']=statistics.median(times) if times else None
        s['truncated_count']=sum(r['truncated'] for r in rows)
        summaries.append(s)
    comparisons=[]
    for track,split,model in sorted({(r['track'],r['split'],r['model']) for r in records if r['strategy']!='baseline'}):
        for strategy in ('cite','verify'):
            left=grouped[(track,split,model,'direct','raw')];right=grouped[(track,split,model,strategy,'raw')]
            if left and right and {r['case_id'] for r in left}=={r['case_id'] for r in right}:
                comparisons.append({'track':track,'split':split,'model':model,'comparison':strategy+' minus direct',**paired_delta(left,right)})
        for strategy in ('direct','cite','verify'):
            left=grouped[(track,split,model,strategy,'raw')];right=grouped[(track,split,model,strategy,'literal_gate')]
            if left and right:comparisons.append({'track':track,'split':split,'model':model,'comparison':strategy+' gate minus raw',**paired_delta(left,right)})
    expected=protocol['planned_inferences']
    expected_keys={(m,c,s) for m in protocol['models'] for c in cases for s in STRATEGIES}
    result={'project':payload['project'],'dataset_hash':digest(payload),'recorded_inferences':len(raw),
        'planned_inferences':expected,'complete':seen==expected_keys,'summaries':summaries,
        'comparisons':comparisons,'records':records,
        'notes':['Bootstrap intervals are descriptive cluster intervals, not proof of generalization or corrected significance.',
                 'No independent human label review. Synthetic facts are fictional; XQuAD negatives provisional.',
                 'Quote existence does not prove semantic support. Gate reuses outputs and is not another model run.',
                 'Models differ in generation and size: no causal claim that parameter count alone explains differences.']}
    dest=ROOT/'results';dest.mkdir(exist_ok=True)
    (dest/'analysis.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    with (dest/'summary.csv').open('w',encoding='utf-8-sig',newline='') as f:
        flat=[{k:v for k,v in s.items() if k!='conditions'} for s in summaries]
        w=csv.DictWriter(f,fieldnames=list(flat[0]));w.writeheader();w.writerows(flat)
    print(json.dumps({'recorded':len(raw),'planned':expected,'complete':result['complete'],'groups':len(summaries)}))

if __name__=='__main__':main()
