from __future__ import annotations
import ipaddress,json,os,socket,time,urllib.parse
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from typing import Any
from playwright.sync_api import sync_playwright
HOST=os.getenv('PA_BROWSER_HOST','0.0.0.0');PORT=int(os.getenv('PA_BROWSER_PORT','8000'));MAX_BODY=131072;TIMEOUT=int(os.getenv('PA_BROWSER_TIMEOUT_MS','30000'))
def blocked_ip(v):
 try: ip=ipaddress.ip_address(v.split('%',1)[0])
 except ValueError:return True
 return bool(ip.is_loopback or ip.is_private or ip.is_link_local or ip.is_multicast or ip.is_reserved or ip.is_unspecified)
def validate_url(v):
 p=urllib.parse.urlparse(v.strip())
 if p.scheme not in {'http','https'} or not p.hostname or p.username or p.password:raise ValueError('only public http(s) URLs are allowed')
 host=p.hostname.rstrip('.').lower()
 if host in {'localhost','host.docker.internal','gateway.docker.internal'} or host.endswith('.local'):raise ValueError('local host is blocked')
 infos=socket.getaddrinfo(host,p.port or (443 if p.scheme=='https' else 80),type=socket.SOCK_STREAM);addrs={x[4][0] for x in infos}
 if not addrs or any(blocked_ip(x) for x in addrs):raise ValueError('private/link-local/loopback destination is blocked')
 return urllib.parse.urlunparse(p._replace(fragment=''))
def render(url,max_chars):
 target=validate_url(url)
 with sync_playwright() as pw:
  browser=pw.chromium.launch(headless=True,args=['--no-sandbox','--disable-dev-shm-usage']);ctx=browser.new_context(locale='ru-RU',user_agent='PersonalAgentRusBrowser/0.3');page=ctx.new_page()
  def route_handler(route):
   try:validate_url(route.request.url);route.continue_()
   except Exception:route.abort()
  page.route('**/*',route_handler);page.goto(target,wait_until='domcontentloaded',timeout=TIMEOUT)
  try:page.wait_for_load_state('networkidle',timeout=min(8000,TIMEOUT))
  except Exception:pass
  final=validate_url(page.url);title=page.title().strip()
  try:text=page.locator('body').inner_text(timeout=5000)
  except Exception:text=page.content()
  text='\n'.join(x.strip() for x in text.splitlines() if x.strip())[:max_chars];ctx.close();browser.close();return {'ok':True,'url':final,'title':title,'text':text,'rendered_at':int(time.time())}
class H(BaseHTTPRequestHandler):
 def log_message(self,fmt,*args):
  rid=str(self.headers.get('X-Request-ID') or '')[:128];cid=str(self.headers.get('X-Correlation-ID') or '')[:128];print(f"{time.strftime('%Y-%m-%dT%H:%M:%S')} request_id={rid or '-'} correlation_id={cid or '-'} {fmt%args}",flush=True)
 def sendj(self,status,obj):
  raw=json.dumps(obj,ensure_ascii=False).encode();self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Content-Length',str(len(raw)));self.send_header('Cache-Control','no-store');rid=str(self.headers.get('X-Request-ID') or '').strip();cid=str(self.headers.get('X-Correlation-ID') or '').strip() or rid;
  if rid:self.send_header('X-Request-ID',rid[:128])
  if cid:self.send_header('X-Correlation-ID',cid[:128])
  self.end_headers();self.wfile.write(raw)
 def body(self):
  n=int(self.headers.get('Content-Length','0'))
  if n<=0 or n>MAX_BODY:raise ValueError('invalid request size')
  x=json.loads(self.rfile.read(n).decode());
  if not isinstance(x,dict):raise ValueError('JSON object required')
  return x
 def do_GET(self):
  if urllib.parse.urlparse(self.path).path=='/health':self.sendj(200,{'ok':True,'service':'browser'});return
  self.sendj(404,{'ok':False,'error':'not found'})
 def do_POST(self):
  if urllib.parse.urlparse(self.path).path!='/render':self.sendj(404,{'ok':False,'error':'not found'});return
  try:
   b=self.body();self.sendj(200,render(str(b.get('url','')),max(1000,min(int(b.get('max_chars',120000)),150000))))
  except ValueError as e:self.sendj(400,{'ok':False,'error':str(e)})
  except Exception as e:self.sendj(502,{'ok':False,'error':f'browser failed: {type(e).__name__}: {e}'[:600]})
if __name__=='__main__':ThreadingHTTPServer((HOST,PORT),H).serve_forever()
