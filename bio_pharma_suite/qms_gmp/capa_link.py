"""OOS → CAPA 闭环：一键开立 + 关闭门禁。"""

import frappe
from frappe import _


@frappe.whitelist()
def make_capa_from_oos(oos_name):
	"""从 OOS 预填开立 CAPA，返回新 CAPA 文档（供前端跳转）。"""
	oos = frappe.get_doc("OOS Investigation", oos_name)
	if frappe.db.exists("CAPA", {"oos_investigation": oos_name, "docstatus": ["<", 2]}):
		frappe.throw(
			_("A CAPA already exists for OOS {0}.").format(oos_name),
			title=_("CAPA Already Exists"),
		)

	capa = frappe.new_doc("CAPA")
	capa.source_type = "OOS Investigation"
	capa.oos_investigation = oos_name
	capa.capa_type = "Corrective and Preventive"
	capa.description = _("{0}: {1}").format(
		oos_name,
		oos.get("failed_parameters") or oos.get("conclusion") or _("Out-of-specification result"),
	)
	capa.responsible = oos.responsible
	capa.insert(ignore_permissions=True)
	return capa


@frappe.whitelist()
def make_capa_from_supplier_audit(audit_name):
	"""从供应商审计预填开立 CAPA（防重复）。"""
	audit = frappe.get_doc("Supplier Audit", audit_name)
	if frappe.db.exists("CAPA", {"supplier_audit": audit_name, "docstatus": ["<", 2]}):
		frappe.throw(
			_("A CAPA already exists for Supplier Audit {0}.").format(audit_name),
			title=_("CAPA Already Exists"),
		)

	findings = [f.finding_description for f in (audit.findings or []) if f.severity in ("Critical", "Major")]
	capa = frappe.new_doc("CAPA")
	capa.source_type = "Supplier Audit"
	capa.supplier_audit = audit_name
	capa.capa_type = "Corrective and Preventive"
	capa.description = _("{0}: {1}").format(
		audit_name,
		"; ".join(findings) or audit.get("summary") or _("Supplier audit findings"),
	)
	capa.responsible = audit.lead_auditor
	capa.insert(ignore_permissions=True)
	return capa
