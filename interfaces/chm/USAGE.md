# chm Q1 接口使用说明（chm.q1.v1.2）

维护分支：\`integration/chm-q1-clean-20260923\`。

在仓库根目录验收：
\`\`\`powershell
python src/chm/q1_interface.py
python -m unittest discover -s src/chm -p 'test_q1_interface.py'
\`\`\`

Python：
\`\`\`python
from pathlib import Path
from src.chm.q1_interface import Q1Interface

q1 = Q1Interface(Path("."))
book = q1.quality("book")
mapped = q1.mapped_quality("gutenberg_pg_19")
p = q1.reference.copy()
effect = q1.relative_effect(p, "pile_cc")
validation = q1.ranking_validation("pile_cc")
\`\`\`

\`effect_vector(mixture)\` 一次返回全部 13 个 target 的相对效应；\`interaction_matrix()\` 返回 $13\\times17$ 零和 Ridge 系数矩阵。两者仍属于 A4+A5 的 1M target-loss 坐标，不改变跨尺度和 A→B 桥接边界。

\`relative_effect()\` 定义
\[
m_k(\mathbf p)
=
\sum_j\hat\beta_{k,j}(p_j-p_{{\rm ref},j}).
\]
返回的是 A4+A5 1M target-specific cross-entropy contrast。v1.2 不接受 \(N\)、\(D\) 或 \(\eta\)，也不允许把返回值直接加到 B1 \`val_loss\`。

13 个 target 应优先保持向量形式：
\[
\mathbf m(\mathbf p)
=
(m_1(\mathbf p),\ldots,m_{13}(\mathbf p))^\top.
\]
若需要单一决策指标，权重/保护阈值必须由调用者显式给出；等权只能解释为能力等权情景。
