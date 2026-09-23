import unittest
import numpy as np
import pandas as pd
from q1_quality_analysis import compress_list, conflict_pairs, QUALITY_FIELDS, add_quality_scores


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


if __name__ == '__main__':
    unittest.main()
