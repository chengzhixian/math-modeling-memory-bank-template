# 第四至七章参考文献修订交接

用户授权：查找近年权威来源、只增加引用与书目，并修改匹配 LaTeX 源文件生成 PDF。用户随后提供桌面 RAR；此次修订严格以该压缩包源文件为准，不改写原始 PDF 或压缩包。

分支 docs/paper-citations-20260926，从 origin/main c6b36c08b5a85c81a3889d48d50c26ac136a048b 建立。完成 Gadre + 10篇新增文献的官网核验，第四至七章12处 cite，共13篇被引用文献。OpenLM 数据集引用为第6.6.3节第一段“公开的 OpenLM 训练记录”之后，最终编号[9]，原GitHub脚注保留。

交付目录 paper/citation_revision_20260926：修订PDF、revised_project完整源文件及图片、INSERTION_GUIDE.md、references_verified.bib、CHANGE_MANIFEST.json、QA/checks.json。source-cited.zip 为本地源文件打包产物，不重复入库；原解压包和可再生渲染图不入库。

验证：移除新增 cite 后全部章节与原压缩包字节一致；图片字节一致。XeLaTeX/BibTeX通过，无未定义引用、缺字或超宽盒；46页逐页渲染检查，重点页放大核验。此次新PDF46页，用户之前上传PDF47页，分页变化已在清单说明。原模板未闭合条件分支已修复；LiSu缺失时回退KaiTi；书目标题可点击权威来源。

本任务未采用历史数据说明隐藏文字、未重算或改动模型结论、未修改公共六个记忆文件。原有Kaplan/Hoffmann记录和键保留。引用只支撑方法/背景，不替本文原创映射、题面成本系数或数值结果背书。

下一步：集成人自行验收此分支的论文副本，依据实际提交流程选用。远端状态由push及ls-remote核验后报告，不预写成功。
