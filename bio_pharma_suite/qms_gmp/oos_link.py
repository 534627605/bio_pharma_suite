"""Orchestrate：Quality Inspection 提交判定 Rejected → 自动创建 OOS Investigation。"""

import frappe
from frappe import _


def _collect_failed_parameters(doc):
	"""从 QI readings 中提取不合格项（防御式读取，字段缺失时降级为提示文本）。"""
	parts = []
	for r in doc.get("readings") or []:
		status = (r.get("status") or "").strip().lower()
		if status in ("rejected", "fail", "failed"):
			parameter = r.get("parameter") or r.get("specification") or "Reading"
			result = r.get("result") or r.get("mean") or "-"
			parts.append(f"{parameter}: {result}")
	return "\n".join(parts)


def create_oos_from_qi(doc, method=None):
	"""QI on_submit：status=Rejected 时自动开立 OOS Investigation（幂等）。"""
	if doc.status != "Rejected":
		return
	if frappe.db.exists("OOS Investigation", {"quality_inspection": doc.name}):
		return

	failed = _collect_failed_parameters(doc)

	oos = frappe.new_doc("OOS Investigation")
	oos.quality_inspection = doc.name
	oos.lab_sample = doc.get("lab_sample") or None
	oos.failed_parameters = failed or "See Quality Inspection readings"
	oos.phase = "Phase I - Laboratory Investigation"
	oos.status = "Open"
	oos.responsible = doc.get("inspected_by") or None
	oos.insert(ignore_permissions=True)

	frappe.msgprint(
		_("OOS Investigation {0} auto-created for rejected Quality Inspection {1}.").format(
			oos.name, doc.name
		)
	)
