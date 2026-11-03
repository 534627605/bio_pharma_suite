frappe.ui.form.on("CAPA", {
	refresh(frm) {
		if (frm.doc.docstatus === 1 && frm.doc.status === "Closed") {
			frm.add_custom_button(__("Create Change Control"), () => {
				frappe.call({
					method: "bio_pharma_suite.qms_gmp.change_link.make_change_control_from_capa",
					args: { capa_name: frm.doc.name },
					freeze: true,
					freeze_message: __("Creating Change Control..."),
					callback(r) {
						if (r.message) {
							frappe.set_route("Form", "Change Control", r.message.name);
						}
					},
				});
			});
		}
	},
});