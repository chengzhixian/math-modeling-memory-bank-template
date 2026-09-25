"""Plot frozen Q4 core results for explanation; never writes to paper/."""
from pathlib import Path
import hashlib
import json
import os
import sys

ROOT = Path(__file__).resolve().parents[2]
os.environ.setdefault('MPLCONFIGDIR', str(ROOT / 'data/processed/zhh_plot_cache'))
sys.path.append(str(ROOT / 'data/processed/zhh_runtime'))
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager

DATA = ROOT / 'outputs/zhh/q4_core_v3'
OUT = ROOT / 'outputs/zhh/q4_core_v3_visuals'
OUT.mkdir(parents=True, exist_ok=True)
font_path = Path('C:/Windows/Fonts/msyh.ttc')
if font_path.exists():
    font_manager.fontManager.addfont(str(font_path))
    plt.rcParams['font.family'] = font_manager.FontProperties(fname=str(font_path)).get_name()
plt.rcParams.update({'axes.unicode_minus': False, 'font.size': 11,
    'axes.spines.top': False, 'axes.spines.right': False,
    'figure.facecolor': '#f6f8fb', 'axes.facecolor': 'white', 'savefig.dpi': 150})
BLUE, GREEN, RED = '#285caa', '#24856a', '#c15c52'
inputs = {}


def read(path):
    inputs[str(path.relative_to(ROOT)).replace('\\', '/')] = hashlib.sha256(path.read_bytes()).hexdigest()
    return pd.read_csv(path)


def finish(fig, name, footer):
    fig.text(.04, .02, footer, fontsize=10, color='#526076')
    fig.tight_layout(rect=[.02, .065, .98, .94])
    fig.savefig(OUT / name)
    plt.close(fig)


# Exact standardized decomposition, separate from the full-sample composition gap.
history = read(DATA / 'historical_standardized_contributions.csv')
main = history[(history['filter'] == 'primary') & (history.window_months == 2)
    & (history.bin_width_decades == .5) & (~history.developer_control)]
fig, axes = plt.subplots(1, 2, figsize=(14, 6.4))
fig.suptitle('历史能力增长来自哪里？——共同参数规模支持上的均值分解', fontsize=18)
for ax, kind, title in zip(axes, ['non_pretrained', 'pretrained'], ['后训练模型：chat / 领域微调', '基础预训练模型']):
    r = main[main.type == kind].iloc[0]
    start = r.standardized_start
    scale, temporal, end = r.scale_distribution_points, r.within_scale_temporal_points, r.standardized_end
    levels = [(0, start), (start, start+scale), (start+scale, end), (0, end)]
    colors = [BLUE, RED, GREEN, BLUE]
    for i, ((lo, hi), color) in enumerate(zip(levels, colors)):
        ax.bar(i, abs(hi-lo), bottom=min(lo, hi), color=color, width=.62)
        value = [start, scale, temporal, end][i]
        label = f'{value:.2f}' if i in (0, 3) else f'{value:+.2f}'
        ax.text(i, max(lo, hi)+.6, label, ha='center', fontsize=13, color=color)
        if i < 3:
            ax.plot([i+.31, i+1-.31], [hi, hi], color='#9ba7b6', ls='--', lw=1)
    ax.set_xticks(range(4), ['起点均值', '规模分布项', '同规模时间项', '终点均值'])
    ax.set_ylim(0, 30)
    ax.set_ylabel('六任务平均能力（0—100分）')
    ax.set_title(title, fontsize=13, pad=15)
    ax.grid(axis='y', alpha=.15)
    ax.text(.03, .89, f'标准化增长：{r.standardized_change:+.3f} 分\n'
        f'全样本增长：{r.full_observed_mean_change:+.3f} 分\n'
        f'组成 / 支持差：{r.composition_support_gap_points:+.3f} 分', transform=ax.transAxes,
        fontsize=10, va='top', bbox={'facecolor':'white', 'edgecolor':'#dbe2eb', 'alpha':.95})
finish(fig, '01_contributions.png', '同规模时间项仅在组内数据量、样本选择及评测混杂可忽略时解释为技术贡献；组成 / 支持差单列，不计入技术。')

