# Copyright (c) 2026, Bio Pharma Suite and contributors
# For license information, please see license.txt

"""Batch 360 View - single-page quality dossier per batch.

Regulatory basis: GMP (2010 Rev.) batch record requirements, 21 CFR Part 11.
Aggregates identity, quality status, QI results, OOS, batch release,
temperature excursions and stability studies for one batch at a glance.
"""

import frappe
from frappe import _


def execute(filters=None):
    filters = _norm(filters)
    return get_columns(), get_data(filters)


def _norm(filters):
    f = frappe._dict(filters or {})
    batch_no = f.get("batch_no") or f.get("batch") or f.get("name") or None
    return frappe._dict({"batch_no": batch_no})


def get_columns():
    return [
        {"label": _("Batch No"), "fieldname": "batch_no", "fieldtype": "Link",
         "options": "Batch", "width": 150},
        {"label": _("Item Code"), "fieldname": "item_code", "fieldtype": "Link",
         "options": "Item", "width": 140},
        {"label": _("Item Name"), "fieldname": "item_name", "fieldtype": "Data", "width": 180},
        {"label": _("Quality Status"), "fieldname": "quality_status", "fieldtype": "Data", "width": 110},
        {"label": _("Expiry Date"), "fieldname": "expiry_date", "fieldtype": "Date", "width": 100},
        {"label": _("QI Total"), "fieldname": "qi_total", "fieldtype": "Int", "width": 80},
        {"label": _("QI Rejected"), "fieldname": "qi_rejected", "fieldtype": "Int", "width": 90},
        {"label": _("OOS Total"), "fieldname": "oos_total", "fieldtype": "Int", "width": 80},
        {"label": _("OOS Open"), "fieldname": "oos_open", "fieldtype": "Int", "width": 80},
        {"label": _("Release Decision"), "fieldname": "release_decision", "fieldtype": "Data", "width": 130},
        {"label": _("Released On"), "fieldname": "released_on", "fieldtype": "Data", "width": 110},
        {"label": _("Temp Excursions"), "fieldname": "temp_excursions", "fieldtype": "Int", "width": 100},
        {"label": _("Stability Studies"), "fieldname": "stability_count", "fieldtype": "Int", "width": 110},
    ]


def _fields_of(doctype, wanted):
    """Return only wanted fieldnames that actually exist on the DocType."""
    try:
        meta = frappe.get_meta(doctype)
        valid = {df.fieldname for df in meta.fields}
    except Exception:
        valid = set()
    valid.update({"name", "docstatus", "creation", "modified", "owner"})
    return [f for f in wanted if f in valid]


def get_data(filters):
    batches = _get_batches(filters)
    if not batches:
        return []

    batch_nos = [b.get("name") for b in batches]
    qi = _qi_stats(batch_nos)
    oos = _oos_stats(batch_nos)
    brr = _brr_stats(batch_nos)
    exc = _excursion_stats(batch_nos)
    stab = _stability_stats(batches, batch_nos)

    out = []
    for b in batches:
        name = b.get("name")
        q = qi.get(name, {"total": 0, "rejected": 0})
        o = oos.get(name, {"total": 0, "open": 0})
        r = brr.get(name, {})
        out.append({
            "batch_no": name,
            "item_code": b.get("item") or "",
            "item_name": b.get("item_name") or "",
            "quality_status": b.get("quality_status") or "",
            "expiry_date": b.get("expiry_date"),
            "qi_total": q["total"],
            "qi_rejected": q["rejected"],
            "oos_total": o["total"],
            "oos_open": o["open"],
            "release_decision": r.get("decision", ""),
            "released_on": r.get("released_on", ""),
            "temp_excursions": exc.get(name, 0),
            "stability_count": stab.get(name, 0),
        })
    return out


