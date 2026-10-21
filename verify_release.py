"""Verify frozen data/prompts, full run coverage, stored analyses and release checksums."""
import argparse, hashlib, json, pathlib
from core import OPTIONS, SCHEMA, STRATEGIES, SYSTEM, digest
ROOT=pathlib.Path(__file__).resolve().parent
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write-checksums',action='store_true',help='Maintainer step: create a new checksum manifest after deliberate release edits')
    args=parser.parse_args()
    protocol=json.loads((ROOT/'protocol.json').read_text(encoding='utf-8'))
    data=json.loads((ROOT/'data'/'cases.json').read_text(encoding='utf-8'))
    assert protocol['dataset_hash']==digest(data),'Frozen data changed'
    assert protocol['prompt_hash']==digest({'strategies':STRATEGIES,'system':SYSTEM,'schema':SCHEMA,'options':OPTIONS}),'Frozen prompts changed'
    analysis=json.loads((ROOT/'results'/'analysis.json').read_text(encoding='utf-8'))
    assert analysis['complete'] and analysis['recorded_inferences']==816
    assert all(s['complete'] for s in analysis['summaries'])
    assert analysis['dataset_hash']==digest(data)
    assert len([r for r in analysis['records'] if r['strategy']!='baseline'])==1632
    assert all(r['correct'] for r in analysis['records'] if r['model']=='rule_extractor' and r['track']=='controlled_technical')
    assert (ROOT/'reports'/'vietevidence-report.pdf').read_bytes().startswith(b'%PDF')
    assert '/*PAYLOAD*/' not in (ROOT/'index.html').read_text(encoding='utf-8')
    checksums={}
    for path in sorted(ROOT.rglob('*')):
        if path.is_file() and '__pycache__' not in path.parts and path.name!='checksums.json':
            checksums[str(path.relative_to(ROOT)).replace('\\','/')]=hashlib.sha256(path.read_bytes()).hexdigest()
    checksum_path=ROOT/'checksums.json'
    if args.write_checksums:
        checksum_path.write_text(json.dumps(checksums,indent=2)+'\n',encoding='utf-8')
    else:
        assert checksum_path.exists(),'Checksum manifest missing'
        assert json.loads(checksum_path.read_text(encoding='utf-8'))==checksums,'Release checksum mismatch'
    print(json.dumps({'status':'PASS','verified_files':len(checksums),'model_calls':816,'dataset_hash':digest(data)}))
