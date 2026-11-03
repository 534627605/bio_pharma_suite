# Copyright (c) 2026, Bio Pharma Suite Team and contributors
# For license information, please see license.txt

"""GMP audit trail query report (21 CFR Part 11 / data integrity).

Aggregates framework-level change tracking (tabVersion) for all
bio_pharma_suite controlled doctypes into one queryable evidence view.
"""

import json

import frappe
from frappe import _
from frappe.utils import get_datetime, nowdate

SUITE_DOCTYPES = [
	"Lab Sample",
	"Sample Type",
	"Sampling Point",
	"Test Method",
	"Instrument",
	"Stability Study",
	"Master Formula",
	"Master Formula Version",
	"Batch Production Record",
	"Controlled Document",
	"OOS Investigation",
	"CAPA",
	"Deviation Report",
	"Change Control",
	"Training Record",
	"Batch Release Record",
	"Validation Master Plan",
	"Supplier Audit",
	"Temperature Zone",
	"Temperature Log",
	"Temperature Excursion",
	"Regulation Library",
	"Product License",
	"Waste Disposal Log",
	"Safety Incident",
	"Reason Code",
	"Data Integrity Settings",
]

SUMMARY_MAX_LEN = 500


def execute(filters=None):
	filters = frappe._dict(filters or {})
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{"label": _("Timestamp"), "fieldname": "creation", "fieldtype": "Datetime", "width": 160},
		{"label": _("User"), "fieldname": "owner", "fieldtype": "Link", "options": "User", "width": 190},
		{"label": _("Record Type"), "fieldname": "ref_doctype", "fieldtype": "Data", "width": 180},
		{
			"label": _("Record"),
			"fieldname": "docname",
			"fieldtype": "Dynamic Link",
			"options": "ref_doctype",
			"width": 190,
		},
		{"label": _("Change Summary"), "fieldname": "change_summary", "fieldtype": "Small Text", "width": 520},
	]


def get_data(filters):
	from_date = filters.get("from_date") or "2026-01-01"
	to_date = filters.get("to_date") or nowdate()

	conditions = ["v.ref_doctype IN %(doctypes)s", "v.creation >= %(from)s", "v.creation <= %(to)s"]
	values = {
		"doctypes": tuple(SUITE_DOCTYPES),
		"from": get_datetime(from_date).strftime("%Y-%m-%d 00:00:00"),
		"to": get_datetime(to_date).strftime("%Y-%m-%d 23:59:59"),
	}

	if filters.get("record_doctype"):
		conditions.append("v.ref_doctype = %(record_doctype)s")
		values["record_doctype"] = filters.record_doctype
	if filters.get("user"):
		conditions.append("v.owner = %(user)s")
		values["user"] = filters.user
	if filters.get("record_name"):
		conditions.append("v.docname LIKE %(record_name)s")
		values["record_name"] = f"%{filters.record_name}%"

	rows = frappe.db.sql(
		f"""
		SELECT v.creation, v.owner, v.ref_doctype, v.docname, v.data
		FROM `tabVersion` v
		WHERE {" AND ".join(conditions)}
		ORDER BY v.creation DESC
		LIMIT 2000
		""",
		values=values,
		as_dict=1,
	)

	return [
		{
			"creation": row.creation,
			"owner": row.owner,
			"ref_doctype": row.ref_doctype,
			"docname": row.docname,
			"change_summary": summarize(row.data),
		}
		for row in rows
	]


def summarize(data):
	"""Render the framework change JSON into a human-readable one-liner."""
	if not data:
		return ""
	try:
		changes = json.loads(data)
	except (ValueError, TypeError):
		return ""

	parts = []
	for field, old, new in changes.get("changed") or []:
		parts.append(f"{field}: {old!r} → {new!r}")

	for field, row_doc in changes.get("added") or []:
		try:
			parts.append(_("added row in {0} ({1})").format(field, _row_hint(row_doc)))
		except Exception:
			parts.append(_("added row in {0}").format(field))

	for field, rows in (changes.get("row_changed") or {}).items():
		try:
			hints = ", ".join(_row_hint(r) for r in rows.get("added", [])[:3])
		except Exception:
			hints = ""
		parts.append(_("updated rows in {0}").format(field) + (f" ({hints})" if hints else ""))

	for field, row_doc in changes.get("removed") or []:
		try:
			parts.append(_("removed row from {0} ({1})").format(field, _row_hint(row_doc)))
		except Exception:
			parts.append(_("removed row from {0}").format(field))

	summary = "; ".join(parts)
	return summary[:SUMMARY_MAX_LEN]


def _row_hint(row_doc):
	if isinstance(row_doc, dict):
		for key in ("name", "idx", "test_name", "item_code", "participant"):
			if row_doc.get(key):
				return str(row_doc[key])
	return ""