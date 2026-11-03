"""核心 DocType 扩展字段定义（零侵入，经 patch 安装、经 fixtures 导出）。

注意：Lab Sample / Test Method 的 Link 目标 DocType 在 LIMS 批次交付后生效，
在此之前字段存在但不影响运行。
"""


def get_custom_fields():
	return {
		"Item": [
			dict(
				fieldname="bio_pharma_section",
				label="Bio Pharma GMP",
				fieldtype="Section Break",
				insert_after="quality_inspection_template",
				collapsible=1,
			),
			dict(
				fieldname="gmp_category",
				label="GMP Category",
				fieldtype="Select",
				options="\nAPI\nExcipient\nFinished Product\nPackaging Material\nBiological Product\nReagent",
				insert_after="bio_pharma_section",
			),
			dict(
				fieldname="requires_cold_chain",
				label="Requires Cold Chain",
				fieldtype="Check",
				insert_after="gmp_category",
			),
			dict(
				fieldname="storage_condition",
				label="Storage Condition",
				fieldtype="Select",
				options="\nFrozen (-25 to -15 C)\nRefrigerated (2 to 8 C)\nCool (below 20 C)\nRoom Temperature",
				insert_after="requires_cold_chain",
				depends_on="eval:doc.requires_cold_chain",
			),
		],
		"Warehouse": [
			dict(
				fieldname="temperature_zone",
				label="Temperature Zone",
				fieldtype="Link",
				options="Temperature Zone",
				insert_after="company",
			),
			dict(
				fieldname="qualified_for_gmp",
				label="Qualified for GMP Storage",
				fieldtype="Check",
				insert_after="temperature_zone",
			),
		],
		"Batch": [
			dict(
				fieldname="quality_status",
				label="Quality Status",
				fieldtype="Select",
				# 待检 Quarantine / 合格 Released / 不合格 Rejected / 冻结 Hold（待改善复检/召回中）
				options="Quarantine\nReleased\nRejected\nHold",
				insert_after="expiry_date",
				default="Quarantine",
				in_list_view=1,
				in_standard_filter=1,
			),
			dict(
				fieldname="release_date",
				label="Release Date",
				fieldtype="Date",
				insert_after="quality_status",
				read_only=1,
			),
			dict(
				fieldname="released_by",
				label="Released By",
				fieldtype="Link",
				options="User",
				insert_after="release_date",
				read_only=1,
			),
		],
		"Quality Inspection": [
			dict(
				fieldname="lab_sample",
				label="Lab Sample",
				fieldtype="Link",
				options="Lab Sample",
				insert_after="batch_no",
			),
			dict(
				fieldname="test_method_ref",
				label="Test Method",
				fieldtype="Link",
				options="Test Method",
				insert_after="lab_sample",
			),
			dict(
				fieldname="esign_confirmed",
				label="E-Signature Confirmed",
				fieldtype="Check",
				insert_after="test_method_ref",
			),
		],
		"Work Order": [
			dict(
				fieldname="master_formula",
				label="Master Formula (Controlled)",
				fieldtype="Link",
				options="Master Formula",
				insert_after="bom_no",
			),
			dict(
				fieldname="batch_release_required",
				label="Batch Release Required before Sale",
				fieldtype="Check",
				insert_after="master_formula",
			),
		],
	}
