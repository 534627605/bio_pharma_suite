import frappe
from frappe import _
from frappe.model.document import Document


class TrainingRecord(Document):
	def validate(self):
		if self.controlled_document:
			if not frappe.db.exists("Controlled Document", self.controlled_document):
				frappe.throw(_("Controlled Document {0} does not exist.").format(self.controlled_document))

			doc_status, current_version = frappe.db.get_value(
				"Controlled Document", self.controlled_document, ["document_status", "current_version"]
			)
			if doc_status != "Effective":
				frappe.throw(
					_("Controlled Document {0} is not Effective. Train on the effective version only.").format(
						self.controlled_document
					),
					title=_("Document Not Effective"),
				)
			# 版本快照（首次带出后锁定；若受控文件版本已前进则阻断）
			if not self.document_version:
				self.document_version = current_version
			elif current_version and self.document_version != current_version:
				frappe.throw(
					_("Document version mismatch: Training Record targets {0} but current version is {1}.").format(
						self.document_version, current_version
					),
					title=_("Version Mismatch"),
				)
		self._summarize_results()

	def _summarize_results(self):
		self.pass_count = sum(1 for p in self.participants or [] if p.result == "Pass")
		self.fail_count = sum(1 for p in self.participants or [] if p.result == "Fail")

	def before_submit(self):
		self._summarize_results()
		pending = [p.participant or p.employee_name or "-" for p in self.participants or [] if p.result != "Pass"]
		if pending:
			frappe.throw(
				_("All participants must pass before submitting a Training Record."),
				title=_("Training Incomplete"),
			)
		if (
			frappe.db.get_single_value("Data Integrity Settings", "require_esignature_on_qi")
			and not self.esign_confirmed
		):
			frappe.throw(
				_("E-Signature confirmation is required to close a Training Record (21 CFR Part 11)."),
				title=_("E-Signature Required"),
			)
		if self.status != "Completed":
			self.status = "Completed"

	def on_submit(self):
		self.db_set("closed_on", frappe.utils.today())
		frappe.msgprint(_("Training Record {0} closed.").format(self.name))
