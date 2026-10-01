#!/usr/bin/env python3
"""Hop dong schema cua inventory workbook.

Moi gate script va build-inventory.py deu import tu day.
Doi ten cot => chi doi o file nay, KHONG hardcode o noi khac.
Tai lieu nguoi doc: .claude/sys-agent/inventory-spec.md
"""

META_KEYS = [
    "system_name", "customer", "version_label", "version_folder", "version_type",
    "generated_date", "previous_version", "run_mode",
    "scope", "websites", "accounts", "access_approved_by", "crawl_mode",
    "forbidden_zones", "source_repos", "db_mode", "figma_input_url",
    "figma_output_url", "bug_list", "bug_recipient", "bug_scan_scope",
    "lang", "audience",
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

BUG_SHEETS = {
    "00_Meta": ["Key", "Value"],
    "Bugs": [
        "Bug ID", "Title", "Screen / Module", "URL / Route", "Category",
        "Severity", "Repro Steps", "Expected", "Actual", "Evidence",
        "Reproduced", "Detected By", "Business Impact", "Env",
        "Pre-existing", "Report To Customer", "Status", "Note",
    ],
    "Observations": [
        "Obs ID", "Title", "Screen / Module", "Why suspicious",
        "Evidence", "Suggested investigation", "Note",
    ],
}
BUG_SHEETS["Suspected"] = list(BUG_SHEETS["Bugs"])

# --- Enum ---
FUNCTION_STATUS = ["Confirmed", "To verify", "Inferred", "CONFLICT"]
SCREEN_STATUS = ["Confirmed", "To verify", "Inferred"]
SCREEN_TYPE = ["List", "Detail", "Form", "Modal", "Error", "Other"]
EVIDENCE_TYPE = ["screenshot", "har", "console-log", "code-ref", "db-query", "doc-quote"]
EVIDENCE_NEEDS_ARTIFACT = ["screenshot", "har", "console-log"]
CONFIDENCE = ["High", "Medium", "Low"]
QUESTION_TYPE = ["Unknown", "Inference", "Risk", "CONFLICT"]
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

BUG_CATEGORY = ["Functional", "UI/Layout", "Data", "Performance", "Compatibility", "Security"]
BUG_SEVERITY = ["High", "Medium"]
BUG_DETECTED_BY = ["Playwright", "Code review", "DB check", "Console"]
BUG_REPORT = ["Yes", "Internal only"]

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

# --- Change Request impact workbook (Luong 2) ---
CR_META_KEYS = [
    "cr_id", "cr_title", "baseline_version", "cr_version", "source_type",
    "source_ref", "received_date", "requested_by", "summary",
    "overall_risk", "recommendation",
]
CR_AXES = {
    "01_System": "System",
    "02_DB": "DB",
    "03_Business": "Business",
    "04_Screen": "Screen",
    "05_ThirdParty": "ThirdParty",
    "06_Mockup": "Mockup",
}
CR_IMPACT_COLS = [
    "Impact ID", "Change Type", "Baseline Ref", "Item", "Change Description",
    "Impact On Current", "Conflict", "Conflict Detail", "Risk", "Evidence",
    "Open Q", "Note",
]
CR_SHEETS = {"00_Summary": ["Key", "Value"]}
CR_SHEETS.update({s: list(CR_IMPACT_COLS) for s in CR_AXES})
CR_SHEETS["07_Questions"] = ["Q ID", "Question", "Why It Matters", "Axis", "Owner", "Status"]
CR_CHANGE_TYPE = ["NEW", "UPD", "DEL", "NONE"]
CR_CONFLICT = ["Yes", "No", "UNKNOWN"]
CR_RISK = ["High", "Medium", "Low"]
CR_SOURCE_TYPE = ["FILE", "CHAT", "LINK"]
CR_IMPACT_ID = r"^IMP-\d{3,}$"
CR_QUESTION_ID = r"^CQ-\d{3,}$"

NO_IMAGE = "NO IMAGE"
NO_SCREEN = "SYSTEM — no screen"
UNKNOWN = "UNKNOWN"


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
                d[h] = "" if v is None else str(v).strip()
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
