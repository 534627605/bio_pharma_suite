# Copyright (c) 2026 Bio Pharma Suite

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_url_to_form, getdate


class LabSample(Document):
	"""实验室样品全生命周期 + 双码（1D 条码 / 二维码）追溯。

	- sample_no / sample_barcode 均取自单据名（LS-#####），1D 码供扫码枪即扫即得
	- sample_qr 载荷为直达本样品表单的 URL，移动端扫码直接打开记录
	"""

	def validate(self):
		self.set_identification_codes()
		self.validate_due_date()
		self.validate_tests()

	def set_identification_codes(self):
		"""回填双码：autoname 之后 name 才可用（validate 与 after_insert 双保险）"""
		if self.name:
			self.sample_no = self.sample_no or self.name
			self.sample_barcode = self.sample_no
			self.sample_qr = get_url_to_form(self.doctype, self.name)

	def after_insert(self):
		# insert 流程中 set_new_name 可能晚于 validate，插入后确保双码落库
		if not (self.sample_barcode and self.sample_qr):
			self.set_identification_codes()
			frappe.db.set_value(
				self.doctype,
				self.name,
				{
					"sample_no": self.sample_no,
					"sample_barcode": self.sample_barcode,
					"sample_qr": self.sample_qr,
				},
				update_modified=False,
			)

	def validate_due_date(self):
		if self.due_date and self.collection_date:
			if getdate(self.due_date) < getdate(self.collection_date):
				frappe.throw(
					_("Due Date cannot be earlier than the Collection Date"),
					title=_("Invalid Due Date"),
				)

	def validate_tests(self):
		methods = [row.test_method for row in (self.tests or []) if row.test_method]
		if len(methods) != len(set(methods)):
			frappe.throw(_("Duplicate Test Methods are not allowed in one Lab Sample"))

	def before_submit(self):
		"""提交门禁：至少一项检验、且全部引用生效中的检验方法（方法受控）"""
		if not self.tests:
			frappe.throw(
				_("At least one test is required before submitting the Lab Sample"),
				title=_("Submission Blocked"),
			)
		for row in self.tests:
			if row.test_method and not frappe.db.get_value("Test Method", row.test_method, "is_effective"):
				frappe.throw(
					_("Row #{0}: Test Method {1} is not Effective").format(row.idx, row.test_method),
					title=_("Controlled Method Required"),
				)
