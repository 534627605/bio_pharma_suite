# Copyright (c) 2026
# Quality KPI Summary: monthly aggregated KPIs across the quality chain.
# Feeds management review / official Quality Goal with objective numbers.

import frappe
from frappe import _


MONTH_FMT = "%Y-%m"


def _month_range(from_date, to_date):
	"""Inclusive list of 'YYYY-MM' buckets between from_date and to_date."""
	months = []
	cur = frappe.utils.getdate(from_date)
	end = frappe.utils.getdate(to_date)
	while cur <= end:
		months.append(cur.strftime(MONTH_FMT))
		# advance to next month
		cur = frappe.utils.add_months(frappe.utils.getdate(cur.strftime("%Y-%m-01")), 1)
	return months


def _count_by_month(doctype, date_field, from_date, to_date, extra=None):
	"""Return {month: count} for non-cancelled docs grouped by month of date_field."""
	# datetime columns need end-of-day bound, else same-day records are excluded
	to_dt = f"{to_date} 23:59:59"
	rows = frappe.get_all(
		doctype,
		filters=[[date_field, ">=", from_date], [date_field, "<=", to_dt], ["docstatus", "<", 2]],
		pluck=date_field,
	)
	out = {}
	for d in rows:
		m = frappe.utils.getdate(d).strftime(MONTH_FMT)
		out[m] = out.get(m, 0) + 1
	return out


def _closed_by_month(doctype, from_date, to_date):
	"""Submitted docs grouped by month of modified (approx. closure month)."""
	to_dt = f"{to_date} 23:59:59"
	rows = frappe.get_all(
		doctype,
		filters=[["docstatus", "=", 1], ["modified", ">=", from_date], ["modified", "<=", to_dt]],
		pluck="modified",
	)
	out = {}
	for d in rows:
		m = frappe.utils.getdate(d).strftime(MONTH_FMT)
		out[m] = out.get(m, 0) + 1
	return out


def execute(filters=None):
	filters = filters or {}
	to_date = filters.get("to_date") or frappe.utils.today()
	from_date = filters.get("from_date") or frappe.utils.add_months(to_date, -11)

	oos_opened = _count_by_month("OOS Investigation", "creation", from_date, to_date)
	oos_closed = _closed_by_month("OOS Investigation", from_date, to_date)
	capa_opened = _count_by_month("CAPA", "creation", from_date, to_date)
	capa_closed = _closed_by_month("CAPA", from_date, to_date)
	dev_total = _count_by_month("Deviation Report", "creation", from_date, to_date)
	dev_crit = _count_by_month("Deviation Report", "creation", from_date, to_date, extra={"severity": "Critical"})
	brr = _count_by_month("Batch Release Record", "creation", from_date, to_date)
	exc = _count_by_month("Temperature Excursion", "creation", from_date, to_date)
	inc = _count_by_month("Safety Incident", "creation", from_date, to_date)

	columns = [
		{"label": _("Month"), "fieldname": "month", "fieldtype": "Data", "width": 100},
		{"label": _("OOS Opened"), "fieldname": "oos_opened", "fieldtype": "Int", "width": 110},
		{"label": _("OOS Closed"), "fieldname": "oos_closed", "fieldtype": "Int", "width": 110},
		{"label": _("CAPA Opened"), "fieldname": "capa_opened", "fieldtype": "Int", "width": 110},
		{"label": _("CAPA Closed"), "fieldname": "capa_closed", "fieldtype": "Int", "width": 110},
		{"label": _("Deviations"), "fieldname": "deviations", "fieldtype": "Int", "width": 100},
		{"label": _("Critical Deviations"), "fieldname": "critical_deviations", "fieldtype": "Int", "width": 130},
		{"label": _("Batch Releases"), "fieldname": "batch_releases", "fieldtype": "Int", "width": 120},
		{"label": _("Temp Excursions"), "fieldname": "temp_excursions", "fieldtype": "Int", "width": 120},
		{"label": _("Safety Incidents"), "fieldname": "safety_incidents", "fieldtype": "Int", "width": 120},
	]

	data = []
	for m in _month_range(from_date, to_date):
		data.append(
			{
				"month": m,
				"oos_opened": oos_opened.get(m, 0),
				"oos_closed": oos_closed.get(m, 0),
				"capa_opened": capa_opened.get(m, 0),
				"capa_closed": capa_closed.get(m, 0),
				"deviations": dev_total.get(m, 0),
				"critical_deviations": dev_crit.get(m, 0),
				"batch_releases": brr.get(m, 0),
				"temp_excursions": exc.get(m, 0),
				"safety_incidents": inc.get(m, 0),
			}
		)

	return columns, data