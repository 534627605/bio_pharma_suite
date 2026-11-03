import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, cint


class StabilityStudy(Document):
	def validate(self):
		self.schedule_timepoints()

	def schedule_timepoints(self):
		if not self.start_date:
			return
		for tp in self.get("timepoints") or []:
			if not tp.scheduled_date:
				interval = cint(tp.interval_days) or cint(tp.timepoint_months) * 30
				tp.scheduled_date = add_days(self.start_date, interval)
			if tp.scheduled_date < self.start_date:
				frappe.throw(
					_("Row {0}: scheduled date {1} is before study start date.").format(
						tp.idx, tp.scheduled_date
					),
					title=_("Invalid Timepoint"),
				)

		dates = [tp.scheduled_date for tp in (self.get("timepoints") or [])]
		if len(dates) != len(set(dates)):
			frappe.throw(_("Duplicate scheduled dates in timepoints."), title=_("Invalid Timepoint"))
