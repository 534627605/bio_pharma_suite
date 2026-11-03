# Copyright (c) 2026 Bio Pharma Suite
"""设备 / 仪器 / 仪表数据传输接口。

统一接入端点（仪器侧只管推数，协议差异在 Instrument 主数据声明）：
- ingest_reading: 通用读数接入
  - 仪器 data_protocol = REST Push / MQTT / OPC-UA / Serial-CSV / File Drop
  - payload 种类：
    * kind="temperature" → 落 Temperature Log（温区/仓库从仪器绑定解析，越限自动联动）
    * kind="process"     → 原始过程读数，暂存 remarks/JSON（供后续扩展）
  - 认证：Frappe 原生 token（Authorization: token <key>:<secret>），
    网关/串口采集器可为每个仪器建专用 API User 并按仪器授权。
  - 幂等：同仪器+时间戳+读数 重复推送不重复入库。

温度载荷示例（POST JSON）：
  {"instrument_code": "INC-01", "kind": "temperature",
   "reading": -21.5, "timestamp": "2026-10-14 08:00:00"}
"""

import json

import frappe
from frappe import _
from frappe.utils import get_datetime, now_datetime


@frappe.whitelist()
def ingest_reading(instrument_code, kind="temperature", reading=None, timestamp=None, warehouse=None, payload=None):
	"""仪器/网关统一推数入口。返回入库结果；温度读数自动走冷链联动。

	warehouse 可选：不传时取仪器 location（必须是有效 Warehouse 名，否则报错）。
	"""
	ins = frappe.db.get_value(
		"Instrument",
		{"instrument_code": instrument_code},
		["name", "status", "location", "data_protocol", "active_interface", "api_user"],
		as_dict=True,
	)
	if not ins:
		frappe.throw(_("Unknown instrument_code: {0}").format(instrument_code), frappe.DoesNotExistError)
	if ins.status == "Retired":
		frappe.throw(_("Instrument {0} is retired; readings rejected").format(instrument_code))

	# 数据完整性：仪器绑定了专属 API 用户时，仅该用户（或系统管理员）可推数
	if ins.get("api_user"):
		if frappe.session.user != ins.api_user and not (
			frappe.session.user == "Administrator" or "System Manager" in frappe.get_roles()
		):
			frappe.throw(
				_("Instrument {0} accepts readings only from its bound API user {1}").format(
					instrument_code, ins.api_user
				),
				frappe.PermissionError,
			)

	ts = get_datetime(timestamp) if timestamp else now_datetime()

	if kind == "temperature":
		if reading is None:
			frappe.throw(_("temperature readings require field: reading"))
		effective_wh = warehouse or ins.location
		if not frappe.db.exists("Warehouse", effective_wh):
			frappe.throw(
				_("Warehouse {0} not found for instrument {1}. Pass a valid warehouse.").format(
					effective_wh, instrument_code
				)
			)

		# 幂等检查：同仓库同秒同值不重复入库
		if frappe.db.exists(
			"Temperature Log",
			{"warehouse": effective_wh, "reading_timestamp": ts, "temperature": float(reading)},
		):
			return {"ingested": 0, "reason": "duplicate"}

		log = frappe.new_doc("Temperature Log")
		log.warehouse = effective_wh
		log.temperature = float(reading)
		log.reading_timestamp = ts
		log.source = "IoT API"
		log.instrument = ins.name
		log.insert(ignore_permissions=True)
		created = log.name
	else:
		# 非温度过程读数：完整原始报文留痕（数据完整性可审计）
		created = None
		frappe.logger("bio_pharma_suite").info(
			"instrument_reading: {0} kind={1} reading={2} payload={3}".format(
				instrument_code, kind, reading, json.dumps(payload or {}, ensure_ascii=False, default=str)
			)
		)

	frappe.db.set_value("Instrument", ins.name, "last_data_sync", now_datetime(), update_modified=False)
	return {"ingested": 1, "kind": kind, "record": created, "instrument": ins.name}
