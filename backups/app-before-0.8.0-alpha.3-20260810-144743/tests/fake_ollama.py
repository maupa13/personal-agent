from __future__ import annotations
import json, os, sys, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

MODELS={"qwen3:0.6b":523_000_000,"qwen3:8b":5_200_000_000,"<img src=x onerror=window.__parXssAdmin=1>":123}
LOCK=threading.Lock()
LAST={"model":None,"messages":None,"request_id":"","correlation_id":""}
class H(BaseHTTPRequestHandler):
    def log_message(self,*args): pass
    def sendj(self,status,obj):
        raw=json.dumps(obj,ensure_ascii=False).encode('utf-8');self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
    def record_trace(self):
        with LOCK:
            LAST['request_id']=str(self.headers.get('X-Request-ID') or '');LAST['correlation_id']=str(self.headers.get('X-Correlation-ID') or '')
    def body(self):
        n=int(self.headers.get('Content-Length','0'));return json.loads(self.rfile.read(n) or b'{}')
    def do_GET(self):
        if self.path=='/api/tags':
            self.record_trace()
            with LOCK: models=[{"name":k,"size":v} for k,v in MODELS.items()]
            self.sendj(200,{"models":models});return
        if self.path=='/v1/models':
            with LOCK: models=[{'id':k,'object':'model'} for k in MODELS]
            self.sendj(200,{'object':'list','data':models});return
        if self.path=='/test/last':
            with LOCK: state=dict(LAST)
            self.sendj(200,state);return
        self.sendj(404,{})
    def do_POST(self):
        if self.path=='/v1/chat/completions':
            self.record_trace();body=self.body()
            with LOCK:
                LAST['model']=body.get('model');LAST['messages']=body.get('messages')
            self.sendj(200,{'choices':[{'message':{'role':'assistant','content':'PAR_OPENAI_COMPAT_OK'}}],'usage':{'prompt_tokens':21,'completion_tokens':9,'total_tokens':30}});return
        if self.path=='/api/chat':
            self.record_trace();body=self.body()
            with LOCK:
                LAST["model"]=body.get('model');LAST["messages"]=body.get('messages')
            content='PAR_TEST_OK'
            msgs=body.get('messages') or []
            latest_user=next((str(m.get('content','')).strip() for m in reversed(msgs) if isinstance(m,dict) and str(m.get('role','')).lower()=='user'),'')
            system_text=' '.join(str(m.get('content','')) for m in msgs if isinstance(m,dict) and str(m.get('role','')).lower()=='system')
            if latest_user.lower()=='ок':
                content='Хорошо.' if 'ВАЖНО: на этот запрос ответь только на русском языке.' in system_text else 'Hello! How can I assist you today?'
            if any('PAR_XSS' in str(m.get('content','')) for m in msgs if isinstance(m,dict)):
                content='<img src=x onerror=window.__parXss=1>'
            if 'PAR_WEB_BAD_ANSWER' in latest_user:
                content='Вот некоторые источники: SOURCE 1, SOURCE 2'
                if 'Предыдущая попытка была неприемлемой' in system_text:
                    content='Качественная сводка: событие подтверждено несколькими веб-источниками, сырые списки не выведены.'
            self.sendj(200,{"message":{"role":"assistant","content":content},"used":body.get('model'),"prompt_eval_count":17,"eval_count":8});return
        if self.path=='/api/pull':
            body=self.body();model=str(body.get('model') or '')
            with LOCK: MODELS[model]=1_000_000
            lines=[{"status":"pulling manifest"},{"status":"downloading","total":100,"completed":50},{"status":"success","total":100,"completed":100}]
            raw=b''.join(json.dumps(x).encode()+b'\n' for x in lines);self.send_response(200);self.send_header('Content-Type','application/x-ndjson');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw);return
        self.sendj(404,{})
if __name__=='__main__':
    host=os.getenv('PA_FAKE_HOST','127.0.0.1')
    ThreadingHTTPServer((host,int(sys.argv[1])),H).serve_forever()
