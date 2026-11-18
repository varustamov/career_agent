import tempfile, unittest
from pathlib import Path
import career_agent as agent
import career_mcp
from unittest.mock import patch

class CareerMcpTests(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();self.old=agent.DB;agent.DB=str(Path(self.t.name)/'test.sqlite3')
 def tearDown(self): agent.DB=self.old;self.t.cleanup()
 def test_list_jobs_hides_descriptions_by_default(self):
  agent.save([{'source':'hh','id':'1','title':'Engineer','company':'Test','url':'https://example.com','location':'Remote','description':'secret description','salary':None}])
  result=career_mcp.list_jobs(limit=10)
  self.assertEqual(result['jobs'][0]['id'],'1')
  self.assertNotIn('description',result['jobs'][0])
 def test_get_job_requires_exact_source_and_id(self):
  agent.save([{'source':'hh','id':'1','title':'Engineer','company':'Test','url':'https://example.com','location':'Remote','description':'job data','salary':None}])
  self.assertEqual(career_mcp.get_job('hh','1')['description'],'job data')
  with self.assertRaises(ValueError):career_mcp.get_job('hh','other')
 def test_profile_requires_explicit_call(self):
  agent.save_profile({'name':'Test User','notes':'private'})
  self.assertEqual(career_mcp.get_profile()['name'],'Test User')
 def test_limit_bounds(self):
  with self.assertRaises(ValueError): career_mcp.list_jobs(limit=101)
 def test_run_search_uses_dashboard(self):
  with patch.object(career_mcp, '_dashboard_request', return_value={'count':3}) as request:
   self.assertEqual(career_mcp.search_jobs()['count'],3)
   request.assert_called_once_with('/api/search', {})
 def test_schedule_validation_before_request(self):
  with patch.object(career_mcp, '_dashboard_request') as request:
   for enabled,interval in [(True,59),(True,True),('yes',60),(True,10081)]:
    with self.assertRaises(ValueError): career_mcp.configure_search_schedule(enabled,interval)
   request.assert_not_called()
 def test_schedule_config_sent_to_dashboard(self):
  with patch.object(career_mcp, '_dashboard_request', return_value={'enabled':True}) as request:
   career_mcp.configure_search_schedule(True, 120)
   request.assert_called_once_with('/api/schedule', {'enabled':True,'interval_minutes':120})
