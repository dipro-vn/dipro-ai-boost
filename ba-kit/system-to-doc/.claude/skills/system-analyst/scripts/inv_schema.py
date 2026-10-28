#!/usr/bin/env python3
"""Hop dong schema cua inventory workbook.

Moi gate script va build-inventory.py deu import tu day.
Doi ten cot => chi doi o file nay, KHONG hardcode o noi khac.
Tai lieu nguoi doc: .claude/sys-agent/inventory-spec.md
"""
import re

META_KEYS = [
    "system_name", "customer", "version_label", "version_folder", "version_type",
    "generated_date", "previous_version", "run_mode",
    "scope", "websites", "accounts", "access_approved_by", "crawl_mode",
    "forbidden_zones", "source_repos",
    "repo_commit",  # "REPO-01=<commit>;REPO-02=<commit>" (scan-repo.py stdout) — so lan sau de biet repo doi chua
    "db_mode", "figma_input_url", "ds_publish",
    "figma_output_url", "bug_list", "bug_recipient", "bug_scan_scope",
    "lang", "audience",
    "baseline",  # folder baseline goc (CR: baseline CR tro toi · baseline moi: baseline truoc + CR da promote)
    "sensitive_scan", "env_observed", "crawl_budget_used",
]

SHEETS = {
    "00_Meta": ["Key", "Value"],
    "01_Function": [
        "Function ID", "Module", "Function", "Primary Actor", "Description",
        "Entry / Trigger", "Screen IDs", "Related Tables", "Evidence",
        "Source", "Status", "Open Q", "Note",
    ],
    "02_Screen": [
        "Screen ID", "Site", "URL / Route", "Screen Name", "Type", "Actor",
        "Entry From", "Function IDs", "Screenshot EV", "Item Count",
        "Status", "Note",
    ],
    "03_DB_Tables": [
        "Table", "Purpose", "PK", "FK", "Important Columns", "Est Rows",
        "Related Function IDs", "Evidence", "Confidence", "Note",
    ],
    "04_DB_Columns": [
        "Table", "Column", "Type", "PK", "FK", "Nullable", "Default",
        "Max Length", "Format", "Constraint",
        "Meaning", "Used By", "Evidence", "Confidence",
    ],
    "05_Evidence": [
        "EV ID", "Type", "Locator", "Captured At", "Actor/Role",
        "Artifact", "Note",
    ],
    "06_OpenQuestions": [
        "Q ID", "Type", "Item", "Reason / Evidence", "Required Action",
        "Owner", "Status", "Note",
    ],
    "07_API": [
        "API ID", "Group", "Kind", "Method", "Path / Schedule", "Summary",
        "Auth", "Handler", "Repo", "Called By Screens", "Related Tables",
        "Evidence", "Status", "Open Q", "Note",
    ],
    "08_API_Fields": [
        "API ID", "Direction", "In", "Field", "Type", "Required",
        "Format / Constraint", "Description", "Evidence",
    ],
    "09_Integration": [
        "EXT ID", "Name", "Kind", "Purpose", "Direction", "Used By",
        "Config Keys", "Evidence", "Status", "Note",
    ],
    "10_Site": [
        "Site ID", "Site Name", "URL", "Env", "Roles Observed", "Crawl Mode",
        "FE Repo", "Screen Count", "Note",
    ],
    "11_Repo": [
        "Repo ID", "Path", "Kind", "Stack", "For Site", "Note",
    ],
}

# O7 — 1 sheet duy nhat (feedback 28/10/2026): bug muc High tro len, anh huong thao tac nguoi dung,
# tim thay khi doc source code va / hoac khi crawl website. Pham vi quet + nguoi nhan nam o 00_Meta cua inventory.
BUG_SHEET = "Bug List"
BUG_SHEETS = {
    BUG_SHEET: [
        "Bug ID", "Title", "Screen / Module", "URL / Route", "Category",
        "Severity", "Repro Steps", "Expected", "Actual", "Evidence",
        "Reproduced", "Detected By", "Business Impact", "Env",
        "Pre-existing", "Status", "Note",
    ],
}

# --- Enum ---
FUNCTION_STATUS = ["Confirmed", "To verify", "Inferred", "CONFLICT"]
SCREEN_STATUS = ["Confirmed", "To verify", "Inferred"]
SCREEN_TYPE = ["List", "Detail", "Form", "Modal", "Error", "Other"]
EVIDENCE_TYPE = ["screenshot", "har", "console-log", "code-ref", "db-query", "doc-quote"]
EVIDENCE_NEEDS_ARTIFACT = ["screenshot", "har", "console-log"]
CONFIDENCE = ["High", "Medium", "Low"]
QUESTION_TYPE = ["Thiếu thông tin", "Inference", "Risk", "CONFLICT"]
QUESTION_STATUS = ["Open", "Answered", "Closed"]
SOURCE_TOKENS = ["UI", "Code", "DB", "Doc"]
CRAWL_MODE = ["READ_ONLY", "SUBMIT_STAGING", "SUBMIT_PROD", "NO_CRAWL"]
RUN_MODE = ["FULL", "DELTA", "READ_ONLY_REVIEW"]
DB_MODE = ["DUMP", "READONLY_CONN", "MIGRATION", "NONE"]
VERSION_TYPE = ["BASELINE", "CR"]

