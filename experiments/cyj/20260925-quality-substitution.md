# B7 joint 条件模型的局部与有限替代

脚本 `src/cyj/quality_substitution.py` 读取 joint 输出 `b7_joint_fit.json`，于三个基点 N/D=(.1,20)、(.7,150)、(7,500)，Q0=.5，扫描 Q1=.1…1 共 273 行。输出 `outputs/cyj/quality/substitution_results.csv` SHA256 `468d8df79db3aab215859006c6cca853c01be7cab822aa30b765ef692a9ef86f`，另有 metadata JSON 和四张图。局部公式、单位、有限替代求根及无根处理见 `20260925-q2-q3-mathematics.md`。

Q 上升时等损失 N 或 D 通常下降；在边界附近，一部分目标 Loss 不可由声明支持域内的 N1/D1 实现，CSV 给出 `no_equal_loss_root_in_support` 与空值。图的断线忠实反映无支持域根，不通过外推补线。这些是 joint 曲面的数学条件结论，B7 半合成且并非因果置换实验。
