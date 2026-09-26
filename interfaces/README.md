# 三条工作线的交接接口

> 2026-09-26 集成状态：下文的计划接口和旧分支观察保留作历史记录。当前 Q1 正式接口 `chm.q1.v2.0`，Q2 条件接口 `cyj.ndqp.scenario.v8`，Q3 使用该 v8 冻结生产者给出条件优化；精确来源和数值清单见 `outputs/Q1`、`outputs/Q2`、`outputs/Q3`。A/B 的质量与 Loss 坐标仍未成对标定，不得把条件桥接写成实证识别。

Q1 v2 清单 `interfaces/chm/q1_interface_v2.json` 保留原发布路径及 SHA256；main 的同字节九个输入现位于 `outputs/Q1/`，`src/chm/q1_interface_v2.py` 将原路径只读映射至该目录并逐文件复核哈希。个人生产分支仍使用原 `outputs/chm/q1_v2/` 路径，不能改写其冻结发布包。

Q2 v8 的正式条件接口说明和 18 组冻结请求/预期样例已按问题归入 [`interfaces/Q2`](Q2/README.md)。原来源路径仍可由 `outputs/Q2/upstream_manifest.json` 和固定 CYJ 提交定位；CYJ 对 CHM Q3 v8 的独立消费者签收尚在其远端任务清单中。

本文件由集成人维护；a/、b/、c/ 的接口说明由对应生产者维护。当前均为计划接口，没有真实结果；生产者与使用者须在 09-23 18:00 前核对字段后确认 v1。不得把建议字段当成已经存在的附件字段。

| 交接 | 生产者 → 使用者 | 第一版最晚时间 | 正式交付最晚时间 |
|---|---|---|---|
| 质量定义、域映射与配比输出 | chm → cyj | 09-24 12:00 质量部分 | 09-24 18:00 Q1 完整 |
| 标度律、目标函数、约束和有效范围 | cyj → chm | 09-24 12:00 接口与经典基线 | 09-24 22:00 验证版 |
| C7 支持的上下文取值表 | zhh → chm/cyj | 09-23 18:00 | 09-24 12:00 复核版 |
| 可比 Loss 定义和模型版本 | cyj → zhh | 09-24 18:00 | 09-24 22:00 验证版 |
| 优化配置和不确定性 | chm → zhh | 09-25 12:00 | 09-25 15:00 |

每次交付附 manifest：接口名/版本、draft 或 validated、生产者、生成命令、代码版本（由交付 Git 提交或显式 SHA 定位）、输入路径/哈希、输出文件/哈希、行数/形状、字段与单位、随机种子、适用域、验证和局限。数据文件保存在 outputs/chm|cyj|zhh/；较大产物提供团队获取方式。

消费者须记录实际读取的版本与哈希，检查必需字段、单位、有限值、约束和适用范围。拒绝静默用旧缓存替代缺失输入。变更列名、单位、域顺序、评分尺度或模型定义时发新版本，旧版不覆盖，交接列明受影响任务与重跑范围。占位或半合成输出显式标注来源；占位仅用于流程调试。

## 2026-09-23 当前接口状态与强制协作点

本节覆盖文件开头早期“均为计划接口、没有真实结果”的初始化描述；该旧描述仅代表项目启动时状态。

### 个人分支当前状态（尚未自动视为 main validated）

| 接口 | 当前个人分支状态 | 消费限制 |
|---|---|---|
| chm → cyj：Q/p | `team/chm-data` 已有 p 的逐目标域 Ridge、尺度传递 draft；质量 Q 尚待 A1–A3 LFS 实跑 | p 可用于方法联调，但 Q 未冻结；正式 Q2 必须记录精确 chm SHA |
| cyj → chm：Scaling predictor | `team/cyj-scaling` 仅完成 B 审计；尚无验证版 predictor | Q3 只能搭框架，不得产出正式最优配置 |
| zhh → chm/cyj：C7 | `team/zhh-frontier` 已有 2048 / 8192 / 131072 Token 情景 | 作为外生敏感性情景；正式采用前由 zhh 更新合同并通过集成验收 |
| cyj/chm → zhh：Loss | 尚未形成统一正式 Loss 输出 | zhh 不得用异质 Loss 直接做最终能力映射 |
| zhh：Loss→Benchmark | 个人分支已有基线，但外推较弱 | 只能作带误差映射，不得确定性转换 |

### 两个必须联合冻结的接口

**A. Q 坐标：chm + cyj**

chm 的 Q1 评分与 B6–B8 的 `Q_score` 不在天然同一尺度。双方必须明确主 mapping、敏感性 mapping 和有效范围后，cyj 才能将 Q 接入广义标度律。

**B. p→Loss：chm + cyj**

chm 的 p 接口有 13 个具体 domain Loss；B1 只有泛化 `val_loss`。双方必须共同确定 Q2 Loss 定义、主 anchor、敏感性 target、p 项的函数形式和适用范围。禁止默认 `pile_cc == B1 val_loss`。

详细规则见 `TEAM_COLLABORATION_DEPENDENCIES.md`。

### 消费者同步规则

接收任何跨成员接口前：

```powershell
git fetch origin --prune
git switch <本人分支>
git pull --ff-only
git merge origin/main
```

若暂不合并 main，至少读取：

```powershell
git show origin/main:TEAM_COLLABORATION_DEPENDENCIES.md
git show origin/main:memory-bank/activeContext.md
git show origin/main:interfaces/README.md
```

个人分支上的 draft 接口可以提前联调，但必须记录精确 SHA；只有验收并进入 main 的版本才是默认正式输入。
