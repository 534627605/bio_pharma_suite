"""实验室安全事故升级：Safety Incident 提交 → 自动创建官方 Non Conformance（零侵入复用 ERPNext QMS）。

规则：
- 所有提交的事故 → 创建 Non Conformance（subject 携带事故编号保证幂等）；
- Major/Critical → 额外邮件通知 QA；建议在官方 NC 上走 corrective/preventive action 闭环。
"""

import frappe
from frappe import _


def _get_default_procedure():
	"""解析/兜底默认质量程序：优先复用站点已有 Quality Procedure，否则创建专用程序。"""
	existing = frappe.db.get_value("Quality Procedure", {}, "name")
	if existing:
		return existing
	qp = frappe.new_doc("Quality Procedure")
	qp.quality_procedure_name = "Lab Safety Incident Handling"
	qp.insert(ignore_permissions=True)
	return qp.name


def escalate_incident(doc, method=None):
	"""Orchestrate: 事故提交 → 官方质量体系承接（Non Conformance）。"""
	subject = "[{0}] {1} - {2}".format(doc.name, _(doc.incident_type), doc.severity)

	if frappe.db.exists("Non Conformance", {"subject": subject}):
		return  # 幂等：同一事故只升级一次

	nc = frappe.new_doc("Non Conformance")
	nc.procedure = _get_default_procedure()
	nc.subject = subject
	nc.details = _(
		"Auto-escalated from Safety Incident {0}.\n"
		"Type: {1} | Severity: {2} | Location: {3} | Date: {4}\n"
		"Reported by: {5}\n\nDescription: {6}\n\nImmediate Action: {7}\n\n"
		"Root Cause: {8}\nCorrective Action: {9}"
	).format(
		doc.name, _(doc.incident_type), _(doc.severity), doc.location or "-",
		doc.incident_date, doc.reported_by or "-", doc.description or "-",
		doc.immediate_action or "-", doc.root_cause or "-", doc.corrective_action or "-",
	)
	nc.insert(ignore_permissions=True)

	if doc.severity in ("Major", "Critical"):
		frappe.sendmail(
			recipients=["admin@example.com"],
			subject=_("High-severity lab incident escalated: {0}").format(doc.name),
			message=_(
				"Safety Incident {0} ({1}, severity {2}) was submitted and escalated to "
				"Non Conformance {3}. QA review required."
			).format(doc.name, _(doc.incident_type), _(doc.severity), nc.name),
		)

	frappe.msgprint(
		_("Non Conformance {0} created from Safety Incident {1}.").format(nc.name, doc.name),
		indicator="blue",
	)
