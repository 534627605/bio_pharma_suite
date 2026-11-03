"""QI reference_type Select 选项扩展：追加 Lab Sample（零侵入，Property Setter）。"""

import frappe
from frappe.custom.doctype.property_setter.property_setter import make_property_setter


def execute():
	if not frappe.db.exists("DocType", "Quality Inspection"):
		return
	df = frappe.get_meta("Quality Inspection").get_field("reference_type")
	if not df:
		return
	options = df.options or ""
	if "Lab Sample" in options.split("\n"):
		return
	ps_name = make_property_setter(
		"Quality Inspection", "reference_type", "options", options + "\nLab Sample", "Select"
	)
	if ps_name:
		try:
			frappe.db.set_value(
				"Property Setter", ps_name, "module", "Bio Pharma Suite", update_modified=False
			)
		except Exception:
			pass