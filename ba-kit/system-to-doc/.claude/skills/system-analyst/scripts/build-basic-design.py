#!/usr/bin/env python3
"""Dung O5 Basic Design (1 workbook / website) tu inventory + recon, theo template cong ty.

  python3 build-basic-design.py --inventory $I/inventory.xlsx --site WEB-01 --version ver1 \
      --fe-api-calls $I/recon/code/REPO-01/fe-api-calls.csv [--fe-api-calls ...] \
      [--crawl $I/recon/crawl/WEB-01] [--spec $I/bd/WEB-01.json] --q-start <next_q> \
      # Giai đoạn 1 (chi doc code): bo --crawl · Giai đoạn 2 (Playwright da chay): them --crawl
      --out $V/05_Basic_Design/BasicDesign_WEB-01_ver1.xlsx --before $I/bd_before_WEB-01.xlsx \
      [--template templates/sample_basic_design.xlsx] [--questions-out $I/bd/questions-WEB-01.csv] \
      [--repo REPO-01=inputs/repo/web]     # mac dinh lay Path o 11_Repo; can de tra nhan nut -> handler trong code

Nguon theo thu tu (R3 · D2): CODE truoc — fe-api-calls.csv (man -> trigger / nut -> API), --spec do agent
viet sau khi doc handler / validation / i18n (item, P/Q, code-ref, error message) — roi WEBSITE: pages.json
(item that, trang thai ban dau), network.json / console.json (4xx/5xx, JS error; bo qua noise cua cong cu).
  - Cot S "API gọi" (D2): "POST /api/orders (API-015)"; dong "Mở màn" -> "Mở màn → GET ... (API-012)";
    link -> "Không gọi API — chuyển trang"; khong co bang chung -> "Cần xác nhận — Q-xxx".
  - Nut tren web khong khop nhan voi fe-api-calls.csv -> tra tiep: nhan gan dung -> CODE cua man
    (fe-screen-files.json canh fe-api-calls.csv, do scan-repo.py ghi): aria-label / chu hien thi / icon <XxxIcon>
    -> handler gan do -> Trigger / Trigger Ref trong fe-api-calls (goi API) hoac than ham (chuyen trang / mo
    hop thoai / doi trang thai); date picker, o chon, phan trang co luat rieng. Moi mo ta deu kem code-ref.
    Chi doc file co trong fe-screen-files.json (scan-repo da loc file nhay cam).
  - Nhan tu web duoc chuan hoa (D1, privacy): bo "selected date is ...", ngay / gio / so cu the -> （日付）（時刻）
    （数値）; nhieu item cung nhan sau chuan hoa (o ngay lich, so trang) gop 1 dong.
  - "Screenshot EV" nhieu EV ("EV-1; EV-2") -> ghep tung EV voi pages.json, lay trang dau tien khop.
  - Nut co trong code nhung khong thay tren web (READ-ONLY / thieu quyen) -> dong item tu handler, code-ref o cot R.
  - ERROR SCENARIOS = loi tu code (spec.errors) + loi thay khi quet web; moi dong co nguon o cot S.
  - Khong lap noi dung khong co bang chung (D1): cho nao khong biet -> "Cần xác nhận — Q-xxx" + 1 dong
    Open Question trong --questions-out (cot 06_OpenQuestions, dan vao inventory). Khong freeze panel (R13).
  - Ten sheet = "title" cua man (spec) hoac Screen Name o 02_Screen da bo ma / route; Screen ID o F1 + Screen Index
    (co hyperlink). Ten / mo ta item KHONG chua API / METHOD /api/... / ten ham — chi o cot R (code-ref), S (API gọi).
  - Item nhap lieu (textbox, select, date ...) khong bao gio trong required / maxlength: spec -> "field" tra
    08_API_Fields (Required, Format / Constraint) + 04_DB_Columns (Max Length) -> ghi kem nguon o cot R;
    select / radio / checkbox / date -> maxlength "ー"; con lai -> "Cần xác nhận — Q-xxx".
  - Anh: spec "image" (anh da danh so) hoac Giai đoạn 2: item co "mark": [x, y] (0..1) + crawl/evidence/<EV>.png ->
    tu danh so theo cot # (annotate-ui-image.py). Khong anh: Giai đoạn 1 ghi "Chưa có ảnh — bổ sung ở Giai đoạn 2 (Playwright)".
spec (tuy chon, moi key deu tuy chon):
  {"screens": {"SC-001": {"title": "予約編集", "purpose": "...", "access": "...", "logic": "...",
     "image": "annotated/SC-001.png",
     "items": [{"name_jp", "name_vn", "type", "status", "required", "maxlength", "default", "p", "q", "r",
                "label", "field", "next", "api", "mark"}],
        # co items -> dung thay item cua crawl; "label" = nhan nut de khop code; "field" = ten field form trong
        # code; "next" = SC-xxx / route man dich -> "Bấm → chuyển sang màn 「...」"; "mark" = [x, y] badge tren anh
     "errors": [{"item", "category", "display", "code", "msg_jp", "msg_vn", "action_jp", "action_vn",
                 "next", "source"}]}}}      # source = code-ref / EV (bat buoc); code bo trong -> tu dat
                                            # o loi thieu -> "Cần xác nhận — Q-xxx" (khong de trong)
stdout: JSON {screens, phase, sheets, items, api_cells, code_matched, field_filled, images, confirm_cells, errors,
        next_q, out, questions}
Exit: 0 OK · 1 sai tham so / thieu file · 2 thieu openpyxl
"""
import argparse
import csv
import json
import os
import re
import shutil
import sys
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import inv_schema as S  # noqa: E402
try:
    import openpyxl
    from openpyxl.worksheet.hyperlink import Hyperlink
    import bd_styles as ST
except ImportError:
    print("Thieu openpyxl. Chay: pip install openpyxl", file=sys.stderr)
    sys.exit(2)

KIT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
TEMPLATE = os.path.join(KIT, "templates", "sample_basic_design.xlsx")
NA = "ー"
HDR, FIRST = 8, 9                 # Sample: header bang item row 8, data tu row 9 (workbook-structure.md §2.4)
COLS = range(8, 20)               # H..S
CAT_SYS = "🔵 System"
TYPE_MAP = {"checkbox": "Checkbox", "radio": "Radio", "select": "Dropdown", "textarea": "Textarea",
            "submit": "Button", "button": "Button", "reset": "Button", "image": "Button", "a": "Hyperlink",
            "date": "Date", "datetime-local": "Date", "time": "Date", "number": "Number", "email": "Email",
            "password": "Password", "tel": "Textbox", "search": "Textbox"}
CLICK = ("Button", "Hyperlink", "Link", "Form", "Submit")
CLICK_L = {c.lower() for c in CLICK}
# item nhap lieu: required / maxlength khong bao gio trong (dung chung voi verify-basic-design.py check 22)
INPUT_TYPES = {"textbox", "text", "input", "textarea", "select", "dropdown", "combobox", "radio", "checkbox",
               "date", "datepicker", "time", "number", "password", "email"}
