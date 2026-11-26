#!/usr/bin/env python3
"""
Kiểm máy cho bộ test case (`[module]-testcases-vN.md`), dùng trước bước review của AI
(và có thể dùng trong Self-check của /gen-tcs). Tiêu chí: `.claude/skills/rbt_manual_testing/review_criteria.md`.

Lệnh:
  python3 -I review_checks.py <testcases.md> [--spec spec.md] [--analysis analysis.md]
                              [--gen-rules] [--json out.json] [--md out.md]

- Không có --md: in bảng markdown ra stdout.
- --analysis có thì chạy theo bản Full (AC lấy từ bảng Acceptance Criteria);
  không có thì bản Quick (AC lấy từ spec theo mẫu `F<n>` + `- AC<n>:`; TC trace `REQ-0n (ACm)`).
- --gen-rules: thêm các quy ước riêng của gen (L1, L2, L3). Mặc định tắt khi review.

Kết quả chia hai loại:
  chắc chắn : máy kết luận được, AI không cần kiểm lại.
  ứng viên  : máy lọc ra, AI (hoặc người) xác nhận từng dòng.
Exit code luôn 0 nếu đọc được file; 2 nếu lỗi input.
"""
import argparse
import difflib
import json
import re
import sys
from pathlib import Path

TC_HEADER = ["ID", "Function Name", "Category", "Traceability ID", "Test Scenario",
             "Precondition", "Steps", "Expected Results", "Test Data"]
REQUIRED = ["Function Name", "Category", "Traceability ID", "Test Scenario", "Steps", "Expected Results"]
CATEGORIES = {"UI", "Validate", "Behavior", "Logic", "Happy Path", "Negative", "Security",
              "Pass-through", "Transformation", "Invalid-boundary", "Consistency"}
NEG_CATEGORIES = {"Negative", "Security", "Invalid-boundary"}

TAG_RE = re.compile(r"\[(ASSUMED|UNCONFIRMED)\]")
NEG_RE = re.compile(
    r"báo lỗi|thông báo lỗi|hiện lỗi|\blỗi\b|từ chối|bị chặn|\bchặn\b|không (được|thể|cho phép|lưu|mở|hiện|tạo|cộng|"
    r"thực hiện|bắt đầu|đổi|thay đổi|gửi|có)|disabled|vô hiệu|bị khoá|bị khóa|\b(401|403|404|409|422|500)\b|"
    r"\bvẫn (là|chỉ|giữ|không)|chỉ có (1|một)\b|không đổi|giữ nguyên|"
    r"\berror\b|reject|denied|not allowed|cannot|blocked|unchanged|only one", re.I)
PLACEHOLDER_RE = re.compile(
    r"không hợp lệ|hợp lệ|bất kỳ|tuỳ ý|tùy ý|không tồn tại|đúng định dạng|sai định dạng|thông tin đúng|"
    r"dữ liệu đúng|nhập đúng|\binvalid\b|\bvalid\b|\bany\b|\brandom\b|non-existent|does not exist", re.I)
WEAK_VAGUE = {"thành công", "bình thường", "successfully"}  # chỉ báo khi mục Expected ngắn (≤ 6 từ)
VAGUE_RE = re.compile(
    r"hiển thị đúng|thành công|bình thường|kế tiếp|trước đó|được ghi nhận|kiểm tra backend|đúng dữ liệu|"
    r"phản hồi nhanh|load nhanh|như mong đợi|chính xác|hoạt động đúng|"
    r"displayed correctly|successfully|as expected|works correctly|next screen|previous screen", re.I)
UI_POLICY_RE = re.compile(r"UI thống nhất với design|UI matches (the )?design", re.I)
TBD_RE = re.compile(r"to be (confirmed|decided)|\bTBD\b|chưa chốt|cần xác nhận", re.I)
REF_PHRASE_RE = re.compile(r"như TC|xem TC|giống TC|TC trước|TC sau|các TC sau|bước trước|kết quả bước trước|"
                           r"same as TC|see TC|previous TC", re.I)
