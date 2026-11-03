# Copyright (c) 2026 Bio Pharma Suite
"""数据导入导出通道。

三层能力：
1. 原生（零开发）：Frappe Data Import 支持全部 DocType 的 CSV/XLSX 导入导出
   （侧边栏 → Data Import；列表视图 → Export）。GMP 场景建议配模板校验。
2. API 导出（本模块）：面向外部系统（MATLAB/LIMS/CDS/集团数据湖）的结构化导出，
   见 matlab_api.export_dataset（字段白名单 + 过滤器 + CSV/JSON 双格式）。
3. 批量导入辅助（本模块）：仪器历史温度 CSV 批量回灌（Data Import 不便处理的
   高频时序数据），逐行走 ingest_reading 联动，保留幂等与越限检查。
"""

import csv
import io

import frappe
from frappe import _


@frappe.whitelist()
def import_temperature_csv(file_url, warehouse=None, instrument_code=None, dry_run=1):
	"""批量回灌仪器历史温度 CSV（列：timestamp,temperature[,instrument_code][,warehouse]）。

	instrument_code：全局默认仪器（CSV 内列优先）；没有仪器归属的历史数据无法通过
	ingest_reading 的校验，故为必填之一。
	dry_run=1 只校验不落库；确认后 dry_run=0 正式导入。
	"""
	from bio_pharma_suite.integrations.instrument_api import ingest_reading

	file_doc = frappe.get_doc("File", {"file_url": file_url})
	raw = file_doc.get_content()
	reader = csv.DictReader(io.StringIO(raw.decode("utf-8") if isinstance(raw, bytes) else raw))

	required = {"timestamp", "temperature"}
	if not required.issubset(set(reader.fieldnames or [])):
		frappe.throw(_("CSV must contain columns: {0}").format(", ".join(sorted(required))))

	ok, failed, skipped = 0, [], 0
	for i, row in enumerate(reader, start=2):
		ins = row.get("instrument_code") or instrument_code
		wh = row.get("warehouse") or warehouse
		if not ins:
			failed.append({"line": i, "error": "no instrument_code"})
			continue
		if int(dry_run):
			if frappe.db.exists(
				"Temperature Log",
				{"warehouse": wh, "reading_timestamp": row["timestamp"], "temperature": float(row["temperature"])},
			):
				skipped += 1
			else:
				ok += 1
			continue
		try:
			ingest_reading(
				instrument_code=ins,
				kind="temperature",
				reading=row["temperature"],
				timestamp=row["timestamp"],
				warehouse=wh,
			)
			ok += 1
		except Exception as e:
			failed.append({"line": i, "error": str(e)})

	return {"dry_run": int(dry_run), "valid": ok, "duplicates": skipped, "failed": failed}


@frappe.whitelist()
def export_temperature_csv(warehouse=None, from_date=None, to_date=None, instrument_code=None):
	"""导出温度记录 CSV（与 import_temperature_csv 列格式对称，可回灌）。

	审计场景：QA 导出某温区/某仪器在时间段内的完整温度记录随审计包归档。
	返回内联 CSV（Content-Disposition 附件），与 Data Import/Excel 兼容。
	"""
	filters = {}
	if warehouse:
		filters["warehouse"] = warehouse
	if instrument_code:
		ins_name = frappe.db.get_value("Instrument", {"instrument_code": instrument_code}, "name")
		if not ins_name:
			frappe.throw(_("Unknown instrument_code: {0}").format(instrument_code))
		filters["instrument"] = ins_name
	if from_date and to_date:
		filters["reading_timestamp"] = [
			"between",
			["{} 00:00:00".format(from_date), "{} 23:59:59".format(to_date)],
		]
	elif from_date:
		filters["reading_timestamp"] = [">=", "{} 00:00:00".format(from_date)]
	elif to_date:
		filters["reading_timestamp"] = ["<=", "{} 23:59:59".format(to_date)]

	rows = frappe.get_all(
		"Temperature Log",
		filters=filters,
		fields=["reading_timestamp", "temperature", "instrument", "warehouse", "has_excursion", "name"],
		order_by="reading_timestamp asc",
	)

	code_map = {}
	if rows:
		ins_names = {r.instrument for r in rows if r.instrument}
		if ins_names:
			code_map = dict(frappe.get_all(
				"Instrument",
				filters={"name": ["in", list(ins_names)]},
				fields=["name", "instrument_code"],
				as_list=True,
			))

	buf = io.StringIO()
	writer = csv.writer(buf)
	writer.writerow(["timestamp", "temperature", "instrument_code", "warehouse", "has_excursion"])
	for r in rows:
		writer.writerow([
			r.reading_timestamp,
			r.temperature,
			code_map.get(r.instrument, r.instrument or ""),
			r.warehouse or "",
			int(r.has_excursion or 0),
		])

	frappe.response["result"] = buf.getvalue()
	frappe.response["doctype"] = "temperature_export_{}".format(frappe.utils.today())
	frappe.response["type"] = "csv"
