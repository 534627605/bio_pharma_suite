app_name = "bio_pharma_suite"
app_title = "Bio Pharma Suite"
app_publisher = "Bio Pharma Suite Team"
app_description = "Bio Pharma / Food & Drug Inspection Compliance Suite for ERPNext"
app_email = "admin@example.com"
app_license = "mit"

required_apps = ["erpnext"]

# ------------------------------------------------------------------
# fixtures: 扩展字段随 app 安装导入
# ------------------------------------------------------------------
fixtures = [
{"dt": "Custom Field", "filters": [["module", "=", "Bio Pharma Suite"]]},
{"dt": "Property Setter", "filters": [["module", "=", "Bio Pharma Suite"]]},
{"dt": "Workspace", "filters": [["module", "=", "Bio Pharma Suite"]]},
]

# ------------------------------------------------------------------
# doc_events: 三类注入（补充Extend / 约束Guard / 联动Orchestrate）
# ------------------------------------------------------------------
doc_events = {
"Quality Inspection": {
"before_submit": "bio_pharma_suite.qms_gmp.guards.validate_quality_inspection",
},
"Purchase Receipt": {
"before_submit": "bio_pharma_suite.cold_chain.guards.validate_stock_movement",
},
"Delivery Note": {
"before_submit": "bio_pharma_suite.cold_chain.guards.validate_stock_movement",
"on_submit": "bio_pharma_suite.cold_chain.guards.create_shipment_temperature_record",
},
"Stock Entry": {
"before_submit": "bio_pharma_suite.cold_chain.guards.validate_stock_movement",
},
"Work Order": {
"before_submit": "bio_pharma_suite.qms_gmp.guards.validate_work_order",
"on_submit": "bio_pharma_suite.qms_gmp.guards.assemble_batch_production_record",
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
]
}