TRACE_TOKEN_RE = re.compile(
    r"^(N/A|AC-\d+|IMP-\d+|ASM-\d+|DIF-\d+|Q-[A-Z0-9]+-\d+|[a-z]{1,2}\d+|REQ-\d+(\s*\(AC\s?\d+(\s*,\s*AC\s?\d+)*\))?)$")


# ---------------------------------------------------------------- parsing

def split_row(line):
    cells = re.split(r"(?<!\\)\|", line.strip())
    if cells and cells[0] == "":
        cells = cells[1:]
    if cells and cells[-1] == "":
        cells = cells[:-1]
    return [c.strip().replace("\\|", "|") for c in cells]


def is_sep(line):
    return bool(re.match(r"^\|\s*:?-{2,}", line.strip()))


def read_tables(lines):
    """Trả list (line_no_header, heading, label, header, rows[(line_no, cells)])."""
    tables, i, heading, label = [], 0, "", ""
    while i < len(lines):
        s = lines[i].strip()
        if s.startswith("#"):
            heading = s.lstrip("#").strip()
            label = ""
        elif s.startswith("**") and not s.startswith("|"):
            label = s.strip("*").strip()
        if s.startswith("|") and i + 1 < len(lines) and is_sep(lines[i + 1]):
            header = split_row(s)
            rows, j = [], i + 2
            while j < len(lines) and lines[j].strip().startswith("|"):
                rows.append((j + 1, split_row(lines[j])))
                j += 1
            tables.append((i + 1, heading, label, header, rows))
            i = j
            continue
        i += 1
    return tables


def items(cell):
    """Tách ô theo <br>, trả các mục đánh số `n.`."""
    parts = [p.strip() for p in re.split(r"<br\s*/?>", cell) if p.strip()]
    return [p for p in parts if re.match(r"^(\[(ASSUMED|UNCONFIRMED)\]\s*)?\d+\.", p)]


def expand_ids(text, prefix, width, bare=True):
    """SCR-003, 005, 049–054, SCR-010 đến SCR-012 -> {'SCR-003', ...}
    bare=False: chỉ nhận ID có tiền tố (dùng cho ô nội dung TC, tránh bắt nhầm số như '100 ký tự').
    Không bắt mã Q&A dạng Q-SCR-001."""
    full = r"(?<![A-Za-z0-9]-)(?<![A-Za-z0-9])%s-(\d{%d})\b" % (re.escape(prefix), width)
    if not re.search(full, text):
        return set()
    if not bare:
        return {f"{prefix}-{int(n):0{width}d}" for n in re.findall(full, text)}
    out = set()
    num = r"(?:(?<![A-Za-z0-9]-)(?<![A-Za-z0-9])%s-|(?<![\w-]))(\d{%d})\b" % (re.escape(prefix), width)
    for m in re.finditer(num + r"(?:\s*(?:–|-|—|đến|to)\s*" + num + r")?", text):
        a = int(m.group(1))
        b = int(m.group(2)) if m.group(2) else a
        for n in range(a, b + 1) if b >= a and b - a < 200 else [a]:
            out.add(f"{prefix}-{n:0{width}d}")
    return out


def parse_spec_acs(spec_text):
    """Quick: {(feature_no, ac_no): text} theo mẫu `**F1 ...**` / `### F1` và `- AC1: ...`."""
    acs, feat = {}, None
    for line in spec_text.splitlines():
        m = re.match(r"^\s*(?:#+\s*|\*\*)\s*F(\d+)\b", line)
        if m:
            feat = int(m.group(1))
            continue
        m = re.match(r"^\s*(?:[-*]\s*)+AC-?\s?(\d+)\b[^:]*:\s*(.*)", line)
        if m and feat is not None:
            acs[(feat, int(m.group(1)))] = m.group(2).strip()
    return acs


