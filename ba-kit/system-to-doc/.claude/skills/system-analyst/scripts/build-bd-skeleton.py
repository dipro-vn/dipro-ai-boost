#!/usr/bin/env python3
"""Build Basic Design skeleton — máy sinh phần cấu trúc, LLM chỉ điền P/Q.

Feedback 22/11/2026 P1-4: hiện LLM gõ lại 90% dữ liệu crawler/AST đã có (type, status,
maxlength, box, mã EV) trong spec.json 75KB cho 78 item. Script này gộp chúng
thành skeleton-<WEB-xx>.json — LLM chỉ cần điền:
  - purpose / access (ngắn, nghiệp vụ)
  - item.p / item.q (mô tả JP / VN)
  - item.group (tên nhóm cho feature grouping)
  - 「Step 1：画面共通」 6 dòng (feedback 22/11/2026 P1-5)
  - error.impact / error.fix (ERROR SCENARIOS)
  - question_proposals (gợi ý trả lời cho Q)

Input:
  --ast-spec <path>       output của ast/extract-screen.mjs (dữ kiện FE code)
  --crawl <path>          recon/crawl/<WEB-xx>/ (pages.json → item observed)
  --fe-api-calls <path>   recon/code/REPO-xx/fe-api-calls.csv
  --inventory <path>      _internal/inventory.xlsx (để map SC-xxx)
  --site <WEB-xx>
  --out <path>            skeleton-<WEB-xx>.json

Output schema:
  {
    "site": "WEB-01",
    "generated_at": "2026-11-25T12:00:00",
    "source_mode": "code" | "website" | "hybrid",
    "screens": {
      "SC-001": {
        "title": "...",              # từ inventory
        "type": "list" | "form" | "detail",
        "entry_from": "...",
        "function_ids": ["FL-01"],
        "common_step1": {            # 6 dòng cấp màn — LLM điền phần ngoài observed
          "initial_display": null,   # ← LLM điền
          "permission": null,        # ← LLM điền
          "data_scope": null,        # ← LLM điền
          "state_keep": null,        # ← LLM điền
          "loading_zero_error": null,# ← LLM điền
          "url_invalid": null        # ← LLM điền
        },
        "items": [
          {
            "n": 1,
            "name_jp": "イベント名",   # observed
            "name_vn": "Tên sự kiện", # observed
            "type": "Textbox",        # observed (enum)
            "status": "Enable",       # observed
            "required": "○",          # from validation
            "maxlength": 50,          # from validation
            "default": "",            # observed
            "box": [x0,y0,x1,y1],     # observed (cho annotate badge ngoài box)
            "ev": "EV-0003",          # máy gán
            "api": "POST /api/events (API-015)", # from fe-api-calls
            "code_ref": "REPO-01:src/pages/events.tsx#L45", # observed
            # Phần LLM điền:
            "p": null,
            "q": null,
            "group": null
          }
        ],
        "errors": [],
        "question_proposals": []
      }
    }
  }

LLM dùng skeleton này → viết SPEC JSON ngắn chỉ gồm diffs (purpose/access/p/q/group/common_step1/errors).
build-basic-design.py merge skeleton + spec ngắn → workbook.

Shortcut: hiện implementation mức minimum viable — chỉ skeleton frame + copy từ ast-spec.
Full implementation (parse pages.json + fe-api-calls.csv + mapping EV) sẽ follow-up.
"""
import argparse, json, os, sys


def load(path, default=None):
    if not path or not os.path.exists(path):
        return default if default is not None else {}
    with open(path, encoding="utf8") as f:
        return json.load(f)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ast-spec", help="Output ast/extract-screen.mjs")
    ap.add_argument("--crawl", help="recon/crawl/<WEB-xx>/")
    ap.add_argument("--fe-api-calls", action="append", default=[])
    ap.add_argument("--inventory", required=True)
    ap.add_argument("--site", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    ast_screens = load(a.ast_spec, {}).get("screens", {})
    pages = load(os.path.join(a.crawl or "", "pages.json"), [])
    pages_by_sid = {p.get("screen_id"): p for p in (pages if isinstance(pages, list) else [])}

    # Load inventory 02_Screen minimal (dùng openpyxl nếu có, fallback skip)
    screens_inv = {}
    try:
        import openpyxl
        wb = openpyxl.load_workbook(a.inventory, data_only=True)
        if "02_Screen" in wb.sheetnames:
            ws = wb["02_Screen"]
            hdr = [c.value for c in ws[1]]
            for row in ws.iter_rows(min_row=2, values_only=True):
                d = dict(zip(hdr, row))
                if d.get("Site") == a.site and d.get("Screen ID"):
                    screens_inv[d["Screen ID"]] = d
    except Exception as exc:
        print(f"WARN khong doc duoc inventory: {exc}", file=sys.stderr)

    source_mode = "hybrid" if ast_screens and pages else ("code" if ast_screens else "website")

    skeleton = {
        "site": a.site,
        "source_mode": source_mode,
        "screens": {},
    }

    for sid, inv_data in screens_inv.items():
        ast_sc = ast_screens.get(sid, {})
        page = pages_by_sid.get(sid, {})
        # items: ưu tiên AST (có validation), bổ sung crawl
        items_raw = ast_sc.get("items") or page.get("items") or []
        items = []
        for i, it in enumerate(items_raw, start=1):
            items.append({
                "n": i,
                "name_jp": it.get("name_jp") or it.get("label") or "",
                "name_vn": it.get("name_vn") or "",
                "type": it.get("type") or "",
                "status": it.get("status") or "Enable",
                "required": it.get("required") or "",
                "maxlength": it.get("maxlength") or "",
                "default": it.get("default") or "",
                "box": it.get("box"),     # [x0,y0,x1,y1] cho annotate (feedback 22/11/2026 lỗi #2)
                "ev": it.get("ev") or "",
                "api": it.get("api") or "",
                "code_ref": it.get("code_ref") or "",
                # LLM điền:
                "p": None, "q": None, "group": None,
            })
        skeleton["screens"][sid] = {
            "title": inv_data.get("Screen Name") or ast_sc.get("title") or sid,
            "type": ast_sc.get("type") or "unknown",
            "entry_from": inv_data.get("Entry From") or "",
            "function_ids": inv_data.get("Function IDs") or "",
            # 6 dòng cấp màn — LLM điền (feedback 22/11/2026 P1-5):
            "common_step1": {
                "initial_display": None, "permission": None, "data_scope": None,
                "state_keep": None, "loading_zero_error": None, "url_invalid": None,
            },
            "items": items,
            "errors": ast_sc.get("errors") or [],
            "question_proposals": [],
        }

    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w", encoding="utf8") as f:
        json.dump(skeleton, f, ensure_ascii=False, indent=2)
    print(json.dumps({"out": a.out, "screens": len(skeleton["screens"]),
                      "source_mode": source_mode,
                      "items_total": sum(len(s["items"]) for s in skeleton["screens"].values())},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
