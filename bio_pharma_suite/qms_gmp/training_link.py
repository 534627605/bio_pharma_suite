"""培训联动：变更控制关闭后，为受控文件自动开立再培训记录。"""

import frappe
from frappe import _


def create_retraining_from_change(doc, method=None):
	"""Orchestrate: Change Control 提交（=关闭）时，若涉及受控文件，自动创建再培训记录。

	参训人员预填：该受控文件历史培训记录（最近一条已提交）中的全部合格人员。
	"""
	if not doc.get("controlled_document"):
		return

	# 防重复：同一受控文件已有未完成的再培训记录则跳过
	existing = frappe.db.exists(
		"Training Record",
		{
			"controlled_document": doc.controlled_document,
			"training_type": "Retraining",
			"docstatus": 0,
		},
	)
	if existing:
		return

	# 预填上次培训的合格人员
	prev = frappe.get_all(
		"Training Record",
		filters={
			"controlled_document": doc.controlled_document,
			"docstatus": 1,
		},
		order_by="training_date desc",
		limit=1,
		pluck="name",
	)
	participants = []
	if prev:
		for row in frappe.get_all(
			"Training Participant",
			filters={"parent": prev[0], "parenttype": "Training Record", "result": "Pass"},
			fields=["participant", "employee_name"],
		):
			participants.append(row)

	tr = frappe.new_doc("Training Record")
	tr.training_type = "Retraining"
	tr.training_date = frappe.utils.add_days(frappe.utils.today(), 7)
	tr.status = "Planned"
	tr.controlled_document = doc.controlled_document
	tr.document_version = frappe.db.get_value(
		"Controlled Document", doc.controlled_document, "current_version"
	)
	tr.notes = _("Retraining required after document change") + f" ({doc.name})"
	for p in participants:
		tr.append(
			"participants",
			{"participant": p.participant, "employee_name": p.employee_name, "result": "Pending"},
		)
	tr.insert(ignore_permissions=True)

	frappe.msgprint(
		_("Retraining record {0} auto-created for changed document {1}.").format(
			tr.name, doc.controlled_document
		),
		indicator="blue",
	)