def _get_batches(filters):
    fields = _fields_of("Batch", ["name", "item", "expiry_date", "quality_status"])
    conds = {}
    if filters.get("batch_no"):
        conds["name"] = filters["batch_no"]
    batches = frappe.get_all("Batch", filters=conds, fields=fields, limit=500)
    item_names = {i.get("name"): i.get("item_name") for i in
        frappe.get_all("Item", fields=["name", "item_name"])}
    for b in batches:
        b["item_name"] = item_names.get(b.get("item"), "")
    return batches


def _qi_stats(batch_nos):
    stats = {}
    fields = _fields_of("Quality Inspection", ["name", "batch_no", "status"])
    if "batch_no" not in fields:
        return stats
    rows = frappe.get_all("Quality Inspection",
        filters={"batch_no": ("in", batch_nos), "docstatus": ("<", 2)},
        fields=fields)
    for r in rows:
        s = stats.setdefault(r.get("batch_no"), {"total": 0, "rejected": 0})
        s["total"] += 1
        if r.get("status") == "Rejected":
            s["rejected"] += 1
    return stats


def _oos_stats(batch_nos):
    stats = {}
    sfields = _fields_of("Lab Sample", ["name", "batch_no"])
    if "batch_no" not in sfields:
        return stats
    samples = {s.get("name"): s.get("batch_no") for s in frappe.get_all("Lab Sample",
        filters={"batch_no": ("in", batch_nos)}, fields=sfields)}
    if not samples:
        return stats
    ofields = _fields_of("OOS Investigation", ["name", "sample", "docstatus", "status"])
    if "sample" not in ofields:
        return stats
    rows = frappe.get_all("OOS Investigation",
        filters={"sample": ("in", list(samples.keys())), "docstatus": ("<", 2)},
        fields=ofields)
    for r in rows:
        batch = samples.get(r.get("sample"))
        if not batch:
            continue
        s = stats.setdefault(batch, {"total": 0, "open": 0})
        s["total"] += 1
        if r.get("docstatus") == 0 and (r.get("status") or "") != "Closed":
            s["open"] += 1
    return stats


def _brr_stats(batch_nos):
    stats = {}
    fields = _fields_of("Batch Release Record",
        ["name", "batch_no", "release_decision", "release_date", "creation"])
    if "batch_no" not in fields:
        return stats
    rows = frappe.get_all("Batch Release Record",
        filters={"batch_no": ("in", batch_nos), "docstatus": 1}, fields=fields)
    for r in rows:
        stats[r.get("batch_no")] = {
            "decision": r.get("release_decision") or "",
            "released_on": str(r.get("release_date") or r.get("creation") or ""),
        }
    return stats


def _excursion_stats(batch_nos):
    stats = {}
    fields = _fields_of("Temperature Excursion Batch", ["parent", "batch_no"])
    if "batch_no" not in fields:
        return stats
    per_batch = {}
    rows = frappe.get_all("Temperature Excursion Batch",
        filters={"batch_no": ("in", batch_nos)}, fields=fields)
    for r in rows:
        per_batch.setdefault(r.get("batch_no"), set()).add(r.get("parent"))
    for b, parents in per_batch.items():
        stats[b] = len(parents)
    return stats


def _stability_stats(batches, batch_nos):
    stats = {}
    fields = _fields_of("Stability Study",
        ["name", "batch_no", "item_code", "docstatus"])
    if not fields:
        return stats
    rows = frappe.get_all("Stability Study",
        filters={"docstatus": ("<", 2)}, fields=fields)
    if "batch_no" in fields:
        wanted = set(batch_nos)
        for r in rows:
            bn = r.get("batch_no")
            if bn in wanted:
                stats[bn] = stats.get(bn, 0) + 1
    elif "item_code" in fields:
        item_to_batches = {}
        for b in batches:
            item_to_batches.setdefault(b.get("item"), set()).add(b.get("name"))
        for r in rows:
            for bn in item_to_batches.get(r.get("item_code"), set()):
                stats[bn] = stats.get(bn, 0) + 1
    return stats
