# Copyright (c) 2026 Bio Pharma Suite

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, nowdate


class ControlledDocument(Document):
	"""体系文件受控：四级层级（质量手册/程序文件/SOP/记录模板）。

	编号规则（层级码-部门-流水号-版本）由 Phase 2 的 Document Number Rule 提供；
	本层先以 document_code=name 承载，层级与版本随字段演进。
	"""

	def validate(self):
		if self.name:
			self.document_code = self.name
		self.validate_effective_window()

	def validate_effective_window(self):
		if self.effective_from and self.effective_upto:
			if getdate(self.effective_from) > getdate(self.effective_upto):
				frappe.throw(
					_("Effective From cannot be later than Effective Upto"),
					title=_("Invalid Validity Window"),
				)
		if self.document_status == "Effective":
			today = getdate(nowdate())
			if self.effective_upto and getdate(self.effective_upto) < today:
				frappe.throw(
					_("Document validity has expired — cannot stay in Effective status"),
					title=_("Document Expired"),
				)
