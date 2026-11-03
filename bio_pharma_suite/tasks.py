"""scheduler_events：每日巡检（对未交付的 DocType 防御式跳过，模块渐进落地不崩调度）"""

import frappe
from frappe import _


def _doctype_ready(name):
	try:
		return frappe.db.exists("DocType", name)
	except Exception:
		return False


def scan_calibration_due():
	"""Instrument 校准到期 → 仪器自动隔离（Quarantined）+ 通知仪器保管人与 QA。"""
	if not _doctype_ready("Instrument"):
		return

	today = frappe.utils.today()
	overdue = frappe.get_all(
		"Instrument",
		filters={"status": "Active", "next_calibration_date": ["<", today]},
		fields=["name", "instrument_name", "next_calibration_date", "custodian"],
	)
	for inst in overdue:
		frappe.db.set_value("Instrument", inst.name, "status", "Quarantined")
		recipients = [u for u in {inst.custodian, "admin@example.com"} if u]
		frappe.sendmail(
			recipients=recipients,
			subject=_("Instrument {0} quarantined: calibration overdue").format(inst.instrument_name),
			message=_(
				"Instrument {0} ({1}) was quarantined automatically because its next "
				"calibration date {2} has passed. Recalibrate and update the record to re-activate."
			).format(inst.instrument_name, inst.name, inst.next_calibration_date),
		)
	if overdue:
		frappe.db.commit()
		frappe.logger("bio_pharma_suite").info(
			"scan_calibration_due: quarantined {0} instruments".format(len(overdue))
		)


def scan_product_licence_expiry():
	"""Product License 效期预警：刷新状态 + RA/QA 通知，过期证照阻断批放行（见 release_guard）。"""
	if not _doctype_ready("Product License"):
		return

	from frappe import _
	from frappe.utils import today, date_diff

	expiring = frappe.get_all(
		"Product License",
		filters={"status": ["in", ["Valid", "Expiring Soon"]]},
		fields=["name", "license_no", "license_name", "expiry_date", "reminder_days", "status"],
	)

	notify_rows = []
	for lic in expiring:
		days = date_diff(lic.expiry_date, today())
		reminder = lic.reminder_days or 90
		if days < 0:
			frappe.db.set_value("Product License", lic.name, "status", "Expired")
			notify_rows.append((lic, "expired", 0))
		elif days <= reminder:
			frappe.db.set_value("Product License", lic.name, "status", "Expiring Soon")
			notify_rows.append((lic, "expiring", days))

	frappe.db.commit()

	if not notify_rows:
		return

	recipients = [
		u.name
		for u in frappe.get_all(
			"User",
			filters={"enabled": 1},
			or_filters={
				"role_profile_name": ("like", "%Bio Pharma%"),
			},
			fields=["name"],
		)
	]
	if not recipients:
		recipients = ["Administrator"]

	expired = [r for r in notify_rows if r[1] == "expired"]
	expiring = [r for r in notify_rows if r[1] == "expiring"]

	lines = []
	if expired:
		lines.append(_("### License Expired"))
		for lic, kind, days_left in expired:
			lines.append(f"- **{lic.license_no}** {lic.license_name} ({lic.name})")
	if expiring:
		lines.append(_("### License Expiring Soon"))
		for lic, kind, days_left in expiring:
			lines.append(f"- **{lic.license_no}** {lic.license_name} ({lic.name}) — {days_left}d")

	try:
		frappe.sendmail(
			recipients=recipients,
			subject=_("Product License Expiry Alert"),
			message="<br>".join(lines),
		)
	except Exception:
		frappe.log_error(title=_("License expiry email failed"), message=frappe.get_traceback())


