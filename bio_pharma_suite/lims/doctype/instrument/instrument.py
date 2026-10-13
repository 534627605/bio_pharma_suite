# Copyright (c) 2026 Bio Pharma Suite

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, getdate


class Instrument(Document):
	"""仪器台账：校准到期由 scheduler（tasks.scan_calibration_due）自动隔离，
	被隔离仪器不得继续用于检验（Lab Sample Test.instrument 仅允许 Active）。"""

	def validate(self):
		self.set_next_calibration_date()
		self.validate_status_change()

	def set_next_calibration_date(self):
		"""下次校准日 = 上次校准日 + 校准周期（落库后由每日巡检监控）"""
		if self.last_calibration_date and self.calibration_frequency_days and not self.next_calibration_date:
			self.next_calibration_date = add_days(
				getdate(self.last_calibration_date), self.calibration_frequency_days
			)

	def validate_status_change(self):
		"""校准过期后不得手工改回 Active（须先完成校准并更新校准日期）"""
		if self.status == "Active" and self.next_calibration_date:
			if getdate(self.next_calibration_date) < getdate():
				frappe.throw(
					_(
						"Next Calibration Date ({0}) has passed. Instrument cannot be marked Active "
						"until recalibration is recorded."
					).format(self.next_calibration_date)
				)