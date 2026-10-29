#!/usr/bin/env python3
"""Bo nho cau tra loi preflight cap du an (R9 · R10 · D8) — outputs/_project/preflight-memory.json.

  python3 preflight-memory.py missing --outputs outputs [--memory <json>] [--sensitive-files f1 f2 ...]
  python3 preflight-memory.py list    --outputs outputs [--memory <json>]
  python3 preflight-memory.py get     --code P2b [--memory <json>]
  python3 preflight-memory.py set     --code P2b --answer "..." --by-role "PM" [--source user|code|meta] [--pending]
  python3 preflight-memory.py confirm --outputs outputs --codes all|P0a,P1 [--by-role "PM"]
  python3 preflight-memory.py set-sensitive --classification "..." --files f1 f2 --by-role "PM"

Memory nam NGOAI folder version (dung cho moi lan chay ver1 / CR / ver<N+1>). Moi cau: answer · date · by_role ·
source ("người dùng trả lời" / "đọc từ code" / "kế thừa 00_Meta") · status (answered | pending).
KHONG BAO GIO luu gia tri credential — chi ten role / duong dan file (set tu choi, exit 2).
missing -> JSON: ask (chua co / pending / qua cu) · confirm_safety (4 cau an toan da co: hoi lai gon
"vẫn như lần trước chứ?") · confirm_table (cau da co: in 1 bang "Tôi đang dùng các thông tin sau — có gì đổi
không?") · sensitive_unclassified (file S1 chua duoc phan loai). Cau chua co trong memory nhung co trong 00_Meta cua
baseline moi nhat (version-tool.py context) -> coi la da co, nguon "kế thừa 00_Meta".
Danh sach cau + wording: sys-agent/preflight-questions.md (sua 1 cho -> sua ca QUESTIONS ben duoi).
"""
import argparse
import datetime
import importlib.util
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import inv_schema as S  # noqa: E402

_spec = importlib.util.spec_from_file_location("vt", os.path.join(HERE, "version-tool.py"))
VT = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(VT)

SOURCES = {"user": "người dùng trả lời", "code": "đọc từ code", "meta": "kế thừa 00_Meta"}
STALE_DAYS = 90
# (ma, chu de / luot hoi, khoa 00_Meta hoac None, an toan?) — chu de = 1 luot AskUserQuestion (toi da 4 cau)
QUESTIONS = [
    ("P0a", "Tên & phạm vi", "system_name", False),
    ("P0b", "Tên & phạm vi", "version_label", False),
    ("P0c", "Tên & phạm vi", "scope", False),
    ("P1", "Website", "websites", False),
    ("P1-env", "Website", None, True),            # an toan: moi truong thu nghiem hay that
    ("P2a", "Website", "accounts", False),
    ("P2b", "Website", "access_approved_by", True),   # an toan: tai khoan duoc phep quet tu dong
    ("P3", "Website", "crawl_mode", True),            # an toan: quyen thao tac
    ("P4", "Website", "forbidden_zones", False),
    ("P5", "Source code & database", "source_repos", False),
    ("P6", "Source code & database", "db_mode", False),
    ("P7", "Figma", "figma_input_url", False),
    ("P7b", "Figma", "ds_publish", False),
    ("P8", "Figma", "figma_output_url", False),
    ("P9", "Tài liệu & dữ liệu", "bug_list", False),
    ("P10", "Tài liệu & dữ liệu", "lang", False),
    ("P11", "Tài liệu & dữ liệu", None, True),       # an toan: co du lieu that cua nguoi dung
    # R10 — quyet dinh lon, hoi trong Discovery Brief sau Pha A
    ("B1", "Quyết định lớn", None, False),   # 1 hay nhieu Design System
    ("B2", "Quyết định lớn", None, False),   # lam O6 / O5 / O7 khong
    ("B3", "Quyết định lớn", None, False),   # repo legacy / khong dung toi
    ("B4", "Quyết định lớn", None, False),   # pham vi site / role
    ("B5", "Quyết định lớn", None, False),   # dong y dua so do DB / API len Figma (cloud ngoai) — D5
]
SAFETY = [q[0] for q in QUESTIONS if q[3]]
EMPTY = ("", "—", "-", S.NEED_CONFIRM)
# shortcut: chi bat dang "key=value" / "key: value" / user:pass@host, khong bat mat khau dung tran — van chay H06
CRED_RX = re.compile(r"(?i)(pass(word)?|passwd|pwd|secret|token|api[_-]?key|mật\s*khẩu|mat\s*khau)\s*[:=]\s*\S+"
                     r"|[^\s/:@]+:[^\s/@]+@[\w.-]+")


