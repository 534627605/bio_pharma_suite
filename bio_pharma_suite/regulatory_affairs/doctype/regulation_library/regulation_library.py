# Copyright (c) 2026 Bio Pharma Suite

from frappe.model.document import Document


class RegulationLibrary(Document):
	"""法规条款库：中国 GMP / GSP / 食品安全法 / ICH / 21 CFR / 药典条款一处维护，
	被 Controlled Document / Deviation / OOS / Change Control 以 Link 引用为法规依据。
	"""

	pass
