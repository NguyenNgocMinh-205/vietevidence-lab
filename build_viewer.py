"""Build a self-contained result explorer. Can be opened offline without dependencies."""
import json, pathlib
ROOT=pathlib.Path(__file__).resolve().parent
if __name__=='__main__':
    data=json.loads((ROOT/'data'/'cases.json').read_text(encoding='utf-8'))
    analysis=json.loads((ROOT/'results'/'analysis.json').read_text(encoding='utf-8'))
    # Serve compact scored outputs; original API responses remain separately available.
    payload={'data':data,'analysis':analysis}
    template=(ROOT/'viewer-template.html').read_text(encoding='utf-8')
    encoded=json.dumps(payload,ensure_ascii=False).replace('<','\\u003c')
    (ROOT/'index.html').write_text(template.replace('/*PAYLOAD*/',encoded),encoding='utf-8')
    print('Built index.html: complete='+str(analysis['complete']))
