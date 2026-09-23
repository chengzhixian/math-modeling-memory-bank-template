# cyj 交付约定 草案 v1.1

生产者 cyj；使用者 chm（Q3）、zhh（桥接及论文）。本版为生产者侧草案，尚未取得 chm/zhh 验收，不能标记 validated。

## 已有审计交付

- `outputs/cyj/b_data_audit.json`，schema_version=1，状态为 audit-only。
- 输入版本：`e85956fe7cd3ce7e6a6c8b930ae444b1ee93184d`。
- 生成命令：`python src/cyj/audit_b_scaling_laws.py --input-version <SHA>`；实际 Python 路径和版本见 `problem/cyj/environment.md`。
- 输出字段：逐文件 path/bytes/SHA256/rows/columns/header/missing/duplicate/numeric summary/source metadata，以及 check_id/status/evidence/note。
- 该文件不包含拟合参数或预测，不得作为 Q3 的预测接口。

数据使用边界：B1 为主拟合候选；B2/B3、B4/B5 分别保留作验证；B6–B8 保持半合成标记；B9/B10 只用于外推讨论并先处理非正 D、缺失 FLOPs 与键换行。完整限制见 `problem/cyj/b_data_audit.md`。

## 计划中的模型交付

建议交付：
- 模型说明：Loss 精确定义、尺度、数学表达式、N/D/Q/p 顺序与单位、有效范围、模型族及跨来源假设。
- 参数文件：参数名/估计值、拟合方式、不确定性表达、输入版本、实测/估算/半合成来源标记。具体模型形式由团队确定。
- 可调用预测入口或独立复现命令：输入 N/D/Q/p，输出预测 Loss；同时给出小型真实核验案例和容差。占位案例只能用于接口测试，不能用于论文。
- Q3 理论说明：目标、三项成本、约束、质量基线、边界条件、成本参数来源、结构性转移的识别定义；与 chm 协商实现但不修改 chm 代码。
- 验证结果：B1 拟合、B2/B3、B4/B5、质量补充、B9/B10 外推的分别表现。

输出放 outputs/cyj/，预测实现归 src/cyj/；chm 通过约定接口调用。zhh 使用可比的 Loss 定义和版本，禁止把异质验证损失直接拼接。

模型接口必须另发版本并包含 manifest、参数单位、有效范围、验证结果与小型真实核验案例。在该文件出现并通过实际验证前，消费者不得用审计 JSON 替代预测结果。
