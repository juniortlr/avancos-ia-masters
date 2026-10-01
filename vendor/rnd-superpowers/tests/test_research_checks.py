import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from audit_split import audit
from plan_ab import plan


def rows():
    return [dict(row_id='1', entity_id='A', split='train', prediction_time='2025-01-01T00:00:00Z',
                 label_end='2025-02-01T00:00:00Z', feature_available_at='2024-12-31T00:00:00Z'),
            dict(row_id='2', entity_id='B', split='test', prediction_time='2025-03-01T00:00:00Z',
                 label_end='2025-04-01T00:00:00Z', feature_available_at='2025-02-28T00:00:00Z')]


class SplitTests(unittest.TestCase):
    def test_valid_group_and_time(self):
        self.assertTrue(audit(rows(), True)['passed'])
    def test_shared_entity_fails_when_required(self):
        r=rows(); r[1]['entity_id']='A'
        self.assertFalse(audit(r, True)['passed'])
        self.assertTrue(audit(r, False)['passed'])
    def test_overlapping_label_window_fails(self):
        r=rows(); r[0]['label_end']='2025-03-02T00:00:00Z'
        self.assertFalse(audit(r)['passed'])
    def test_future_feature_fails(self):
        r=rows(); r[1]['feature_available_at']='2025-03-02T00:00:00Z'
        self.assertFalse(audit(r)['passed'])
    def test_duplicate_rows_fail(self):
        r=rows(); r.append(copy.copy(r[0]))
        self.assertFalse(audit(r)['passed'])
    def test_naive_timestamps_fail(self):
        r=rows(); r[0]['prediction_time']='2025-01-01'
        self.assertFalse(audit(r)['passed'])
    def test_empty_fails(self):
        self.assertFalse(audit([])['passed'])
    def test_offset_equivalence(self):
        r=rows(); r[1]['prediction_time']='2025-02-28T21:00:00-03:00'
        self.assertTrue(audit(r)['passed'])


class PlanningTests(unittest.TestCase):
    def test_known_normal_approximation(self):
        # Standard two-sided 5%, 80% power, .50 -> .60: approximately 388 per arm.
        self.assertEqual(plan(.5,.1)['n_per_arm'],388)
    def test_smaller_effect_needs_more_data(self):
        self.assertGreater(plan(.5,.05)['n_total'],plan(.5,.1)['n_total'])
    def test_more_power_needs_more_data(self):
        self.assertGreater(plan(.5,.1,power=.9)['n_total'],plan(.5,.1)['n_total'])
    def test_duration_is_total_over_traffic(self):
        self.assertEqual(plan(.5,.1,units_per_period=100)['ideal_recruitment_periods'],7.76)
    def test_invalid_inputs(self):
        for base, effect in [(0,.1),(.9,.2),(.5,0),(float('nan'),.1)]:
            with self.assertRaises(ValueError): plan(base,effect)


if __name__ == '__main__':
    unittest.main()
