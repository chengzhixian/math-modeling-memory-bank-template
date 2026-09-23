# chm→cyj Q1 生产者接口交接

日期：2026-09-24（北京时间）；工作分支：`integration/chm-q1-clean-20260923`。

用户已确定按专业归属分工：chm 定义 A 侧 Q/p，cyj 直接消费；cyj 定义 B 侧标度律、Loss/anchor、预测器和 Q3 理论，chm 直接消费。chm 现发布 `chm.q1.v1`，入口 `interfaces/chm/CONTRACT.md`、机器清单 `interfaces/chm/q1_interface_v1.json`、调用说明 `interfaces/chm/USAGE.md`、只读实现 `src/chm/q1_interface.py`。清单锁定 7 个质量域、17 个配比域、13 个目标 Loss 及六个现有产物的 SHA256/行数，不生成重复数据文件。`CYJ_REQUIRED_INTERFACE.md` 列出需 cyj 定义的消费者侧依赖。

验收：`python src/chm/q1_interface.py` 校验文件身份和结构；`python -m unittest discover -s src/chm -p 'test_q1*.py' -q` 通过；参考配比相对效应为 0，非法配比报错，inferred 域返回 null；真实样例数值见 USAGE。数据说明只用可见正文，原始资料及其他成员文件未改。

尚未解决：A `Q_z` 与 B `Q_score` 无配对标定；A 13 域 Loss 与 B1 `val_loss` 无已证同口径桥接；η 是条件尺度情景，不能代替跨 Loss λ。由 cyj 交付其正式预测器、Q/anchor/p 使用规则和 Q3 成本理论；chm 收到后按其合同写适配器并验收，不在此分支代定义 B 模型。最终 Q3 仍取决于 cyj 正式 predictor 及 zhh C7 合同验收。