# Forecasts are discrete endpoints: no invented monthly trajectory or predictive coverage.
forecast = read(DATA / 'frontier_candidate_forecasts.csv')
union = read(DATA / 'frontier_scenario_union.csv')
comparison = read(DATA / 'frontier_model_comparison.csv')
fig, axes = plt.subplots(2, 2, figsize=(14, 9), gridspec_kw={'height_ratios':[1.45, 1]})
fig.suptitle('算力增长放缓后的能力前沿与模型诊断', fontsize=18)
names = {'constant':'常数', 'frontier_trend':'前沿趋势', 'mean_resource':'均值资源', 'quantile_resource':'q90资源'}
for col, kind, title in [(0, 'non_pretrained', '后训练模型'),
                         (1, 'pretrained', '基础预训练模型')]:
    anchor = float(forecast[(forecast.type == kind) & (forecast.resource_gate == 'primary')
        & (forecast.compute_scenario == 'half') & (forecast.horizon_months == 12)
        & (forecast.model == 'constant')].iloc[0].score)
    f = forecast[(forecast.type == kind) & (forecast.resource_gate == 'primary')
        & (forecast.compute_scenario == 'half') & forecast.selected_by_diagnostic_rmse].sort_values('horizon_months')
    u = union[(union.type == kind) & (union.resource_gate == 'primary')
        & (union.compute_scenario == 'half')].sort_values('horizon_months')
    assert list(f.horizon_months) == [12, 24]
    assert list(u.horizon_months) == [12, 24]
    ax = axes[0, col]
    ax.scatter([0], [anchor], s=55, color=BLUE, label='观测起点 q90', zorder=5)
    x = f.horizon_months.to_numpy()
    lo, hi = u.scenario_union_lower.to_numpy(), u.scenario_union_upper.to_numpy()
    ax.errorbar(x, (lo+hi)/2, yerr=(hi-lo)/2, fmt='none', lw=9, alpha=.28,
        color='#9cacc1', capsize=9, label='多假设条件范围并集')
    ax.errorbar(x, f.score, yerr=np.vstack([f.score-f.conditional_p05,
        f.conditional_p95-f.score]), fmt='o', color=BLUE, capsize=6, lw=2.5,
        label='主情景点值及块抽样5—95%范围', zorder=4)
    for row in f.itertuples():
        ax.annotate(f'{row.score:.2f}', (row.horizon_months, row.score), xytext=(9, 3), textcoords='offset points', color=BLUE)
    ax.set(title=f'{title}｜从 {f.iloc[0].origin} 起算', ylabel='近期能力前沿（q90，0—100分）',
        xlabel='距数据起点的月份', xticks=[0,12,24], xlim=(-3,29), ylim=(0,100))
    ax.grid(axis='y', alpha=.15)
    if col == 0:
        ax.legend(loc='upper left', fontsize=9)
    scores = comparison[(comparison.type == kind) & (comparison.resource_gate == 'primary')]
    ax = axes[1, col]
    values = scores.rmse.to_numpy()
    best = int(np.argmin(values))
    ax.bar(range(4), values, color=[GREEN if i == best else '#9eafc5' for i in range(4)])
    for i, value in enumerate(values):
        ax.text(i, value+.17, f'{value:.3f}', ha='center', fontsize=10)
    ax.set(xticks=range(4), xticklabels=[names[m] for m in scores.model], ylabel='滚动诊断 RMSE / 分',
        title='相同两个月目标窗口：误差越小越好', ylim=(0,13))
    ax.grid(axis='y', alpha=.15)
finish(fig, '02_frontier_and_validation.png', '放缓情景：历史算力对数增速减半（主口径年倍率约 2.21）；各类仅4个重叠诊断窗。所有范围均无未来覆盖概率保证。')

# Loss maps are source-specific. In-sample curves and LOO errors are explicitly separated.
models = read(DATA / 'bridge_source_coordinate_models.csv')
validation = read(DATA / 'bridge_source_coordinate_validation.csv')
bridge = read(ROOT / 'outputs/zhh/q4_v2/bridge_sample.csv')
fig, axes = plt.subplots(1, 3, figsize=(16, 6.2))
fig.suptitle('Loss 如何连接能力得分？——逐来源建模，比较误差', fontsize=18)
candidates = models[models.diagnostic_primary_candidate].sort_values('coordinate_id')
assert len(candidates) == 2
for ax, r in zip(axes[:2], candidates.itertuples()):
    points = bridge[bridge.Loss_Source == r.coordinate_id]
    assert len(points) == r.n
    grid = np.linspace(r.loss_min, r.loss_max, 150)
    fitted = 100 / (1+np.exp(-(r.a+r.bLoss*grid)))
    ax.scatter(points.Val_Loss, points.S, s=65, color=BLUE, zorder=3, label=f'附件观测：{r.n} 条')
    ax.plot(grid, fitted, color=GREEN, label='来源内单调 logit 拟合')
    ax.set(title='Qwen2.5 来源' if 'Qwen2.5' in r.coordinate_id else 'Qwen2 来源',
        xlabel='该来源的 Loss 坐标', ylabel='六任务平均能力 / 分', ylim=(0,65))
    ax.legend(fontsize=9)
    ax.grid(alpha=.15)
v = validation[validation.coordinate_id.isin(candidates.coordinate_id) |
    validation.coordinate_id.str.startswith('Pythia training log')].copy()
v['short'] = v.coordinate_id.map(lambda s: 'Pythia（高可比）' if s.startswith('Pythia')
    else ('Qwen2.5（中可比）' if 'Qwen2.5' in s else 'Qwen2（中可比）'))
x = np.arange(len(v))
ax = axes[2]
ax.bar(x-.18, v.monotone_LOO_RMSE, width=.36, color=BLUE, label='Loss 映射')
ax.bar(x+.18, v.constant_LOO_RMSE, width=.36, color='#a9b3c3', label='同源常数基线')
for xpos, values in [(x-.18, v.monotone_LOO_RMSE), (x+.18, v.constant_LOO_RMSE)]:
    for xx, yy in zip(xpos, values):
        ax.text(xx, yy+.25, f'{yy:.2f}', ha='center', fontsize=9)
ax.set(xticks=x, xticklabels=v.short, ylabel='留一法 RMSE / 分', title='来源内留一诊断：误差越小越好', ylim=(0,18))
ax.tick_params(axis='x', labelsize=9)
ax.legend(fontsize=9)
ax.grid(axis='y', alpha=.15)
finish(fig, '03_loss_bridge.png', '左两图为训练数据拟合；Qwen仅为附件标签的验证Loss候选。Q3跨来源坐标依赖声明的转换假设，超支持域不换算。')

artifacts = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(OUT.glob('*.png'))}
manifest = {'schema':'zhh.q4.visuals.v3', 'scope':'visualization of frozen results; no refit or paper edit',
    'inputs_sha256':inputs, 'outputs_sha256':artifacts,
    'plot_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    'versions':{'numpy':np.__version__, 'pandas':pd.__version__, 'matplotlib':matplotlib.__version__}}
(OUT / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps({'figures':list(artifacts), 'input_files':len(inputs)}, ensure_ascii=False))
