"""QMS 约束与联动：注入 Quality Inspection / Work Order 生命周期。"""

import json

import frappe
from frappe import _
from frappe.utils import now


def validate_quality_inspection(doc, method=None):
	"""Guard: QI 提交前——电子签名确认 + 生效检验方法版本。"""
	if frappe.db.get_single_value("Data Integrity Settings", "require_esignature_on_qi"):
		if not doc.get("esign_confirmed"):
			frappe.throw(
				_("E-Signature confirmation is required before submitting a Quality Inspection (21 CFR Part 11)."),
				title=_("E-Signature Required"),
			)

	if (
		frappe.db.get_single_value("Data Integrity Settings", "require_effective_test_method")
		and doc.get("test_method_ref")
	):
		if frappe.db.exists("DocType", "Test Method"):
			if not frappe.db.get_value("Test Method", doc.test_method_ref, "is_effective"):
				frappe.throw(
					_("Test Method {0} is not in-force. Reference an effective version.").format(
						doc.test_method_ref
					),
					title=_("Test Method Not Effective"),
				)

	if doc.status == "Rejected":
		frappe.msgprint(
			_("Result is Rejected. OOS Investigation auto-creation lands with the Phase 2 QMS module — record the investigation manually for now."),
			indicator="red",
		)


def validate_work_order(doc, method=None):
	"""Guard: 工单提交前——受控工艺规程必须有生效版本，且 BOM 一致。"""
	mf = doc.get("master_formula")
	if not mf or not frappe.db.exists("Master Formula", mf):
		return

	active = frappe.db.get_value("Master Formula", mf, "active_version")
	if not active:
		frappe.throw(
			_("Master Formula {0} has no in-force version. Approve an effective version before production.").format(mf),
			title=_("No Effective Master Formula"),
		)

	mf_bom = frappe.db.get_value("Master Formula", mf, "bom_no")
	if doc.bom_no and mf_bom != doc.bom_no:
		frappe.throw(
			_("Work Order BOM {0} does not match controlled BOM {1} of Master Formula {2}.").format(
				doc.bom_no, mf_bom, mf
			),
			title=_("BOM Mismatch"),
		)


def assemble_batch_production_record(doc, method=None):
	"""Orchestrate: 工单提交自动汇编电子批生产记录（BMR）。

	汇编内容：工艺规程版本 + 计划/实际产量 + 工序(Job Card) + 过程检验(QI) 汇总快照。
	"""
	mf = doc.get("master_formula")
	if not mf:
		return
	if frappe.db.exists("Batch Production Record", {"work_order": doc.name}):
		return

	active = frappe.db.get_value("Master Formula", mf, "active_version")

	job_cards = frappe.get_all(
		"Job Card",
		filters={"work_order": doc.name},
		fields=["name", "operation", "status", "total_time"],
	)
	job_card_names = [j.name for j in job_cards]

	qis = frappe.get_all(
		"Quality Inspection",
		filters={
			"reference_name": ["in", [doc.name] + job_card_names],
		},
		fields=["name", "reference_type", "reference_name", "item_code", "status"],
	)

	compiled = {
		"generated_at": now(),
		"work_order": doc.name,
		"production_item": doc.production_item,
		"planned_qty": doc.planned_qty,
		"produced_qty": doc.produced_qty,
		"bom_no": doc.bom_no,
		"master_formula": mf,
		"formula_version": active,
		"job_cards": job_cards,
		"quality_inspections": qis,
		"notes": "Auto-assembled by bio_pharma_suite on Work Order submit",
	}

	bmr = frappe.new_doc("Batch Production Record")
	bmr.work_order = doc.name
	bmr.item_code = doc.production_item
	bmr.master_formula = mf
	bmr.formula_version = active
	bmr.compiled_data = json.dumps(compiled, ensure_ascii=False, indent=1, default=str)
	bmr.assembled_on = now()
	bmr.job_card_count = len(job_cards)
	bmr.qi_count = len(qis)
	bmr.deviations_found = 0
	bmr.insert(ignore_permissions=True)

	frappe.msgprint(
		_("Batch Production Record {0} auto-assembled for Work Order {1} (formula version {2}).").format(
			bmr.name, doc.name, active or "-"
		)
	)
