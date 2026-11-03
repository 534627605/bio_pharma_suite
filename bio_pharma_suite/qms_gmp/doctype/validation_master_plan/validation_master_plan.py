import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import today


class ValidationMasterPlan(Document):
	def validate(self):
		self.total_activities = len(self.activities)
		self.overdue_count = sum(
			1 for a in self.activities if a.status_row in ("Planned", "In Progress", "Overdue") and a.planned_end and a.planned_end < today()
		)

	def before_submit(self):
		open_rows = [a.subject for a in self.activities if a.status_row != "Completed"]
		if open_rows:
			frappe.throw(
				_("All validation activities must be Completed before submitting the plan. Open: {0}.").format(
					", ".join(open_rows[:5])
				),
				title=_("Validation Activities Incomplete"),
			)
		missing_reports = [a.subject for a in self.activities if not a.report_no]
		if missing_reports:
			frappe.throw(
				_("Validation report number is required for: {0}.").format(", ".join(missing_reports[:5])),
				title=_("Report Number Missing"),
			)
		if (
			frappe.db.get_single_value("Data Integrity Settings", "require_esignature_on_qi")
			and not self.esign_confirmed
		):
			frappe.throw(
				_("E-Signature confirmation is required to close a Validation Master Plan (21 CFR Part 11)."),
				title=_("E-Signature Required"),
			)

	def on_submit(self):
		self.db_set("status", "Completed")
		self.db_set("closed_on", frappe.utils.today())
		frappe.msgprint(_("Validation Master Plan {0} completed.").format(self.name))
