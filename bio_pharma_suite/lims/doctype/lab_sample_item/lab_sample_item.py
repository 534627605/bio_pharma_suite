# Copyright (c) 2026 Bio Pharma Suite

from frappe.model.document import Document


class LabSampleItem(Document):
	"""样品物料行（子表）。

	命名遵循 ERPNext Quality Inspection 的官方约定：
	reference_type="Lab Sample" 的 QI 提交时，set_child_row_reference 会
	按 reference_type + " Item" 规则查找本子表，实现 QI ↔ 样品行
	(child_row_reference) 的官方级联。类名必须为 LabSampleItem
	（框架按 doctype 名机械去空格推导，勿用其他驼峰形式）。
	"""

	pass