NO_MAXLEN = {"select", "dropdown", "combobox", "radio", "checkbox", "date", "datepicker", "time"}
ERR_FIELD = {"item": "vị trí lỗi", "category": "nhóm lỗi", "display": "cách hiển thị", "msg_jp": "message (JP)",
             "msg_vn": "message (VN)", "action_jp": "thao tác người dùng (JP)", "action_vn": "thao tác người dùng (VN)",
             "next": "xử lý tiếp theo", "source": "nguồn"}
PHASE1_IMG = "Chưa có ảnh — bổ sung ở Giai đoạn 2 (Playwright)"
PHASE2_IMG = "Chưa có ảnh — Playwright chưa chụp / chưa đánh số màn này"
SYSTEM_SHEETS = {"common mesage", "screen error message", "screen index", "change history", "sample"}
# ma trong ten / mo ta: "GET /api/..", tu "API", ten ham camelCase (fetchData, onUpdateConfirmed)
CODE_RX = re.compile(r"\b(?:GET|POST|PUT|PATCH|DELETE)\s+/|\bAPI\b|\b[a-z]+[A-Z][A-Za-z0-9]*\b|=>|\w+\(\)")
VERB = {"GET": ("データを取得して表示する", "tải và hiển thị dữ liệu"),
        "POST": ("データを登録・送信する", "gửi / đăng ký dữ liệu"),
        "PUT": ("データを更新する", "cập nhật dữ liệu"), "PATCH": ("データを更新する", "cập nhật dữ liệu"),
        "DELETE": ("データを削除する", "xóa dữ liệu")}


def act(es):
    """Hanh vi theo nghiep vu tu METHOD (khong ghi path / ten ham vao mo ta) -> (jp, vn)."""
    vs = []
    for e in es:
        v = VERB.get((e.get("Method") or "").upper(), ("処理を実行する", "xử lý dữ liệu"))
        if v not in vs:
            vs.append(v)
    return "・".join(v[0] for v in vs), ", ".join(v[1] for v in vs)


def looks_code(s):
    return bool(CODE_RX.search(s or ""))


def clean_title(s):
    """Screen Name o 02_Screen -> ten doc duoc: bo SC-xxx, route /..., ngoac rong."""
    s = re.sub(r"\bSC-\d+\b|(?<![\w])/[\w\-/:\[\].{}]*", " ", s or "")
    s = re.sub(r"[(（\[]\s*[)）\]]", " ", s)
    return re.sub(r"\s+", " ", s).strip(" -–—:|・,、")


def sheet_titles(screens, spec, q):
    """-> {sid: ten sheet}: Excel-safe (bo []:*?/\\), <= 31 ky tu, khong trung (them " (2)")."""
    out, used = {}, set(SYSTEM_SHEETS)
    for sc in screens:
        sid = sc["Screen ID"]
        t = (spec.get(sid) or {}).get("title") or clean_title(sc.get("Screen Name"))
        t = re.sub(r"[\[\]:*?/\\]", " ", t or "")
        t = re.sub(r"\s+", " ", t).strip(" '")[:31].strip()
        if not t:
            # gate check 24 se FAIL -> agent phai them "title" vao spec
            q.ask("%s — tên màn hiển thị cho khách hàng" % sid, "02_Screen không có tên màn đọc được, spec chưa có title")
            t = sid
        base, k = t, 2
        while t.lower() in used:
            suf = " (%d)" % k
            t = base[:31 - len(suf)].rstrip() + suf
            k += 1
        used.add(t.lower())
        out[sid] = t
    return out


def norm_yes(v):
    v = str(v or "").strip()
    if re.match(r"(?i)^(y|yes|true|required|必須|✓|○|1)$", v):
        return "Yes"
    if re.match(r"(?i)^(n|no|false|optional|任意|0)$", v):
        return "No"
    return ""


def maxlen_of(*texts):
    for t in texts:
        t = str(t or "")
        m = (re.search(r"(?i)max(?:imum)?[\s_-]*(?:length|len)?\s*[:=(<]?\s*=?\s*(\d+)", t)
             or re.search(r"(?i)(?:var)?char\s*\(\s*(\d+)\s*\)", t)
             or re.search(r"(\d+)\s*(?:文字|chars?|characters|ký tự)", t)
             or (re.match(r"^\s*(\d+)\s*$", t)))
        if m:
            return m.group(1)
    return ""


class Fields:
    """Tra required / maxlength theo ten field form: 08_API_Fields (request) + 04_DB_Columns."""
    def __init__(self, inv):
        self.api, self.db = {}, {}
        for r in inv.get("08_API_Fields", []):
            if re.match(r"(?i)^res", r.get("Direction") or ""):
                continue
            self.api.setdefault(self.key(r.get("Field")), []).append(r)
        for r in inv.get("04_DB_Columns", []):
            self.db.setdefault(self.key(r.get("Column")), []).append(r)

    @staticmethod
    def key(f):
        f = str(f or "").split(".")[-1].split("[")[0]
        return re.sub(r"[_\-\s]", "", f).lower()   # userName = user_name = user-name

    def get(self, field):
        """-> (required, maxlength, nguon) — "" khi khong co."""
        k = self.key(field)
        req, mx, src = "", "", []
        for r in self.api.get(k, []):
            rq, ml = norm_yes(r.get("Required")), maxlen_of(r.get("Format / Constraint"), r.get("Type"))
            if rq or ml:
                req, mx = req or rq, mx or ml
                src.append("08_API_Fields %s.%s%s" % (r.get("API ID") or "", r.get("Field"),
                                                       (" · " + r["Evidence"]) if r.get("Evidence") else ""))
        if not mx:
            for r in self.db.get(k, []):
                ml = maxlen_of(r.get("Max Length"), r.get("Type"))
                if ml:
                    mx = ml
                    src.append("04_DB_Columns %s.%s%s" % (r.get("Table") or "", r.get("Column"),
                                                         (" · " + r["Evidence"]) if r.get("Evidence") else ""))
                    break
        return req, mx, "; ".join(src)


def norm_route(r):
    r = re.sub(r"^https?://[^/]+", "", (r or "").strip()).split("?")[0].rstrip("/") or "/"
    return re.sub(r"\[\.{0,3}[^\]]+\]|\{[^}]+\}|:[A-Za-z_]\w*", ":p", r)


def read_json(path, default):
    try:
        return json.load(open(path, encoding="utf8"))
    except (OSError, ValueError):
        return default


def call_text(e):
    aid = e["API ID"] if re.match(r"^API-\d+", e.get("API ID", "")) else ""
    return "%s %s" % (e["Method"], e["Path"]) + (" (%s)" % aid if aid else "")


class Q:
    """Cap Q-xxx cho o 'Cần xác nhận' + dong Open Question tuong ung."""
    def __init__(self, start, site):
        self.n, self.site, self.rows = start, site, []

    def ask(self, item, reason):
        qid = "Q-%03d" % self.n
        self.n += 1
        self.rows.append([qid, S.QUESTION_TYPE[0], item, reason, "Đọc handler trong code hoặc hỏi khách hàng",
                          "BrSE", "Open", "O5 Basic Design %s" % self.site])
        return qid


def ev_ids(s):
    return re.findall(r"EV-\d+", s or "")


def page_of(pages, ev_cell):
    """O "Screenshot EV" co the ghi nhieu EV ("EV-0001; EV-0002") -> trang dau tien khop."""
    by = {p.get("evId"): p for p in pages if p.get("evId")}
    return next((by[e] for e in ev_ids(ev_cell) if e in by), None)