def parse_analysis_acs(text):
    """Full: {AC-xx: (content, status)} từ bảng có cột `AC ID`."""
    acs = {}
    for _, _, _, header, rows in read_tables(text.splitlines()):
        if "AC ID" not in header:
            continue
        ia = header.index("AC ID")
        ic = header.index("AC Content") if "AC Content" in header else None
        ist = header.index("Status") if "Status" in header else None
        for _, cells in rows:
            if ia < len(cells) and re.match(r"^AC-\d+$", cells[ia]):
                acs[cells[ia]] = (cells[ic] if ic is not None and ic < len(cells) else "",
                                  cells[ist] if ist is not None and ist < len(cells) else "")
    return acs


def trace_targets(trace, quick):
    """Trả tập khoá AC mà TC trace tới. Full: 'AC-01'; Quick: (feat, ac) hoặc (feat, None)."""
    out = set()
    if quick:
        for m in re.finditer(r"REQ-(\d+)(?:\s*\(([^)]*)\))?", trace):
            feat = int(m.group(1))
            acs = re.findall(r"AC\s?(\d+)", m.group(2) or "")
            if acs:
                out.update((feat, int(a)) for a in acs)
            else:
                out.add((feat, None))
    else:
        out.update(re.findall(r"AC-\d+", trace))
    return out


# ---------------------------------------------------------------- checks

class Report:
    def __init__(self):
        self.findings = []

    def add(self, code, rev, kind, tc, detail, line=None):
        self.findings.append({"check": code, "rev": rev, "kind": kind, "tc": tc,
                              "detail": detail, "line": line})


