import unittest
from unittest.mock import Mock
from scheduler import SearchScheduler

class SchedulerTests(unittest.TestCase):
 def test_disabled_by_default(self):
  s=SearchScheduler(Mock())
  self.assertFalse(s.status()['enabled'])
  self.assertEqual(s.status()['interval_minutes'],60)
 def test_validates_minimum_interval(self):
  s=SearchScheduler(Mock())
  with self.assertRaises(ValueError): s.configure(True,1)
  self.assertFalse(s.status()['enabled'])
 def test_never_runs_when_disabled(self):
  action=Mock();s=SearchScheduler(action);s.tick(100000)
  action.assert_not_called()
 def test_enabled_runs_only_after_interval(self):
  action=Mock(return_value={'count':0,'errors':[]});s=SearchScheduler(action, clock=lambda:100)
  s.configure(True,60);s.tick(200);action.assert_not_called();s.tick(3700);action.assert_called_once()
 def test_failure_recorded(self):
  action=Mock(side_effect=RuntimeError('problem'));s=SearchScheduler(action,clock=lambda:100)
  s.configure(True,60);s.tick(3700)
  self.assertIn('problem',s.status()['last_error'])