DYN = [(re.compile(r"(?i)\s*[,、]?\s*selected (?:date|time|value)s? (?:is|are)\b.*$"), ""),
       (re.compile(r"(?<!\d)\d{4}[/.\-年]\d{1,2}[/.\-月]\d{1,2}日?(?:\s*[(（]?[月火水木金土日][)）]?)?(?!\d)"), "（日付）"),
       (re.compile(r"(?i)\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+\d{1,2}(?:st|nd|rd|th)?,?"
                   r"(?:\s+\d{4})?\b"), "（日付）"),
       (re.compile(r"(?<!\d)\d{1,2}月\d{1,2}日(?:\s*[(（]?[月火水木金土日][)）]?)?"), "（日付）"),
       (re.compile(r"(?<!\d)\d{1,2}/\d{1,2}(?!\d)"), "（日付）"),
       (re.compile(r"(?<!\d)\d{1,2}:\d{2}(?::\d{2})?(?!\d)"), "（時刻）"),
       (re.compile(r"(?<![A-Za-z\d])\d+(?:[.,]\d+)*(?![A-Za-z\d])"), "（数値）")]


def norm_label(label):
    """Nhan tu web khong bao gio mang gia tri dong: ngay da chon, ngay / gio / so cu the."""
    s = re.sub(r"\s+", " ", label or "").strip()
    for rx, sub in DYN:
        s = rx.sub(sub, s)
    return s.strip(" ,、")


def web_items(page, ev):
    out, seen = [], {}
    for it in (page or {}).get("items") or []:
        kind = TYPE_MAP.get(it.get("type") or "", TYPE_MAP.get(it.get("tag") or "", "Textbox"))
        if it.get("tag") == "a":
            kind = "Hyperlink"
        label = norm_label(it.get("label") or it.get("name") or it.get("id") or "")
        if not label:
            continue
        if (label, kind) in seen:      # o ngay lich / so trang sau chuan hoa -> 1 dong
            seen[(label, kind)]["_n"] += 1
            continue
        st = "Disable" if it.get("disabled") else "Enable"
        out.append({"name_jp": label, "name_vn": label, "type": kind, "status": st,
                    # web khong co attr required / maxlength != khong bat buoc (co the validate bang JS) -> de ""
                    "required": "Yes" if it.get("required") else "",
                    "maxlength": str(it["maxlength"]) if it.get("maxlength") else "",
                    # chi biet CO / KHONG co gia tri ban dau — khong bao gio ghi gia tri (privacy)
                    "default": "値あり（値は記録しない）" if it.get("hasValue") else NA,
                    "p": "・%s\n・初期表示：%s" % (label, "有効" if st == "Enable" else "無効"),
                    "q": "・%s\n・Trạng thái ban đầu: %s" % (label, st),
                    "r": ev, "label": label, "_web": True, "_n": 1})
        seen[(label, kind)] = out[-1]
    for x in out:
        n = x.pop("_n")
        if n > 1:
            x["p"] += "\n・同種の項目 %d 件（値は記録しない）" % n
            x["q"] += "\n・Cùng loại: %d item (không ghi giá trị)" % n
    return out


def loose(s):
    s = unicodedata.normalize("NFKC", s or "").lower()
    return re.sub(r"[\s\W_]+", "", s)


def loose_hit(clicks, labels):
    """Nhan gan dung: bo khoang trang / dau / full-width; trung hoac chua nhau (>= 2 ky tu)."""
    want = [loose(x) for x in labels if len(loose(x)) >= 2]
    out = []
    for e in clicks:
        k = loose(e["UI Label"])
        if len(k) >= 2 and any(k == w or k in w or w in k for w in want):
            out.append(e)
    return out


