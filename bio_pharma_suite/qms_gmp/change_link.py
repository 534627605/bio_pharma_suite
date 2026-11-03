"""变更控制联动：从 CAPA 一键开立变更单。"""

import frappe
from frappe import _


@frappe.whitelist()
def make_change_control_from_capa(capa_name):
	"""从 CAPA 预填开立 Change Control，返回新单（供前端跳转）。"""
	capa = frappe.get_doc("CAPA", capa_name)
	if frappe.db.exists(
		"Change Control", {"capa_reference": capa_name, "docstatus": ["<", 2]}
	):
		frappe.throw(
			_("A Change Control already exists for CAPA {0}.").format(capa_name),
			title=_("Change Control Already Exists"),
		)

	cc = frappe.new_doc("Change Control")
	cc.change_type = "Document Change"
	cc.title = _("Change arising from CAPA {0}").format(capa_name)
	cc.reason = capa.get("description") or ""
	cc.capa_reference = capa_name
	cc.requested_by = capa.get("responsible")
	cc.insert(ignore_permissions=True)
	return cc
