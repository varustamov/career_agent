import unittest
from career_agent import score

class ScoringTest(unittest.TestCase):
    def test_unknown_salary_is_neutral_and_never_autoeligible(self):
        s = score({'title':'AI automation lead', 'description':'AI automation project', 'location':'Remote', 'salary':None})
        self.assertEqual(s['parts']['salary'], 10)
        self.assertFalse(s['auto_eligible'])
    def test_low_salary_is_blocked(self):
        s = score({'title':'AI automation lead', 'description':'AI automation', 'location':'Remote', 'salary':{'currency':'USD','max':2000,'period':'month'}})
        self.assertIn('below_minimum', s['blockers'])
    def test_office_requires_review(self):
        s = score({'title':'AI automation lead', 'description':'AI automation', 'location':'Moscow office', 'salary':None})
        self.assertIn('location_unverified', s['blockers'])
if __name__ == '__main__': unittest.main()
