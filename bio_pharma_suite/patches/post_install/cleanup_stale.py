"""临时清理：移除上次失败安装的残留（Module Def / DocType 行 / DB 表）。仅在安装排障时手动调用。"""

import frappe

MODULES = [
	"Compliance Foundation",
	"LIMS",
	"QMS GMP",
	"Cold Chain",
	"Regulatory Affairs",
]

TABLES = [
	"tabTemperature Zone",
	"tabTemperature Log",
	"tabTemperature Excursion",
	"tabTemperature Excursion Batch",
	"tabReason Code",
	"tabControlled Document",
	"tabMaster Formula",
	"tabMaster Formula Version",
	"tabBatch Production Record",
	"tabRegulation Library",
	"tabRegulation Clause",
]


def run():
	deleted = frappe.get_all("DocType", filters={"module": ["in", MODULES]}, pluck="name")
	for dt in deleted:
		frappe.db.delete("DocType", dt)
		frappe.db.delete("DocField", {"parent": dt})
		frappe.db.delete("DocPerm", {"parent": dt})
	for m in MODULES:
		frappe.db.delete("Module Def", m)
	frappe.db.delete("Installed Application", {"app_name": "bio_pharma_suite"})
	for t in TABLES:
		frappe.db.sql_ddl("DROP TABLE IF EXISTS `{0}`".format(t))
	frappe.db.commit()
	return "CLEANUP_DONE: " + ", ".join(deleted) if deleted else "CLEANUP_DONE: nothing to delete"