def run(tc_path, spec_path=None, analysis_path=None, gen_rules=False):
    text = Path(tc_path).read_text(encoding="utf-8")
    lines = text.splitlines()
    tables = read_tables(lines)
    rep = Report()
    info = {"file": str(tc_path), "mode": "Full" if analysis_path else "Quick"}

    # --- tách bảng TC và bảng High Risk
    tcs, tc_tables, b1, b2 = [], [], None, None
    in_hr = False
    for ln, heading, label, header, rows in tables:
        in_hr = "high risk" in heading.lower()
        is_b1 = in_hr and ("bảng 1" in label.lower() or any(h.startswith("Lý do") for h in header))
        is_b2 = in_hr and ("bảng 2" in label.lower() or any("Luồng" in h for h in header))
        if "ID" in header and "Test Scenario" in header and not in_hr:
            tc_tables.append((ln, heading, header))
            col = {h: k for k, h in enumerate(header)}
            for rl, cells in rows:
                row = {h: (cells[k] if k < len(cells) else "") for h, k in col.items()}
                row.update(_line=rl, _section=heading, _ncells=len(cells), _nheader=len(header))
                tcs.append(row)
        elif is_b1:
            b1 = (ln, header, rows)
        elif is_b2:
            b2 = (ln, header, rows)

    if not tcs:
        raise SystemExit("Không tìm thấy bảng TC (cần cột ID và Test Scenario).")

    m = re.match(r"^([A-Z][A-Z0-9]*)-(\d+)$", tcs[0]["ID"])
    prefix, width = (m.group(1), len(m.group(2))) if m else ("TC", 3)
    info.update(prefix=prefix, total_tc=len(tcs))
    ids = [t["ID"] for t in tcs]
    idset = set(ids)

    # K1 cấu trúc
    for ln, heading, header in tc_tables:
        if header not in (TC_HEADER, TC_HEADER + ["Notes"]):
            rep.add("K1", "REV-08", "chắc chắn", "-", f"Bảng ở '{heading}' có cột {header}, chuẩn là {TC_HEADER}", ln)
    seen = {}
    for t in tcs:
        if t["_ncells"] != t["_nheader"]:
            rep.add("K1", "REV-08", "chắc chắn", t["ID"], f"Dòng có {t['_ncells']} ô, header có {t['_nheader']} cột", t["_line"])
        if not re.match(r"^%s-\d{%d}$" % (re.escape(prefix), width), t["ID"]):
            rep.add("K1", "REV-08", "chắc chắn", t["ID"], f"ID không đúng mẫu {prefix}-{'n' * width}", t["_line"])
        if t["ID"] in seen:
            rep.add("K1", "REV-08", "chắc chắn", t["ID"], f"ID trùng (dòng {seen[t['ID']]})", t["_line"])
        seen.setdefault(t["ID"], t["_line"])
    nums = sorted(int(i.split("-")[1]) for i in idset if re.match(r"^%s-\d+$" % prefix, i))
    gaps = [n for n in range(nums[0], nums[-1] + 1) if n not in set(nums)] if nums else []
    if gaps:
        rep.add("K1", "REV-08", "chắc chắn", "-", "ID nhảy số, thiếu: " + ", ".join(f"{prefix}-{g:0{width}d}" for g in gaps))

    # K2 ô bắt buộc, Category
    for t in tcs:
        empty = [c for c in REQUIRED if not t.get(c, "").strip()]
        if empty:
            rep.add("K2", "REV-08", "chắc chắn", t["ID"], "Ô trống: " + ", ".join(empty), t["_line"])
        cat = t.get("Category", "").strip()
        if cat and cat not in CATEGORIES:
            rep.add("K2", "REV-08", "chắc chắn", t["ID"], f"Category '{cat}' không thuộc danh sách chuẩn", t["_line"])

    # K3 tham chiếu TC khác
    for t in tcs:
        for col in ("Precondition", "Steps", "Expected Results", "Test Data"):
            cell = t.get(col, "")
            refs = sorted(r for r in expand_ids(cell, prefix, width, bare=False) if r != t["ID"])
            phr = REF_PHRASE_RE.findall(cell)
            if refs or phr:
                what = ", ".join(refs) if refs else ""
                if phr:
                    what = (what + "; " if what else "") + "cụm: " + ", ".join(sorted(set(p if isinstance(p, str) else p[0] for p in phr)))
                rep.add("K3", "REV-06", "chắc chắn", t["ID"], f"{col} tham chiếu TC khác ({what})", t["_line"])

    # --- nguồn AC
    quick = analysis_path is None
    universe, tbd = {}, set()
    if analysis_path:
        a = parse_analysis_acs(Path(analysis_path).read_text(encoding="utf-8"))
        universe = {k: v[0] for k, v in a.items()}
        tbd = {k for k, v in a.items() if v[1].upper().startswith("TBD")}
        info["ac_source"] = f"analysis: {len(universe)} AC"
    elif spec_path:
        sp = parse_spec_acs(Path(spec_path).read_text(encoding="utf-8"))
        feats_in_tc = set()
        for t in tcs:
            feats_in_tc |= {f for f, _ in trace_targets(t.get("Traceability ID", ""), True)}
        universe = {k: v for k, v in sp.items() if k[0] in feats_in_tc}
        tbd = {k for k, v in universe.items() if TBD_RE.search(v)}
        info["ac_source"] = (f"spec: {len(universe)} AC thuộc các REQ có trong file TC (REQ-0n ↔ F n)"
                             if universe else "spec: không trích được AC theo mẫu F<n> / - AC<n>:")
    else:
        info["ac_source"] = "không có spec/analysis: bỏ qua K4 (tồn tại), K7, K8, K9"

    def key_label(k):
        return k if isinstance(k, str) else (f"REQ-{k[0]:02d} (AC{k[1]})" if k[1] else f"REQ-{k[0]:02d}")

    # K4 Traceability
    uses_ac_suffix = quick and any(re.search(r"REQ-\d+\s*\(AC", t.get("Traceability ID", "")) for t in tcs)
    for t in tcs:
        tr = t.get("Traceability ID", "").strip()
        if not tr:
            continue
        tokens = [x.strip() for x in re.split(r",(?![^()]*\))", tr) if x.strip()]
        bad = [x for x in tokens if not TRACE_TOKEN_RE.match(x)]
        if bad:
            rep.add("K4", "REV-08", "chắc chắn", t["ID"], "Traceability sai mẫu: " + "; ".join(bad), t["_line"])
        if uses_ac_suffix:
            bare = [x for x in tokens if re.match(r"^REQ-\d+$", x)]
            if bare and t.get("Category", "").strip() != "UI":
                rep.add("K4", "REV-08", "chắc chắn", t["ID"], "REQ không ghi AC: " + ", ".join(bare), t["_line"])
        if universe:
            miss = [key_label(k) for k in trace_targets(tr, quick)
                    if k not in universe and not (quick and k[1] is None)]
            if miss:
                rep.add("K4", "REV-01.1", "chắc chắn", t["ID"], "Trace tới AC không có trong nguồn: " + ", ".join(miss), t["_line"])

    # map AC -> TC
    by_ac = {}
    for t in tcs:
        for k in trace_targets(t.get("Traceability ID", ""), quick):
            by_ac.setdefault(k, []).append(t)

    # K7 AC chưa có TC
    if universe:
        for k in sorted(universe, key=lambda x: (str(type(x)), x)):
            if k not in by_ac:
                rep.add("K7", "REV-01.1", "ứng viên", "-", f"{key_label(k)} chưa có TC trace: \"{universe[k][:90]}\"")

    # K8 AC có TC nhưng không có negative
    def is_negative(t):
        return t.get("Category", "").strip() in NEG_CATEGORIES or bool(NEG_RE.search(t.get("Expected Results", "")))
    for k, lst in sorted(by_ac.items(), key=lambda x: (str(type(x[0])), str(x[0]))):
        if quick and isinstance(k, tuple) and k[1] is None:
            continue
        if not any(is_negative(t) for t in lst):
            rep.add("K8", "REV-01.4", "ứng viên", ", ".join(t["ID"] for t in lst),
                    f"{key_label(k)} có {len(lst)} TC nhưng không TC nào có dấu hiệu negative")

    # K9 TC dựa AC còn TBD mà không gắn tag
    for k in sorted(tbd, key=str):
        for t in by_ac.get(k, []):
            if not TAG_RE.search(t.get("Expected Results", "") + t.get("Test Scenario", "")):
                rep.add("K9", "REV-02.1", "ứng viên", t["ID"],
                        f"{key_label(k)} còn chưa chốt trong nguồn nhưng TC không gắn [ASSUMED]/[UNCONFIRMED]", t["_line"])

    # K10 placeholder
    for t in tcs:
        for col in ("Test Data", "Steps"):
            hits = set()
            for part in re.split(r"<br\s*/?>", t.get(col, "")):
                part = re.sub(r"^\s*\d+\.\s*", "", part)
                if ":" in part:
                    target = part.split(":", 1)[1]          # chỉ xét phần giá trị sau dấu ':'
                elif len(part.split()) <= 8:
                    target = part                           # dòng ngắn không có giá trị cụ thể
                else:
                    target = ""
                hits |= {m.group(0).lower() for m in PLACEHOLDER_RE.finditer(target)}
            hits = sorted(hits)
            if hits:
                rep.add("K10", "REV-05.1", "ứng viên", t["ID"], f"{col} có cụm: {', '.join(hits)}", t["_line"])

    # K11 Expected mơ hồ (+ "Kiểm tra backend" trong Steps)
    ui_policy = 0
    for t in tcs:
        exp = t.get("Expected Results", "")
        if UI_POLICY_RE.search(exp):
            ui_policy += 1
        hits = set()
        for p in re.split(r"<br\s*/?>", exp):
            for m in VAGUE_RE.finditer(p):
                w = m.group(0).lower()
                if w == "hiển thị đúng" and "test data" in p.lower():
                    continue
                if w in WEAK_VAGUE and len(re.sub(r"^\s*(\[\w+\]\s*)?\d+\.\s*", "", p).split()) > 6:
                    continue
                hits.add(w)
        if hits:
            rep.add("K11", "REV-03.2", "ứng viên", t["ID"], "Expected có cụm: " + ", ".join(sorted(hits)), t["_line"])
        if re.search(r"kiểm tra backend|check (the )?backend", t.get("Steps", ""), re.I):
            rep.add("K11", "REV-03.1", "ứng viên", t["ID"], "Steps có 'Kiểm tra backend' mà không nói kiểm gì", t["_line"])
    info["ui_policy_expected"] = ui_policy

    # K12 Steps và Expected lệch số bước
    for t in tcs:
        nst = len(items(t.get("Steps", "")))
        refs = [int(n) for n in re.findall(r"(?:Bước|Step)\s+(\d+)", t.get("Expected Results", ""), re.I)]
        over = [n for n in refs if nst and n > nst]
        if over:
            rep.add("K12", "REV-03.1", "chắc chắn", t["ID"], f"Expected nhắc Bước {over} nhưng Steps chỉ có {nst} bước", t["_line"])

    # K13 Precondition trống (trừ TC UI)
    empty_pre = [t["ID"] for t in tcs if not t.get("Precondition", "").strip() and t.get("Category", "").strip() != "UI"]
    if empty_pre:
        rep.add("K13", "REV-05.2", "ứng viên", ", ".join(empty_pre),
                f"{len(empty_pre)} TC (không phải UI) để trống Precondition: AI xem TC nào thực sự cần trạng thái")

    # K14 Function Name nhiều kiểu
    groups = {}
    for t in tcs:
        if t.get("Category", "").strip() == "UI":
            continue  # TC UI tổng thể dùng "Màn hình [tên Screen]" theo quy ước của skill
        fn = t.get("Function Name", "").strip()
        k = re.sub(r"màn hình|screen|màn|\s|[-–_]", "", fn.lower())
        if k:
            groups.setdefault(k, {}).setdefault(fn, []).append(t["ID"])
    for k, variants in groups.items():
        if len(variants) > 1:
            rep.add("K14", "REV-08", "ứng viên", "-",
                    "Cùng tên viết nhiều kiểu: " + "; ".join(f"'{v}' ({', '.join(i[:3])}{'…' if len(i) > 3 else ''})" for v, i in variants.items()))

    # K6 vị trí tag
    styles = {"đầu ô": [], "trong mục": []}
    for t in tcs:
        exp = t.get("Expected Results", "")
        if re.match(r"^\s*\[(ASSUMED|UNCONFIRMED)\]\s*1\.", exp):
            styles["đầu ô"].append(t["ID"])
        elif re.search(r"(^|<br>)\s*\d+\.\s*\[(ASSUMED|UNCONFIRMED)\]", exp):
            styles["trong mục"].append(t["ID"])
        ts = t.get("Test Scenario", "")
        if TAG_RE.search(ts) and not re.match(r"^\s*\[(ASSUMED|UNCONFIRMED)\]\s*Check", ts):
            rep.add("K6", "REV-08", "chắc chắn", t["ID"], "Tag trong Test Scenario không đứng ngay trước 'Check'", t["_line"])
    if styles["đầu ô"] and styles["trong mục"]:
        minor = min(styles, key=lambda s: len(styles[s]))
        rep.add("K6", "REV-08", "chắc chắn", ", ".join(styles[minor]),
                f"Tag đặt '{minor}' ({len(styles[minor])} TC), khác số đông đặt "
                f"'{'trong mục' if minor == 'đầu ô' else 'đầu ô'}' ({len(styles['trong mục' if minor == 'đầu ô' else 'đầu ô'])} TC)")

    # K15 TC gần trùng
    sig = [(t, re.sub(r"\s+", " ", (t.get("Steps", "") + "|" + t.get("Test Data", "") + "|" + t.get("Expected Results", "")).lower()))
           for t in tcs if t.get("Category", "").strip() != "UI"]  # TC UI tổng thể vốn giống nhau
    for a in range(len(sig)):
        for b in range(a + 1, len(sig)):
            ta, sa = sig[a]
            tb, sb = sig[b]
            if abs(len(sa) - len(sb)) > 0.3 * max(len(sa), len(sb), 1):
                continue
            r = difflib.SequenceMatcher(None, sa, sb).ratio()
            if r >= 0.9:
                rep.add("K15", "REV-04.2", "ứng viên", f"{ta['ID']}, {tb['ID']}",
                        f"Steps + Test Data + Expected giống nhau {int(r * 100)}%")

    # K5 Bảng 1 / Bảng 2
    if b1 is None and b2 is None:
        rep.add("K5", "REV-07", "chắc chắn", "-", "Không tìm thấy Bảng 1 và Bảng 2 trong mục High Risk & E2E")
    if b1:
        ln, header, rows = b1
        ic = header.index("TC") if "TC" in header else (header.index("ID") if "ID" in header else None)
        all_b1, where = [], {}
        for rl, cells in rows:
            got = expand_ids(cells[ic] if ic is not None and ic < len(cells) else "", prefix, width)
            for i in got:
                if i in where:
                    rep.add("K5", "REV-07", "chắc chắn", i, f"Bảng 1: TC xuất hiện ở cả dòng {where[i]} và dòng {rl}", rl)
                where.setdefault(i, rl)
            all_b1 += list(got)
            for i in sorted(got - idset):
                rep.add("K5", "REV-07", "chắc chắn", i, "Bảng 1: ID không có trong bảng TC", rl)
        ratio = len(set(all_b1)) / len(tcs)
        info["bang1"] = f"{len(set(all_b1))} TC ({ratio:.0%} tổng)"
        if ratio > 0.32:
            rep.add("K5", "REV-07", "chắc chắn", "-", f"Bảng 1 chiếm {ratio:.0%} tổng TC, vượt khoảng 30% (chỉ cảnh báo)")
    if b2:
        ln, header, rows = b2
        ic = next((k for k, h in enumerate(header) if h.startswith("TC")), None)
        ifail = next((k for k, h in enumerate(header) if "fail" in h.lower()), None)
        # Hai kiểu: mỗi luồng một dòng, hoặc mỗi bước một dòng (có cột 'Bước', ô luồng chỉ ghi ở dòng đầu)
        per_step = any(h.strip() == "Bước" for h in header)
        nflow = sum(1 for _, c in rows if c and c[0].strip()) if per_step else len(rows)
        info["bang2"] = f"{nflow} luồng"
        if not 3 <= nflow <= 6:
            rep.add("K5", "REV-07", "chắc chắn", "-", f"Bảng 2 có {nflow} luồng, quy ước 3–6")
        if ifail is None:
            rep.add("K5", "REV-07", "chắc chắn", "-", "Bảng 2 không có cột 'Nếu fail thì'")
        for n, (rl, cells) in enumerate(rows, 1):
            cell = cells[ic] if ic is not None and ic < len(cells) else ""
            for i in sorted(expand_ids(cell, prefix, width) - idset):
                rep.add("K5", "REV-07", "chắc chắn", i, f"Bảng 2 luồng {n}: ID không có trong bảng TC", rl)
            if "thiếu TC" in cell:
                rep.add("K5", "REV-07", "ứng viên", "-", f"Bảng 2 luồng {n} có bước ghi 'thiếu TC'", rl)
            if ifail is not None and (ifail >= len(cells) or not cells[ifail].strip()):
                rep.add("K5", "REV-07", "chắc chắn", "-", f"Bảng 2 luồng {n}: cột 'Nếu fail thì' trống", rl)

    # quy ước riêng của gen
    if gen_rules:
        for t in tcs:
            ts = t.get("Test Scenario", "")
            if re.search(r"→|->", ts):
                rep.add("L1", "REV-08", "chắc chắn", t["ID"], "Test Scenario có ký hiệu rút gọn → / ->", t["_line"])
            if not re.match(r"^\s*(\[(ASSUMED|UNCONFIRMED)\]\s*)?Check\b", ts):
                rep.add("L1", "REV-08", "chắc chắn", t["ID"], "Test Scenario không bắt đầu bằng 'Check'", t["_line"])
            for part in re.split(r"<br\s*/?>", t.get("Test Data", "")):
                if ";" in part:
                    rep.add("L2", "REV-08", "chắc chắn", t["ID"], f"Test Data nối nhiều field bằng ';': {part[:60]}", t["_line"])
                    break
            pre, td = t.get("Precondition", ""), t.get("Test Data", "")
            if re.search(r"đăng nhập", pre, re.I) or "@" in pre:
                rep.add("L3", "REV-08", "chắc chắn", t["ID"], "Precondition có 'đăng nhập' hoặc email", t["_line"])
            if "@" in td or td.strip() == "—":
                rep.add("L3", "REV-08", "chắc chắn", t["ID"], "Test Data có email hoặc chỉ ghi '—'", t["_line"])

    return info, rep.findings


