# Copyright (c) 2026 Bio Pharma Suite
"""MATLAB 应用 API 接口。

MATLAB 侧通过 webread/webwrite 以 Frappe 原生 token 认证调用：
    opts = weboptions("HeaderFields", {"Authorization", "token <key>:<secret>"});
    r = webread("https://<site>/api/method/bio_pharma_suite.integrations.matlab_api.get_test_requests", opts);
    resp = webwrite(url, weboptions("RequestMethod","post","MediaType","application/json", ...
        "HeaderFields",{"Authorization","token <key>:<secret>"}), struct(...));

三个端点：
- get_test_requests   拉取待检样品 + 方法规格（MATLAB 读取分析任务）
- push_analysis_result 推送计算结果 → 回写 Lab Sample Test（幂等）
- export_dataset      导出数据集（JSON/CSV）供 MATLAB 离线建模
"""

import csv
import io

import frappe
from frappe import _


@frappe.whitelist()
def get_test_requests(sample_status="In Testing", instrument=None):
	"""MATLAB 拉取分析任务：待检样品 + 检验行（方法/规格/仪器）。"""
	filters = {"docstatus": 0, "sample_status": sample_status}
	samples = frappe.get_all(
		"Lab Sample", filters=filters, fields=["name", "sample_no", "item_code", "batch_no"], limit=100
	)
	out = []
	for s in samples:
		tests = frappe.get_all(
			"Lab Sample Test",
			filters={"parent": s.name, "parenttype": "Lab Sample"},
			fields=["test_method", "specification", "instrument", "result_status"],
		)
		if instrument:
			tests = [t for t in tests if t.instrument == instrument]
		if not tests:
			continue
		out.append(
			{
				"sample": s.name,
				"sample_no": s.sample_no,
				"item_code": s.item_code,
				"batch_no": s.batch_no,
				"tests": tests,
			}
		)
	return {"count": len(out), "requests": out}


@frappe.whitelist(allow_guest=False)
def push_analysis_result(sample, test_method, result_value, result_status="Pass", remarks=None):
	"""MATLAB 推送分析结果 → 写回 Lab Sample Test 行（幂等：同方法未出结果则更新）。"""
	if not frappe.db.exists("Lab Sample", sample):
		frappe.throw(_("Lab Sample {0} not found").format(sample), frappe.DoesNotExistError)
	if not frappe.db.exists("Test Method", test_method):
		frappe.throw(_("Test Method {0} not found").format(test_method), frappe.DoesNotExistError)

	doc = frappe.get_doc("Lab Sample", sample)
	if doc.docstatus == 2:
		frappe.throw(_("Cancelled Lab Sample cannot receive results"))

	row = next(
		(
			t
			for t in (doc.get("tests") or [])
			if t.test_method == test_method and not t.result_value
		),
		None,
	)
	if row:
		row.result_value = str(result_value)
		row.result_status = result_status
		row.tested_by = frappe.session.user
		row.tested_on = frappe.utils.now()
		row.remarks = remarks or row.remarks
		if doc.docstatus == 0:
			doc.save(ignore_permissions=True)
		else:
			row.db_update()
	else:
		# 没有匹配行：先检查是否已有同方法结果（幂等保护）
		existing = [
			t for t in (doc.get("tests") or []) if t.test_method == test_method and t.result_value
		]
		if existing:
			return {"sample": sample, "updated": 0, "reason": "result already present"}
		doc.append(
			"tests",
			{
				"test_method": test_method,
				"result_value": str(result_value),
				"result_status": result_status,
				"tested_by": frappe.session.user,
				"tested_on": frappe.utils.now(),
				"remarks": remarks,
			},
		)
		if doc.docstatus == 0:
			doc.save(ignore_permissions=True)
		else:
			doc.tests[-1].db_insert()

	return {"sample": sample, "test_method": test_method, "updated": 1}


@frappe.whitelist()
def export_dataset(doctype="Lab Sample", filters=None, fields=None, limit=500, as_csv=0):
	"""导出数据集给 MATLAB / 外部分析工具（JSON 或 CSV）。"""
	allowed = {
		"Lab Sample": ["name", "sample_no", "item_code", "batch_no", "sample_status", "collection_date"],
		"Temperature Log": ["name", "warehouse", "temperature_zone", "temperature", "reading_timestamp", "has_excursion"],
		"Stability Study": ["name", "item_code", "batch_no", "study_type", "status", "start_date"],
		"Waste Disposal Log": ["name", "waste_type", "quantity", "disposal_date", "status"],
	}
	if doctype not in allowed:
		frappe.throw(_("Export not allowed for {0}. Allowed: {1}").format(doctype, ", ".join(allowed)))
	field_list = fields or allowed[doctype]
	filter_dict = frappe.parse_json(filters) if filters else {}
	rows = frappe.get_all(doctype, filters=filter_dict, fields=field_list, limit=int(limit))

	if int(as_csv):
		buf = io.StringIO()
		writer = csv.DictWriter(buf, fieldnames=field_list)
		writer.writeheader()
		writer.writerows(rows)
		frappe.local.response["type"] = "csv"
		frappe.local.response["filecontent"] = buf.getvalue()
		frappe.local.response["filename"] = f"{doctype}_export.csv"
		return
	return {"doctype": doctype, "count": len(rows), "data": rows}
