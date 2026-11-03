# Copyright (c) 2026 Bio Pharma Suite
"""Lab Sample → Quality Inspection 自动联动（Phase 1 收口）。

Lab Sample 提交时：
1. 按检验行逐条自动创建 Quality Inspection 草稿（幂等：同样品+同方法不重复建）；
   QI 以 reference_type="Lab Sample" 直接回指样品，检验数据双向可溯。
2. 延续既有 stability_link.update_stability_results（稳定性结果回写）。
"""

import frappe
from frappe import _
from frappe.utils import today


def on_lab_sample_submit(doc, method=None):
	create_quality_inspections(doc)

	from bio_pharma_suite.lims.stability_link import update_stability_results

	update_stability_results(doc)


def create_quality_inspections(doc):
	"""为每个检验行创建 QI 草稿（状态默认 Accepted，数据齐备后方提交）。"""
	created, skipped = [], 0
	for row in doc.tests or []:
		if not row.test_method:
			continue
		if frappe.db.exists(
			"Quality Inspection",
			{"reference_type": "Lab Sample", "reference_name": doc.name, "test_method_ref": row.test_method},
		):
			skipped += 1
			continue

		qi = frappe.new_doc("Quality Inspection")
		qi.naming_series = "MAT-QA-.YYYY.-"
		qi.inspection_type = "In Process"
		qi.reference_type = "Lab Sample"
		qi.reference_name = doc.name
		qi.company = doc.company
		qi.item_code = doc.item_code or next((r.item_code for r in (doc.get("items") or [])), None)
		if doc.get("batch_no"):
			qi.batch_no = doc.batch_no
		qi.sample_size = 1
		qi.inspected_by = frappe.session.user
		qi.report_date = today()
		qi.lab_sample = doc.name
		qi.test_method_ref = row.test_method
		qi.insert(ignore_permissions=True)
		created.append(qi.name)

	if created:
		frappe.msgprint(
			_("Auto-created Quality Inspection(s) for {0}: {1}").format(doc.name, ", ".join(created))
		)
	return {"created": created, "skipped": skipped}