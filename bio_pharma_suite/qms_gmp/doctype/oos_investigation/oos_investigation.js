frappe.ui.form.on("OOS Investigation", {
	refresh(frm) {
		if (frm.doc.docstatus === 0 && !frm.doc.__islocal) {
			frm.add_custom_button(__("Create CAPA"), () => {
				frappe.call({
					method: "bio_pharma_suite.qms_gmp.capa_link.make_capa_from_oos",
					args: { oos_name: frm.doc.name },
					freeze: true,
					freeze_message: __("Creating CAPA..."),
					callback(r) {
						if (r.message) {
							frappe.show_alert({
								message: __("CAPA {0} created", [r.message.name]),
								indicator: "green",
							});
							frappe.set_route("Form", "CAPA", r.message.name);
						}
					},
				});
			});
		}
	},
});
