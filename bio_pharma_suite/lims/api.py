# Copyright (c) 2026 Bio Pharma Suite
"""条码 / 二维码应用场景 API。

移动端或扫码枪场景：
- resolve_scan: 扫 1D 条码（样品号）或 QR（记录 URL）→ 返回样品档案 + 待办上下文
- log_custody_handover: 扫码确认交接 → 写入 Chain of Custody（scan_verified=1）
"""

import frappe
from frappe import _
from frappe.utils import now_datetime


def _extract_record_name(scanned):
	"""兼容三种扫码载荷：纯样品号 / 表单 URL / app 路径。"""
	scanned = (scanned or "").strip()
	if not scanned:
		frappe.throw(_("Scanned value is empty"))
	# /app/lab-sample/LS-00001 或 ...?name=LS-00001
	if "/lab-sample/" in scanned:
		return scanned.split("/lab-sample/")[-1].split("?")[0].split("#")[0].strip("/")
	if "name=" in scanned:
		for part in scanned.split("?")[-1].split("&"):
			if part.startswith("name="):
				return part.split("=", 1)[1]
	return scanned


@frappe.whitelist()
def resolve_scan(scanned):
	"""扫码 → 样品档案（1D: sample_no；QR: URL）。供移动端/扫码枪调用。"""
	if not _doctype_ready("Lab Sample"):
		frappe.throw(_("Lab Sample doctype is not ready"), title=_("LIMS Not Installed"))

	name = _extract_record_name(scanned)
	sample = frappe.db.get_value(
		"Lab Sample",
		name,
		["name", "sample_no", "sample_status", "item_code", "batch_no", "due_date", "docstatus"],
		as_dict=True,
	)
	if not sample:
		frappe.throw(_("No Lab Sample found for scanned code: {0}").format(name), title=_("Scan Failed"))

	return {
		"doctype": "Lab Sample",
		"name": sample.name,
		"sample_no": sample.sample_no,
		"status": sample.sample_status,
		"item_code": sample.item_code,
		"batch_no": sample.batch_no,
		"due_date": sample.due_date,
		"form_url": frappe.utils.get_url_to_form("Lab Sample", sample.name),
	}


@frappe.whitelist()
def log_custody_handover(scanned, custody_action="Handover", location=None, purpose=None):
	"""扫码确认样品交接：免手工填报，自动记录 from=当前用户、时间戳、scan_verified。"""
	if not _doctype_ready("Lab Sample"):
		frappe.throw(_("Lab Sample doctype is not ready"), title=_("LIMS Not Installed"))

	name = _extract_record_name(scanned)
	sample = frappe.get_doc("Lab Sample", name)
	if sample.docstatus == 2:
		frappe.throw(_("Cancelled Lab Sample cannot change custody"))

	sample.append(
		"custody_log",
		{
			"custody_action": custody_action,
			"from_party": frappe.session.user,
			"custody_datetime": now_datetime(),
			"location": location,
			"purpose": purpose,
			"scan_verified": 1,
		},
	)
	# 已提交单据走子表直接落库（不触发全量回写）
	if sample.docstatus == 1:
		sample.custody_log[-1].db_insert()
	else:
		sample.save()

	frappe.msgprint(_("Custody recorded via scan for {0}").format(name))
	return {"name": name, "recorded": 1}


def _doctype_ready(name):
	return frappe.db.exists("DocType", name)