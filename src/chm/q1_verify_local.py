"""Compare checked-in web results with isolated local reruns; never overwrite v0."""
from pathlib import Path
import json
import numpy as np
import pandas as pd


def main():
    base = Path('outputs/chm')
    legacy = base / 'archive' / 'web_v0'
    rerun = base / 'local_recheck_v1'
    reports = []
    for name in ['mixture_effect_ridge_v0.csv', 'mixture_reference_v0.csv',
                 'mixture_scale_calibration_v0.csv', 'q1_regmix_direct_scale_rank_stability.csv',
                 'q1_regmix_ridge_domainwise_metrics.csv']:
        old, new = pd.read_csv(legacy / name), pd.read_csv(rerun / name)
        keys = ['target'] if 'target' in old else ['mixture_domain']
        if 'pair' in new:
            if 'pair' not in old:
                old['pair'] = 'test_1m_vs_test_60m'
            keys.append('pair')
        common = [c for c in old if c in new and c not in keys]
        joined = old.merge(new, on=keys, suffixes=('_web', '_local'), validate='one_to_one')
        diffs = {c: float(np.nanmax(np.abs(joined[c+'_web'] - joined[c+'_local'])))
                 for c in common if pd.api.types.is_numeric_dtype(old[c])}
        reports.append({'file': name, 'old_rows': len(old), 'new_rows': len(new),
                        'matched_rows': len(joined), 'old_only_columns': sorted(set(old)-set(new)),
                        'new_only_columns': sorted(set(new)-set(old)), 'max_abs_differences': diffs})
    (base / 'q1_local_reproduction_check.json').write_text(json.dumps(reports, indent=2), encoding='utf-8')
    old = pd.read_csv(legacy / 'mixture_effect_ridge_v0.csv')
    new = pd.read_csv(rerun / 'mixture_effect_ridge_v0.csv')
    cols = ['target', 'alpha', 'cv_rmse']
    comparison = old[cols].merge(new[cols], on='target', suffixes=('_web', '_local'))
    comparison.to_csv(rerun / 'web_local_cv_comparison.csv', index=False)
    print(comparison.to_string(index=False))
    print(new.loc[new.target == 'pile_cc', ['test_1m_spearman', 'test_60m_spearman', 'test_1B_spearman']])
    print(new[['test_1m_spearman', 'test_60m_spearman', 'test_1B_spearman']].median())


if __name__ == '__main__':
    main()
