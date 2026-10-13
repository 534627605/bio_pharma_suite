# Copyright (c) 2026 Bio Pharma Suite

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class TemperatureZone(Document):
	def validate(self):
		if flt(self.min_temperature) > flt(self.max_temperature):
			frappe.throw(_("Min Temperature cannot be greater than Max Temperature"))
