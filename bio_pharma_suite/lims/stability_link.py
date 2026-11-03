"""稳定性研究结果联动：Lab Sample 提交 → 回写时间点结论 + 异常结果告警（ICH Q1A）。

数据流：Stability Study 到点自动建样（tasks.scan_stability_timepoints）
→ 检测填写 Lab Sample.tests → 提交时回写 Stability Timepoint.result_status
→ 任一 Fail 触发 OOT/OOS 告警邮件给研究负责人。
"""

import frappe
from frappe import _


def update_stability_results(doc, method=None):
	"""Orchestrate: 稳定性来源样品提交后，汇总检验行结论并回写时间点。"""
	if doc.get("reference_type") != "Stability Study" or not doc.get("reference_name"):
		return

	rows = doc.get("tests") or []
	if not rows:
		return

	statuses = {(r.result_status or "Pending") for r in rows}
	if "Fail" in statuses:
		tp_status = "Fail"
	elif "Pending" in statuses:
		tp_status = "Pending"
	else:
		tp_status = "Pass"

	updated = frappe.db.set_value(
		"Stability Timepoint",
		{"lab_sample": doc.name, "parenttype": "Stability Study"},
		"result_status",
		tp_status,
	)

	if tp_status == "Fail":
		_send_oot_alert(doc, rows)

	if updated:
		frappe.msgprint(
			_("Stability Timepoint {0} marked as {1}.").format(doc.name, _(tp_status)),
			indicator="red" if tp_status == "Fail" else "green",
		)


def _send_oot_alert(doc, rows):
	"""异常结果（Fail）→ 邮件研究负责人；打开稳定性研究行的人都能看到时间点标记。"""
	study = frappe.db.get_value(
		"Stability Study", doc.reference_name,
		["name", "item_code", "batch_no", "responsible"], as_dict=True,
	)
	if not study:
		return

	failed = [r for r in rows if (r.result_status or "") == "Fail"]
	failed_desc = "; ".join(
		"{0}: {1} (spec: {2})".format(
			r.test_method, r.result_value or "-", r.specification or "-"
		)
		for r in failed
	)
	frappe.sendmail(
		recipients=[u for u in {study.responsible, "admin@example.com"} if u],
		subject=_("Stability OOT/OOS Alert: {0} ({1})").format(doc.name, study.name),
		message=_(
			"Lab Sample {0} from Stability Study {1} (item {2}, batch {3}) has failed test(s): {4}. "
			"Investigate per ICH Q1A and record the outcome."
		).format(doc.name, study.name, study.item_code or "-", study.batch_no or "-", failed_desc),
	)
	frappe.logger("bio_pharma_suite").info(
		"stability_link: OOT alert sent for {0}".format(doc.name)
	)
