# Bio Pharma Suite — 开发状态快照

> 每轮开工前先读本文件，避免重复探测。每完成一轮开发必须更新本文件。
> 最后更新: 2026-10-24

## 1. 环境事实（勿再探测）

- bench: `/home/my/frappe-bench`, site: `xianghe`, Frappe v16.x
- app 路径: `apps/bio_pharma_suite/bio_pharma_suite/`
- 编译检查: `cd apps/bio_pharma_suite && python3 -m compileall -q bio_pharma_suite`
- 环境卫生: 业务表残留全 0; 无临时脚本; 4 报表已入 tabReport
- heredoc 写 python 会剥 tab → **一律用 editor 工具写文件**
- 直连 python 脚本须 `FRAPPE_STREAM_LOGGING=1`（否则相对路径日志报错）

## 2. 已交付 DocType（25+，六子域）

| 子域 | DocType |
|---|---|
| Compliance Foundation | Data Integrity Settings, Reason Code (+报表: Bio Pharma Audit Trail) |
| LIMS | Lab Sample(+Item/CoC), Test Method, Instrument, Sample Type, Sampling Point, Stability Study(+Timepoint) |
| QMS GMP | Master Formula(+Version), Batch Production Record, Controlled Document, OOS Investigation, CAPA(+Action), Deviation Report, Change Control, Training Record(+Participant), Batch Release Record, Validation Master Plan(+Activity), Supplier Audit |
| Cold Chain | Temperature Zone, Temperature Log, Temperature Excursion(+Batch) |
| Regulatory Affairs | Regulation Library(+Clause), Product License |
| Lab Safety | Waste Disposal Log, Safety Incident |

## 3. 已交付报表（全部已在 DB）

- Batch 360 View (QMS GMP) — Script Report, 列定义在 get_columns()
- Quality KPI Summary (QMS GMP) — Script Report, 近12月滚动
- Bio Pharma Audit Trail (Compliance Foundation) — Query Report, tabVersion 聚合
- Waste Disposal Monthly Summary (Lab Safety) — Script Report

## 4. hooks 集成点（已验证）

- Quality Inspection on_submit → oos_link (Rejected → 自动开 OOS)
- Change Control on_submit → training_link (自动开再培训)
- Delivery Note before_submit → release_guard (未放行批次阻断出库)
- Stock Entry/PR/DN before_submit → cold_chain guards (温区/冻结校验)
- Work Order before_submit → qms_gmp guards (工艺版本门禁)
- scheduler_events: scan_stability_timepoints, scan_calibration_due, scan_product_licence_expiry, scan_validation_overdue

## 5. 关键字段陷阱（写代码前必查）

- 子表字段: VMP Activity 用 `status_row`; CAPA Action 用 `status`; Lab Sample Item 是 Table of "Lab Sample Item"
- Batch 官方无 status → 我们的 custom field `quality_status` (Quarantine/Released/Rejected/...)
- QI status 官方选项: Accepted / Partially Accepted / Rejected
- BRR release_decision: Full Release / Concession Release / Rejected / Scrap / Recall
- JSON Select options 曾出现字面 `\n` 转义 bug（两轮踩坑）→ 新 JSON 生成后必须 grep -rl '\\n' 检查
- Role: Bio Pharma QP / QA Officer / QC Analyst / Lab Supervisor / Release Approver / System Manager

## 6. e2e 测试模式（固化，勿再临时重写）

测试放 `tests/` 目录，运行方式:
`bench --site xianghe execute bio_pharma_suite.tests.test_xxx.run`
标准结构: 预清理(带 HD Customer 联动) → 造数据 → 断言 → finally 清理(cancel 逆序) → 输出 RESULT_JSON

## 7. 路线图状态

- [x] GMP 主链: 偏差/OOS/CAPA/变更/培训/放行双签/COA/VMP/供应商审计
- [x] 审计追踪报表 + KPI 报表 + Batch 360 + 危废月报
- [x] MATLAB API / 仪器接口 / CSV 导入导出 / 条码二维码
- [ ] QI 联检→放行决定自动判定 (BRR 汇总核验已有, 缺自动 release_decision 推荐)
- [ ] Scrap 分支会计科目联检
- [ ] 实验室安全深化 (MSDS/生物风险评估)
- [ ] README 架构图更新至 25+ DocType 全景
