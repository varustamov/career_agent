import json, sqlite3, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
import career_agent as app

class DashboardTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.db=str(Path(self.temp.name)/'test.db')
        self.old=app.DB; app.DB=self.db
    def tearDown(self): app.DB=self.old; self.temp.cleanup()
    def test_hh_normalization_keeps_salary_and_remote(self):
        raw={'id':'123','name':'AI lead','alternate_url':'https://hh.ru/vacancy/123','employer':{'name':'Acme'},'area':{'name':'Москва'},'schedule':{'id':'remote','name':'Удаленная работа'},'salary':{'from':250000,'to':350000,'currency':'RUR','gross':True},'snippet':{}}
        with patch('career_agent.get', return_value={'items':[raw]}): job=list(app.hh('AI'))[0]
        self.assertEqual(job['salary']['min'],250000); self.assertTrue(job['salary']['gross']); self.assertEqual(job['work_format'],'remote')
    def test_approval_does_not_send_and_survives_refresh(self):
        j={'source':'hh','id':'1','title':'AI lead','company':'A','url':'https://hh.ru/vacancy/1','location':'Москва','description':'AI','salary':None}
        app.save([j]); app.set_decision('hh','1','approved'); app.save([j])
        self.assertEqual(app.get_jobs()[0]['decision'],'approved'); self.assertEqual(app.get_jobs()[0]['application_status'],'not_sent')
    def test_unknown_job_and_invalid_decision_are_rejected(self):
        with self.assertRaises(ValueError): app.set_decision('hh','missing','approved')
        with self.assertRaises(ValueError): app.set_decision('hh','1','sent')
    def test_salary_first_then_score(self):
        for id,sal in [('a',None),('b',{'currency':'RUR','min':1})]:
            app.save([{'source':'hh','id':id,'title':'AI automation lead','company':'A','url':'https://hh.ru','location':'Remote','description':' AI ','salary':sal}])
        self.assertEqual(app.get_jobs()[0]['id'],'b')
if __name__=='__main__': unittest.main()
