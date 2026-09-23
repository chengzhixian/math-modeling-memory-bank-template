import unittest
import numpy as np
import pandas as pd
from q1_quality_analysis import compress_list, conflict_pairs, QUALITY_FIELDS, add_quality_scores, assert_domain_id_integrity


class QualityRegressionTests(unittest.TestCase):
    def test_missing_logits_never_become_zero_class(self):
        for mode in ['expectation', 'argmax']:
            for value in [[None, None], [0.0, None], [np.inf, 0.0]]:
                self.assertTrue(np.isnan(compress_list('ad_en', value, mode)))

    def test_frozen_score_scale_on_extension(self):
        data = pd.DataFrame({field: [-1., 0., 1.] for field in QUALITY_FIELDS})
        _, params = add_quality_scores(data)
        extension, reused = add_quality_scores(data + 2, frozen_q=params)
        self.assertEqual(params, reused)
        self.assertGreater(extension.Q_z.mean(), 1)

    def test_conflict_retains_negative_pair_and_ignores_constant(self):
        data = pd.DataFrame({field: np.arange(8.) for field in QUALITY_FIELDS})
        data['_source_domain'] = 'example'
        data[QUALITY_FIELDS[1]] = -data[QUALITY_FIELDS[0]]
        data[QUALITY_FIELDS[2]] = 1.
        pairs = conflict_pairs(data)
        pair = pairs[(pairs.metric_a == QUALITY_FIELDS[0]) & (pairs.metric_b == QUALITY_FIELDS[1])]
        self.assertAlmostEqual(float(pair.iloc[0].conflict_strength), 1.)
        self.assertFalse(((pairs.metric_a == QUALITY_FIELDS[2]) | (pairs.metric_b == QUALITY_FIELDS[2])).any())

    def test_id_integrity_rejects_blank_and_duplicate(self):
        good = pd.DataFrame({
            '_source_domain': ['a', 'a', 'b'],
            '_id': ['1', '2', '1'],
        })
        rows = assert_domain_id_integrity(good, 'A1')
        self.assertEqual(sum(r['duplicate_ids'] for r in rows), 0)

        bad_blank = good.copy()
        bad_blank.loc[1, '_id'] = ''
        with self.assertRaises(ValueError):
            assert_domain_id_integrity(bad_blank, 'A1')

        bad_dup = good.copy()
        bad_dup.loc[1, '_id'] = '1'
        with self.assertRaises(ValueError):
            assert_domain_id_integrity(bad_dup, 'A1')


if __name__ == '__main__':
    unittest.main()
