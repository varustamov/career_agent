import tempfile, unittest
from pathlib import Path
from unittest.mock import patch
import career_agent as agent
import source_setup

class SourceSetupTests(unittest.TestCase):
 def test_company_page_urls_and_ids(self):
  self.assertEqual(source_setup.normalize_boards('greenhouse','https://boards.greenhouse.io/anthropic/jobs/123, stripe'),['anthropic','stripe'])
  self.assertEqual(source_setup.normalize_boards('lever','https://jobs.lever.co/leverdemo/123'),['leverdemo'])
  self.assertEqual(source_setup.normalize_boards('ashby','https://jobs.ashbyhq.com/openai'),['openai'])
  self.assertEqual(source_setup.normalize_boards('smartrecruiters','https://jobs.smartrecruiters.com/Visa/123'),['Visa'])
 def test_invalid_hosts_and_paths_rejected(self):
  for bad in ['https://jobs.lever.co.evil.test/acme','https://jobs.eu.lever.co/acme','../acme','https://jobs.lever.co/','https://user@jobs.lever.co/acme']:
   with self.subTest(bad=bad), self.assertRaises(ValueError): source_setup.normalize_boards('lever',bad)
 def test_check_empty_board_is_not_confirmed(self):
  with patch('sources.lever',return_value=iter([])):
   result=source_setup.check_source('lever','https://jobs.lever.co/example')
  self.assertEqual(result['items'][0]['status'],'empty')
 def test_check_reports_per_board_failure(self):
  def fetch(name):
   if name=='broken': raise OSError('offline')
   return iter([{'id':'1'}])
  with patch('sources.lever',side_effect=fetch):
   result=source_setup.check_source('lever','good,broken')
  self.assertEqual([item['status'] for item in result['items']],['ok','error'])
 def test_check_rejects_unknown_sources(self):
  with self.assertRaises(ValueError): source_setup.check_source('unknown','')
 def test_profile_saves_canonical_ids(self):
  with tempfile.TemporaryDirectory() as directory:
   previous=agent.DB; agent.DB=str(Path(directory)/'db.sqlite3')
   try:
    saved=agent.save_profile({'boards_lever':'https://jobs.lever.co/leverdemo, acme'})
    self.assertEqual(saved['boards_lever'],'leverdemo, acme')
    self.assertEqual(agent.get_profile()['boards_lever'],'leverdemo, acme')
    with self.assertRaises(ValueError): agent.save_profile({'boards_greenhouse':'https://evil.test/foo'})
   finally: agent.DB=previous
