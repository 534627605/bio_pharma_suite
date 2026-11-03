import frappe


def execute():
	"""Enable track_changes on all bio_pharma_suite master DocTypes (GMP audit trail)."""
	CHILD_TABLES = {
		"Audit Finding", "CAPA Action", "Lab Sample Item", "Lab Sample Test",
		"Stability Timepoint", "Temperature Excursion Batch", "Training Participant",
		"Validation Activity", "Regulation Clause", "Chain of Custody",
	}
	doctypes = frappe.get_all(
		"DocType",
		filters={"module": (
			["in", ["Compliance Foundation", "LIMS", "QMS GMP", "Cold Chain",
				"Regulatory Affairs", "Lab Safety"]]
		)},
		pluck="name",
	)
	for dt in doctypes:
		if dt in CHILD_TABLES:
			continue
		meta = frappe.get_meta(dt)
		if not meta.track_changes:
			frappe.db.set_value("DocType", dt, "track_changes", 1)
			frappe.clear_cache(doctype=dt)
	frappe.db.commit()
	print(f"track_changes enabled: {len(doctypes) - len(CHILD_TABLES)} doctypes scanned")
