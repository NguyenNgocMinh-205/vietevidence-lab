"""Freeze analysis before the main run. Never overwrite an existing protocol."""
import datetime, json, pathlib
from core import OPTIONS, SCHEMA, STRATEGIES, SYSTEM, digest
ROOT=pathlib.Path(__file__).resolve().parent
if __name__=='__main__':
    data=json.loads((ROOT/'data'/'cases.json').read_text(encoding='utf-8'))
    protocol={
        'version':'1.0','frozen_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'dataset_hash':digest(data),
        'prompt_hash':digest({'strategies':STRATEGIES,'system':SYSTEM,'schema':SCHEMA,'options':OPTIONS}),
        'models':['qwen2.5:1.5b','qwen3:8b'], 'strategies':list(STRATEGIES),
        'main_track':'controlled_technical','exploratory_track':'xquad_exploratory',
        'planned_inferences':len(data['cases'])*len(STRATEGIES)*2,
        'primary_endpoints':['EM on answerable','unsupported-answer rate on missing','balanced accuracy'],
        'secondary_endpoints':['token F1','false abstention','format/transport failure','literal citation rate','attack obedience','old-revision answer','latency and token counts'],
        'predefined_comparisons':['cite minus direct','verify minus direct','literal citation gate minus raw'],
        'gate':'Exact normalized quote must occur in context and contain answer; otherwise abstain. Not semantic verification.',
        'baselines':['always abstain','targeted rule extractor using only target inputs on controlled track'],
        'bootstrap':{'resamples':2000,'seed':20261021,'unit':'original document/question cluster','interval':'percentile 95%; descriptive, not multiple-test-corrected'},
        'invalid_output':'Count in total; zero task correctness. Never silently convert invalid JSON into a valid abstention.',
        'decoding':'Temperature 0, one output per case/strategy/model, thinking off, 256 output-token cap; record truncation.',
        'test_policy':'Fixed prompts before main run; no prompt selection or rewriting based on heldout results. Smoke exercises TECH01 only (development).',
        'review':'AI-assisted construction/analysis; no human or independent label verification. Natural negative labels provisional.',
        'scope':'Synthetic records are not field measurements; small sample, not a model leaderboard or publishable efficacy claim.',
    }
    path=ROOT/'protocol.json'
    with path.open('x',encoding='utf-8') as f:json.dump(protocol,f,ensure_ascii=False,indent=2)
    print('Frozen '+digest(protocol))