# ---------------------------------------------------------------- output

CHECK_NAMES = {
    "K1": "Cấu trúc bảng và ID", "K2": "Ô bắt buộc, Category", "K3": "Tham chiếu TC khác",
    "K4": "Traceability", "K5": "Bảng High Risk & E2E", "K6": "Vị trí tag",
    "K7": "AC chưa có TC", "K8": "AC thiếu negative", "K9": "AC chưa chốt mà TC không gắn tag",
    "K10": "Placeholder", "K11": "Expected/Steps mơ hồ", "K12": "Expected nhắc bước không có",
    "K13": "Precondition trống", "K14": "Function Name nhiều kiểu", "K15": "TC gần trùng",
    "L1": "Gen: Test Scenario", "L2": "Gen: Test Data một field một dòng", "L3": "Gen: Precondition/Test Data",
}


def to_md(info, findings):
    out = [f"# Kiểm máy: {Path(info['file']).name}", "",
           f"- Chế độ: {info['mode']} · Tổng TC: {info['total_tc']} · Nguồn AC: {info.get('ac_source', '-')}"]
    if "bang1" in info or "bang2" in info:
        out.append(f"- Bảng 1: {info.get('bang1', 'không có')} · Bảng 2: {info.get('bang2', 'không có')}")
    out.append(f"- Expected theo UI Policy (\"UI thống nhất với design\"), không tính mơ hồ: {info.get('ui_policy_expected', 0)} TC")
    out += ["", "| Kiểm | Tên | Loại | Số dòng |", "|---|---|---|---|"]
    order = list(CHECK_NAMES)
    for code in order:
        f = [x for x in findings if x["check"] == code]
        if f:
            out.append(f"| {code} | {CHECK_NAMES[code]} | {f[0]['kind']} | {len(f)} |")
    for code in order:
        f = [x for x in findings if x["check"] == code]
        if not f:
            continue
        out += ["", f"## {code} — {CHECK_NAMES[code]} ({f[0]['kind']}, {f[0]['rev']})", "",
                "| TC | Chi tiết |", "|---|---|"]
        for x in f:
            out.append(f"| {x['tc']} | {x['detail'].replace('|', '/')} |")
    if not findings:
        out += ["", "Không có dòng nào."]
    return "\n".join(out) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("testcases")
    ap.add_argument("--spec")
    ap.add_argument("--analysis")
    ap.add_argument("--gen-rules", action="store_true")
    ap.add_argument("--json")
    ap.add_argument("--md")
    a = ap.parse_args()
    for p in (a.testcases, a.spec, a.analysis):
        if p and not Path(p).is_file():
            print(f"Không thấy file: {p}", file=sys.stderr)
            sys.exit(2)
    info, findings = run(a.testcases, a.spec, a.analysis, a.gen_rules)
    if a.json:
        Path(a.json).write_text(json.dumps({"info": info, "findings": findings}, ensure_ascii=False, indent=1), encoding="utf-8")
    md = to_md(info, findings)
    if a.md:
        Path(a.md).write_text(md, encoding="utf-8")
    else:
        sys.stdout.write(md)


if __name__ == "__main__":
    main()
