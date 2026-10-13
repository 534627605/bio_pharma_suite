"""冷链与批次冻结约束（Guard）：注入 Purchase Receipt / Delivery Note / Stock Entry 的 before_submit。"""

import frappe
from frappe import _


def validate_stock_movement(doc, method=None):
	"""提交前校验：①批次冻结阻断 ②冷链物料温区/GMP 仓库匹配。"""
	if not frappe.db.get_single_value("Data Integrity Settings", "cold_chain_guard_enabled"):
		return

	require_qualified = frappe.db.get_single_value(
		"Data Integrity Settings", "cold_chain_require_qualified_warehouse"
	)

	for row in doc.get("items") or []:
		# ① 批次冻结阻断（Batch.quality_status == Hold）
		batch_no = getattr(row, "batch_no", None)
		if batch_no and frappe.db.get_value("Batch", batch_no, "quality_status") == "Hold":
			frappe.throw(
				_("Row #{0}: Batch {1} (Item {2}) is on Quality Hold. Stock movement is blocked until QA disposition.").format(
					row.idx, batch_no, row.item_code
				),
				title=_("Batch on Quality Hold"),
			)

		# ② 冷链温区匹配
		if not frappe.db.get_value("Item", row.item_code, "requires_cold_chain"):
			continue

		item_condition = frappe.db.get_value("Item", row.item_code, "storage_condition")
		warehouses = set()
		for attr in ("s_warehouse", "t_warehouse", "warehouse", "target_warehouse", "source_warehouse"):
			if getattr(row, attr, None):
				warehouses.add(getattr(row, attr))

		for wh in warehouses:
			if require_qualified and not frappe.db.get_value("Warehouse", wh, "qualified_for_gmp"):
				frappe.throw(
					_("Row #{0}: cold chain item {1} cannot move through non GMP-qualified warehouse {2}.").format(
						row.idx, row.item_code, wh
					),
					title=_("Cold Chain Guard"),
				)
			wh_zone = frappe.db.get_value("Warehouse", wh, "temperature_zone")
			if wh_zone:
				zone_condition = frappe.db.get_value("Temperature Zone", wh_zone, "storage_condition")
				if item_condition and zone_condition != item_condition:
					frappe.throw(
						_("Row #{0}: storage condition mismatch — cold chain item {1} requires '{2}' but warehouse {3} is zone '{4}'.").format(
							row.idx, row.item_code, item_condition, wh, zone_condition
						),
						title=_("Cold Chain Guard"),
					)
			elif require_qualified:
				frappe.throw(
					_("Row #{0}: warehouse {1} must define a Temperature Zone to receive cold chain item {2}.").format(
						row.idx, wh, row.item_code
					),
					title=_("Cold Chain Guard"),
				)


def create_shipment_temperature_record(doc, method=None):
	"""Orchestrate：冷链出库强制携带运输温度随行记录（DocType 于 Phase 2 交付前防御式提醒）。"""
	item_codes = {row.item_code for row in doc.get("items") or []}
	has_cold_chain = any(
		frappe.db.get_value("Item", item_code, "requires_cold_chain") for item_code in item_codes
	)
	if not has_cold_chain:
		return
	if not frappe.db.exists("DocType", "Shipment Temperature Record"):
		frappe.msgprint(
			_("Cold chain delivery detected — attach the temperature recorder data of this shipment for archive. (Shipment Temperature Record automation lands in Phase 2)"),
			indicator="orange",
		)
		return
