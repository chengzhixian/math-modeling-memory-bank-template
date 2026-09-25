# CYJ 独立 Q3、v4 接口与总审计交接

## 本次变更

- 以新八参数 joint B7 候选替换本轮独立诊断中的旧两阶段参数，固定 CHM `92e0592000cba58fca355a881dc59caadbd446b2` 求解器源码，扫描 11 预算 × 10 上下文 × 3 成本族。330 场景中 321 可行、9 因支持域最低成本不可行；可行场景含 81 个预算松弛但支持域上界饱和。对数预算扫描与二分给出 180 个数值活跃集变化括区。结果/代码/图见 `experiments/cyj/20260925-q3-joint-conditional-sweep.md`。
- 新增 `cyj.chm.v4` 条件接口、manifest、批量 CLI/期望输出和本地消费者 smoke。v4 使用 joint B7 与 200 次 ND 簇参数重抽；`p` 仅作 A 侧敏感性；不继承历史 v3 参数作当前科学候选。支持域外及非有限输入 fail-fast；科学 metadata 和 `ready_for_Q3=false` 明示。见 `interfaces/cyj/CHM_API_V4.md`。
- 本人 Q2/Q3 论文更新联合参数、嵌套外留级、边际、成本/KKT 与条件结果；结论强度及外部依赖另见 `experiments/cyj/20260925-claim-strength-and-dependencies.md`。新一键脚本 `python -B -m src.cyj.run_full_audit` 校验 14 类证据，输出 `outputs/cyj/audit/full_audit.{json,md}`。

## 证据和复现

Python 3.12.14、NumPy 2.3.5、SciPy 1.18.1、Matplotlib 3.11.2；本机科学运行环境路径见 `problem/cyj/environment.md`。命令 `python -B src/cyj/q3_joint_sweeps.py --starts 20 --transition-points 30`，seed `20260925`。B7 SHA256 `880fd265ca3e1d9bc93b4559af7ed7c18f89040634266c50bae03d88486e0f3a`；joint 模型 SHA256 `c7426036164238d41b92ca08e9ca9087224aeb0c74554478b66093774a5b5b1a`；Q3 主 CSV SHA256 `baa0ce59ddf5e69b603c4f07fcc15bf5da0076ea0a931c1e51c568162d586ce2`。14/14 总审计项 PASS，56/56 本人单测 PASS；统一科学状态 `PASS_WITH_LIMITATIONS`，XeLaTeX 8 页无 overfull。v4 manifest 12 个文件哈希重建一致。精确本次 commit SHA 以 Git 提交及远程核验为准。

## 未解决问题和下一步

1. `BLOCKED_EXTERNAL`，CHM：在 CHM 自己分支消费/验收 `cyj.chm.v4`，采用 B7 D 下界 10 和正式准入关闭的策略，并回传本人验收记录。CYJ 已做本地 pinned CHM solver 与 batch CLI 自测，不能代替 CHM owner 签收。
2. `BLOCKED_EXTERNAL`，ZHH/集成人：提供经正式确认的 Loss--Benchmark 桥接/误差及发布身份；此前不将条件 Q3 解解释为 Q4 结果。
3. `BLOCKED_EXTERNAL`，数据源/团队：B1 生成流程、B4/B5 Loss 同口径、真实训练独立外测均缺证据；这不妨碍已有 CYJ 条件结果，但正式 `ready_for_Q3=false`。
4. cyj：保持 v3 精确历史发布不改；后续若获得新成对证据，先冻结协议再独立验证。其他成员不要把本分支论文候选数字同步为公共正式结论；由集成人审查合并后更新公共记忆。
