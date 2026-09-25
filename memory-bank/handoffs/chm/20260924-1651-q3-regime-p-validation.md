# chm 交接：Q3 连续预算、结构转移与配比选择验证

日期：2026-09-24
分支：integration/chm-q1-clean-20260923
状态：阶段性 diagnostic/scenario 成果，正式 Q3 仍 blocked

## 本阶段完成

1. 建立连续预算 regime scan，解析得到 N_min_bound → interior → D_max_bound → support_corner 四段。
2. 用 25 起点 L-BFGS-B 与解析解交叉验证，最佳 Loss 最大差约 4.44e-16，N/D 最大相对误差约 4.23e-08。
3. 建立 A-side 配比优化选择验证：A4/A5 拟合，A6/A8/A10 预测选择，A7/A9/A11 真实 Loss 评估。
4. 全 39 个 scale-target 中 25 次精确选中真实最优，34 次进入前 10%；主五 target 为 11/15 精确最优、14/15 前 10%。
5. 识别 1B target-dependent 风险以及训练支持候选极端化风险。
6. 数学上确认：当前线性 p 代理在固定 target、lambda>0 下不会产生预算驱动的 p 排序切换，因此不把 p 结构转移写成当前模型结论。

## 仍未满足

- cyj ready_for_Q3=true；
- B7 native Q 实际 fit 与消费者接口；
- B1/B7 Loss 处理；
- p primary anchor / lambda_loss 正式状态；
- zhh versioned C7 合同；
- 总不确定性。

## 下一步

在等待上游期间，可继续做质量成本三函数的纯成本几何/临界条件和 formal solver 插件测试；不得用虚构 Q 性能项生成最终配置。上游版本变化后先重跑 q3_preflight，再决定是否切 formal。
