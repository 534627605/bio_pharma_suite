import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import nowdate


class BatchReleaseRecord(Document):
	# ------------------------------------------------------------------
	# 合规核验（只读自动统计）
	# ------------------------------------------------------------------
	def _qi_stats(self) -> tuple[int, int]:
		"""返回 (该批次已提交 QI 总数, 其中 Rejected 数)。"""
		total = frappe.db.count(
			"Quality Inspection", {"batch_no": self.batch_no, "docstatus": 1}
		)
		rejected = frappe.db.count(
			"Quality Inspection",
			{"batch_no": self.batch_no, "docstatus": 1, "status": "Rejected"},
		)
		return total, rejected

	def _open_oos(self) -> int:
		return frappe.db.count(
			"OOS Investigation",
			{"batch_no": self.batch_no, "docstatus": ["<", 2], "status": ["!=", "Closed"]},
		)

	def _open_excursions(self) -> int:
		"""未关闭且 affected_batches 中包含该批次的越限事件。"""
		open_ids = frappe.get_all(
			"Temperature Excursion",
			filters={"docstatus": ["<", 2], "status": ["!=", "Closed"]},
			pluck="name",
		)
		if not open_ids:
			return 0
		return frappe.db.count(
			"Temperature Excursion Batch",
			{"parent": ["in", open_ids], "parenttype": "Temperature Excursion", "batch_no": self.batch_no},
		)

	def _refresh_checks(self):
		self.qi_total, self.qi_rejected = self._qi_stats()
		self.open_oos = self._open_oos()
		self.open_excursions = self._open_excursions()

	def validate(self):
		self._refresh_checks()

	# ------------------------------------------------------------------
	# 提交门禁：双人独立电子签名 + 全部合规核验通过
	# ------------------------------------------------------------------
	def _blocking_reasons(self) -> list[str]:
		reasons = []
		if self.qi_total == 0:
			reasons.append(_("no submitted Quality Inspection records for this batch"))
		if self.qi_rejected > 0:
			reasons.append(_("{0} rejected Quality Inspection(s) not resolved").format(self.qi_rejected))
		if self.open_oos > 0:
			reasons.append(_("{0} open OOS Investigation(s)").format(self.open_oos))
		if self.open_excursions > 0:
			reasons.append(_("{0} unresolved Temperature Excursion(s)").format(self.open_excursions))
		return reasons

	def before_submit(self):
		# 提交时取最新合规统计（不依赖 validate 是否已跑过）
		self._refresh_checks()
		if not (self.esign_prepared and self.esign_qp):
			frappe.throw(
				_("Both e-signatures (Preparer and Qualified Person) are required for batch release."),
				title=(_("Dual E-Signature Required")),
			)
		if not frappe.db.exists("Has Role", {"parent": self.qp_approver, "role": "Bio Pharma QP"}):
			frappe.throw(
				_("Qualified Person role (Bio Pharma QP) is required to approve batch release."),
				title=(_("Insufficient Privilege")),
			)
		if self.prepared_by == self.qp_approver:
			frappe.throw(
				_("Preparer and Qualified Person must be different users (independent dual sign-off)."),
				title=(_("Dual Sign-Off Violation")),
			)
		if self.release_decision == "Rejected" and not self.rejection_reason:
			frappe.throw(
				_("Rejection reason is required when the release decision is Rejected."),
				title=(_("Rejection Reason Required")),
			)
		# 判定矩阵门禁：每个决策都有法定记录要求（有据可依）
		if self.release_decision == "Concession Release" and not (
			(self.concession_scope or "").strip() and (self.decision_justification or "").strip()
		):
			frappe.throw(
				_(
					"Concession release requires both a concession scope (permitted deviation, quantity, use restrictions) and a documented justification."
				),
				title=(_("Concession Justification Required")),
			)
		if self.release_decision == "Recall" and not (self.recall_notice_no or "").strip():
			frappe.throw(
				_("A recall notice number is required for a recall decision."),
				title=(_("Recall Notice Required")),
			)
		if self.release_decision == "Scrap":
			if not (self.decision_justification or "").strip():
				frappe.throw(
					_("A justification is required for a scrap decision."),
					title=(_("Scrap Justification Required")),
				)
			if not self.disposal_stock_entry or frappe.db.get_value(
				"Stock Entry", self.disposal_stock_entry, "docstatus"
			) != 1:
				frappe.throw(
					_(
						"A submitted Disposal Stock Entry (transfer to Rejection/Scrap warehouse) is required before submitting a scrap decision — inventory and accounting must be written off."
					),
					title=(_("Disposal Stock Entry Required")),
				)
		if self.release_decision in ("Released", "Concession Release"):
			if not (self.appointment_doc_no or "").strip():
				frappe.throw(
					_(
						"A QP authorization document number is required to release a batch (authorization traceability)."
					),
					title=(_("Authorization Document Required")),
				)
			reasons = self._blocking_reasons()

			if reasons:
				frappe.throw(
					_("Batch {0} is not releasable: {1}").format(self.batch_no, "; ".join(reasons)),
					title=(_("Release Blocked")),
				)

	# ------------------------------------------------------------------
	# 提交联动：回写批次质量状态（判定矩阵）
	#   Released           → Released  合格放行
	#   Concession Release → Released  让步放行（例外放行，凭据留痕）
	#   Rejected           → Hold      拒绝放行（待改善复检）
	#   Recall             → Hold      召回中
	#   Scrap              → Rejected  报废（不合格，库存与账务经处置单核销）
	# ------------------------------------------------------------------
	def on_submit(self):
		self.release_effective_date = nowdate()
		decision_status = {
			"Released": ("Released", "green", "released to market"),
			"Concession Release": ("Released", "yellow", "released under concession"),
			"Rejected": ("Hold", "red", "REJECTED — held for rework and retest"),
			"Recall": ("Hold", "red", "RECALLED — held under recall notice {0}"),
			"Scrap": ("Rejected", "red", "SCRAPPED — inventory written off via {0}"),
		}
		if self.release_decision in ("Released", "Concession Release"):
			frappe.db.set_value(
				"Batch",
				self.batch_no,
				{"quality_status": "Released", "release_date": nowdate(), "released_by": self.qp_approver},
			)
		elif self.release_decision == "Scrap":
			frappe.db.set_value("Batch", self.batch_no, "quality_status", "Rejected")
		else:
			frappe.db.set_value("Batch", self.batch_no, "quality_status", "Hold")
		_status, color, verb = decision_status[self.release_decision]
		detail = (
			self.recall_notice_no
			if self.release_decision == "Recall"
			else (self.disposal_stock_entry if self.release_decision == "Scrap" else "")
		)
		frappe.msgprint(
			_("Batch Release Record {0}: Batch {1} {2}.").format(
				self.name, self.batch_no, verb.format(detail) if "{0}" in verb else verb
			),
			indicator=color,
		)

	def on_cancel(self):
		frappe.db.set_value("Batch", self.batch_no, "quality_status", "Quarantine")
		frappe.msgprint(_("Batch release cancelled: Batch {0} reverted to Quarantine.").format(self.batch_no))
