import frappe
from frappe import _
from frappe.model.document import Document

BLOCKING_SEVERITIES = ("Critical", "Major")


class SupplierAudit(Document):
	def _finding_capa(self, finding_description: str) -> bool:
		"""审计发现闭环：严重/主要发现必须有已提交且生效的 CAPA。"""
		return bool(
			frappe.db.exists(
				"CAPA",
				{
					"supplier_audit": self.name,
					"docstatus": 1,
					"effective": "Effective",
				},
			)
		)

	def validate(self):
		if self.supplier and not frappe.db.exists("Supplier", self.supplier):
			frappe.throw(_("Supplier {0} does not exist.").format(self.supplier))
		severities = {f.severity for f in self.findings or []}
		if self.overall_rating == "Satisfactory" and severities & {"Critical", "Major"}:
			frappe.throw(
				_("Overall Rating cannot be 'Satisfactory' while Critical/Major findings exist."),
				title=_("Rating Inconsistent"),
			)

	def before_submit(self):
		if not self.summary:
			frappe.throw(
				_("Audit summary is required before closing a Supplier Audit."),
				title=_("Summary Missing"),
			)
		if self.overall_rating == "Pending":
			frappe.throw(
				_("Overall Rating is required before closing a Supplier Audit."),
				title=_("Rating Missing"),
			)
		blocking = [f for f in self.findings or [] if f.severity in BLOCKING_SEVERITIES]
		if blocking and not self._finding_capa(blocking[0].finding_description):
			frappe.throw(
				_("{0} Critical/Major finding(s) exist: a closed and Effective CAPA referencing this audit is required before closing (GMP supplier control).").format(len(blocking)),
				title=_("CAPA Required"),
			)
		if frappe.db.get_single_value("Data Integrity Settings", "require_esignature_on_qi") and not self.esign_confirmed:
			frappe.throw(
				_("E-Signature confirmation is required to close a Supplier Audit (21 CFR Part 11)."),
				title=_("E-Signature Required"),
			)
		self.closed_on = frappe.utils.today()
