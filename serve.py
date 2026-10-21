"""Serve the research viewer and optional local-model demo on loopback only."""
import json, pathlib, time, urllib.request
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from core import OPTIONS, SCHEMA, SYSTEM, STRATEGIES, citation_gate, parse_response, prompt

ROOT=pathlib.Path(__file__).resolve().parent
PORT=8766
MODELS={'qwen2.5:1.5b','qwen3:8b'}

class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*args,**kwargs):super().__init__(*args,directory=str(ROOT),**kwargs)
    def log_message(self,*args):pass
    def do_POST(self):
        if self.path!='/api/ask':return self.send_error(404)
        if self.headers.get('Origin') not in (None,f'http://127.0.0.1:{PORT}',f'http://localhost:{PORT}'):
            return self.send_error(403,'Only same-origin requests are allowed')
        try:
            size=int(self.headers.get('Content-Length','0'))
            if not 0<size<=40000:raise ValueError('Request too large or empty')
            if self.headers.get_content_type()!='application/json':raise ValueError('JSON required')
            data=json.loads(self.rfile.read(size))
            model=data.get('model');strategy=data.get('strategy')
            if model not in MODELS or strategy not in STRATEGIES:raise ValueError('Unknown model or strategy')
            case={'context':str(data.get('context','')),'question':str(data.get('question',''))}
            if not 0<len(case['context'])<=10000 or not 0<len(case['question'])<=1000:raise ValueError('Check document/question length')
            body={'model':model,'prompt':prompt(case,strategy),'system':SYSTEM,'stream':False,
                  'think':False,'format':SCHEMA,'options':OPTIONS,'keep_alive':'2m'}
            start=time.monotonic()
            req=urllib.request.Request('http://127.0.0.1:11434/api/generate',data=json.dumps(body,ensure_ascii=False).encode(),headers={'Content-Type':'application/json'})
            with urllib.request.urlopen(req,timeout=240) as response:raw=json.load(response)
            parsed,error=parse_response(raw.get('response',''))
            result={'model':model,'raw_text':raw.get('response',''),'parsed':parsed,'parse_error':error,
                    'gated':citation_gate(parsed,case),'seconds':round(time.monotonic()-start,3),
                    'note':'Ad hoc local demo; not appended to frozen benchmark and not a correctness judgment.'}
            encoded=json.dumps(result,ensure_ascii=False).encode()
            self.send_response(200);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Content-Length',str(len(encoded)));self.end_headers();self.wfile.write(encoded)
        except Exception as exc:
            encoded=json.dumps({'error':str(exc)},ensure_ascii=False).encode()
            self.send_response(400);self.send_header('Content-Type','application/json; charset=utf-8');self.end_headers();self.wfile.write(encoded)

if __name__=='__main__':
    print(f'Viewer: http://127.0.0.1:{PORT} (Ctrl+C to stop)',flush=True)
    ThreadingHTTPServer(('127.0.0.1',PORT),Handler).serve_forever()
