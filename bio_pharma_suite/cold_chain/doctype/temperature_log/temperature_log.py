# Copyright (c) 2026 Bio Pharma Suite

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class TemperatureLog(Document):
	def validate(self):
		self.temperature_zone = frappe.db.get_value("Warehouse", self.warehouse, "temperature_zone")
		self.has_excursion = 0
		if self.temperature_zone and self.temperature is not None:
			zmin, zmax = frappe.db.get_value(
				"Temperature Zone", self.temperature_zone, ["min_temperature", "max_temperature"]
			)
			if flt(self.temperature) < flt(zmin) or flt(self.temperature) > flt(zmax):
				self.has_excursion = 1

	def on_submit(self):
		if self.has_excursion and frappe.db.get_single_value(
			"Data Integrity Settings", "excursion_auto_hold"
		):
			exc_name = make_temperature_excursion(self)
			self.db_set("excursion", exc_name)


def make_temperature_excursion(log):
	"""Orchestrate: 越限读数自动创建 QA 评估事件（受影响批次由 QA 界定后处置）"""
	ext = frappe.new_doc("Temperature Excursion")
	ext.warehouse = log.warehouse
	ext.temperature_zone = log.temperature_zone
	ext.temperature_log = log.name
	ext.excursion_start = log.reading_timestamp
	ext.peak_temperature = log.temperature
	ext.disposition = "Pending"
	ext.status = "Open"
	ext.insert(ignore_permissions=True)
	ext.add_comment(
		"Comment",
		_("Out-of-range reading {0} C at warehouse {1} (zone {2}). QA to identify affected batches and record disposition.").format(
			log.temperature, log.warehouse, log.temperature_zone
		),
	)
	return ext.name
