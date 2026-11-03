import frappe
from frappe import _
from frappe.model.document import Document


class WasteDisposalLog(Document):
	def validate(self):
		if self.handled_by and self.verified_by and self.handled_by == self.verified_by:
			frappe.throw(
				_("Handler and verifier must be different users (segregation of duties)."),
				title= _("Segregation of Duties"),
			)

		if self.docstatus == 1 and not self.disposal_method:
			frappe.throw(_("Disposal Method is required before submission."))
