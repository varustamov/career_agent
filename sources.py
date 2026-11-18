"""Read-only public vacancy feeds. Board names are data, not arbitrary URLs."""
import re, json, urllib.request
from urllib.parse import quote

def get_json(url):
 req=urllib.request.Request(url,headers={'User-Agent':'CareerAgent/0.3 (local job search)','Accept':'application/json'})
 with urllib.request.urlopen(req,timeout=20) as response: return json.load(response)
def board_name(board):
 if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,99}',board): raise ValueError('Invalid company board')
 return quote(board,safe='')
def lever(board):
 slug=board_name(board)
 for j in get_json(f'https://api.lever.co/v0/postings/{slug}?mode=json'):
  loc=j.get('categories') or {}
  yield {'source':'lever:'+board,'id':str(j['id']),'company':board,'title':j.get('text',''),'url':j.get('hostedUrl',''),'location':loc.get('location',''),'description':j.get('descriptionPlain',''),'salary':None,'published':'','work_format':'unknown'}
def ashby(board):
 slug=board_name(board)
 for j in get_json(f'https://api.ashbyhq.com/posting-api/job-board/{slug}?includeCompensation=true').get('jobs',[]):
  url=j.get('jobUrl',''); job_id=j.get('id') or url.rstrip('/').split('/')[-1]
  if not job_id or not url: continue
  yield {'source':'ashby:'+board,'id':str(job_id),'company':board,'title':j.get('title',''),'url':url,'location':j.get('location',''),'description':j.get('descriptionPlain',''),'salary':None,'published':j.get('publishedAt',''),'work_format':'remote' if j.get('isRemote') else 'unknown'}
def smartrecruiters(board):
 slug=board_name(board)
 for j in get_json(f'https://api.smartrecruiters.com/v1/companies/{slug}/postings?limit=100').get('content',[]):
  loc=j.get('location') or {}; place=', '.join(str(loc.get(k,'')) for k in ('city','country') if loc.get(k))
  yield {'source':'smartrecruiters:'+board,'id':str(j['id']),'company':(j.get('company') or {}).get('name',board),'title':j.get('name',''),'url':f"https://jobs.smartrecruiters.com/{slug}/{quote(str(j['id']),safe='')}",'location':place,'description':'','salary':None,'published':j.get('releasedDate',''),'work_format':'remote' if loc.get('remote') else 'unknown'}
def remotive():
 for j in get_json('https://remotive.com/api/remote-jobs').get('jobs',[]):
  yield {'source':'remotive','id':str(j['id']),'company':j.get('company_name',''),'title':j.get('title',''),'url':j.get('url',''),'location':j.get('candidate_required_location',''),'description':j.get('description',''),'salary':None,'published':j.get('publication_date',''),'work_format':'remote'}
def arbeitnow():
 for j in get_json('https://www.arbeitnow.com/api/job-board-api').get('data',[]):
  yield {'source':'arbeitnow','id':str(j['slug']),'company':j.get('company_name',''),'title':j.get('title',''),'url':j.get('url',''),'location':j.get('location',''),'description':j.get('description',''),'salary':None,'published':'','work_format':'remote' if j.get('remote') else 'unknown'}

def hackernews():
 """Recent HN job stories, not the separate Who is hiring comment threads."""
 from datetime import datetime, timezone
 from concurrent.futures import ThreadPoolExecutor
 base='https://hacker-news.firebaseio.com/v0'
 ids=get_json(base+'/jobstories.json')[:20]
 def fetch(item_id): return get_json(base+'/item/'+str(int(item_id))+'.json')
 with ThreadPoolExecutor(max_workers=4) as pool:
  items=list(pool.map(fetch,ids))
 for j in items:
  if not j or j.get('deleted') or j.get('dead') or j.get('type')!='job': continue
  published=datetime.fromtimestamp(j.get('time',0),timezone.utc).isoformat()
  yield {'source':'hackernews','id':str(j['id']),'company':'','title':j.get('title',''),'url':j.get('url') or 'https://news.ycombinator.com/item?id='+str(j['id']),'location':'','description':j.get('text',''),'salary':None,'published':published,'work_format':'unknown'}
