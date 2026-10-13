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
	"""Product License 效期预警（RA 批次交付后生效）"""
	if not _doctype_ready("Product License"):
		return
	# TODO Phase 2: 预警通知 RA；过期 → Batch Release 放行门禁


def scan_stability_timepoints():
	"""Stability Study 到点 → 自动创建 Lab Sample + 取样提醒（LIMS 批次交付后生效）"""
	if not _doctype_ready("Stability Study"):
		return
	# TODO Phase 2/3: ICH 时间点扫描
