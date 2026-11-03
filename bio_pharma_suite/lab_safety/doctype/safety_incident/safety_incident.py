import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import today


class SafetyIncident(Document):
	def validate(self):
		if self.docstatus == 1:
			self.validate_investigation()
		if self.status == "Closed" and not self.closed_on:
			self.closed_on = today()

	def validate_investigation(self):
		if not (self.root_cause or "").strip():
			frappe.throw(
				_("Root Cause is required before submitting a Safety Incident."),
				title=_("Investigation Incomplete"),
			)
		if not (self.corrective_action or "").strip():
			frappe.throw(
				_("Corrective Action is required before submitting a Safety Incident."),
				title=_("Investigation Incomplete"),
			)
