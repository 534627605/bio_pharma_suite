app_name = "bio_pharma_suite"
app_title = "Bio Pharma Suite"
app_publisher = "Bio Pharma Suite Team"
app_description = "Bio Pharma / Food & Drug Inspection Compliance Suite for ERPNext"
app_email = "admin@example.com"
app_license = "mit"

# ------------------------------------------------------------------
# add_to_apps_screen: 应用九宫格入口
# ------------------------------------------------------------------
add_to_apps_screen = [
	{
		"name": app_name,
		"logo": "/assets/bio_pharma_suite/images/bio-pharma-suite.svg",
		"title": "Bio Pharma Suite",
		"route": "/desk/bio-pharma-suite",
		"sequence_id": 50,
	}
]

required_apps = ["erpnext"]

# ------------------------------------------------------------------
# fixtures: 扩展字段随 app 安装导入
# ------------------------------------------------------------------
fixtures = [
{"dt": "Custom Field", "filters": [["module", "=", "Bio Pharma Suite"]]},
{"dt": "Property Setter", "filters": [["module", "=", "Bio Pharma Suite"]]},
{"dt": "Workspace", "filters": [["module", "=", "Compliance Foundation"]]},
{"dt": "Sidebar", "filters": [["module", "=", "Compliance Foundation"]]},
{"dt": "Dock", "filters": [["app", "=", "bio_pharma_suite"]]},
# 官方 Quality 模块侧边栏扩展（零侵入：Custom Sidebar 增量层）
{"dt": "Custom Sidebar", "filters": [["name", "=", "bps_quality_sidebar"]]},
{"dt": "Print Format", "filters": [["module", "=", "QMS GMP"]]},
]

# after_migrate: 每次迁移同步自定义字段（可重入，修复 patch 一次性创建导致的定义漂移）
after_migrate = "bio_pharma_suite.install.after_migrate"

# ------------------------------------------------------------------
# doc_events: 三类注入（补充Extend / 约束Guard / 联动Orchestrate）
# ------------------------------------------------------------------
doc_events = {
"Quality Inspection": {
"before_submit": "bio_pharma_suite.qms_gmp.guards.validate_quality_inspection",
"on_submit": "bio_pharma_suite.qms_gmp.oos_link.create_oos_from_qi",
},
"Purchase Receipt": {
"before_submit": "bio_pharma_suite.cold_chain.guards.validate_stock_movement",
},
"Delivery Note": {
"before_submit": [
"bio_pharma_suite.cold_chain.guards.validate_stock_movement",
"bio_pharma_suite.qms_gmp.release_guard.validate_batch_release",
],
"on_submit": "bio_pharma_suite.cold_chain.guards.create_shipment_temperature_record",
},
"Stock Entry": {
"before_submit": "bio_pharma_suite.cold_chain.guards.validate_stock_movement",
},
"Work Order": {
"before_submit": "bio_pharma_suite.qms_gmp.guards.validate_work_order",
"on_submit": "bio_pharma_suite.qms_gmp.guards.assemble_batch_production_record",
},
"Lab Sample": {
"on_submit": "bio_pharma_suite.lims.qi_link.on_lab_sample_submit",
},
"Safety Incident": {
"on_submit": "bio_pharma_suite.lab_safety.escalation.escalate_incident",
},
"Change Control": {
"on_submit": "bio_pharma_suite.qms_gmp.training_link.create_retraining_from_change",
},
}

# ------------------------------------------------------------------
# scheduler_events: 每日巡检
# ------------------------------------------------------------------
scheduler_events = {
"daily": [
"bio_pharma_suite.tasks.scan_calibration_due",
"bio_pharma_suite.tasks.scan_product_licence_expiry",
"bio_pharma_suite.tasks.scan_stability_timepoints",
"bio_pharma_suite.tasks.scan_validation_overdue",
]
}
