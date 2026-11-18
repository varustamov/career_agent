import tempfile, unittest
from pathlib import Path
from unittest.mock import patch
import career_agent as app
import sources

class SourceTests(unittest.TestCase):
 def test_lever_normalization(self):
  data=[{'id':'a','text':'Automation Lead','hostedUrl':'https://jobs.lever.co/acme/a','categories':{'location':'Remote'},'descriptionPlain':'AI'}]
  with patch('sources.get_json',return_value=data): jobs=list(sources.lever('acme'))
  self.assertEqual(jobs[0]['title'],'Automation Lead');self.assertEqual(jobs[0]['source'],'lever:acme')
 def test_ashby_normalization(self):
  data={'jobs':[{'id':'b','title':'AI Lead','jobUrl':'https://jobs.ashbyhq.com/acme/b','location':'Remote','isRemote':True,'descriptionPlain':'AI'}]}
  with patch('sources.get_json',return_value=data): jobs=list(sources.ashby('acme'))
  self.assertEqual(jobs[0]['work_format'],'remote'); self.assertEqual(jobs[0]['id'],'b')
 def test_reject_untrusted_board(self):
  with self.assertRaises(ValueError): list(sources.lever('../evil'))
 def test_profile_terms_influence_score(self):
  job={'title':'Designer','description':'Visual design','location':'Remote','salary':None}
  designer=app.score(job,{'keywords':'designer'})
  manager=app.score(job,{'keywords':'engineer'})
  self.assertGreater(designer['total'],manager['total'])
 def test_hacker_news_fetches_job_stories_only(self):
  def fixture(url):
   if url.endswith('/jobstories.json'): return [1,2,3]
   return {'id':int(url.rsplit('/',1)[-1].split('.')[0]),'type':'job','title':'AI engineer','url':'https://example.com/job','time':1,'deleted':url.endswith('/2.json')}
  with patch('sources.get_json',side_effect=fixture): jobs=list(sources.hackernews())
  self.assertEqual([j['id'] for j in jobs],['1','3'])
  self.assertEqual(jobs[0]['source'],'hackernews')
 def test_profile_roundtrip(self):
  with tempfile.TemporaryDirectory() as d:
   old=app.DB;app.DB=str(Path(d)/'jobs.sqlite3')
   try:
    app.save_profile({'name':'Example','keywords':'design, automation','location':'UK','notes':'portfolio','currency':'USD','minimum':'3000'})
    self.assertEqual(app.get_profile()['keywords'],'design, automation')
   finally:app.DB=old
if __name__=='__main__':unittest.main()
