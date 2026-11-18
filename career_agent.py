#!/usr/bin/env python3
"""Local, read-only job discovery. No candidate data is sent to sources."""
import argparse, html, json, re, sqlite3, sys, urllib.request, os
from datetime import datetime, timezone
from contextlib import closing
from urllib.parse import urlencode

DB = os.environ.get('CAREER_DB_PATH') or os.path.join(os.path.dirname(os.path.abspath(__file__)), 'jobs.sqlite3')
HEADERS = {'User-Agent': os.environ.get('CAREER_USER_AGENT', 'CareerAgent/0.3 (local job search)'), 'Accept': 'application/json'}
TERMS = ('automation','implementation','solutions','transformation','workflow','operations','agent','автоматизац','внедрен','трансформац')
AI = (' ai ', 'artificial intelligence', 'machine learning',' llm','искусственн',' ии ')
def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=30) as r:
        return json.load(r)
def clean(s):
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]*>', ' ', s or ''))).strip()
def score(job, profile=None):
    if profile and profile.get('keywords','').strip():
        words=[x.strip().lower() for x in profile['keywords'].split(',') if x.strip()][:8]
        title=job.get('title','').lower(); text=title+' '+job.get('description','').lower()
        matches=[w for w in words if w in text]
        title_hits=sum(w in title for w in words)
        parts={'experience':min(35,10+title_hits*15),'ai_tasks':min(25,5+len(matches)*10),'geography':10,'salary':10,'potential':3}
        return {'total':sum(parts.values()),'parts':parts,'blockers':['location_unverified','requirements_unverified','salary_unverified'],'auto_eligible':False,'explanation':{'experience':'Поиск слов в названии; реальный опыт не проверен','ai_tasks':'Совпадения: '+(', '.join(matches) or 'нет'),'geography':'Требует проверки','salary':'Предварительно, требует проверки','potential':'Нейтральная оценка'}}
    title = ' '+job.get('title','').lower()+' '
    text = title + ' '+job.get('description','').lower()+' '
    interest = sum(1 for term in TERMS if term in title)
    ai = any(term in text for term in AI)
    parts = {'experience': min(35, 10 + (10 if ai else 0) + min(15, interest*5)), 'ai_tasks': min(25, (12 if ai else 0)+min(13,interest*5)), 'geography': 10 if 'remote' in job.get('location','').lower() or 'удален' in job.get('location','').lower() else 3, 'salary':10, 'potential':3}
    blockers = ['location_unverified', 'requirements_unverified']
    salary=job.get('salary')
    if salary and salary.get('currency')=='USD' and salary.get('max') is not None and salary.get('period') in ('year','month'):
        ceiling=salary['max']/(12 if salary['period']=='year' else 1)
        if ceiling < 3000: blockers.append('below_minimum'); parts['salary']=0
        elif ceiling>=4000: parts['salary']=15
    else: blockers.append('salary_unverified')
    total=sum(parts.values())
    return {'total':total,'parts':parts,'blockers':blockers,'auto_eligible':False, 'explanation': {'experience':'Эвристика по названиям и ключевым словам; опыт и требования не сопоставлены вручную', 'ai_tasks':f'AI: {ai}; совпадения направлений в названии: {interest}', 'geography':'Формат и допустимость страны проживания требуют проверки', 'salary':'10/15 при неизвестной зарплате; налоги и валюты не рассчитаны', 'potential':'Предварительная нейтральная оценка'}}
def greenhouse(board):
    data=get('https://boards-api.greenhouse.io/v1/boards/'+board+'/jobs?content=true')
    for j in data.get('jobs',[]):
        title=j.get('title',''); description=clean(j.get('content','')); t=(' '+title+' '+description+' ').lower()
        yield {'source':'greenhouse:'+board,'id':str(j['id']),'company':board,'title':title,'url':j['absolute_url'],'location':j.get('location',{}).get('name',''), 'description':description, 'salary':None, 'published':j.get('updated_at','')}
def hh(query='AI automation'):
    data=get('https://api.hh.ru/vacancies?'+urlencode({'text':query,'per_page':50, 'order_by':'publication_time'}))
    for j in data.get('items',[]):
        salary=j.get('salary') or None
        yield {'source':'hh','id':str(j['id']),'company':(j.get('employer') or {}).get('name',''),'title':j['name'],'url':j['alternate_url'],'location':(j.get('area') or {}).get('name','')+' '+(j.get('schedule') or {}).get('name',''),'description':clean(' '.join((j.get('snippet') or {}).get(k) or '' for k in ('requirement','responsibility'))),'salary':{'currency':salary.get('currency'),'min':salary.get('from'),'max':salary.get('to'),'gross':salary.get('gross'),'period':'month'} if salary else None,'work_format':(j.get('schedule') or {}).get('id','unknown'),'published':j.get('published_at','')}
def save(jobs):
    db=sqlite3.connect(DB); db.execute('CREATE TABLE IF NOT EXISTS jobs (source TEXT, id TEXT, data TEXT NOT NULL, score INTEGER NOT NULL, fetched TEXT NOT NULL, PRIMARY KEY(source,id))')
    for job in jobs:
        job['assessment']=score(job)
        db.execute('INSERT INTO jobs VALUES(?,?,?,?,?) ON CONFLICT(source,id) DO UPDATE SET data=excluded.data,score=excluded.score,fetched=excluded.fetched',(job['source'],job['id'],json.dumps(job,ensure_ascii=False),job['assessment']['total'],datetime.now(timezone.utc).isoformat()))
    db.commit(); db.close()