class Code:
    """Tra nhan nut tren web -> handler trong code cua man (thay cho spec viet tay). Chi doc file trong
    fe-screen-files.json (scan-repo.py da loc file nhay cam)."""
    JSX_HANDLER = re.compile(r"on(?:Click|Change|PageChange|Submit)\s*=\s*\{\s*(?:async\s*)?"
                             r"(?:(?:\([^)]*\)|[A-Za-z_$][\w$]*)\s*=>\s*)?\{?\s*([A-Za-z_$][\w$.]*)")

    def __init__(self, roots, screen_files):
        self.roots, self.sf, self.txt = roots, screen_files, {}

    def files(self, route):
        return self.sf.get(norm_route(route), [])

    def text(self, f):
        if f not in self.txt:
            rid, rel = f
            root = self.roots.get(rid)
            full = os.path.realpath(os.path.join(root, rel)) if root else ""
            ok = root and full.startswith(os.path.realpath(root) + os.sep)
            try:
                self.txt[f] = open(full, encoding="utf8", errors="ignore").read().split("\n") if ok else []
            except OSError:
                self.txt[f] = []
        return self.txt[f]

    def find(self, files, rx):
        r = re.compile(rx)
        for f in files:
            for i, ln in enumerate(self.text(f), 1):
                if r.search(ln):
                    return f, i
        return None

    @staticmethod
    def ref(f, a, b=None):
        return "%s:%s#L%d" % (f[0], f[1], a) + ("-L%d" % b if b and b != a else "")

    def handler_near(self, f, n):
        L = self.text(f)
        for d in (0, -1, -2, -3, -4, -5, -6, 1, 2, 3):   # onX cung dong / the mo phia tren / ngay duoi
            i = n - 1 + d
            m = self.JSX_HANDLER.search(L[i]) if 0 <= i < len(L) else None
            if m and m.group(1) not in ("e", "event"):
                return m.group(1), i + 1
        return None, None

    def body(self, f, h):
        L = self.text(f)
        for i, ln in enumerate(L):
            if re.search(r"(?:const|let|function)\s+%s\b" % re.escape(h), ln):
                depth, started = 0, False
                for j in range(i, min(len(L), i + 60)):
                    depth += L[j].count("{") - L[j].count("}")
                    started = started or "{" in L[j]
                    if started and depth <= 0:
                        return "\n".join(L[i:j + 1]), i + 1, j + 1
                return "\n".join(L[i:i + 60]), i + 1, i + 60
        return None, None, None

    @staticmethod
    def ref_line(e):
        m = re.match(r"^(REPO-\d+):(.+)#L(\d+)", e.get("Trigger Ref") or "")
        return ((m.group(1), m.group(2)), int(m.group(3))) if m else (None, 0)

    def near_edges(self, f, n, clicks, span=1):
        """Loi goi API viet thang trong JSX (onClick={() => api(...)}) -> Trigger Ref ngay dong onClick."""
        return [e for e in clicks if re.match(r"^on[A-Z]\w*$", e["Trigger"]) and self.ref_line(e)[0] == f
                and abs(self.ref_line(e)[1] - n) <= span]

    def classify(self, f, h, clicks, hl=None):
        if re.match(r"^(router\.(push|replace|back)|navigate|push)$", h):
            return "nav", None, (hl, hl)
        h = h.split(".")[-1]
        hit = [e for e in clicks if re.split(r"[\s→>]+", e["Trigger"])[0] == h]
        b, a, z = self.body(f, h)
        if not hit and not b and hl:          # h khong phai handler cua file (ham API import) -> goi thang
            hit = self.near_edges(f, hl, clicks)
        if hit:
            return "api", hit, (a, z)
        if not b and re.match(r"^set[A-Z]", h):        # onClick={() => setOpen(true)}
            return "state", None, (hl, hl)
        if hit:
            return "api", hit, (a, z)
        if not b:
            return None, None, None
        inner = [e for e in clicks if self.ref_line(e)[0] == f and a <= self.ref_line(e)[1] <= z]
        if inner:
            return "api", inner, (a, z)
        if re.search(r"router\.(push|replace)|navigate\(|window\.location|redirect\(|href\s*=", b):
            return "nav", None, (a, z)
        if re.search(r"\bset[A-Z]\w*\(|\b(show|open|toggle|close)\w*\(", b):
            return "state", None, (a, z)
        return None, None, None

    def lookup(self, it, route, clicks):
        """-> (edges, api, p_jp, q_vn, code-ref) hoac None (code khong cho biet)."""
        files = self.files(route)
        if not files:
            return None
        lab = it.get("label") or it.get("name_jp") or ""
        if re.match(r"(?i)^choose (date|time)|^(日付|時刻|日時)を?選択", lab):
            hit = self.find(files, r"(Date|Time|DateTime)Picker\b|type=[\"'](date|time|datetime-local)[\"']")
            if hit:
                return ([], "Không gọi API — mở bộ chọn ngày / giờ", "日付・時刻ピッカーを開く（APIなし）",
                        "Mở bộ chọn ngày / giờ, chưa gửi dữ liệu", self.ref(*hit))
        if lab in ("開く", "閉じる", "Open", "Close", "open", "close"):
            hit = self.find(files, r"<(Autocomplete|Select|Combobox|Listbox)\b|<TextField[^>]*\bselect\b")
            if hit:
                return ([], "Không gọi API — mở / đóng danh sách chọn", "選択肢リストの開閉（APIなし）",
                        "Mở / đóng danh sách lựa chọn của ô chọn", self.ref(*hit))
        if re.match(r"(?i)^(前のページへ|次のページへ|最初のページへ|最後のページへ|ページ（数値）へ?|（数値）|"
                    r"go to (next|previous|first|last) page|go to page.*|next page|previous page)$", lab):
            hit = self.find(files, r"<(DataGrid\w*|TablePagination|Pagination)\b")
            if hit:
                h2 = self.find([hit[0]], r"on(Page|Pagination\w*)Change\s*=|paginationMode=[\"']server")
                if not h2:
                    return ([], "Không gọi API — chuyển trang trong bảng (phía trình duyệt)",
                            "表の改ページ（クライアント側、APIなし）",
                            "Chuyển trang trong bảng, dữ liệu đã tải sẵn trên trình duyệt", self.ref(*hit))
                h, hl = self.handler_near(*h2)
                k, es, rng = self.classify(h2[0], h, clicks, hl) if h else (None, None, None)
                if k == "api":
                    return (es, "\n".join(call_text(e) for e in es), "改ページ：一覧を再取得する",
                            "Chuyển trang → tải lại danh sách", self.ref(h2[0], hl or h2[1]))
        esc = re.escape(lab)
        icon = re.sub(r"[^A-Za-z]", "", lab.title())
        rxs = [r"""(aria-label|title|alt)\s*=\s*\{?\s*['"]%s['"]""" % esc, r">\s*%s\s*<" % esc,
               r"""['"]%s['"]""" % esc] + ([r"<%s(Outlined|Outline|Rounded|Sharp)?Icon\b" % icon] if len(icon) >= 3 else [])
        hit = next((x for x in (self.find(files, rx) for rx in rxs) if x), None)
        if not hit:
            return None
        f, n = hit
        h, hl = self.handler_near(f, n)
        near = self.near_edges(f, hl or n, clicks)
        if near and not h:
            jp, vn = act(near)
            return (near, "\n".join(call_text(e) for e in near), "押下時：" + jp,
                    "Hành vi khi nhấn: " + vn, self.ref(f, n))
        if not h:
            if re.search(r'type=["\']submit', "\n".join(self.text(f)[max(0, n - 6):n + 3])):
                subs = [e for e in clicks if e["Trigger"].startswith("onSubmit") or "→ onSubmit" in e["Trigger"]]
                subs = [e for e in subs if self.ref_line(e)[0] == f]
                if subs:
                    jp, vn = act(subs)
                    return (subs, "\n".join(call_text(e) for e in subs), "フォーム送信：" + jp,
                            "Gửi form → " + vn, self.ref(f, n) + " · " + subs[0]["Trigger Ref"])
            return None
        k, es, rng = self.classify(f, h, clicks, hl)
        r = self.ref(f, hl) + (" · " + self.ref(f, *rng) if rng and rng[0] and rng[0] != hl else "")
        if k == "api":
            jp, vn = act(es)
            return (es, "\n".join(call_text(e) for e in es), "押下時：" + jp, "Hành vi khi nhấn: " + vn, r)
        if k == "nav":
            return ([], "Không gọi API — chuyển trang", "押下時：画面遷移",
                    "Hành vi khi nhấn: chuyển trang", r)
        if k == "state":
            extra, ej, ev = "", "", ""
            if re.search(r"(?i)delete|remove|削除", lab + h):
                dels = [e for e in clicks if e["Method"] == "DELETE"]
                if dels:
                    extra = "\nKhi đồng ý trong hộp thoại: %s" % " / ".join(call_text(e) for e in dels)
                    ej, ev = "\n・確認ダイアログで同意 → データを削除する", "\n・Đồng ý trong hộp thoại xác nhận → xóa dữ liệu"
            return ([], "Không gọi API khi nhấn — mở hộp thoại / đổi trạng thái màn" + extra,
                    "押下時：ダイアログ表示・画面状態の変更" + ej,
                    "Hành vi khi nhấn: mở hộp thoại hoặc đổi trạng thái màn, chưa gửi dữ liệu" + ev, r)
        return None


NO_NEXT = ("", "ー", "—", "-", "なし", "none")


INPUT_KINDS = ("textbox", "textarea", "select", "radio", "checkbox", "date", "number", "password", "email", "toggle")


