#!/usr/bin/env python3
"""Loopback-only dashboard. Approval is local; no application is submitted."""
import json, os, secrets, threading, urllib.error
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
import career_agent as agent
import sources
import source_setup
import ai_workflow
from source_registry import ACTIVE_SOURCES
from scheduler import SearchScheduler

PORT=int(os.environ.get('CAREER_PORT','8765'))
TOKEN=secrets.token_urlsafe(32)
BASE=Path(__file__).resolve().parent/'dashboard'
search_lock=threading.Lock()
QUERIES=['AI automation','AI implementation','AI product manager','автоматизация искусственный интеллект']
def run_search():
    if not search_lock.acquire(False): raise RuntimeError('Search already running')
    try:
        found=[]; errors=[]; counts={}; profile=agent.get_profile()
        keywords=[x.strip() for x in profile.get('keywords','').split(',') if x.strip()][:8]
        terms=keywords or QUERIES[:2]
        selected=agent.get_sources_config()['enabled']
        if not isinstance(selected,list): raise ValueError('Invalid sources')
        tasks=[]
        if 'hh' in selected:
            for term in terms: tasks.append(('hh',lambda term=term:agent.hh(term)))
        for key,fetcher in [('greenhouse',agent.greenhouse),('lever',sources.lever),('ashby',sources.ashby),('smartrecruiters',sources.smartrecruiters)]:
            if key not in selected: continue
            boards=[v.strip() for v in profile.get('boards_'+key,'').split(',') if v.strip()][:15]
            for board in boards: tasks.append((key+':'+board,lambda board=board,fetcher=fetcher:fetcher(board)))
        for name,fetcher in [('remotive',sources.remotive),('arbeitnow',sources.arbeitnow),('hackernews',sources.hackernews)]:
            if name in selected: tasks.append((name,fetcher))
        hh_blocked=False
        for name,fetcher in tasks:
            if name=='hh' and hh_blocked: continue
            try:
                candidates=list(fetcher())
                if name!='hh' and keywords:
                    candidates=[j for j in candidates if any(k.lower() in (j.get('title','')+' '+j.get('description','')).lower() for k in keywords)]
                found.extend(candidates); counts[name]=len(candidates)
            except Exception as e:
                errors.append(f'{name}: {type(e).__name__}: {e}')
                if name=='hh' and isinstance(e,urllib.error.HTTPError) and e.code in (401,403,429): hh_blocked=True
        agent.save(found)
        return {'count':len({(j['source'],j['id']) for j in found}),'counts':counts,'errors':errors}
    finally: search_lock.release()

scheduler=SearchScheduler(run_search)
ai_lock=threading.Lock()
def run_ai():
    if not ai_lock.acquire(False): raise RuntimeError('AI review already running')
    try:
        config=ai_workflow.get_config()
        return ai_workflow.run_once(config['provider'],config['search_first'],run_search)
    finally: ai_lock.release()
ai_scheduler=SearchScheduler(run_ai)

def configure_ai(body):
    config=ai_workflow.save_config(body)
    ai_scheduler.configure(config['enabled'],config['interval_minutes'])
    return {'config':config,'schedule':ai_scheduler.status()}

def start_ai_background():
    ai_workflow.require_profile_share(ai_workflow.get_config()['provider'])
    if ai_lock.locked(): raise ValueError('AI review already running')
    def run():
        try: run_ai()
        except Exception: pass  # The workflow records failures in its local journal.
    threading.Thread(target=run,daemon=True,name='career-ai-review').start()

class Handler(BaseHTTPRequestHandler):
    def allowed(self):
        return self.headers.get('Host') in (f'127.0.0.1:{PORT}',f'localhost:{PORT}')
    def reply(self, code, data, mime='application/json; charset=utf-8'):
        content=data if isinstance(data,bytes) else json.dumps(data,ensure_ascii=False).encode()
        self.send_response(code); self.send_header('Content-Type',mime); self.send_header('Content-Length',str(len(content))); self.send_header('Cache-Control','no-store'); self.send_header('X-Content-Type-Options','nosniff'); self.end_headers(); self.wfile.write(content)
    def do_GET(self):
        if not self.allowed(): return self.reply(403,{'error':'Недопустимый адрес'})
        path=urlparse(self.path).path
        if path=='/api/jobs': return self.reply(200,{'jobs':agent.get_jobs(),'token':TOKEN})
        if path=='/api/runtime': return self.reply(200,{'server_mode':os.environ.get('CAREER_SERVER_MODE')=='1'})
        if path=='/api/schedule': return self.reply(200,scheduler.status())
        if path=='/api/ai': return self.reply(200,{'config':ai_workflow.get_config(),'schedule':ai_scheduler.status(),'runs':ai_workflow.recent_runs(),'running':ai_lock.locked()})
        if path=='/api/profile': return self.reply(200,{'profile':agent.get_profile()})
        if path=='/api/sources': return self.reply(200,{'sources':ACTIVE_SOURCES,**agent.get_sources_config()})
        files={'/':('index.html','text/html; charset=utf-8'),'/app.js':('app.js','text/javascript; charset=utf-8'),'/style.css':('style.css','text/css; charset=utf-8'),'/profile.js':('profile.js','text/javascript; charset=utf-8'),'/ai.js':('ai.js','text/javascript; charset=utf-8')}
        if path not in files: return self.reply(404,{'error':'Не найдено'})
        filename,mime=files[path]; self.reply(200,(BASE/filename).read_bytes(),mime)
    def do_POST(self):
        if not self.allowed() or self.headers.get('Origin') not in (f'http://127.0.0.1:{PORT}',f'http://localhost:{PORT}') or not secrets.compare_digest(self.headers.get('X-Career-Token',''),TOKEN): return self.reply(403,{'error':'Запрос отклонён'})
        try:
            length=int(self.headers.get('Content-Length','0'))
            if length>65536: return self.reply(413,{'error':'Запрос слишком большой'})
            body=json.loads(self.rfile.read(length) or b'{}')
            if self.path=='/api/sources':
                return self.reply(200,agent.save_sources_config(body.get('enabled')))
            if self.path=='/api/source-check':
                return self.reply(200,source_setup.check_source(body.get('source'),body.get('boards','')))
            if self.path=='/api/profile':
                return self.reply(200,{'profile':agent.save_profile(body)})
            if self.path=='/api/decision':
                agent.set_decision(body['source'],body['id'],body['decision']); return self.reply(200,{'ok':True})
            if self.path=='/api/schedule':
                return self.reply(200,scheduler.configure(body.get('enabled'),body.get('interval_minutes')))
            if self.path=='/api/ai': return self.reply(200,configure_ai(body))
            if self.path=='/api/ai/run':
                start_ai_background(); return self.reply(202,{'started':True})
            if self.path=='/api/search':
                return self.reply(200,run_search())
            return self.reply(404,{'error':'Не найдено'})
        except (ValueError,KeyError,TypeError,json.JSONDecodeError) as e: return self.reply(400,{'error':str(e)})
        except Exception as e: return self.reply(500,{'error':str(e)})
    def log_message(self, fmt,*args): pass
if __name__=='__main__':
    print(f'Откройте http://127.0.0.1:{PORT}',flush=True)
    scheduler.start()
    config=ai_workflow.get_config()
    ai_scheduler.configure(config['enabled'],config['interval_minutes'])
    ai_scheduler.start()
    ThreadingHTTPServer(('127.0.0.1',PORT),Handler).serve_forever()
