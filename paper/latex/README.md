# Q1 v2 定型论文

当前最新版为 output/chm-q1-v2-latest.pdf，17 页 A4。它是 chm 分支的第一问独立论文，源码入口 q1_final.tex，正文 sections/chm/q1.tex。此版本固定 Q1 交互主模型 chm.q1.v2.0，补入 A12--A15 的 v2 估算压力结果和 30 次训练行重拟合选方敏感性。完整机器结果与结论索引见 outputs/chm/Q1_FINAL_ANSWER_V2.md。

复现命令（在仓库根目录运行）：

    ./src/chm/build_paper.ps1 -SourceName q1_final.tex -OutputName chm-q1-v2-latest

脚本把所需 TeX、参考文献和图片复制到忽略的 .build/ 目录，在本机 MiKTeX 上依次运行 XeLaTeX、BibTeX 和后续 XeLaTeX 轮次，并检查未定义引用、缺字和溢出。output/chm-q1-v2-latest-build.json 记录 PDF 与源文件的 SHA256。生成后仍须逐页检查视觉排版。

原 main.tex 是多成员协作总稿入口，不用于生成这份 Q1 独立论文。若需要四问合稿，应由集成人用各成员已验收的最新版另行总装。本文件夹保留原竞赛模板类与引用格式；最终正式提交格式应由集成人核对当年官方要求。
