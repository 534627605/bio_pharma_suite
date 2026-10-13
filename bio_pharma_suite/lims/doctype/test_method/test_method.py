# Copyright (c) 2026 Bio Pharma Suite

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate


class TestMethod(Document):
	"""受控检验方法：版本 + 生效窗口双管控。

	- is_effective 仅在 Approved 且当前日期落在生效窗口内才允许勾选（validate 强制）
	- Lab Sample 提交门禁只允许引用 is_effective=1 的方法（方法受控）
	"""

	def validate(self):
		self.validate_effective_window()

	def validate_effective_window(self):
		if not self.is_effective:
			return
		if self.status != "Approved":
			frappe.throw(
				_("Only Approved methods can be marked Effective"),
				title=_("Controlled Method"),
			)
		today = getdate()
		if self.effective_from and getdate(self.effective_from) > today:
			frappe.throw(_("Effective From cannot be a future date for an Effective method"))
		if self.effective_upto and getdate(self.effective_upto) < today:
			frappe.throw(
				_("Method {0} has expired on {1}; uncheck Effective or raise a new version").format(
					self.method_name, self.effective_upto
				)
			)
