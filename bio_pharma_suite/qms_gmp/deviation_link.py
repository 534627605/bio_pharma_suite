"""偏差 → CAPA 闭环：一键开立 + 回写。"""

import frappe
from frappe import _


@frappe.whitelist()
def make_capa_from_deviation(deviation_name):
	"""从偏差报告预填开立 CAPA，返回新 CAPA 文档（供前端跳转）。"""
	dev = frappe.get_doc("Deviation Report", deviation_name)
	if frappe.db.exists("CAPA", {"deviation_report": deviation_name, "docstatus": ["<", 2]}):
		frappe.throw(
			_("A CAPA already exists for Deviation {0}.").format(deviation_name),
			title=_("CAPA Already Exists"),
		)

	capa = frappe.new_doc("CAPA")
	capa.source_type = "Deviation Report"
	capa.deviation_report = deviation_name
	capa.capa_type = "Corrective and Preventive"
	capa.description = _("{0}: {1}").format(deviation_name, dev.get("description") or _("Deviation"))
	capa.responsible = dev.get("detected_by")
	capa.insert(ignore_permissions=True)
	return capa
