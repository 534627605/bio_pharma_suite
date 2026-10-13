// Copyright (c) 2026 Bio Pharma Suite
// 样品表单：扫码交接按钮（1D 条码/二维码场景），调用 lims/api.py

frappe.ui.form.on("Lab Sample", {
	refresh(frm) {
		if (frm.doc.docstatus === 1) {
			frm.add_custom_button(__("Scan Handover"), () => {
				frappe.prompt(
					[
						{
							fieldname: "scanned",
							fieldtype: "Data",
							label: __("Scan / Enter Sample Code"),
							reqd: 1,
							default: frm.doc.sample_no,
						},
						{
							fieldname: "custody_action",
							fieldtype: "Select",
							label: __("Custody Action"),
							options: "Handover\nReceipt\nReturn\nDisposal",
							default: "Handover",
						},
						{
							fieldname: "location",
							fieldtype: "Data",
							label: __("Location"),
						},
					],
					(values) => {
						frappe.call({
							method: "bio_pharma_suite.lims.api.log_custody_handover",
							args: values,
						 freeze: true,
							freeze_message: __("Recording custody..."),
							callback: () => frm.reload_doc(),
						});
					},
					__("Scan Verified Handover"),
				);
			});
		}
	},
});