# Copyright (c) 2026 Bio Pharma Suite

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, nowdate


class MasterFormula(Document):
	"""工艺规程：BOM+Routing 的受控版本投影层（生产执行数据仍在 ERPNext 核心单据）。"""

	def validate(self):
		self.validate_bom_item()
		self.validate_active_version()

	def validate_bom_item(self):
		bom_item = frappe.db.get_value("BOM", self.bom_no, "item")
		if bom_item and bom_item != self.item_code:
			frappe.throw(
				_("BOM {0} belongs to item {1}, not {2}").format(self.bom_no, bom_item, self.item_code),
				title=_("BOM Mismatch"),
			)

	def validate_active_version(self):
		currents = [v for v in self.versions if v.is_current]
		if len(currents) > 1:
			frappe.throw(
				_("Only one version can be marked Current at a time (found {0})").format(len(currents)),
				title=_("Version Control"),
			)
		if not currents:
			self.active_version = None
			return
		v = currents[0]
		today = getdate(nowdate())
		if v.effective_from and getdate(v.effective_from) > today:
			frappe.throw(
				_("Version {0} is not effective yet (from {1})").format(v.version, v.effective_from),
				title=_("Version Control"),
			)
		if v.effective_upto and getdate(v.effective_upto) < today:
			frappe.throw(
				_("Version {0} has expired on {1}").format(v.version, v.effective_upto),
				title=_("Version Control"),
			)
		self.active_version = v.version

	def get_effective_version(self):
		for v in self.versions:
			if v.is_current:
				return v
		return None
