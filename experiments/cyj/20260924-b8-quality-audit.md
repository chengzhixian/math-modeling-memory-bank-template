# B8 质量方向与跨文件坐标审计

2026-09-24，cyj。结论：B8 不能仅凭 calibrated 标签并入 B6/B7 的共同质量标度律。此为数据兼容性诊断，不认定官方数据有误，也不改写任何原始值。

## 输入与复现

- 数据/清单输入提交 `cebd51bd0116ef3194728cfbeed9569239e085db`；main 已合并版本 `7d8081fbf50cd380904505759c116580356f102d`。
- 三个原始 CSV 均通过 F_MANIFEST 的 bytes/SHA256 校验；完整身份及执行代码 SHA256 写入 `outputs/cyj/diagnostics/b_quality_audit.json`。本轮新脚本以代码内容哈希标识，不能把输入提交称为新脚本代码提交。
- 输出 SHA256 `1d9576dc63bdc078b72f0dd530e8b568bed68ca3ad905c49543ee0d3c734684d`。
- Windows / bundled Python 3.12.14，无随机过程。以下 `$py` 为运行时路径变量。

```powershell
$py = 'C:/Users/muyehuangyi/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
& $py -B src/cyj/diagnose_b_quality.py --input-version cebd51bd0116ef3194728cfbeed9569239e085db
& $py -B -m unittest discover -s src/cyj/tests
Get-FileHash outputs/cyj/diagnostics/b_quality_audit.json -Algorithm SHA256
```

## 已验证结果

固定 N,D，对 Q 排序后比较相邻 Loss；不池化不同 N,D，也不设任意显著性阈值。端点是每组实际最小/最大 Q，不同组范围可能不同。数值比较针对文件显示值，不推断潜在未舍入值。

| 子集 | 行数 | N,D 组数 | Q 相邻 Loss 升/降/平 | Q 两端 Loss 升/降 |
|---|---:|---:|---:|---:|
| B6 | 360 | 45 | 80/235/0 | 0/45 |
| B7 | 450 | 45 | 102/303/0 | 0/45 |
| B8 calibrated | 984 | 90 | 825/1/68 | 90/0 |
| B8 extrapolated | 720 | 60 | 486/1/173 | 60/0 |

B6/B7 并非处处单调下降，B8 也非处处上升，不能用总体方向抹去局部逆序。N、D 的条件相邻统计同时保存于 JSON。

- B6 的 360 个 N,D,Q 坐标和 Loss 全部原样出现在 B7，合并后只有 450 个独特坐标。两文件间切训练/测试会泄漏。
- B6/B8 160 个同坐标全部 Loss 不同；B7/B8 224 个同坐标也全部不同，B8−B7 范围 [-2.5769,0.0569]。例：N=0.07B、D=10B、Q=0.5，B7 第 362 行 Loss=3.568，B8 第 15 行 Loss=2.0372；实验 ID 相同。这里行号含表头，完整例证在 JSON。
- B8 共 362/1704 行 Loss 恰为最小值 0.5，其中 calibrated 129 行、extrapolated 233 行。这提示检查生成器是否存在截断，但**尚未证实存在 clipping，也不能把 0.5 认作真实不可约 Loss**。
- B8 calibrated 的 N 取值为 0.07/0.16/0.41/0.7/1/2.8/4/6.9/12B，extrapolated 为 20/40/70/120/300/700B。标签与这两个 N 集合分离；标签不是独立观测证据。

## 对接口与下一步的影响

chm 可立即使用 `Q3_API.md` 中 B1 diagnostic、显式 lambda/eta/p scenario、三成本族和约束导数。当前不能进行正式含 Q 的 Q3 优化；不允许将 B8 趋势反向接入 `Q_score` 成本函数，也不能以 `1-Q` 静默修复。

zhh 可使用 B1 条件 bootstrap 与上述数据风险作为独立不确定性来源，但不能把 B8 extrapolated 或 B6/B7 重复行作为外部验证；Loss–Benchmark 桥接误差仍须单独传播。`ready_for_Q3=false` 不变。

下一步 cyj：基于去重 B7 做原生 Q 的候选模型比较与组级留出，始终标半合成；另查 B8 原始生成说明、Q 方向、Loss 评估口径与最小值堆积来源。未获得证据前隔离 B8，两组模型不强行统一。chm+cyj 仍需冻结 Q 尺度、Loss anchor 和 lambda，zhh 确认 C7 情景。集成人验收后汇总公共状态。

## 验证、参考与清理

单元测试 29/29 通过，包括新加混合方向、重复坐标拒绝、同坐标不同 Loss 和单点组测试。数据诊断两次确定性复现哈希一致（按最终代码）；无新模型拟合或因果解释。原始 CSV 不变、没有生成中间 CSV 或缓存，保留一个 JSON 结果与必要代码/测试。

仅阅读 main 的 `references/award_papers/README.md`，采用“结论附近给范围、统计量、例证和限制”的组织方式；本轮没有独立阅读索引链接的原文 PDF，不据此声称论文奖项/方法经过本轮验证。电子表格技能用于保留原始记录、区分诊断与来源、核查重复及数值边界；未创建或修改 Excel 工作簿。