def scan_stability_timepoints():
	"""Stability Study 到点 → 自动创建 Lab Sample + 通知负责人（ICH Q1A 自动化）。"""
	if not (_doctype_ready("Stability Study") and _doctype_ready("Lab Sample")):
		return

	today = frappe.utils.today()
	studies = frappe.get_all(
		"Stability Study",
		filters={"status": "Ongoing"},
		fields=["name", "item_code", "batch_no", "storage_zone", "responsible"],
	)
	created = 0
	for study in studies:
		due_rows = frappe.get_all(
			"Stability Timepoint",
			filters={
				"parent": study.name,
				"parenttype": "Stability Study",
				"sample_created": 0,
				"scheduled_date": ["<=", today],
			},
			fields=["name", "timepoint_months"],
		)
		for tp in due_rows:
			sample = frappe.new_doc("Lab Sample")
			sample.sample_no = "{0}-TP{1}M".format(study.name, tp.timepoint_months)
			sample.sample_type = _ensure_stability_sample_type()
			sample.source_type = "Stability Study"
			sample.reference_type = "Stability Study"
			sample.reference_name = study.name
			sample.item_code = study.item_code
			sample.batch_no = study.batch_no
			sample.storage_zone = study.storage_zone
			sample.company = frappe.defaults.get_global_default("company")
			sample.reference_name = study.name
			sample.item_code = study.item_code
			sample.batch_no = study.batch_no
			sample.storage_zone = study.storage_zone
			sample.collection_date = frappe.utils.now()
			sample.remarks = _("Auto-created by stability timepoint scan ({0})").format(today)
			sample.insert(ignore_permissions=True)
			frappe.db.set_value(
				"Stability Timepoint",
				tp.name,
				{"sample_created": 1, "lab_sample": sample.name},
			)
			created += 1
			if study.responsible:
				frappe.sendmail(
					recipients=[study.responsible],
					subject=_("Stability sample due: {0}").format(sample.sample_no),
					message=_(
						"Timepoint {0} months of study {1} is due. Lab Sample {2} was created automatically."
					).format(tp.timepoint_months, study.name, sample.name),
				)
	if created:
		frappe.db.commit()
		frappe.logger("bio_pharma_suite").info(
			"scan_stability_timepoints: created {0} stability samples".format(created)
		)


def _ensure_stability_sample_type():
	"""保证存在“Stability Study”样品类型（主数据自举，只建一次）。"""
	name = frappe.db.exists("Sample Type", {"sample_type_name": "Stability Study"})
	if name:
		return name
	st = frappe.new_doc("Sample Type")
	st.sample_type_name = "Stability Study"
	st.description = "Auto-created default type for stability timepoint sampling"
	st.insert(ignore_permissions=True)
	return st.name


def scan_validation_overdue():
	"""Validation Master Plan 逾期验证活动 → 行级标记 Overdue + 通知负责人。"""
	if not _doctype_ready("Validation Master Plan"):
		return

	today = frappe.utils.today()
	plans = frappe.get_all(
		"Validation Master Plan",
		filters={"docstatus": 0},
		fields=["name", "title", "responsible"],
	)
	notified = set()
	marked = 0
	for plan in plans:
		due_rows = frappe.get_all(
			"Validation Activity",
			filters={
				"parent": plan.name,
				"parenttype": "Validation Master Plan",
				"status_row": ["in", ["Planned", "In Progress"]],
				"planned_end": ["<", today],
			},
			fields=["name", "subject", "planned_end"],
		)
		for row in due_rows:
			frappe.db.set_value("Validation Activity", row.name, "status_row", "Overdue")
			marked += 1
			if plan.responsible and plan.responsible not in notified:
				notified.add(plan.responsible)
				frappe.sendmail(
					recipients=[plan.responsible],
					subject=_("Overdue validation activities in plan {0}").format(plan.name),
					message=_(
						"Validation plan {0} ({1}) has overdue activities past {2}. "
						"They were marked Overdue automatically. Complete them or reschedule."
					).format(plan.name, plan.title or "-", today),
				)
	if marked:
		frappe.db.commit()
		frappe.logger("bio_pharma_suite").info(
			"scan_validation_overdue: marked {0} activities overdue".format(marked)
		)
