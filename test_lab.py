import copy, json, pathlib, unittest, unicodedata
from core import citation_gate, digest, f1, lexical_baseline, norm, parse_response, prompt, score
from analyze import metrics, paired_delta

ROOT=pathlib.Path(__file__).resolve().parent
DATA=json.loads((ROOT/'data'/'cases.json').read_text(encoding='utf-8'))

class LabTests(unittest.TestCase):
    def test_normalization_preserves_information(self):
        self.assertEqual(norm(unicodedata.normalize('NFD','Hà Nội!')),norm('HÀ NỘI'))
        self.assertNotEqual(norm('má'),norm('ma'))
        self.assertNotEqual(norm('3.3 V'),norm('33 V'))
        self.assertNotEqual(norm('FW-2.7'),norm('FW-27'))
        self.assertEqual(norm('1519.'),'1519')
        self.assertAlmostEqual(f1('a b b','b b c'),2/3)

    def test_prompt_never_uses_gold(self):
        for case in DATA['cases']:
            altered=copy.deepcopy(case)
            altered.update(reference_answers=['GOLD_SENTINEL'],expected_status='GOLD_SENTINEL',reference_evidence=['GOLD_SENTINEL'])
            for strategy in ('direct','cite','verify'):
                self.assertEqual(prompt(case,strategy),prompt(altered,strategy))

    def test_splits_are_grouped(self):
        groups={}
        for c in DATA['cases']:groups.setdefault(c['cluster_id'],set()).add(c['split'])
        self.assertTrue(all(len(v)==1 for v in groups.values()))

    def test_rule_extractor_without_labels(self):
        for c in DATA['cases']:
            if not c['synthetic']:continue
            blind={k:v for k,v in c.items() if k in {'context','question','target'}}
            prediction=lexical_baseline(blind)
            self.assertTrue(score(prediction,c)['correct'],c['case_id'])

    def test_bad_output_not_valid_abstain(self):
        for text in ['not json','[]','{}','{"status":"abstain","answer":"x","evidence":""}',
                     '{"status":"answer","answer":"","evidence":""}']:
            parsed,error=parse_response(text)
            self.assertIsNone(parsed);self.assertIsNotNone(error)
        c=next(c for c in DATA['cases'] if c['expected_status']=='abstain')
        self.assertFalse(score(None,c)['correct'])
        self.assertFalse(score(None,c)['valid'])

    def test_gate_requires_quote_and_answer(self):
        c={'context':'Giá trị là 3.3 V.'}
        good={'status':'answer','answer':'3.3 V','evidence':'Giá trị là 3.3 V.'}
        self.assertEqual(citation_gate(good,c),good)
        for p in [{**good,'evidence':'Đây là câu bịa.'},{**good,'answer':'9.9 V'},{**good,'evidence':''}]:
            self.assertEqual(citation_gate(p,c)['status'],'abstain')
        self.assertIsNone(citation_gate(None,c))

    def test_task_score_balances_failure_modes(self):
        yes={'expected_status':'answer','reference_answers':['3.3 V'],'context':'Giá trị là 3.3 V.'}
        no={**yes,'expected_status':'abstain','reference_answers':[]}
        answer={'status':'answer','answer':'3.3 V','evidence':'Giá trị là 3.3 V.'}
        abstain={'status':'abstain','answer':'','evidence':''}
        self.assertTrue(score(answer,yes)['correct'])
        self.assertTrue(score(answer,no)['unsupported'])
        self.assertTrue(score(abstain,yes)['false_abstention'])
        self.assertTrue(score(abstain,no)['correct'])

    def test_analysis_denominators_and_pairing(self):
        records=[]
        for idx,expected in enumerate(('answer','abstain')):
            c={'expected_status':expected,'reference_answers':['x'] if expected=='answer' else [],'context':'x'}
            records.append({**score({'status':'abstain','answer':'','evidence':''},c),'case_id':str(idx),'cluster_id':'one'})
        m=metrics(records)
        self.assertEqual(m['balanced_accuracy'],.5)
        self.assertEqual(m['unsupported_rate'],0)
        self.assertEqual(m['false_abstention_rate'],1)
        records[1]={**records[1],'valid':False,'correct':False}
        self.assertEqual(metrics(records)['balanced_accuracy'],0)
        self.assertEqual(metrics(records)['failure_rate'],.5)
        delta=paired_delta(records,records,resamples=10)
        self.assertEqual(delta['delta'],0)
        self.assertEqual(delta['paired_clusters'],1)
        with self.assertRaises(ValueError):paired_delta(records,records[:1],resamples=10)

if __name__=='__main__':unittest.main()
