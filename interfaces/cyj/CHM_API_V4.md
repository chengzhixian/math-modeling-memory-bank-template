# CYJ → CHM joint B7 条件接口 v4

本地精确发布检查点为 `team/cyj-scaling@c11629a032fdca8c0a366b732227711410b305d9`；远端同 SHA 已核对。manifest SHA256 `14ca8049ddf2ab9bd24e804f7bfcb223426ec38882c8814187127162ee128e2c`，exact-object consumer smoke 对 2 个批量请求 PASS。后续 CYJ Q3 诊断脚本的演进不改变这个不可变接口发布身份。

入口 `src/cyj/chm_adapter_v4.py::CHMAdapterV4(mode="conditional_diagnostic")`。本版把八参数联合约束最小二乘、200 次 N-D 簇 bootstrap 与嵌套留级残差接入接口；v3 精确发布保持历史两阶段参数，不在原位改写。

`bounds=((.07,11.97),(10,600),(.1,1))`，N/D 单位十亿参数/十亿 token，Q 为 B7 原生无量纲质量分数，Loss 为 B7 原生半合成 `val_loss`。`value_grad(N_B,D_B,Q)` 返回 Loss 与解析梯度；`elasticities()` 保留带符号的 `x L_x/L` 语义，`improvement_elasticities()` 显式返回 `-x L_x/L`。`substitution_rates()` 含等损失局部 N/Q 与 D/Q 替代率；有限变化及域内无根由 `src/cyj/quality_substitution.py` 给出。

`evaluate()` 返回 B 原生预测、梯度、两种弹性、替代率、条件经验区间、成本与预算检查；可选 `p` 仅返回固定 CHM Q1 v1.2 的 13 target 敏感性，不加进 B Loss。支持 2048/4096/8192/16384/24576/30000/32768/49152/65536/131072 token；仅 2048/8192/131072 标记为原 C7 候选，其余在 `context_policy` 和逐次成本输出中标记为 CYJ 外生敏感性，不冒充 C7 观测。不在清单内的上下文直接报错。顶层及 `capabilities()` 明示 `scientific_status`、`candidate_result_scope`、`formal_result_scope`、`support`、`source_dataset`、`source_hash`、`model_hash`、`ready_for_Q3=false`。无 A/B 换算、无旧 eta、无默认 lambda、无支持域外静默外推。

区间由 200 个 joint 参数 bootstrap 预测加抽样的 N 轴嵌套 OOF 残差构成，`calibrated_coverage_claim=false`。另一个内层残差对称区间在 B7 外层留级达到约 95% 同源覆盖，但方法不同，不能把该数字归给接口区间。B7 函数族历史上看过全 B7、数据半合成、真实训练独立验证和 CHM 所有者验收都未完成，因此正式 Q3 gate 关闭。

在仓库根目录运行：

```powershell
python -B src/cyj/build_chm_release_v4.py
python -B src/cyj/chm_adapter_v4.py --describe
python -B src/cyj/chm_adapter_v4.py --request outputs/cyj/interfaces/chm_v4_request.json
python -B src/cyj/chm_consumer_smoke_v4.py --release-commit c11629a032fdca8c0a366b732227711410b305d9
```

CHM `92e0592` 的 `solve_generic` 需要本人模块 `Support` 对象。消费者沿用 v3 文档中的 `bounds → Support` 包装，但内部上游改为 `CHMAdapterV4`，并把 B7 D 下界固定为 10。SLSQP 对数变换的数值边界误差只允许机器精度级处理；越界输入直接拒绝。CYJ 自己的稠密条件扫描记录在 `outputs/cyj/q3/`，仍须 CHM 所有者在本人分支消费并记录验收。
