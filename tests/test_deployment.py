import os, subprocess, sys, tempfile, unittest
from pathlib import Path

class DeploymentTests(unittest.TestCase):
 def test_database_path_can_be_set_for_service(self):
  with tempfile.TemporaryDirectory() as directory:
   path=str(Path(directory)/'data.sqlite3')
   result=subprocess.run([sys.executable,'-c','import career_agent; print(career_agent.DB)'],env={**os.environ,'CAREER_DB_PATH':path},text=True,capture_output=True,check=True)
   self.assertEqual(result.stdout.strip(),path)
