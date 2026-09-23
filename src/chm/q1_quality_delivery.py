"""Build the descriptive Q interface and evidence summary from executed outputs."""
from pathlib import Path
import pandas as pd
from scipy.stats import spearmanr


def main():
    root = Path('outputs/chm')
    q = pd.read_csv(root / 'domain_quality_v0.csv')
    audit = pd.read_csv(root / 'quality_data_audit_v0.csv')
    missing = audit.groupby(['dataset_scope', 'quality_domain']).missing.sum()
    delivery = q.rename(columns={'Q_z_median': 'Q', 'Q_ci_low': 'uncertainty_low', 'Q_ci_high': 'uncertainty_high'}).copy()
    delivery['Q_scale_definition'] = 'A1-fitted family-balanced z-score; domain median; not B6 Q_score'
    delivery['missing_note'] = [f'{int(missing.loc[(r.dataset_scope, r.quality_domain)])} missing metric cells; available-value family means'
                                for r in q.itertuples()]
    delivery['score_version'] = 'q1_local_descriptive_v0'
    delivery.to_csv(root / 'domain_quality.csv', index=False)
    mapping = pd.read_csv('data/raw/real_attachments/A_data_value/domain_mapping_guide.csv')
    mapping['mapping_weight_or_rule'] = mapping.mapping_type.map({'direct': 'same-name domain median', 'near_direct': 'proxy domain median; sensitivity required', 'inferred': 'unknown; no numeric imputation'})
    mapping['mapping_confidence'] = mapping.mapping_type.map({'direct': 'name match only; not population identity', 'near_direct': 'semantic proxy', 'inferred': 'unknown'})
    mapping.to_csv(root / 'domain_mapping.csv', index=False)
    sample = q[q.dataset_scope == 'sample'].sort_values('Q_z_median', ascending=False)
    sensitivity = pd.read_csv(root / 'quality_list_compression_sensitivity_v0.csv')
    equal_rho = spearmanr(sample.Q_z_median, sample.Q_equal22_median).statistic
    text = ['# Q1 本地全量质量结果（描述性初版）', '',
            '输入起点：远端 4627133；代码见本次提交。A1/A2/A3 全量 51,230 / 17,523 / 203,752 行。',
            '三个输入哈希、A1 标准化参数、随机种子 20260923、bootstrap=1000 见 quality_analysis_manifest_v0.json。', '',
            '| A1 域 | 记录数 | Q 中位数 | 条件 bootstrap 95% CI |', '|---|---:|---:|---:|']
    for r in sample.itertuples():
        text.append(f'| {r.quality_domain} | {r.n_rows} | {r.Q_z_median:.6f} | [{r.Q_ci_low:.6f}, {r.Q_ci_high:.6f}] |')
    text += ['', f'域级排序：expectation 与 argmax 的 Spearman={sensitivity.domain_rank_spearman_all7.iloc[0]:.6f}；三家族等权与 22 指标等权={equal_rho:.6f}。',
             'argmax 交换 github/wikipedia 的次序；22 指标等权交换 book/arxiv 的次序，不能宣称排名完全稳健。', '',
             '## 抽样与扩展', '',
             'ID 核对发现 A1 的 1,419 条 arxiv 和 10,000 条 github 全部包含于 A2/A3。扩展集对照是覆盖度检查，不能称为独立实验。',
             '新增非重叠部分分别为 16,104 / 193,752 条；仍复用 A1 的所有变换、方向和 Q 均值/标准差。',
             '| 域 | A1 Q | 扩展 Q | 非重叠部分 Q |', '|---|---:|---:|---:|']
    nonoverlap = pd.read_csv(root / 'quality_nonoverlap_validation_v0.csv').set_index('quality_domain')
    for r in pd.read_csv(root / 'quality_sample_extended_v0.csv').itertuples():
        text.append(f'| {r.quality_domain} | {r.sample_Q_median:.6f} | {r.extended_Q_median:.6f} | {nonoverlap.loc[r.quality_domain,"Q_z_median"]:.6f} |')
    text += ['', '## 冲突复核与边界', '',
             '所有 231 个指标对在同域 sample/extended 中重算相关；另保存非重叠扩展部分相关。常数指标相关不可定义，排除该域后注明实际 n_domains。',
             '冲突只作描述性负相关，未完成相关系数 bootstrap 与多重比较，不写“显著冲突”。方向锚点是建模假设，不是客观质量真值；DSIR 被经验翻转不能解释为原指标语义改变。',
             '部分指标 pooled 相关近零且方向异质度较大；应在最终冻结前做定向与截断敏感性。',
             'Q 的区间只反映固定预处理下、假定记录独立的重抽样误差，不包含定向、权重和映射不确定性。book 仅 171 条。',
             'Q 可为负，不能直接代入 B6 正值 Q_score 或幂律质量项；需 cyj 明确跨数据集映射。A16 的 11 个 inferred 域仍无数值填补。', '',
             '## 复现', '', '```powershell',
             './.venv/Scripts/python.exe src/chm/q1_quality_analysis.py',
             './.venv/Scripts/python.exe src/chm/q1_quality_delivery.py',
             './.venv/Scripts/python.exe -m unittest discover -s src/chm -p test_q1_quality_analysis.py', '```', '',
             '公开字段语义已于 2026-09-23 复核：https://huggingface.co/datasets/opendatalab/SlimPajama-Meta-rater 。未使用历史隐藏文字。']
    Path('experiments/chm/20260923-q1-local-quality.md').write_text('\n'.join(text)+'\n', encoding='utf-8')
    print('Saved descriptive quality interface, mapping and experiment report.')


if __name__ == '__main__':
    main()