def merge_ast(spec, ast):
    """Du kien AST (--ast-spec) lap cho trong cua spec agent viet (--spec): man chua co -> lay nguyen;
    item khop (field / nhan) -> dien required / maxlength / next / api con trong hoac "Cần xác nhận";
    loi AST chua co trong spec -> them. Khong them dong item (spec co the da gop nhieu o vao 1 dong). Spec agent luon thang khi da co gia tri."""
    def blank(v):
        v = str(v or "").strip()
        return not v or v.startswith(S.NEED_CONFIRM)
    n = {"screens": 0, "filled": 0, "errors": 0}
    for sid, a in ast.items():
        s = spec.setdefault(sid, {})
        if not s.get("items"):
            s.update({k: v for k, v in a.items() if k in ("items", "errors") or (k == "title" and not blank(v) and not s.get("title"))})
            n["screens"] += 1
            continue
        if blank(s.get("title")) and not blank(a.get("title")):
            s["title"] = a["title"]
        for ai in a.get("items", []):
            m = next((x for x in s["items"] if ai.get("field") and x.get("field") == ai["field"]), None) or \
                next((x for x in s["items"] if ai.get("label") in (x.get("label"), x.get("name_jp"))), None)
            if m is None:
                continue    # spec agent da co danh sach item (co the da gop nhieu o 1 dong) -> khong them dong, tranh trung
            got = False
            for k in ("required", "maxlength"):
                if blank(m.get(k)) and not blank(ai.get(k)):
                    m[k], got = ai[k], True
            if str(m.get("next") or "").strip().lower() in NO_NEXT and str(ai.get("next") or "").strip().lower() not in NO_NEXT:
                m["next"], got = ai["next"], True
            if not m.get("api") and ai.get("api"):
                m["api"], got = ai["api"], True
            if got:
                m["r"] = "; ".join(x for x in (m.get("r"), "AST: " + ai.get("r", "")) if x)
                n["filled"] += 1
        have = {e.get("msg_jp") for e in s.get("errors") or []}
        for e in a.get("errors", []):
            if e.get("msg_jp") not in have:
                s.setdefault("errors", []).append(e)
                n["errors"] += 1
    return n


def screen_ref(ref, ctx):
    """SC-xxx / route -> ten man (title) hoac None. Nhieu man ("SC-004 / SC-012") -> noi bang ・."""
    ref = (ref or "").strip()
    sid = ref if ref in ctx["titles"] else ctx["routes"].get(norm_route(ref)) if ref.startswith(("/", "http")) else None
    if ctx["titles"].get(sid):
        return ctx["titles"][sid]
    many = [ctx["titles"][x] for x in re.findall(r"SC-\d{3,}", ref) if x in ctx["titles"]]
    return "」・「".join(dict.fromkeys(many)) or None


def build_items(sc, spec, page, edges, q, code=None, ctx=None):
    ctx = ctx or {"titles": {}, "routes": {}, "fields": None}
    sid = sc["Screen ID"]
    ev = (page or {}).get("evId") or next(iter(ev_ids(sc.get("Screen Shot EV") or sc.get("Screenshot EV"))), "")
    from_spec = bool(spec.get("items"))   # spec co danh sach item day du (viet tu code)
    items = [dict(i) for i in spec.get("items") or []] or web_items(page, ev)
    mount = [e for e in edges if e["Trigger"] == "mount"]
    clicks = [e for e in edges if e["Trigger"] != "mount"]
    used, spec_q = set(), []
    for it in items:
        lab = {it.get("label"), it.get("name_jp"), it.get("name_vn")} - {None, ""}
        hit = [e for e in clicks if e["UI Label"] in lab]
        if it.get("api"):
            used |= {id(e) for e in hit}
            continue
        kind = str(it.get("type") or "").strip().lower()
        click, link = kind in CLICK_L, kind in ("hyperlink", "link")
        if not hit and click and not link:
            hit = loose_hit(clicks, lab)
            found = None if hit or not code else code.lookup(it, sc.get("URL / Route"), clicks)
            if found:
                es, api, pj, qv, ref = found
                used |= {id(e) for e in es}
                it.update(api=api, _code=True)
                it["r"] = "; ".join(x for x in (it.get("r"), ref) if x)
                if it.get("_web"):
                    it["p"] += "\n・押下時の挙動：" + pj
                    it["q"] += "\n・Hành vi khi nhấn: " + qv
                continue
        used |= {id(e) for e in hit}
        if hit:
            it["api"] = "\n".join(call_text(e) for e in hit)
            refs = " · ".join(sorted({e["Trigger Ref"] for e in hit}))
            it["r"] = "; ".join(x for x in (it.get("r"), refs) if x)
            if it.get("_web"):
                jp, vn = act(hit)
                it["p"] += "\n・押下時の挙動：" + jp
                it["q"] += "\n・Hành vi khi nhấn: " + vn
        elif link:
            it["api"] = "Không gọi API — chuyển trang"
        elif click and from_spec and (it.get("p") or it.get("q")):
            # hanh vi da mo ta tu code (cot P/Q); chi cot S (tham chieu dev) chua ghep duoc -> 1 Q chung / man
            if not spec_q:
                spec_q.append(q.ask("%s — ghép nút với lời gọi API (cột S, tham chiếu cho dev)" % sid,
                                    "Hành vi đã mô tả từ code ở cột P/Q; fe-api-calls.csv không có nhãn nút để ghép"))
            it["api"] = "%s — %s" % (S.NEED_CONFIRM, spec_q[0])
        elif click:
            qid = q.ask("%s 「%s」 — hành vi khi nhấn / API gọi" % (sid, it.get("name_jp")),
                        "Không tìm thấy nhãn / handler của nút này trong code của màn; chưa bấm thử trên website")
            it["api"] = "%s — %s" % (S.NEED_CONFIRM, qid)
            if it.get("_web"):
                it["p"] += "\n・押下時の挙動：%s — %s" % (S.NEED_CONFIRM_JP, qid)
                it["q"] += "\n・Hành vi khi nhấn: %s — %s" % (S.NEED_CONFIRM, qid)
                it["r"] = "; ".join(x for x in (it.get("r"), "%s — %s" % (S.NEED_CONFIRM, qid)) if x)
        else:
            it["api"] = NA
    # nut co trong code nhung khong thay tren web -> mo ta tu handler (R3), code-ref o cot R
    # ten item = nhan hien thi; khong co nhan doc duoc -> Cần xác nhận (ten handler chi o cot R)
    # spec da co du item -> KHONG them dong tu trigger chua khop (feedback: dong mang ten ham)
    for e in ([] if from_spec else clicks):
        if id(e) in used:
            continue
        lab = e["UI Label"] if e["UI Label"] not in ("", "—") and not looks_code(e["UI Label"]) else ""
        if not lab:
            qid = q.ask("%s — tên nút / thao tác (code: %s)" % (sid, e["Trigger Ref"]),
                        "Code gọi xử lý này nhưng không có nhãn hiển thị; chưa quan sát trên web")
            lab_jp, lab = "%s — %s" % (S.NEED_CONFIRM_JP, qid), "%s — %s" % (S.NEED_CONFIRM, qid)
        else:
            lab_jp = lab
        jp, vn = act([e])
        items.append({"name_jp": lab_jp, "name_vn": lab, "type": "Button", "status": NA, "required": NA,
                      "maxlength": NA, "default": NA,
                      "p": "・%s（コードより、画面上では未確認）\n・押下時の挙動：%s" % (lab_jp, jp),
                      "q": "・%s (đọc từ code, chưa thấy trên web)\n・Hành vi khi nhấn: %s" % (lab, vn),
                      "r": "%s (%s) · Không hiển thị trên ảnh — chưa quan sát trên web" % (e["Trigger Ref"], e["Trigger"]),
                      "api": call_text(e)})
    if mount and not any(it.get("name_jp") == "画面初期表示" or it.get("name_vn") == "Mở màn" for it in items):
        calls = " / ".join(call_text(e) for e in mount)
        jp, vn = act(mount)
        items.insert(0, {"name_jp": "画面初期表示", "name_vn": "Mở màn", "type": NA, "status": NA,
                         "required": NA, "maxlength": NA, "default": NA,
                         "p": "・画面表示時に" + jp, "q": "・Khi mở màn: " + vn,
                         "r": " · ".join(sorted({e["Trigger Ref"] for e in mount})) + " · Không hiển thị trên ảnh",
                         "api": "\n".join("Mở màn → " + call_text(e) for e in mount)})
    for it in items:
        # "next" -> man dich theo ten man (khach doc), khong ghi SC-xxx / route
        if str(it.get("next") or "").strip().lower() not in NO_NEXT:
            t = screen_ref(it["next"], ctx)
            if t:
                pj, qv = "・押下 → 「%s」へ遷移" % t, "・Bấm → chuyển sang màn 「%s」" % t
            else:
                qid = q.ask("%s 「%s」 — màn đích sau khi bấm (%s)" % (sid, it.get("name_jp"), it["next"]),
                            "Màn đích không có trong 02_Screen")
                pj, qv = "・押下 → %s — %s" % (S.NEED_CONFIRM_JP, qid), "・Bấm → %s — %s" % (S.NEED_CONFIRM, qid)
            it["p"] = "\n".join(x for x in (it.get("p"), pj) if x)
            it["q"] = "\n".join(x for x in (it.get("q"), qv) if x)
        kind = str(it.get("type") or "").strip().lower()
        if kind in INPUT_TYPES:
            if kind in NO_MAXLEN and not str(it.get("maxlength") or "").strip():
                it["maxlength"] = NA          # o chon / ngay: khong co do dai toi da
            if it.get("field") and ctx.get("fields") and not (it.get("required") and it.get("maxlength")):
                rq, ml, src = ctx["fields"].get(it["field"])
                if (rq and not it.get("required")) or (ml and not it.get("maxlength")):
                    it["required"] = it.get("required") or rq
                    it["maxlength"] = it.get("maxlength") or ml
                    it["_field"] = True
                    it["r"] = "; ".join(x for x in (it.get("r"), "required / maxlength: " + src) if x)
            miss = [k for k in ("required", "maxlength") if not str(it.get(k) or "").strip()]
            if miss:
                qid = q.ask("%s 「%s」 — %s" % (sid, it.get("name_jp"), " / ".join(
                    {"required": "bắt buộc nhập", "maxlength": "độ dài tối đa"}[k] for k in miss)),
                    "Không thấy trong validation FE / DTO / 08_API_Fields / 04_DB_Columns")
                for k in miss:
                    it[k] = "%s — %s" % (S.NEED_CONFIRM, qid)
                it["r"] = "; ".join(x for x in (it.get("r"), "%s — %s" % (S.NEED_CONFIRM, qid)) if x)
    for it in items:   # cam o trong (D1): o con thieu = khong ap dung
        for k in ("name_jp", "name_vn", "type", "status", "required", "maxlength", "default", "p", "q"):
            it[k] = str(it.get(k) or NA)
    return items


