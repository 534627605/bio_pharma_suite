# Bio Pharma Suite

生物医药 / 食药检验检疫行业合规套件（ERPNext v16）。五个子域：合规基建、LIMS、QMS-GMP（含工艺文件与法规条款库）、冷链、法规事务。

设计原则：零侵入 ERPNext 核心——扩展字段走 fixtures，流程约束走 doc_events，自动联动走 on_submit/scheduler。

架构文档：../../docs/bio_pharma_suite_architecture.md
