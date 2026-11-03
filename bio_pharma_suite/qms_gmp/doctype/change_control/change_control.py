import frappe
from frappe import _
from frappe.model.document import Document


class ChangeControl(Document):
	def validate(self):
		if self.controlled_document and not frappe.db.exists(
			"Controlled Document", self.controlled_document
		):
			frappe.throw(
				_("Controlled Document {0} does not exist.").format(self.controlled_document)
			)
		if self.capa_reference and not frappe.db.exists("CAPA", self.capa_reference):
			frappe.throw(_("CAPA {0} does not exist.").format(self.capa_reference))

	def before_submit(self):
		if not self.impact_assessment:
			frappe.throw(
				_("Impact assessment is required before submitting a Change Control (GMP requirement)."),
				title=_("Impact Assessment Missing"),
			)
		if self.status not in ("Approved", "Implemented"):
			frappe.throw(
				_("Change Control must be Approved or Implemented before submission. Current status: {0}.").format(
					self.status
				),
				title=_("Change Not Approved"),
			)
		if (
			frappe.db.get_single_value("Data Integrity Settings", "require_esignature_on_qi")
			and not self.esign_confirmed
		):
			frappe.throw(
				_("E-Signature confirmation is required to close a Change Control (21 CFR Part 11)."),
				title=_("E-Signature Required"),
			)

	def on_submit(self):
		self.db_set("status", "Closed")
		self.db_set("closed_on", frappe.utils.today())
		frappe.msgprint(
			_("Change Control {0} closed. Remember to update affected Controlled Documents and re-train users.").format(
				self.name
			)
		)