def init_db(db):
    db.execute('CREATE TABLE IF NOT EXISTS jobs (source TEXT, id TEXT, data TEXT NOT NULL, score INTEGER NOT NULL, fetched TEXT NOT NULL, PRIMARY KEY(source,id))')
    db.execute("CREATE TABLE IF NOT EXISTS decisions (source TEXT, id TEXT, decision TEXT NOT NULL, updated TEXT NOT NULL, PRIMARY KEY(source,id))")

def get_jobs():
    with closing(sqlite3.connect(DB)) as db, db:
        init_db(db)
        rows=db.execute("SELECT jobs.data, decisions.decision, decisions.updated, jobs.fetched FROM jobs LEFT JOIN decisions ON jobs.source=decisions.source AND jobs.id=decisions.id").fetchall()
    jobs=[]; profile=get_profile()
    for raw,decision,updated,fetched in rows:
        j=json.loads(raw); j['assessment']=score(j, profile) if profile.get('keywords') else j.get('assessment',score(j)); j['decision']=decision or 'new'; j['decision_updated']=updated; j['fetched']=fetched; j['application_status']='not_sent'; jobs.append(j)
    jobs.sort(key=lambda j:(bool(j.get('salary')),j.get('assessment',{}).get('total',0),j.get('published','')),reverse=True)
    return jobs

def set_decision(source, job_id, decision):
    if decision not in ('approved','rejected','new'): raise ValueError('Недопустимое решение')
    with closing(sqlite3.connect(DB)) as db, db:
        init_db(db)
        if not db.execute('SELECT 1 FROM jobs WHERE source=? AND id=?',(source,job_id)).fetchone(): raise ValueError('Вакансия не найдена')
        db.execute('INSERT INTO decisions VALUES(?,?,?,?) ON CONFLICT(source,id) DO UPDATE SET decision=excluded.decision,updated=excluded.updated',(source,job_id,decision,datetime.now(timezone.utc).isoformat()))

PROFILE_FIELDS = ('name','keywords','location','notes','currency','minimum','boards_greenhouse','boards_lever','boards_ashby','boards_smartrecruiters')
def get_profile():
    with closing(sqlite3.connect(DB)) as db, db:
        db.execute('CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL)')
        row=db.execute("SELECT value FROM settings WHERE key='profile'").fetchone()
    return json.loads(row[0]) if row else {}
def save_profile(profile):
    if not isinstance(profile,dict): raise ValueError('Invalid profile')
    clean_profile={k:str(profile.get(k,'')).strip()[:6000] for k in PROFILE_FIELDS}
    from source_setup import BOARD_HOSTS, normalize_boards
    for source in BOARD_HOSTS:
        field='boards_'+source
        clean_profile[field]=', '.join(normalize_boards(source,clean_profile[field]))
    with closing(sqlite3.connect(DB)) as db, db:
        db.execute('CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL)')
        db.execute("INSERT INTO settings VALUES('profile',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",(json.dumps(clean_profile,ensure_ascii=False),))
    return clean_profile

def get_sources_config():
    from source_registry import ACTIVE_SOURCES
    with closing(sqlite3.connect(DB)) as db, db:
        db.execute('CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL)')
        row=db.execute("SELECT value FROM settings WHERE key='sources'").fetchone()
    return {'enabled':[name for name in (json.loads(row[0]) if row else list(ACTIVE_SOURCES)) if name in ACTIVE_SOURCES]}

def save_sources_config(enabled):
    from source_registry import ACTIVE_SOURCES
    if not isinstance(enabled,list) or any(not isinstance(x,str) or x not in ACTIVE_SOURCES for x in enabled): raise ValueError('Invalid source')
    enabled=list(dict.fromkeys(enabled))
    with closing(sqlite3.connect(DB)) as db, db:
        db.execute('CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL)')
        db.execute("INSERT INTO settings VALUES('sources',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",(json.dumps(enabled),))
    return {'enabled':enabled}

def main():
    p=argparse.ArgumentParser(); p.add_argument('command',choices=['search','list']); p.add_argument('--boards',default='anthropic,openai'); p.add_argument('--limit',type=int,default=30); a=p.parse_args()
    if a.command=='search':
        jobs=[]
        for name, source in [('hh',hh)]+[(f'greenhouse:{b}',lambda b=b:greenhouse(b)) for b in a.boards.split(',')]:
            try:
                found=list(source()); jobs.extend(found); print(f'{name}: {len(found)} вакансий',file=sys.stderr)
            except Exception as e: print(f'{name}: ошибка {e}',file=sys.stderr)
        save(jobs)
    db=sqlite3.connect(DB)
    try: rows=db.execute('SELECT data FROM jobs ORDER BY score DESC LIMIT ?', (a.limit,)).fetchall()
    except sqlite3.OperationalError: rows=[]
    for (raw,) in rows:
        j=json.loads(raw); print(f"{j['assessment']['total']:>3} | {j['company']} | {j['title']} | {j['location']} | {j['url']}")
    db.close()
if __name__=='__main__': main()
