# Copyright (c) 2026
# Seed Regulation Library with GMP clause framework (Phase A: legal backing).
# Honesty rule: only clause numbers with high confidence are cited at article
# level; everything else is seeded at chapter level with verification_status
# = "Pending Verification" so QA must verify against the original text
# (that verification act is itself a GMP document-control requirement).

import frappe


LIBRARY_NAME = "China Drug GxP Core Framework"

# (clause_no, title, applicability, confidence)
# confidence: "article" = 条号高置信, "chapter" = 章级引用
CLAUSES = [
	("第三章 机构与人员", "Key personnel and the Qualified Person (受权人)",
	 "LIMS/QMS: personnel qualification, QP release authority", "article"),
	("第六章 物料与产品", "Materials and products: quarantine, rejection and disposal of non-conforming materials",
	 "Batch quality status (Quarantine/Rejected/Hold), warehouse segregation", "chapter"),
	("第七章 确认与验证", "Qualification and validation requirements",
	 "Validation Master Plan, instrument calibration", "chapter"),
	("第八章 文件管理", "Documentation control: drafting, review, approval, distribution and recall of documents",
	 "Controlled Document, Training Record", "chapter"),
	("第十章 质量控制与质量保证", "Quality control and quality assurance: OOS handling, deviation management, CAPA",
	 "OOS Investigation, Deviation Report, CAPA, Change Control", "chapter"),
	("第十二章 产品发运与召回", "Product distribution and recall: recall organisation, procedures and reporting to authorities",
	 "Batch Release decision=Recall, Cold Chain shipment records", "chapter"),
	("《药品管理法》", "Drug Administration Law of the PRC: marketing authorization holder responsibilities, batch release",
	 "Product License, Regulatory Affairs", "chapter"),
]


def execute():
	if frappe.db.exists("Regulation Library", LIBRARY_NAME):
		return

	doc = frappe.new_doc("Regulation Library")
	doc.regulation_code = "CN-GXP-CORE"
	doc.regulation_title = "中国药品 GxP 核心法规框架（预置，待 QA 核实）"
	doc.status = "Approved"
	doc.effective_from = frappe.utils.getdate("2011-03-01")  # GMP 2010 rev. publication date
	doc.remarks = (
		"预置框架库：条号仅引用高置信条目，其余为章级引用。"
		"每条 verification_status=Pending Verification，QA 须对照原文核实后置为 Verified。"
	)
	for clause_no, title, applicability, _conf in CLAUSES:
		doc.append(
			"clauses",
			{
				"clause_no": clause_no,
				"clause_title": title,
				"applicability": applicability,
				"verification_status": "Pending Verification",
			},
		)
	doc.insert(ignore_permissions=True)
	frappe.db.commit()
	print(f"Seeded Regulation Library {LIBRARY_NAME} with {len(CLAUSES)} clauses")
