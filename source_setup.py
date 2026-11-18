"""Validate public company boards and check source connectivity; no credentials."""
import re, urllib.error
from urllib.parse import urlsplit
import career_agent as agent
import sources
from source_registry import SOURCES

BOARD_HOSTS={'greenhouse':('boards.greenhouse.io','job-boards.greenhouse.io'), 'lever':('jobs.lever.co',), 'ashby':('jobs.ashbyhq.com',), 'smartrecruiters':('jobs.smartrecruiters.com',)}

def normalize_boards(source, raw):
 if source not in BOARD_HOSTS or not isinstance(raw,str): raise ValueError('Invalid board source')
 parts=[part.strip() for part in raw.split(',') if part.strip()]
 if len(parts)>15: raise ValueError('At most 15 company pages per source')
 result=[]
 for part in parts:
  if '://' in part:
   url=urlsplit(part)
   if url.scheme!='https' or url.netloc not in BOARD_HOSTS[source] or not url.path.strip('/'):
    raise ValueError(f'Unsupported {source} page URL')
   part=url.path.strip('/').split('/')[0]
  if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,99}',part): raise ValueError(f'Invalid {source} company ID')
  if part not in result: result.append(part)
 return result

def check_source(source, boards=''):
 if source not in SOURCES: raise ValueError('Unknown source')
 if source in BOARD_HOSTS:
  names=normalize_boards(source,boards)
  if not names: raise ValueError('Add at least one company page')
  if len(names)>5: raise ValueError('Check at most 5 companies at a time')
  fetch={'greenhouse':agent.greenhouse,'lever':sources.lever,'ashby':sources.ashby,'smartrecruiters':sources.smartrecruiters}[source]
  tasks=[(name,lambda name=name, fn=fetch:fn(name)) for name in names]
 else:
  fetch={'hh':lambda:agent.hh('developer'),'remotive':sources.remotive,'arbeitnow':sources.arbeitnow,'hackernews':sources.hackernews}[source]
  tasks=[(source,fetch)]
 results=[]
 for name,fetch in tasks:
  try:
   count=sum(1 for _ in fetch())
   results.append({'name':name,'status':'ok' if count else 'empty','count':count})
  except urllib.error.HTTPError as exc: results.append({'name':name,'status':'error','error':f'HTTP {exc.code}'})
  except Exception as exc: results.append({'name':name,'status':'error','error':type(exc).__name__})
 return {'source':source,'items':results}