def default_memory(outputs):
    return os.path.join(outputs, "_project", "preflight-memory.json")


def load(path):
    if os.path.isfile(path):
        return json.load(open(path, encoding="utf8"))
    return {"answers": {}, "sensitive": []}


def save(path, mem):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    mem["updated"] = datetime.date.today().isoformat()
    json.dump(mem, open(path, "w", encoding="utf8"), ensure_ascii=False, indent=2)


def meta_answers(outputs):
    """00_Meta cua baseline moi nhat -> {ma: entry nguon 'kế thừa 00_Meta'}."""
    b = VT.latest_baseline(VT.scan(outputs)) if outputs and os.path.isdir(outputs) else None
    inv = os.path.join(b["path"], "_internal", "inventory.xlsx") if b else ""
    kv = VT.read_kv(inv, "00_Meta") if os.path.isfile(inv) else {}
    out = {}
    for code, _, key, _ in QUESTIONS:
        if key and kv.get(key, "") not in EMPTY:
            out[code] = {"answer": kv[key], "date": kv.get("generated_date", ""), "by_role": "—",
                         "source": SOURCES["meta"], "status": "answered", "from": b["folder"]}
    return out


def merged(mem, outputs):
    m = meta_answers(outputs)
    m.update(mem.get("answers", {}))   # memory thang 00_Meta
    return m


def is_stale(e, today):
    try:
        return (today - datetime.date.fromisoformat(e.get("date", "")[:10])).days > STALE_DAYS
    except ValueError:
        return False


def cmd_missing(a, mem):
    ans, today = merged(mem, a.outputs), datetime.date.today()
    res = {"ask": [], "confirm_safety": [], "confirm_table": [], "sensitive_unclassified": []}
    for code, topic, _, safe in QUESTIONS:
        e = ans.get(code)
        if not e or e.get("status") != "answered" or is_stale(e, today):
            res["ask"].append({"code": code, "topic": topic, "safety": safe,
                               "why": "pending" if e and e.get("status") == "pending" else
                               ("stale" if e else "missing")})
        elif safe:
            res["confirm_safety"].append({"code": code, "answer": e["answer"], "date": e.get("date", "")})
        else:
            res["confirm_table"].append({"code": code, "topic": topic, "answer": e["answer"],
                                         "source": e.get("source", ""), "date": e.get("date", "")})
    known = {f for s in mem.get("sensitive", []) for f in s.get("files", [])}
    res["sensitive_unclassified"] = [f for f in (a.sensitive_files or []) if f not in known]
    print(json.dumps(res, ensure_ascii=False, indent=2))
    return 0


def cmd_list(a, mem):
    ans = merged(mem, a.outputs)
    print("| Mã | Chủ đề | Câu trả lời | Nguồn | Ngày | Người trả lời | Trạng thái |")
    print("|---|---|---|---|---|---|---|")
    for code, topic, _, _ in QUESTIONS:
        e = ans.get(code, {})
        print("| %s | %s | %s | %s | %s | %s | %s |" % (code, topic, e.get("answer", "—"), e.get("source", "—"),
                                                     e.get("date", "—"), e.get("by_role", "—"),
                                                     e.get("status", "chưa có")))
    for s in mem.get("sensitive", []):
        print("\nS1 %s — %s (%s, %s)" % (s["classification"], ", ".join(s["files"]), s["by_role"], s["date"]))
    return 0