def web_errors(page, network, console, ev):
    if not page:
        return []
    url, out = page.get("url", ""), []
    src = "%s (screenshot)" % ev if ev else "pages.json"
    if page.get("errorPage"):
        out.append({"item": "画面", "display": "Full screen", "msg_jp": "HTTP %s" % page.get("status"),
                    "msg_vn": "Trang lỗi HTTP %s" % page.get("status"), "source": src + " · pages.json"})
    for n in network:
        if n.get("page") == url and not n.get("noise") and isinstance(n.get("status"), int):
            path = re.sub(r"^https?://[^/]+", "", n.get("url", ""))[:80]
            out.append({"item": "画面表示時の通信", "display": NA, "msg_jp": "HTTP %s — %s" % (n["status"], path),
                        "msg_vn": "Request trả HTTP %s — %s" % (n["status"], path), "source": src + " · network.json"})
    for c in console:
        if c.get("url") == url and not c.get("noise"):
            out.append({"item": "画面", "display": "Console", "msg_jp": "JS error: %s" % c.get("text", "")[:80],
                        "msg_vn": "Lỗi JS: %s" % c.get("text", "")[:80], "source": src + " · console.json"})
    for e in out:
        e.update(category=CAT_SYS, action_jp="画面を開く", action_vn="Mở màn")
    return out


def style_row(ws, r, cols=COLS):
    for c in cols:
        ST.data(ws.cell(row=r, column=c), center=c in (8, 11, 12, 13, 14))


def fill_screen(ws, sc, site_url, ver, date, author, spec, items, errors, img, title, phase):
    """img = duong dan anh da danh so (hoac None). -> True khi co chen anh."""
    sid = sc["Screen ID"]
    route = sc.get("URL / Route", "")
    for ref, val in (("B1", title), ("D1", site_url.rstrip("/") + route),
                     ("B2", author), ("D2", date), ("B3", author), ("D3", date),
                     ("F1", sid), ("F2", sc.get("Function IDs") or "—"), ("F3", "1"), ("E4", None), ("F4", None),
                     ("F5", "%s — AS-IS baseline" % ver), ("F6", "WORKING_SCREEN")):
        ws[ref] = val   # E4/F4 "Status" bo (feedback: khong dung trang thai DRAFT)
    entry = sc.get("Entry From") or "—"
    ws["B4"] = "■目的\n%s\n\n■アクセス方法\n%s\n\n■トレーサビリティ / Traceability\n%s · %s" % (
        spec.get("purpose") or "%s (%s)" % (title, sc.get("Type") or "—"),
        spec.get("access") or (route if entry == "—" else "%s → %s" % (entry, route)),
        sid, sc.get("Function IDs") or "—")
    ws["B5"] = spec.get("logic") or NA
    ws["B6"] = spec.get("access") or ("Mở trực tiếp: %s" % route if entry == "—" else "Từ %s" % entry)
    ws["A8"] = None   # banner template
    ws.cell(row=HDR, column=19, value="API gọi")
    ST.header(ws.cell(row=HDR, column=19))
    ws.column_dimensions["S"].width = 40
    for r in range(FIRST, ws.max_row + 1):   # bo so thu tu dien san cua template
        ws.cell(row=r, column=8).value = None
    r = FIRST
    for n, it in enumerate(items, start=1):
        vals = [n, it["name_jp"], it["name_vn"], it["type"], it["status"], it["required"], it["maxlength"],
                it["default"], it["p"], it["q"], it.get("r") or NA, it.get("api") or NA]
        for c, v in zip(COLS, vals):
            ws.cell(row=r, column=c, value=v)
        style_row(ws, r)
        r += 1
    if errors:
        r += 1
        ws.merge_cells(start_row=r, start_column=8, end_row=r, end_column=18)
        ws.cell(row=r, column=8, value="⚠ ERROR SCENARIOS — %s" % sid)
        ST.row(ws, r, range(8, 19), "err_title")
        hdr = {8: "#", 9: "Item / vị trí", 10: "Nhóm", 11: "Hiển thị", 13: "Message Code",
               16: "Message hiển thị (VN)", 17: "Xử lý tiếp theo", 19: "Nguồn"}
        rows = [(hdr, "header")] + [({8: k, 9: e["item"], 10: e["category"], 11: e.get("display") or NA,
                                      13: e["code"], 16: e["msg_vn"], 17: e.get("next"), 19: e["source"]}, "data")
                                     for k, e in enumerate(errors, start=1)]
        for vals, kind in rows:
            r += 1
            for a, b in ((11, 12), (13, 15), (17, 18)):
                ws.merge_cells(start_row=r, start_column=a, end_row=r, end_column=b)
            for c, v in vals.items():
                ws.cell(row=r, column=c, value=v)
            ST.row(ws, r, COLS, kind)
    if img:
        from openpyxl.drawing.image import Image
        im = Image(img)
        k = min(1.0, 840.0 / im.width, 900.0 / im.height)
        im.width, im.height = int(im.width * k), int(im.height * k)
        ws.add_image(im, "A10")
        numbered = os.sep + "annotated" + os.sep in img or spec.get("image_numbered")
        ws["A9"] = "Ảnh website %s — %s · %s · %s" % (
            sc.get("Screenshot EV") or "", sid, title,
            "số đỏ trên ảnh = # trong bảng item" if numbered else
            "ảnh chưa đánh số%s — giai đoạn 2 thay bằng ảnh mới có đánh số" % (
                (" (" + spec["image_note"] + ")") if spec.get("image_note") else ""))
    else:
        ws["A9"] = PHASE1_IMG if phase == 1 else PHASE2_IMG
    return bool(img)


