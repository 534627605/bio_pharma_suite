import frappe
from frappe import _
from frappe.model.document import Document


class DeviationReport(Document):
	def validate(self):
		if self.capa_reference and not frappe.db.exists("CAPA", self.capa_reference):
			frappe.throw(_("CAPA {0} does not exist.").format(self.capa_reference))

	def before_submit(self):
		if not self.immediate_action:
			frappe.throw(
				_("Immediate action is required before submitting a deviation report."),
				title=_("Immediate Action Missing"),
			)
		if self.severity in ("Critical", "Major"):
			if not self.capa_reference:
				frappe.throw(
					_("Critical/Major deviations require a closed CAPA before submission (GMP)."),
					title=_("CAPA Required"),
				)

	def on_submit(self):
		# 联动官方 Quality Management：自动开立 Non Conformance（幂等）
		if not self.ncr_reference:
			procedure = frappe.db.get_value("Quality Procedure", {}, "name")
			ncr = frappe.new_doc("Non Conformance")
			ncr.subject = _("Deviation {0}").format(self.name)
			ncr.issue = self.description
			if procedure:
				ncr.procedure = procedure
			ncr.insert(ignore_permissions=True)
			self.db_set("ncr_reference", ncr.name)
			frappe.msgprint(
				_("Official Non Conformance {0} auto-created for deviation {1}.").format(ncr.name, self.name)
			)