API_KIND = ["API", "BATCH", "WEBHOOK", "QUEUE"]
API_METHOD = ["GET", "POST", "PUT", "PATCH", "DELETE", "ANY", "CRON", "EVENT"]
API_STATUS = ["Confirmed", "To verify", "Inferred"]
API_FIELD_DIRECTION = ["REQUEST", "RESPONSE"]
API_FIELD_IN = ["path", "query", "header", "cookie", "body", "status", "response-body"]
INTEGRATION_DIRECTION = ["OUTBOUND", "INBOUND", "BOTH"]
INTEGRATION_STATUS = ["Confirmed", "To verify", "Inferred"]
REPO_KIND = ["FE", "BE", "FULLSTACK", "BATCH", "OTHER"]

# O7: code truoc, website sau; chi loi anh huong thao tac nguoi dung, muc High tro len.
BUG_CATEGORY = ["Functional", "UI/Layout", "Performance", "Compatibility"]
BUG_SEVERITY = ["Urgent", "High"]
BUG_DETECTED_BY = ["Code review", "Playwright", "Code review + Playwright"]
BUG_EVIDENCE = ["screenshot", "console-log", "har", "code-ref"]
BUG_CODE_ONLY = "Chỉ đọc từ code"   # gia tri cot Reproduced khi chua tai hien tren man
BUG_NOISE = ["read-only-block", "csp-block"]   # console.json "noise" do crawl-site.js gan -> khong phai bug
BUG_PRE_EXISTING = ["Yes", "Cần xác nhận"]

ID_PATTERNS = {
    "01_Function": ("Function ID", r"^F-\d{3,}$"),
    "02_Screen": ("Screen ID", r"^SC-\d{3,}$"),
    "05_Evidence": ("EV ID", r"^EV-\d{4,}$"),
    "06_OpenQuestions": ("Q ID", r"^Q-\d{3,}$"),
    "07_API": ("API ID", r"^API-\d{3,}$"),
    "09_Integration": ("EXT ID", r"^EXT-\d{3,}$"),
    "10_Site": ("Site ID", r"^WEB-\d{2,}$"),
    "11_Repo": ("Repo ID", r"^REPO-\d{2,}$"),
}

# --- Change Request impact workbook (Luong 2) — 7 sheet ---
# Nguon du lieu: <ver>/_internal/cr.json (agent viet) -> build-cr-impact.py render xlsx.
# Summary (chi cong so + so doi tuong doi + link) · Estimation (theo templates/template_estimation.xlsx)
# · Screen / API / Database / Figma (hang muc theo truc) · Q&A (vi sao la CR, cau hoi KH, khong thuoc CR).
# Truc Business + ThirdParty khong co sheet rieng — chi nam trong Estimation (Flow da the hien tren Figma).
CR_META_KEYS = [
    "cr_id", "cr_title", "baseline_version", "cr_version", "source_type",
    "source_ref", "received_date", "requested_by", "overall_risk", "recommendation",
]
CR_AXES = ["System", "DB", "Business", "Screen", "ThirdParty", "Mockup"]
CR_CHANGE_TYPE = ["NEW", "UPD", "DEL", "IMPACT"]
CR_CONFLICT = ["Yes", "No", "To verify"]
CR_RISK = ["High", "Medium", "Low"]
CR_SOURCE_TYPE = ["FILE", "CHAT", "LINK"]
CR_CRITERIA = {
    "C1": "Chuc nang / man / API / bang moi chua co trong he thong hien tai (baseline)",
    "C2": "Doi hanh vi dang chay da Confirmed trong baseline (khach doi y, khong phai he thong loi)",
    "C3": "Them / bo man, actor, chuc nang, lien ket ben thu 3",
    "C4": "Doi business rule / validation dang chay",
    "C5": "Doi nen tang / thiet bi / yeu cau phi chuc nang (hieu nang, bao mat, trinh duyet)",
    "C6": "Keo theo doi schema DB, API contract hoac tai lieu da ban giao",
}
CR_NOT_CR_LABEL = ["BUG", "QUESTION"]
CR_SHEET_SUMMARY = "Summary"
CR_SHEET_ESTIMATION = "Estimation"
CR_SHEET_QA = "Q&A"
CR_AXIS_SHEETS = [("Screen", ["Screen"]), ("API", ["System"]), ("Database", ["DB"]), ("Figma", ["Mockup"])]
CR_SHEETS = [CR_SHEET_SUMMARY, CR_SHEET_ESTIMATION] + [s for s, _ in CR_AXIS_SHEETS] + [CR_SHEET_QA]
CR_ESTIMATION_ONLY_AXES = ["Business", "ThirdParty"]
ESTIMATION_TEMPLATE_PATH = "templates/template_estimation.xlsx"
CR_IMPACT_COLS = [  # header hien thi cho khach -> tieng Viet co dau
    "No", "Impact ID", "Trục", "Loại", "Baseline Ref", "Hạng mục",
    "Nội dung thay đổi", "Vì sao phải sửa", "Ảnh hưởng tới hiện tại",
    "Xung đột", "Chi tiết xung đột", "Rủi ro", "Mã đơn giá", "Số lượng",
    "MD", "Ghi chú MD", "Evidence", "Câu hỏi",
]
CR_IMPACT_ID = r"^IMP-\d{3,}$"
CR_QUESTION_ID = r"^CQ-\d{3,}$"
MD_RATES_PATH = ".claude/config/md-unit-rates.json"