def auto_marks(items, page):
    """Giai doan 2: ghep item (nhan) voi vi tri tren anh do crawl-site.js ghi (items[].box · tables[].boxes · linkBoxes)
    -> so # dat o goc tren-trai cua phan tu. Khop dung nhan truoc, roi nhan chua nhau; moi vi tri dung 1 lan."""
    cands = [(e.get("label") or "", e["box"]) for e in page.get("items") or [] if e.get("box")]
    cands += [(t, b) for tb in page.get("tables") or [] for t, b in zip(tb.get("headers") or [], tb.get("boxes") or []) if b]
    cands += [(l.get("text") or "", l["box"]) for l in page.get("linkBoxes") or [] if l.get("box")]
    cands = [(loose(t), b) for t, b in cands if loose(t)]
    used, marks = set(), []
    for n, it in enumerate(items, start=1):
        keys = [loose(x) for x in (it.get("label"), it.get("name_jp")) if x and loose(x)]
        if not keys:
            continue
        hit = next((i for i, (t, _) in enumerate(cands) if i not in used and t in keys), None)
        if hit is None:
            hit = next((i for i, (t, _) in enumerate(cands) if i not in used and len(t) >= 2
                        and any(len(k) >= 2 and (k in t or t in k) for k in keys)), None)
        if hit is not None:
            used.add(hit)
            x, y, w, h = cands[hit][1]
            marks.append({"n": n, "x": min(0.99, max(0.0, x + min(w, 0.02))), "y": min(0.99, max(0.0, y + h / 2))})
    return marks


