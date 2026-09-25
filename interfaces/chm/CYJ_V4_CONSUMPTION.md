# CYJ v4 条件消费说明

状态：CHM 所有者验收通过（条件 NDQ）；正式 gate 仍关闭。

```python
from cyj_v4_consumer import consume_release, SolverAdapter
from q3_generic_solver import solve_generic
with consume_release() as (producer, manifest, smoke):
    solution, trials = solve_generic(
        SolverAdapter(producer), budget=1e22, context_tokens=8192,
        Q0=.5, family="power", starts=24)
```

需已 fetch cyj 的不可变提交 3471530d91c8ee7eb709e5cd6c824eb9c423e0df；运行环境安装 numpy/scipy，src/chm 在 PYTHONPATH。加载器验证 manifest 和文件哈希，临时导出后自动清理，不覆盖 CYJ 文件、不复制拟合参数进 CHM 主模型。N/D 单位为十亿，D 下界是 10。producer 本身严格拒绝域外点；SolverAdapter 只修复 exp(log(bound)) 的 8 ulp 级边界误差，不允许实际外推。

可用 context 及 C7/外生角色读取 manifest.context_policy。A 的 p 对比独立于 B Loss；不把 A 的 Q 与 B 的 Q_score 等同。v4 固定历史 Q1 v1.2，当前 v1.3 配比系数/参考一致、A 质量分数不同，下一版本需 CYJ 更新元数据。

全局界只在 q3_joint_certificate 明确检查的模型符号条件下适用。通用 SLSQP 的 KKT 仅必要条件；求解失败不得发布为成功。输出验收文件见 outputs/chm/q3_cyj_v4_acceptance；总区间与正式发布仍等待科学门禁通过。
