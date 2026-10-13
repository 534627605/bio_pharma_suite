# Copyright (c) 2026 Bio Pharma Suite

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, get_datetime


class TemperatureExcursion(Document):
	def validate(self):
		if self.disposition and self.disposition != "Pending":
			self.status = "Under Investigation"
		if self.excursion_start and self.excursion_end:
			delta = get_datetime(self.excursion_end) - get_datetime(self.excursion_start)
			self.duration_minutes = max(0, cint(delta.total_seconds() // 60))

	def before_submit(self):
		if self.disposition in (None, "Pending"):
			frappe.throw(
				_("QA disposition must be recorded before closing the excursion."),
				title=_("Disposition Required"),
			)
		if not self.investigation_summary:
			frappe.throw(
				_("Investigation summary is required before closing the excursion."),
				title=_("Investigation Required"),
			)

	def on_submit(self):
		self.apply_disposition()
		self.db_set({"released_by": frappe.session.user, "status": "Closed"})

	def apply_disposition(self):
		if not self.affected_batches:
			frappe.msgprint(
				_("No affected batches recorded — no batch quality status was changed.")
			)
			return
		new_status = "Released" if self.disposition == "Release Batches" else "Hold"
		for row in self.affected_batches:
			frappe.db.set_value("Batch", row.batch_no, "quality_status", new_status)
			frappe.msgprint(_("Batch {0} set to {1}").format(row.batch_no, new_status))