def screen_image(sid, spec, items, page, crawl, root, idir):
    """spec "image" (anh da danh so) -> dung luon; Giai đoạn 2: item co "mark" + crawl/evidence/<EV>.png
    -> danh so theo cot # (annotate-ui-image.py). -> (duong dan | None, ly do khong co anh)."""
    if spec.get("image"):
        f = os.path.join(root, spec["image"])   # duong dan tinh tu thu muc version
        return (f, "") if os.path.isfile(f) else (None, "ảnh khai báo không có file: %s" % spec["image"])
    marks = [{"n": n, "x": float(it["mark"][0]), "y": float(it["mark"][1])}
             for n, it in enumerate(items, start=1) if isinstance(it.get("mark"), (list, tuple)) and len(it["mark"]) == 2]
    if page and not marks:
        marks = auto_marks(items, page)
    shot = os.path.join(crawl, "evidence", "%s.png" % page["evId"]) if crawl and page and page.get("evId") else ""
    if not (marks and shot and os.path.isfile(shot)):
        return None, ""
    import importlib.util
    try:
        sp = importlib.util.spec_from_file_location("annotate_ui", os.path.join(HERE, "annotate-ui-image.py"))
        mod = importlib.util.module_from_spec(sp)
        sp.loader.exec_module(mod)
    except SystemExit:
        return None, "thiếu Pillow — chưa đánh số được ảnh"
    dst = os.path.join(idir, "bd", "annotated", "%s.png" % sid)
    errs, _ = mod.annotate(shot, dst, marks)
    return (None, "; ".join(errs)) if errs else (dst, "")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inventory", required=True)
    ap.add_argument("--site", required=True)
    ap.add_argument("--version", required=True, help="ver1 ...")
    ap.add_argument("--out", required=True)
    ap.add_argument("--before", help="ghi ban copy template (--before cua gate V-BD)")
    ap.add_argument("--template", default=TEMPLATE)
    ap.add_argument("--fe-api-calls", action="append", default=[])
    ap.add_argument("--crawl", help="recon/crawl/<WEB-xx> (pages.json, network.json, console.json)")
    ap.add_argument("--spec", help="JSON agent viet tu code (item / P,Q / error) — xem docstring")
    ap.add_argument("--ast-spec", help="JSON cua ast/extract-screen.mjs (du kien tu code) — lap cho trong cua --spec")
    ap.add_argument("--q-start", type=int, required=True, help="so Q tiep theo trong 06_OpenQuestions")
    ap.add_argument("--questions-out")
    ap.add_argument("--repo", action="append", default=[], metavar="REPO-01=<path>",
                    help="goc repo de doc handler; mac dinh Path o 11_Repo cua inventory")
    ap.add_argument("--author", default="System Analyst (AI)")
    ap.add_argument("--date", default=None)
    a = ap.parse_args()

    import datetime
    date = a.date or datetime.date.today().isoformat()
    inv = S.load(a.inventory)
    screens = [s for s in inv["02_Screen"] if s.get("Site") == a.site]
    if not screens:
        print("Khong co man nao cua %s trong 02_Screen" % a.site, file=sys.stderr)
        return 1
    site = next((x for x in inv["10_Site"] if x.get("Site ID") == a.site), {})
    edges, sfiles = [], {}
    for p in a.fe_api_calls:
        edges += list(csv.DictReader(open(p, encoding="utf8")))
        rid = os.path.basename(os.path.dirname(os.path.abspath(p)))      # recon/code/REPO-01/fe-api-calls.csv
        for route, fs in read_json(os.path.join(os.path.dirname(p), "fe-screen-files.json"), {}).items():
            sfiles.setdefault(norm_route(route), []).extend((rid, f) for f in fs)
    roots = {r.get("Repo ID"): r.get("Path") for r in inv.get("11_Repo", []) if r.get("Repo ID") and r.get("Path")}
    for kv in a.repo:
        k, _, v = kv.partition("=")
        roots[k.strip()] = v.strip()
    code = Code(roots, sfiles) if sfiles else None
    crawl = a.crawl or ""
    pages = read_json(os.path.join(crawl, "pages.json"), [])
    network = read_json(os.path.join(crawl, "network.json"), [])
    console = read_json(os.path.join(crawl, "console.json"), [])
    spec = read_json(a.spec, {}).get("screens", {}) if a.spec else {}
    ast_fill = merge_ast(spec, read_json(a.ast_spec, {}).get("screens", {})) if a.ast_spec else {}
    root = os.path.dirname(os.path.dirname(os.path.abspath(a.out)))   # thu muc version
    q = Q(a.q_start, a.site)

    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    if a.before:
        os.makedirs(os.path.dirname(os.path.abspath(a.before)), exist_ok=True)
        shutil.copy(a.template, a.before)
    wb = openpyxl.load_workbook(a.template)
    es = wb["Screen Error message"]
    for rng in [m for m in es.merged_cells.ranges if m.min_row > 3]:
        es.unmerge_cells(str(rng))
    er = 4
    idx, stat = wb["Screen Index"], {"items": 0, "api_cells": 0, "code_matched": 0, "errors": 0,
                                     "field_filled": 0, "images": 0}
    # Screen Index bo cot H "Status" (feedback: khong dung DRAFT) -> I..L dich sang H..K
    idx.unmerge_cells("A1:L1")
    widths = {c: idx.column_dimensions[c].width for c in "IJKL"}
    idx.delete_cols(8)
    for old, new in zip("IJKL", "HIJK"):
        idx.column_dimensions[new].width = widths[old]
    idx.merge_cells("A1:K1")
    phase = 2 if a.crawl else 1
    idir = os.path.dirname(os.path.abspath(a.inventory))
    titles = sheet_titles(screens, spec, q)
    ctx = {"titles": titles, "fields": Fields(inv),
           "routes": {norm_route(x.get("URL / Route")): x["Screen ID"] for x in screens if x.get("URL / Route")}}
    for n, sc in enumerate(screens, start=1):
        sid, sp = sc["Screen ID"], spec.get(sc["Screen ID"], {})
        page = page_of(pages, sc.get("Screenshot EV"))
        mine = [e for e in edges if norm_route(e["Screen Route"]) == norm_route(sc.get("URL / Route"))]
        items = build_items(sc, sp, page, mine, q, code, ctx)
        abbr = re.sub(r"\W", "", sid)
        errs = []
        for k, e in enumerate([dict(x) for x in sp.get("errors") or []] +
                              web_errors(page, network, console, sc.get("Screenshot EV", "")), start=1):
            if not str(e.get("code") or "").strip():   # spec de "" = nho builder dat ma
                e["code"] = "E_%s_%s%03d" % (abbr, "S_" if e.get("category") == CAT_SYS else "", k)
            t = screen_ref(e.get("next"), ctx) if re.match(r"^(SC-\d+|/)", e.get("next") or "") else None
            if t:
                e["next"] = "Chuyển sang màn 「%s」" % t
            # o loi khong bao gio trong (feedback): thieu -> 1 Q chung cho ca dong loi
            miss = [k2 for k2 in ("item", "category", "display", "msg_jp", "msg_vn", "action_jp", "action_vn",
                                  "next", "source") if str(e.get(k2) or "").strip() in ("", S.NEED_CONFIRM, S.NEED_CONFIRM_JP)]
            if miss:
                qid = q.ask("%s — lỗi %s: thiếu %s" % (sid, e["code"], ", ".join(ERR_FIELD[k2] for k2 in miss)),
                            "Không thấy trong code / i18n / trên web")
                for k2 in miss:
                    e[k2] = "%s — %s" % (S.NEED_CONFIRM_JP if k2.endswith("_jp") else S.NEED_CONFIRM, qid)
            errs.append(e)
        img, why = screen_image(sid, sp, items, page, crawl, root, idir)
        ws = wb.copy_worksheet(wb["Sample"])
        ws.title = titles[sid]
        has_img = fill_screen(ws, sc, site.get("URL", ""), a.version, date, a.author, sp, items, errs, img,
                              titles[sid], phase)
        for cat in sorted({e["category"] for e in errs}):
            es.merge_cells(start_row=er, start_column=1, end_row=er, end_column=10)
            es.cell(row=er, column=1, value="%s — %s %s" % (cat, sid, titles[sid]))
            ST.row(es, er, range(1, 11), "banner")
            er += 1
            for e in [x for x in errs if x["category"] == cat]:
                for c, v in enumerate([e["code"], sid, e["item"], e["item"], cat, e["action_jp"], e["action_vn"],
                                       e["msg_jp"], e["msg_vn"], e["source"]], start=1):
                    es.cell(row=er, column=c, value=v)
                ST.row(es, er, range(1, 11), "data")
                ST.data(es.cell(row=er, column=1), code=True)
                er += 1
        r = 5 + n
        ui = "Embedded UI images" if has_img else (
            "NO IMAGE — Giai đoạn 1 (chưa chạy Playwright)" if phase == 1 else "NO IMAGE — %s" % (why or "text only"))
        note = "AS-IS — code trước" + (", website sau" if phase == 2 else " (Giai đoạn 1 — chưa quét website)") + (
            "; chưa quét được trên web" if phase == 2 and not page else "")
        for c, v in enumerate([n, sid, sc.get("Function IDs") or "—", titles[sid], titles[sid],
                               "WORKING_SCREEN", "1", ui, "%s — AS-IS baseline" % a.version, date, note], start=1):
            idx.cell(row=r, column=c, value=v)
        idx.cell(row=r, column=2).hyperlink = Hyperlink(ref="B%d" % r, location="'%s'!A1" % titles[sid].replace("'", "''"))
        ST.row(idx, r, range(1, 12), "data")
        ST.data(idx.cell(row=r, column=2), code=True)
        stat["images"] += has_img
        stat["field_filled"] += sum(1 for i in items if i.get("_field"))
        stat["items"] += len(items)
        stat["api_cells"] += sum(1 for i in items if i.get("api") not in (None, NA))
        stat["errors"] += len(errs)
        stat["code_matched"] += sum(1 for i in items if i.get("_code"))

    ch = wb["Change History"]
    r = 6
    while ch.cell(row=r, column=1).value:
        r += 1
    prev = ch.cell(row=r - 1, column=12).value or "—"
    for c, v in enumerate(["CHG-%04d" % (r - 5), date, a.author, "CREATE_SCREEN", "—", "%d màn" % len(screens),
                           "Workbook", "Screen sheets · Screen Index · Screen Error message",
                           "AS-IS baseline %s — %s" % (a.version, a.site),
                           "inventory + recon (code trước, website sau)", prev, a.version, "WAITING APPROVAL",
                           "—", "—", "build-basic-design.py"], start=1):
        ch.cell(row=r, column=c, value=v)
    ST.row(ch, r, range(1, 17), "data")
    wb.move_sheet("Sample", offset=len(wb.sheetnames))   # working sheet truoc, Sample cuoi
    for w in wb.worksheets:
        w.freeze_panes = None   # R13: kit khong freeze panel (template co san o Screen Index / Change History)
    wb.save(a.out)

    qout = a.questions_out or os.path.join(os.path.dirname(os.path.abspath(a.inventory)), "bd",
                                           "questions-%s.csv" % a.site)
    os.makedirs(os.path.dirname(qout), exist_ok=True)
    with open(qout, "w", encoding="utf8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(S.SHEETS["06_OpenQuestions"])
        w.writerows(q.rows)
    print(json.dumps(dict(stat, screens=len(screens), phase=phase, sheets=titles, confirm_cells=len(q.rows), next_q=q.n, ast_fill=ast_fill,
                          out=a.out, questions=qout), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
