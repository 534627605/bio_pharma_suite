from frappe.model.document import Document
from frappe.utils import today, date_diff


class ProductLicense(Document):
	def validate(self):
		if self.issue_date and self.expiry_date and self.issue_date > self.expiry_date:
			from frappe import _
			from frappe.exceptions import ValidationError

			raise ValidationError(_("Issue Date cannot be after Expiry Date"))
		self.refresh_status()

	def refresh_status(self):
		if not self.expiry_date:
			return
		days = date_diff(self.expiry_date, today())
		if days < 0:
			self.status = "Expired"
		elif days <= (self.reminder_days or 90):
			self.status = "Expiring Soon"
		else:
			self.status = "Valid"
