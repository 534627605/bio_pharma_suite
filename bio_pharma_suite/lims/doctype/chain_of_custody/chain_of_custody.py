# Copyright (c) 2026 Bio Pharma Suite

from frappe.model.document import Document


class ChainofCustody(Document):
	"""样品流转记录：每次交接需扫码确认（scan_verified），满足样品链条完整可审计

	注意类名：Frappe 按单据名去空格推导类名（Chain of Custody → ChainofCustody），
	故此类名必须为 ChainofCustody 而非 CamelCase 的 ChainOfCustody。
	"""

	pass


# 兼容别名：外部代码若引用 ChainOfCustody 仍可用
ChainOfCustody = ChainofCustody