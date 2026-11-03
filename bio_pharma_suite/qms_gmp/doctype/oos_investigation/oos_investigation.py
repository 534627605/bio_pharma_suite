import frappe
from frappe import _
from frappe.model.document import Document


class OOSInvestigation(Document):
	def _capa_closed(self) -> bool:
		"""GMP 偏差闭环：结论为 OOS Confirmed 时，必须存在已提交且生效的 CAPA。"""
		return bool(
			frappe.db.exists(
				"CAPA",
				{
					"oos_investigation": self.name,
					"docstatus": 1,
					"effective": "Effective",
				},
			)
		)

	def validate(self):
		if (
			self.re_test_quality_inspection
			and self.re_test_quality_inspection == self.quality_inspection
		):
			frappe.throw(
				_("Re-test Quality Inspection must differ from the original."),
				title=_("Invalid Re-test Reference"),
			)

	def before_submit(self):
		if not self.investigation_summary:
			frappe.throw(
				_("Investigation summary is required before closing an OOS."),
				title=_("Investigation Incomplete"),
			)
		if self.conclusion == "Pending":
			frappe.throw(
				_("Conclusion is required before closing an OOS."),
				title=_("Investigation Incomplete"),
			)
		if self.conclusion == "OOS Confirmed" and not self._capa_closed():
			frappe.throw(
				_("Conclusion is 'OOS Confirmed': a closed CAPA must exist before closing this OOS (GMP deviation-to-CAPA loop)."),
				title=_("CAPA Required"),
			)
		if frappe.db.get_single_value(
			"Data Integrity Settings", "require_esignature_on_qi"
		) and not self.esign_confirmed:
			frappe.throw(
				_("E-Signature confirmation is required to close an OOS (21 CFR Part 11)."),
				title=_("E-Signature Required"),
			)
		self.closed_on = frappe.utils.today()
