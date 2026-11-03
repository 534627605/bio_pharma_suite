import frappe
from frappe import _
from frappe.model.document import Document


class CAPA(Document):
	def validate(self):
		if self.oos_investigation and not frappe.db.exists("OOS Investigation", self.oos_investigation):
			frappe.throw(_("OOS Investigation {0} does not exist.").format(self.oos_investigation))
		if self.deviation_report and not frappe.db.exists("Deviation Report", self.deviation_report):
			frappe.throw(_("Deviation Report {0} does not exist.").format(self.deviation_report))

	def before_submit(self):
		if not self.root_cause:
			frappe.throw(
				_("Root cause analysis is required before closing a CAPA."),
				title=_("Root Cause Missing"),
			)
		if not self.actions:
			frappe.throw(
				_("At least one corrective/preventive action is required before closing a CAPA."),
				title=_("Actions Missing"),
			)
		open_actions = [a for a in self.actions if a.status != "Done"]
		if open_actions:
			frappe.throw(
				_("{0} action(s) are not yet Done. Complete all actions before closing.").format(len(open_actions)),
				title=_("Actions Not Complete"),
			)
		if not self.effectiveness_check:
			frappe.throw(
				_("Effectiveness verification is required before closing a CAPA (GMP requirement)."),
				title=_("Effectiveness Check Missing"),
			)
		if self.effective == "Ineffective":
			frappe.throw(
				_("CAPA is marked Ineffective. Re-open with new actions instead of closing."),
				title=_("CAPA Ineffective"),
			)
		if self.effective != "Effective":
			frappe.throw(
				_("Effectiveness verdict must be 'Effective' before closing a CAPA."),
				title=_("Effectiveness Not Confirmed"),
			)
		if frappe.db.get_single_value("Data Integrity Settings", "require_esignature_on_qi") and not self.esign_confirmed:
			frappe.throw(
				_("E-Signature confirmation is required to close a CAPA (21 CFR Part 11)."),
				title=_("E-Signature Required"),
			)
		self.closed_on = frappe.utils.today()
		self.status = "Closed"

	def on_submit(self):
		# 回写 OOS：CAPA 闭环后将引用写回关联调查单
		if self.oos_investigation and frappe.db.exists("OOS Investigation", self.oos_investigation):
			frappe.db.set_value(
				"OOS Investigation", self.oos_investigation, "capa_reference", self.name
			)
		# 回写偏差报告
		if self.deviation_report and frappe.db.exists("Deviation Report", self.deviation_report):
			frappe.db.set_value("Deviation Report", self.deviation_report, "capa_reference", self.name)
		# 回写供应商审计
		if self.supplier_audit and frappe.db.exists("Supplier Audit", self.supplier_audit):
			frappe.db.set_value("Supplier Audit", self.supplier_audit, "capa_reference", self.name)

	def on_cancel(self):
		if self.oos_investigation and frappe.db.exists("OOS Investigation", self.oos_investigation):
			frappe.db.set_value("OOS Investigation", self.oos_investigation, "capa_reference", None)
		if self.deviation_report and frappe.db.exists("Deviation Report", self.deviation_report):
			frappe.db.set_value("Deviation Report", self.deviation_report, "capa_reference", None)
		if self.supplier_audit and frappe.db.exists("Supplier Audit", self.supplier_audit):
			frappe.db.set_value("Supplier Audit", self.supplier_audit, "capa_reference", None)
