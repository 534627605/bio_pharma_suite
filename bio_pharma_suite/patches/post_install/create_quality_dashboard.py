"""Create the Bio Pharma Quality KPI dashboard.

Inserts (idempotently):
- 1 Report-type Dashboard Chart driven by the Quality KPI Summary script report
- Group-By charts for status / severity distributions
- Number Cards for core QMS document counts
- One public Dashboard assembling charts + cards

erpnext-style post-install patch. Meta is introspected at runtime so field
names stay correct across Frappe schema variations.
"""

import frappe

DASHBOARD_LABEL = "Bio Pharma Quality KPI"

GROUP_BY_SPECS = [
	("OOS by Status", "OOS Investigation", ["status"]),
	("CAPA by Status", "CAPA", ["status"]),
	(
		"Deviations by Severity",
		"Deviation Report",
		["severity", "deviation_level", "deviation_severity"],
	),
	("Batch Release Decisions", "Batch Release Record", ["release_decision"]),
	("Safety Incidents by Severity", "Safety Incident", ["severity"]),
	("Temperature Excursions by Status", "Temperature Excursion", ["status"]),
]

CARD_SPECS = [
	("OOS Investigations", "OOS Investigation"),
	("CAPAs", "CAPA"),
	("Deviation Reports", "Deviation Report"),
	("Batch Releases", "Batch Release Record"),
	("Temperature Excursions", "Temperature Excursion"),
	("Safety Incidents", "Safety Incident"),
]


def _options(doctype, fieldname):
	df = frappe.get_meta(doctype).get_field(fieldname)
	if not df or not df.options:
		return []
	return [o.strip() for o in df.options.split("\n") if o.strip()]


def _pick(doctype, fieldname, preferences):
	opts = _options(doctype, fieldname)
	for pref in preferences:
		if pref in opts:
			return pref
	return opts[0] if opts else None


def _insert(doctype, match, data):
	name = frappe.db.exists(doctype, match)
	if name:
		return name, False
	doc = frappe.get_doc(dict(data, doctype=doctype))
	doc.flags.ignore_permissions = True
	doc.insert()
	return doc.name, True


def try_insert(doctype, match, data):
	try:
		name, created = _insert(doctype, match, data)
	except Exception as e:
		return None, False, str(e)
	return name, created, None


def _link_fieldname(child, target):
	for df in frappe.get_meta(child).fields:
		if df.fieldtype == "Link" and df.options == target:
			return df.fieldname
	return None


def run():
	frappe.set_user("Administrator")
	created, skipped, errors = [], [], []
	chart_names, card_names = [], []

	# 1) Trend chart from the existing script report
	if frappe.db.exists("Report", {"name": "Quality KPI Summary"}):
		name, is_new, err = try_insert(
			"Dashboard Chart",
			{"chart_name": "Quality KPI Trend"},
			{
				"chart_name": "Quality KPI Trend",
				"chart_type": "Report",
				"report_name": "Quality KPI Summary",
				"type": _pick("Dashboard Chart", "type", ["Line", "Bar"]),
				"is_public": 1,
				"color": "#449CF0",
			},
		)
		if name:
			chart_names.append(name)
			(created if is_new else skipped).append("Chart: " + name)
		else:
			errors.append("Chart Quality KPI Trend: " + err)
	else:
		skipped.append("Chart skipped (report missing): Quality KPI Trend")

	# 2) Group-by distribution charts
	for label, doctype, candidates in GROUP_BY_SPECS:
		field = next(
			(c for c in candidates if frappe.get_meta(doctype).get_field(c)),
			None,
		)
		if not field:
			skipped.append("Chart skipped (no field): " + label)
			continue
		name, is_new, err = try_insert(
			"Dashboard Chart",
			{"chart_name": label},
			{
				"chart_name": label,
				"chart_type": "Group By",
				"document_type": doctype,
				"group_by_based_on": field,
				"group_by_type": _pick(
					"Dashboard Chart", "group_by_type", ["Count"]
				)
				or "Count",
				"type": _pick(
					"Dashboard Chart", "type", ["Bar", "Percentage", "Pie"]
				),
				"is_public": 1,
			},
		)
		if name:
			chart_names.append(name)
			(created if is_new else skipped).append("Chart: " + name)
		else:
			errors.append("Chart " + label + ": " + err)

	# 3) Number cards (total counts)
	fn_field = next(
		(
			f
			for f in ("function", "aggregate_function")
			if frappe.get_meta("Number Card").get_field(f)
		),
		None,
	)
	for label, doctype in CARD_SPECS:
		data = {
			"label": label,
			"type": "Document Type",
			"document_type": doctype,
			"is_public": 1,
		}
		if fn_field:
			data[fn_field] = "Count"
		name, is_new, err = try_insert("Number Card", {"label": label}, data)
		if name:
			card_names.append(name)
			(created if is_new else skipped).append("Card: " + name)
		else:
			errors.append("Card " + label + ": " + err)

	# 4) Assemble the dashboard
	chart_field = _link_fieldname("Dashboard Chart Link", "Dashboard Chart")
	card_field = _link_fieldname("Number Card Link", "Number Card")
	dash = {"label": DASHBOARD_LABEL}
	if chart_field and chart_names:
		dash["charts"] = [{chart_field: n} for n in chart_names]
	if card_field and card_names:
		dash["cards"] = [{card_field: n} for n in card_names]
	name, is_new, err = try_insert("Dashboard", {"label": DASHBOARD_LABEL}, dash)
	if name:
		(created if is_new else skipped).append("Dashboard: " + name)
	else:
		errors.append("Dashboard: " + err)

	frappe.db.commit()
	print("CREATED:", len(created))
	for line in created:
		print("  +", line)
	print("SKIPPED:", len(skipped))
	for line in skipped:
		print("  =", line)
	print("ERRORS:", len(errors))
	for line in errors:
		print("  !", line)
