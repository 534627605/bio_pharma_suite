"""after_migrate: 自定义字段每次迁移强制与 fixtures/custom_fields.py 同步。

背景：字段最初由 post_install patch（仅执行一次）创建，该通道不设置 module，
导致 fixtures 按 module 过滤无法命中，后续定义变更（如 Batch.quality_status
从三态扩为四态）不会落库。after_migrate + update=True 是官方推荐的可重入通道。
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

from bio_pharma_suite.fixtures.custom_fields import get_custom_fields


def after_migrate():
	create_custom_fields(get_custom_fields(), ignore_validate=True, update=True)
	frappe.db.commit()
