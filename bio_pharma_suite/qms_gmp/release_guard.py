"""批放行出库门禁（Guard）：未放行（Released）的成品/API 批次禁止销售出库。

GMP 最后一环：QP 双签放行（Batch Release Record）之前，批次 quality_status 为
Quarantine / Hold，Delivery Note 提交即被阻断。入库（Purchase Receipt）与内部
转移（Stock Entry）不受此门禁限制——放行约束只针对面向市场的交付。
"""

import frappe
from frappe import _

# 需要放行才能销售的 GMP 类别
RELEASE_CONTROLLED_CATEGORIES = {"Finished Product", "API", "Biological Product"}


def _license_blocked(item_code):
	"""该物料的注册证是否失效（Expired / Revoked）。无关联证照则不阻断。"""
	if not frappe.db.exists("DocType", "Product License"):
		return None

	lic = frappe.db.get_value(
		"Product License",
		{"item_code": item_code, "status": ["in", ["Expired", "Revoked"]]},
		["name", "license_no", "status"],
		as_dict=True,
	)
	return lic or None


def validate_batch_release(doc, method=None):
	"""Delivery Note before_submit：受控类别的批次必须 quality_status == Released，
	且关联注册证必须有效。"""
	if not frappe.db.get_single_value("Data Integrity Settings", "batch_release_guard_enabled"):
		return

	for row in doc.get("items") or []:
		batch_no = getattr(row, "batch_no", None)
		if not batch_no:
			continue

		category = frappe.db.get_value("Item", row.item_code, "gmp_category")
		if category not in RELEASE_CONTROLLED_CATEGORIES:
			continue

		quality_status = frappe.db.get_value("Batch", batch_no, "quality_status")
		if quality_status != "Released":
			frappe.throw(
				_(
					"Row #{0}: Batch {1} (Item {2}, GMP category '{3}') is '{4}' — only Released batches can be delivered to market. Complete Batch Release with dual QP sign-off first."
				).format(row.idx, batch_no, row.item_code, category, quality_status or "Quarantine"),
				title=_("Batch Not Released"),
			)

		lic = _license_blocked(row.item_code)
		if lic:
			frappe.throw(
				_(
					"Row #{0}: Item {1} cannot be delivered — Product License {2} is {3}. Renew the license in Regulatory Affairs first."
				).format(row.idx, row.item_code, lic.license_no, lic.status),
				title=_("License Expired"),
			)
