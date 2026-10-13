import json

import frappe


def run():
    for page in ["Setup", "Home", "Stock"]:
        try:
            data = frappe.call(
                "frappe.desk.desktop.get_desktop_page",
                page=json.dumps({"page": page}),
            )
            ws = (data or {}).get("workspace", {})
            print(f"PAGE {page} :: KEYS {list((data or {}).keys())}")
            if isinstance(ws, dict):
                print(f"  workspace keys={list(ws.keys())}")
            print(f"  content start={str(workspace)[:800]}") if False else None
            for k, v in (data or {}).items():
                if isinstance(v, dict) and isinstance(v.get("items"), list):
                    print(f"  {k}.items -> {len(v['items'])}")
                elif isinstance(v, list):
                    print(f"  {k} -> list len={len(v)}")
                elif isinstance(v, dict):
                    print(f"  {k} -> dict keys={list(v.keys())}")
                else:
                    print(f"  {k}={v!r}")
        except Exception as e:
            import traceback

            traceback.print_exc()
            print(f"PAGE {page} :: FAIL {type(e).__name__} {str(e)[:200]}")
