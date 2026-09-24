# CYJ Q3 形式敏感性与 v4 上下文扩展交接

## 本次变更

对 B7 联合拟合函数族做 Q3 条件消融：no-Q、恒定 G、单 logN、单 logD 四族各在 36 个预算/上下文/成本情景求解，并与双交互主候选交叉计算条件 regret。输出 144 行、132 可行，发现 N/D 配置随质量函数族显著移动，即使条件 Loss 差很小；详见 `experiments/cyj/20260925-q3-form-sensitivity-{protocol,results}.md`。no-Q 全部可行解采用 Q0=0.5；所有可行解 KKT 数值检查通过，双向 regret 在 `1e-5` 容差内非负。

同时把 v4 条件 API 扩展到 10 个显式上下文，将 4096/16384/24576/30000/32768/49152/65536 标为 CYJ 外生敏感性而非 C7 观测。新增 32768 token 批量 fixture、manifest 锁定的 `q3_costs.py`，边界/NaN 防护及 30000 token attention=training 数值导数测试；v3 旧调用的默认三上下文不变。论文 Q2 说明最弱 95% 留出组覆盖 84%/88%/89%，Q3 说明配置对族敏感。

## 证据和复现

运行 `python -B src/cyj/q3_form_sensitivity.py`，seed `20260925`，替代模型 12 起点、优化 20 起点；B7 SHA256 `880fd265ca3e1d9bc93b4559af7ed7c18f89040634266c50bae03d88486e0f3a`，双交互模型 SHA256 `c7426036164238d41b92ca08e9ca9087224aeb0c74554478b66093774a5b5b1a`，Q3 敏感性 CSV SHA256 `6a265880611a3e5bd47d0a53d00e1ca7c6553e5a9d711697dc30c87bf4252107`。Q3 主网格重新运行后 330 场景/321 可行/180 括区不变，主 CSV SHA256 `baa0ce59ddf5e69b603c4f07fcc15bf5da0076ea0a931c1e51c568162d586ce2`。`python -B -m src.cyj.run_full_audit`：15/15 检查 PASS、60/60 CYJ 单测、XeLaTeX 8 页无 overfull；统一 `PASS_WITH_LIMITATIONS`。v4 扩展上下文本地精确发布 `3471530d91c8ee7eb709e5cd6c824eb9c423e0df`，manifest SHA256 `dcd50430b88cc754e1d8f43a3890013bcc45b07f877b315e9a812d2978fd41f7`，3 请求 exact-object smoke PASS。首次推送两次遭 GitHub 连接重置/443 失败，当前远端同步待最终核验。

## 未解决与负责人

- CHM：在自己的分支验收新的 v4 manifest/批量请求；确认使用 B7 的 D 下界 10，区分 C7 候选与 CYJ 外生上下文。标记 `BLOCKED_EXTERNAL`，CYJ 本地真实 pinned 求解器/CLI 消费测试不能代替其签收。
- ZHH/集成人：提供 Loss--Benchmark 桥接和误差传播正式产物；此前 Q3 不转换为 Q4 结论。标记 `BLOCKED_EXTERNAL`。
- 数据源/团队：B1 生成及跨 B4/B5 口径、真实训练独立外测仍未知。正式科学门槛 `ready_for_Q3=false`；本轮函数族敏感性不能消除此限制。
