from __future__ import annotations
import json, sys, threading, uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

LOCK=threading.Lock(); PAYMENTS={}
class H(BaseHTTPRequestHandler):
    def log_message(self,*args): pass
    def body(self):
        n=int(self.headers.get('Content-Length','0'));return json.loads(self.rfile.read(n) or b'{}')
    def sendj(self,status,obj):
        raw=json.dumps(obj,ensure_ascii=False).encode();self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
    def do_POST(self):
        if self.path!='/v3/payments': self.sendj(404,{});return
        body=self.body();pid='pay-'+uuid.uuid4().hex[:12]
        saved=bool(body.get('save_payment_method')) or bool(body.get('payment_method_id'))
        obj={'id':pid,'status':'pending' if 'confirmation' in body else 'succeeded','amount':body.get('amount') or {'value':'0.00','currency':'RUB'},'metadata':body.get('metadata') or {},'payment_method':{'id':'pm-test-saved','saved':saved},'confirmation':{'type':'redirect','confirmation_url':f'https://pay.example.test/{pid}'}}
        with LOCK: PAYMENTS[pid]=obj
        self.sendj(200,obj)
    def do_GET(self):
        if self.path.startswith('/v3/payments/'):
            pid=self.path.rsplit('/',1)[-1]
            with LOCK: obj=dict(PAYMENTS.get(pid) or {})
            if not obj: self.sendj(404,{});return
            # Webhook authenticity check in product re-fetches current object; fixture completes payment.
            obj['status']='succeeded';obj['paid']=True
            self.sendj(200,obj);return
        self.sendj(404,{})
if __name__=='__main__': ThreadingHTTPServer(('127.0.0.1',int(sys.argv[1])),H).serve_forever()
