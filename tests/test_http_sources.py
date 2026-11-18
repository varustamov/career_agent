import json, tempfile, threading, unittest, urllib.request, urllib.error
from pathlib import Path
from http.server import ThreadingHTTPServer
from unittest.mock import patch
import career_agent as agent
import dashboard_server as web

class SourceHTTPTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(); self.old_db=agent.DB; self.old_port=web.PORT
  agent.DB=str(Path(self.tmp.name)/'data.sqlite3')
  self.server=ThreadingHTTPServer(('127.0.0.1',0),web.Handler);web.PORT=self.server.server_port
  self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
  self.base=f'http://127.0.0.1:{web.PORT}'
 def tearDown(self):
  self.server.shutdown();self.server.server_close();self.thread.join();agent.DB=self.old_db;web.PORT=self.old_port;self.tmp.cleanup()
 def get(self,path):
  with urllib.request.urlopen(self.base+path,timeout=5) as r:return json.load(r)
 def post(self,path,body):
  req=urllib.request.Request(self.base+path,data=json.dumps(body).encode(),method='POST',headers={'Origin':self.base,'Content-Type':'application/json','X-Career-Token':web.TOKEN})
  with urllib.request.urlopen(req,timeout=5) as r:return json.load(r)
 def test_config_controls_search(self):
  self.post('/api/sources',{'enabled':['remotive']})
  fixture={'source':'remotive','id':'1','company':'Example','title':'Design','url':'https://example.com','description':'','location':'Remote','salary':None}
  with patch('sources.remotive',return_value=iter([fixture])):
   result=self.post('/api/search',{})
  self.assertEqual(result['counts'],{'remotive':1})
  self.assertEqual(self.get('/api/jobs')['jobs'][0]['application_status'],'not_sent')
 def test_scheduler_switch_is_opt_in_and_rejects_invalid_intervals(self):
  self.assertFalse(self.get('/api/schedule')['enabled'])
  try:
   self.assertTrue(self.post('/api/schedule',{'enabled':True,'interval_minutes':60})['enabled'])
   with self.assertRaises(urllib.error.HTTPError): self.post('/api/schedule',{'enabled':True,'interval_minutes':1})
  finally: self.post('/api/schedule',{'enabled':False,'interval_minutes':60})
 def test_cross_origin_mutation_rejected(self):
  req=urllib.request.Request(self.base+'/api/sources',data=b'{"enabled":[]}',method='POST',headers={'Origin':'https://example.com','X-Career-Token':web.TOKEN})
  with self.assertRaises(urllib.error.HTTPError) as error: urllib.request.urlopen(req,timeout=5)
  self.assertEqual(error.exception.code,403)