NO_IMAGE = "NO IMAGE"
NO_SCREEN = "SYSTEM — no screen"
# D1: chu hien thi khi chua co bang chung (code lan web deu khong co). O cu the ghi kem cau hoi:
# "Cần xác nhận — Q-012" (ban JP "要確認 — Q-012"); trang thai tuong ung = "To verify" + bat buoc Open Question.
NEED_CONFIRM = "Cần xác nhận"
NEED_CONFIRM_JP = "要確認"
# Chuyen doi du lieu cu (truoc D1): version cu con chu "UNKNOWN" / "Unknown" / "Unknow" -> khi doc / carry tu doi:
# cot trang thai -> "To verify", loai cau hoi -> "Thiếu thông tin", o noi dung -> NEED_CONFIRM.
# Day la cho DUY NHAT kit con giu chu nay (+ self-test); gate "khong con chu cu" dung has_legacy() — khong phan
# biet hoa thuong (feedback 28/10/2026: triet de, ke ca chu trich tu code).
LEGACY_WORD = "UNKNOWN"  # _legacy_unknown
LEGACY_RX = re.compile(r"(?i)\bunknown?\b")
STATUS_COLS = ("Status", "Confidence", "Xung đột")


def has_legacy(value):
    return isinstance(value, str) and bool(LEGACY_RX.search(value))


def legacy(value, col=""):
    """Gia tri doc tu version cu -> gia tri theo D1 (khong doi gia tri da dung)."""
    if not has_legacy(value):
        return value
    if col in STATUS_COLS:
        return "To verify"
    if col == "Type" and LEGACY_RX.fullmatch(value.strip()):
        return QUESTION_TYPE[0]
    return LEGACY_RX.sub(NEED_CONFIRM, value)


def load(path, sheets=None):
    """Doc workbook -> {sheet: [dict theo header]}. Raise neu thieu sheet."""
    try:
        from openpyxl import load_workbook
    except ImportError:
        raise SystemExit("Thieu openpyxl. Chay: pip install openpyxl")
    sheets = sheets or SHEETS
    wb = load_workbook(path, data_only=True)
    missing = [s for s in sheets if s not in wb.sheetnames]
    if missing:
        raise SystemExit("Workbook thieu sheet: %s" % ", ".join(missing))
    out = {}
    for name in sheets:
        ws = wb[name]
        rows = []
        header = [str(c.value).strip() if c.value is not None else "" for c in ws[1]]
        for r in ws.iter_rows(min_row=2, values_only=True):
            if all(v is None or str(v).strip() == "" for v in r):
                continue
            d = {}
            for i, h in enumerate(header):
                if not h:
                    continue
                v = r[i] if i < len(r) else None
                d[h] = legacy("" if v is None else str(v).strip(), h)
            d["__row__"] = ws.max_row
            rows.append(d)
        # gan so dong that
        for idx, d in enumerate(rows, start=2):
            d["__row__"] = idx
        out[name] = rows
    return out


def meta(data):
    """00_Meta -> dict key/value."""
    return {r.get("Key", ""): r.get("Value", "") for r in data.get("00_Meta", [])}


def split_ids(value):
    """'EV-1;EV-2' hoac 'F-1,F-2' -> list."""
    if not value:
        return []
    out = []
    for chunk in str(value).replace(";", ",").split(","):
        c = chunk.strip()
        if c and c not in ("—", "-", "N/A"):
            out.append(c)
    return out


# PNG matplotlib (ERD build-db-doc): DejaVu khong co chu Nhat -> o vuong.
CJK_FONTS = ("Hiragino Sans", "Hiragino Kaku Gothic ProN", "Arial Unicode MS", "Noto Sans CJK JP", "Noto Sans JP",
             "IPAexGothic", "IPAGothic", "TakaoGothic", "Yu Gothic", "Meiryo", "MS Gothic")


def use_cjk_font(matplotlib):
    """Dat font.family = font CJK co tren may (macOS / Linux / Windows) + DejaVu cho glyph con thieu."""
    import sys
    from matplotlib import font_manager
    have = {f.name for f in font_manager.fontManager.ttflist}
    pick = [f for f in CJK_FONTS if f in have]
    matplotlib.rcParams["font.family"] = pick + ["DejaVu Sans"]
    if not pick:
        print("canh bao: may khong co font CJK (%s) -> chu Nhat trong PNG thanh o vuong" % ", ".join(CJK_FONTS[:4]),
              file=sys.stderr)
    return pick[0] if pick else None
