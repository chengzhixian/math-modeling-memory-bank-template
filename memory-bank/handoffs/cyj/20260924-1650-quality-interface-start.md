# cyj：原生质量模型与接口完善检查点

起点 `4ad0084453ce50f44119d444b1996a3343c65a7d`；分支 team/cyj-scaling。fetch 后无冲突合并 main `968ef7a36f1503aa222a0b09c8a8cb5d0f535ecd`，merge `55889bf2b942ca9643f49e420035a9f051f2bed3`。main 恢复空白论文模板；本轮只完善本人代码/接口。CHM 最新 `b97d7a4c2e5bfbb8326e17b054518aefc22a01c6` 的 interfaces/chm 相对既定 `7c14a0c` 无改动，继续使用固定旧 SHA。zhh `d47cd2dc921333caecfcb95f09eb5a2f2714d0db` 合同仍滞后，不能代其验收。

已读取规则、公共/本人记忆、接口请求；修正 Q3_API 的 B8 calibrated 拟合建议，与合同隔离决定一致。新增 B7 原生候选、留组验证、bootstrap 与 QualityPredictor 的代码及测试；运行前方案见 `experiments/cyj/20260924-b7-quality-protocol.md`。没有将其标记为已拟合。

复现：代码提交后 `python -B src/cyj/quality_scaling.py --input-version <代码SHA>`，运行全部 unittest。真实实验尚未运行，结果/哈希/样例在下一份交接记录；本检查点保留工作，随后正常 push 并 ls-remote 核验。原始 CSV 不改动。跨 A/B Q、Loss/p 和 Benchmark 仍未识别，正式 Q3/Q4 状态不变。下一步 cyj 执行冻结方案、验证梯度/样本与拒绝非法调用；chm/zhh 接收后仅作限定域联调。