def cmd_get(a, mem):
    print(json.dumps(mem.get("answers", {}).get(a.code), ensure_ascii=False))
    return 0 if a.code in mem.get("answers", {}) else 1


def check_code(code):
    if code not in [q[0] for q in QUESTIONS]:
        raise SystemExit("Ma cau khong co: %s (xem QUESTIONS)" % code)


def no_cred(*texts):
    for t in texts:
        if t and CRED_RX.search(t):
            print("TU CHOI: cau tra loi trong giong credential — chi luu TEN role / duong dan file", file=sys.stderr)
            sys.exit(2)


def cmd_set(a, mem):
    check_code(a.code)
    if a.pending and a.code in SAFETY:
        print("TU CHOI: %s la cau an toan — khong duoc bo qua (D8)" % a.code, file=sys.stderr)
        return 2
    no_cred(a.answer, a.by_role)
    mem.setdefault("answers", {})[a.code] = {
        "answer": a.answer or ("Chưa có — chạy v1 trước, bổ sung sau" if a.pending else ""),
        "date": datetime.date.today().isoformat(), "by_role": a.by_role,
        "source": SOURCES[a.source], "status": "pending" if a.pending else "answered"}
    save(a.memory, mem)
    print(json.dumps(mem["answers"][a.code], ensure_ascii=False))
    return 0


def cmd_confirm(a, mem):
    ans = merged(mem, a.outputs)
    codes = [q[0] for q in QUESTIONS] if a.codes == "all" else a.codes.split(",")
    done = []
    for c in codes:
        e = ans.get(c.strip())
        if e and e.get("status") == "answered":
            e = dict(e, date=datetime.date.today().isoformat(), by_role=a.by_role or e.get("by_role", "—"))
            e.pop("from", None)
            mem.setdefault("answers", {})[c.strip()] = e
            done.append(c.strip())
    save(a.memory, mem)
    print(json.dumps({"confirmed": done}, ensure_ascii=False))
    return 0


def cmd_set_sensitive(a, mem):
    no_cred(a.classification)
    mem.setdefault("sensitive", []).append({"classification": a.classification, "files": a.files,
                                            "date": datetime.date.today().isoformat(), "by_role": a.by_role,
                                            "source": SOURCES["user"]})
    save(a.memory, mem)
    print(json.dumps(mem["sensitive"][-1], ensure_ascii=False))
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("missing", "list", "get", "set", "confirm", "set-sensitive"):
        p = sub.add_parser(name)
        p.add_argument("--outputs", default="outputs")
        p.add_argument("--memory", default=None)
        if name in ("get", "set"):
            p.add_argument("--code", required=True)
        if name == "set":
            p.add_argument("--answer", default="")
            p.add_argument("--by-role", required=True)
            p.add_argument("--source", choices=sorted(SOURCES), default="user")
            p.add_argument("--pending", action="store_true", help="nguoi dung chon 'Chưa có — chạy v1 trước'")
        if name == "missing":
            p.add_argument("--sensitive-files", nargs="*", default=[])
        if name == "confirm":
            p.add_argument("--codes", required=True)
            p.add_argument("--by-role", default=None)
        if name == "set-sensitive":
            p.add_argument("--classification", required=True)
            p.add_argument("--files", nargs="+", required=True)
            p.add_argument("--by-role", required=True)
    a = ap.parse_args()
    a.memory = a.memory or default_memory(a.outputs)
    mem = load(a.memory)
    return {"missing": cmd_missing, "list": cmd_list, "get": cmd_get, "set": cmd_set, "confirm": cmd_confirm,
            "set-sensitive": cmd_set_sensitive}[a.cmd](a, mem)


if __name__ == "__main__":
    sys.exit(main())
