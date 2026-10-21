"""Run real local Ollama inference; incremental JSONL, exact provenance, no cloud calls."""
import argparse, datetime, json, pathlib, platform, random, time, urllib.request
from core import OPTIONS, SCHEMA, STRATEGIES, SYSTEM, digest, parse_response, prompt

ROOT=pathlib.Path(__file__).resolve().parent
BASE='http://127.0.0.1:11434'

def request(path,body=None,timeout=240):
    req=urllib.request.Request(BASE+path,data=None if body is None else json.dumps(body,ensure_ascii=False).encode(),
        headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=timeout) as r:return json.load(r)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--models',nargs='+',default=['qwen2.5:1.5b','qwen3:8b'])
    parser.add_argument('--smoke',action='store_true')
    args=parser.parse_args()
    data=json.loads((ROOT/'data'/'cases.json').read_text(encoding='utf-8'))
    if args.smoke:
        cases=[c for c in data['cases'] if c['cluster_id']=='TECH01']
        out=ROOT/'runs'/'smoke.jsonl'
    else:
        cases=data['cases'];out=ROOT/'runs'/'predictions.jsonl'
    out.parent.mkdir(exist_ok=True)
    tags=request('/api/tags')['models']
    model_lookup={m['name']:m for m in tags}
    absent=[m for m in args.models if m not in model_lookup]
    if absent:raise SystemExit('Models missing locally: '+', '.join(absent))
    protocol=json.loads((ROOT/'protocol.json').read_text(encoding='utf-8'))
    if protocol['dataset_hash']!=digest(data) or protocol['prompt_hash']!=digest({'strategies':STRATEGIES,'system':SYSTEM,'schema':SCHEMA,'options':OPTIONS}):
        raise SystemExit('Frozen dataset/prompt protocol mismatch. Create a new version before running.')
    manifest={'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'python':platform.python_version(),'platform':platform.platform(),
        'ollama':request('/api/version'),'models':[model_lookup[m] for m in args.models],
        'dataset_hash':digest(data),'protocol_hash':digest(protocol),'options':OPTIONS,
        'think':False,'format':SCHEMA,'smoke':args.smoke,'independent_requests':True}
    mp=out.with_suffix('.manifest.json')
    if mp.exists():
        previous=json.loads(mp.read_text(encoding='utf-8'))
        for key in ('models','dataset_hash','protocol_hash','options','think','format'):
            if previous[key]!=manifest[key]:raise SystemExit('Resume configuration mismatch: '+key)
    else:mp.write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    existing=[json.loads(line) for line in out.read_text(encoding='utf-8').splitlines() if line.strip()] if out.exists() else []
    done={(r['model'],r['case_id'],r['strategy']) for r in existing}
    if len(done)!=len(existing):raise SystemExit('Duplicate records in existing file')
    total=len(cases)*len(STRATEGIES)*len(args.models)
    start=time.monotonic();count=len(done)
    for model in args.models:
        jobs=[(c,s) for c in cases for s in STRATEGIES]
        random.Random(data['seed']).shuffle(jobs)
        for case,strategy in jobs:
            key=(model,case['case_id'],strategy)
            if key in done:continue
            text=prompt(case,strategy)
            body={'model':model,'system':SYSTEM,'prompt':text,'stream':False,'think':False,
                'format':SCHEMA,'options':OPTIONS,'keep_alive':'10m'}
            wall=time.monotonic();now=datetime.datetime.now(datetime.timezone.utc).isoformat()
            row={'model':model,'model_digest':model_lookup[model]['digest'],'case_id':case['case_id'],
                'strategy':strategy,'prompt_hash':digest({'system':SYSTEM,'prompt':text}),
                'started_utc':now,'attempt':1}
            try:
                raw=request('/api/generate',body)
                # Do not retain optional internal reasoning; thinking is explicitly disabled.
                raw.pop('thinking',None)
                row['raw']=raw
                parsed,error=parse_response(raw.get('response',''))
                row['parsed']=parsed;row['parse_error']=error
                row['transport_error']=None
            except Exception as exc:
                row.update(raw=None,parsed=None,parse_error=None,transport_error=str(exc))
            row['wall_seconds']=time.monotonic()-wall
            with out.open('a',encoding='utf-8') as f:f.write(json.dumps(row,ensure_ascii=False)+'\n')
            done.add(key);count+=1
            if count%12==0 or count==total:
                print(json.dumps({'completed':count,'planned':total,'model':model,'elapsed_seconds':round(time.monotonic()-start,1)}),flush=True)
        request('/api/generate',{'model':model,'keep_alive':0,'stream':False})
    print('Complete: '+str(out),flush=True)

if __name__=='__main__':main()
