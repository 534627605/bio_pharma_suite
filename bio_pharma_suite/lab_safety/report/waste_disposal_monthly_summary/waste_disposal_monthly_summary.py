# Copyright (c) 2026, Bio Pharma Suite Team and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import get_first_day, get_last_day, today


def execute(filters=None):
	filters = frappe._dict(filters or {})
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{"label": _("Disposal Month"), "fieldname": "disposal_month", "fieldtype": "Data", "width": 110},
		{"label": _("Waste Type"), "fieldname": "waste_type", "fieldtype": "Data", "width": 130},
		{"label": _("Disposal Method"), "fieldname": "disposal_method", "fieldtype": "Data", "width": 170},
		{"label": _("Records"), "fieldname": "record_count", "fieldtype": "Int", "width": 90},
		{"label": _("Total Quantity"), "fieldname": "total_qty", "fieldtype": "Float", "width": 140},
		{"label": _("UOM"), "fieldname": "uom", "fieldtype": "Data", "width": 90},
		{"label": _("Verified Records"), "fieldname": "verified_count", "fieldtype": "Int", "width": 130},
		{"label": _("Licensed Contractor Records"), "fieldname": "contractor_count", "fieldtype": "Int", "width": 190},
	]


def get_data(filters):
	from_date = filters.get("from_date") or get_first_day(today())
	to_date = filters.get("to_date") or get_last_day(today())
	conditions = "AND wdl.disposal_date BETWEEN %(from_date)s AND %(to_date)s"
	values = {"from_date": from_date, "to_date": to_date}

	return frappe.db.sql(
		"""
		SELECT
			DATE_FORMAT(wdl.disposal_date, '%%Y-%%m') AS disposal_month,
			wdl.waste_type,
			wdl.disposal_method,
			COUNT(wdl.name) AS record_count,
			SUM(wdl.quantity) AS total_qty,
			MAX(wdl.uom) AS uom,
			SUM(wdl.status = 'Verified') AS verified_count,
			SUM(wdl.disposal_method = 'Licensed Contractor') AS contractor_count
		FROM `tabWaste Disposal Log` wdl
		WHERE wdl.docstatus < 2 {conditions}
		GROUP BY disposal_month, wdl.waste_type, wdl.disposal_method, wdl.uom
		ORDER BY disposal_month DESC, wdl.waste_type, wdl.disposal_method
		""".format(conditions=conditions),
		values=values,
		as_dict=1,
	)
