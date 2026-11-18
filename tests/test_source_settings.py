import tempfile, unittest
from pathlib import Path
import career_agent as agent
import source_registry as registry

class SettingsTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(); self.old=agent.DB; agent.DB=str(Path(self.tmp.name)/'test.sqlite3')
 def tearDown(self): agent.DB=self.old; self.tmp.cleanup()
 def test_defaults_include_public_sources(self):
  config=agent.get_sources_config()
  self.assertNotIn('hh',config['enabled'])
  self.assertIn('ashby',config['enabled'])
 def test_save_only_known_sources_and_preserve_order(self):
  with self.assertRaises(ValueError): agent.save_sources_config(['hh','unknown'])
  agent.save_sources_config(['lever','ashby','lever'])
  self.assertEqual(agent.get_sources_config()['enabled'],['lever','ashby'])
 def test_unavailable_hh_is_filtered_from_legacy_settings(self):
  import sqlite3, json
  from contextlib import closing
  agent.get_profile()
  with closing(sqlite3.connect(agent.DB)) as db, db: db.execute("INSERT INTO settings VALUES('sources',?)",(json.dumps(['hh','lever']),))
  self.assertEqual(agent.get_sources_config()['enabled'],['lever'])
 def test_hh_has_explicit_not_implemented_oauth(self):
  self.assertEqual(registry.SOURCES['hh']['apply_mode'],'manual')
  self.assertFalse(registry.SOURCES['hh']['oauth_available'])
 def test_application_not_marked_submitted(self):
  for s in registry.SOURCES.values(): self.assertNotEqual(s['apply_mode'],'automatic')
if __name__=='__main__': unittest.main()
