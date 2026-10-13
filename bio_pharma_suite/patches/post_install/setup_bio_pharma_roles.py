"""安装后补丁：创建行业角色 + 注入核心 DocType 扩展字段"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

from bio_pharma_suite.fixtures.custom_fields import get_custom_fields

BIO_PHARMA_ROLES = [
	"Bio Pharma QP",
	"Bio Pharma QC Analyst",
	"Bio Pharma Lab Supervisor",
	"Bio Pharma QA Officer",
	"Bio Pharma RA Officer",
	"Bio Pharma GMP Warehouse",
]


def execute():
	for role in BIO_PHARMA_ROLES:
		if not frappe.db.exists("Role", role):
			frappe.get_doc(
				{"doctype": "Role", "role_name": role, "desk_access": 1}
			).insert(ignore_permissions=True)

	create_custom_fields(get_custom_fields(), ignore_validate=True, update=True)
