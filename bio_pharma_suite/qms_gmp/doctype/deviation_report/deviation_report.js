frappe.ui.form.on("Deviation Report", {
	refresh(frm) {
		if (frm.doc.docstatus === 0 && !frm.is_new()) {
			frm.add_custom_button(__("Create CAPA"), () => {
				frappe.call({
					method: "bio_pharma_suite.qms_gmp.deviation_link.make_capa_from_deviation",
					args: { deviation_name: frm.doc.name },
					freeze: true,
					callback: (r) => {
						if (r.message) {
							frappe.set_route("Form", "CAPA", r.message.name);
						}
					},
				});
			});
		}
	},
});
