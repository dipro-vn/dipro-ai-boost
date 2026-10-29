#!/usr/bin/env python3
"""Sinh file huong dan su dung kit (docx + anh).

  python3 build-guide-docx.py --kit <kit root> [--samples <requirement-to-flow/sample>]
        [--source-guide "<requirement-to-flow>/Hướng dẫn Flow Hoá Requirement chi tiết.docx"]
        [--anonymize-shots "<folder anh chup output that>"]

Output: <kit>/docs/Hướng dẫn sử dụng System to Doc.docx + <kit>/docs/images/*.png

Anh trong docs/images/:
  - so do + anh mau tong hop (bug list, CR Figma, CR Summary, credential): ve bang matplotlib moi lan chay
  - src_*.png  : anh buoc chung lay tu huong dan requirement-to-flow (--source-guide, chay 1 lan)
  - output_O1..O1.png : anh chup output that DA CHE thong tin du an (--anonymize-shots, chay 1 lan).
    Anh goc KHONG bao gio copy vao kit. Khong co flag -> dung lai file da che san trong docs/images/.
"""
import argparse
import os
import sys
import zipfile

BLUE, BLUE_BG = "#0969DA", "#E8F4FD"
ORANGE, ORANGE_BG = "#F4860C", "#FFF9EB"
GREEN, GREEN_BG = "#1A7F37", "#EDFDF0"
RED, RED_BG = "#CF222E", "#FFF6F5"
PURPLE, PURPLE_BG = "#6639BA", "#FBEEFF"
GREY, GREY_BG = "#57606A", "#F6F8FA"
LINE = "#D0D7DE"
INK = "#1F2328"
XL_HEAD = "#1F4E79"
FONT = "Arial"
DRIVE_LINK = "https://drive.google.com/drive/folders/1yBlhC4bjsEO2--PLfjy4KvmKk1utvZ2X?usp=sharing"
DS_LINK_EXAMPLE = "https://claude.ai/artifact/L6VfhzcbZmpfo1wfpYoD2E"


# ---------------------------------------------------------------- matplotlib helpers
def _plt():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyBboxPatch
    plt.rcParams["font.family"] = ["Arial Unicode MS", "Arial", "DejaVu Sans"]
    return plt, FancyBboxPatch


def _box(ax, P, x, y, w, h, text, fc, ec, size=10, bold=False, dashed=False, color=INK, alpha=1.0):
    ax.add_patch(P((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08",
                   fc=fc, ec=ec, lw=1.6, ls="--" if dashed else "-", alpha=alpha))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=size,
            weight="bold" if bold else "normal", color=color, alpha=alpha)


def _arrow(ax, x1, y1, x2, y2, color=BLUE, dashed=False):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="-|>", color=color, lw=1.6, ls="--" if dashed else "-"))


def _canvas(w, h):
    plt, P = _plt()
    fig, ax = plt.subplots(figsize=(w, h), dpi=160)
    ax.set_xlim(0, w)
    ax.set_ylim(0, h)
    ax.axis("off")
    return plt, P, fig, ax


def _save(plt, fig, path):
    fig.savefig(path, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def _rect(ax, x, y, w, h, fc, ec=LINE, lw=0.8):
    from matplotlib.patches import Rectangle
    ax.add_patch(Rectangle((x, y), w, h, fc=fc, ec=ec, lw=lw))


def _grid(ax, x, top, widths, rows, rh=0.42, head_fc=XL_HEAD, size=8.5, fills=None):
    """Ve bang kieu sheet xlsx: rows[0] = header. fills: {(r, c): color}."""
    fills = fills or {}
    y = top
    for r, row in enumerate(rows):
        h = rh * (max(str(v).count("\n") for v in row) + 1) if r else rh
        cx = x
        for c, (w, v) in enumerate(zip(widths, row)):
            fc = head_fc if r == 0 else fills.get((r, c), "white")
            _rect(ax, cx, y - h, w, h, fc)
            ax.text(cx + 0.06, y - h / 2, str(v), va="center", ha="left", fontsize=size,
                    color="white" if r == 0 else INK, weight="bold" if r == 0 else "normal")
            cx += w
        y -= h
    return y


def _tabs(ax, x, y, names, active, w_total):
    _rect(ax, x, y, w_total, 0.38, "#3B3B3B", "#3B3B3B")
    cx = x + 0.3
    for n in names:
        w = 0.16 * len(n) + 0.5
        on = n == active
        _rect(ax, cx, y + 0.02, w, 0.34, "white" if on else "#5A5A5A", "#3B3B3B")
        ax.text(cx + w / 2, y + 0.19, n, ha="center", va="center", fontsize=9,
                color=GREEN if on else "white", weight="bold" if on else "normal")
        cx += w + 0.05


# ---------------------------------------------------------------- so do
def img_two_flows(path):
    plt, P, fig, ax = _canvas(12, 5.2)
    ax.text(0.2, 4.9, "LUỒNG 1 — Baseline  (2 giai đoạn)", fontsize=12, weight="bold", color=BLUE)
    srcs = ["Source code\n(Giai đoạn 1)", "Database\n(tuỳ chọn)", "Figma\n(tuỳ chọn)", "Website\n(Giai đoạn 2)"]
    for i, s in enumerate(srcs):
        _box(ax, P, 0.2, 3.7 - i * 0.9, 1.9, 0.7, s, BLUE_BG, BLUE)
        _arrow(ax, 2.1, 4.05 - i * 0.9, 3.0, 2.6)
    _box(ax, P, 3.0, 2.1, 2.3, 1.0, "/analyze-system\nPhase 1 → dừng xem trước\n→ Giai đoạn 2", ORANGE_BG, ORANGE, bold=True, size=9)
    _arrow(ax, 5.3, 2.6, 6.0, 2.6)
    _box(ax, P, 6.0, 1.6, 2.6, 2.0, "outputs/\nver1_…_baseline/\n\nO1 … O8", GREEN_BG, GREEN, bold=True)
    ax.text(8.9, 4.9, "LUỒNG 2 — Change Request  (/change-request)", fontsize=12, weight="bold", color=RED)
    _box(ax, P, 9.2, 3.7, 2.6, 0.8, "Yêu cầu thay đổi\n(file · chat · link)", RED_BG, RED)
    _arrow(ax, 10.5, 3.7, 10.5, 3.05, RED)
    _box(ax, P, 9.2, 2.1, 2.6, 0.95, "AI đối chiếu baseline\nphân tích 6 trục", ORANGE_BG, ORANGE, bold=True)
    _arrow(ax, 8.6, 2.6, 9.2, 2.6, GREEN)
    ax.text(8.62, 2.75, "đọc", fontsize=9, color=GREEN)
    _arrow(ax, 10.5, 2.1, 10.5, 1.4, RED)
    _box(ax, P, 9.2, 0.4, 2.6, 1.0, "outputs/\nCR-001_…/", GREEN_BG, GREEN, bold=True)
    _save(plt, fig, path)


def img_folder(path):
    plt, P, fig, ax = _canvas(11, 6.9)
    lines = [
        ("my-project/", 0, True), ("CLAUDE.md · POLICIES.md · AGENTS.md · README.md", 1, False),
        (".claude/ · templates/ · docs/            ← kit, không sửa", 1, False),
        ("inputs/               ← CÓ SẴN — bạn chỉ việc bỏ file vào", 1, True),
        ("repo/                ← source code, mỗi repo 1 folder con", 2, False),
        ("db/                  ← schema.sql (chỉ cấu trúc, không dữ liệu)", 2, False),
        ("cr/                  ← file yêu cầu thay đổi (Luồng 2)", 2, False),
        (".auth/                ← CÓ SẴN — tài khoản test, KHÔNG commit", 1, True),
        ("credentials.local.env ← bạn điền (copy từ credentials.example.env)", 2, False),
        ("outputs/              ← AI tự tạo", 1, True),
        ("_project/            ← câu trả lời AI đã nhớ (không commit)", 2, False),
        ("ver1_011026_baseline/ ← khảo sát lần đầu, chạy lại vẫn ghi vào đây", 2, False),
        ("CR-001_151026_them-coupon/ ← yêu cầu thay đổi", 2, False),
    ]
    for i, (t, lvl, bold) in enumerate(lines):
        name, _, note = t.partition("←")
        y = 6.5 - i * 0.5
        color = BLUE if bold else INK
        ax.text(0.3 + lvl * 0.5, y, ("├─ " if lvl else "") + name.strip(), fontsize=12,
                weight="bold" if bold else "normal", color=color)
        if note:
            ax.text(4.6, y, "← " + note.strip(), fontsize=11, color=GREY)
    _save(plt, fig, path)


def img_flow1_steps(path):
    plt, P, fig, ax = _canvas(13, 3.2)
    steps = [("1", "Giai đoạn 1: hỏi\ncâu còn thiếu", BLUE_BG, BLUE), ("2", "Quét nhạy cảm\n→ đọc code", RED_BG, RED),
             ("3", "Bảng tổng hợp +\nquyết định lớn → OK", BLUE_BG, BLUE), ("4", "Sinh O1–O5, O8\n+ tự kiểm tra", ORANGE_BG, ORANGE),
             ("5", "Điểm dừng: xem trước\n→ chạy tiếp?", GREEN_BG, GREEN), ("6", "Giai đoạn 2: Playwright\n→ O6, O7", ORANGE_BG, ORANGE)]
    for i, (n, t, fc, ec) in enumerate(steps):
        x = 0.2 + i * 2.15
        _box(ax, P, x, 0.8, 1.8, 1.4, t, fc, ec, size=10)
        ax.text(x + 0.15, 2.35, "Bước " + n, fontsize=9, weight="bold", color=ec)
        if i < len(steps) - 1:
            _arrow(ax, x + 1.8, 1.5, x + 2.15, 1.5)
    _save(plt, fig, path)


def img_credentials(path):
    plt, P, fig, ax = _canvas(13, 4.6)
    ax.text(0.2, 4.3, "Môi trường TEST (dev / staging, tài khoản test)", fontsize=12, weight="bold", color=GREEN)
    steps = [("Có sẵn .auth/\ncredentials.example.env\n→ copy .local.env", BLUE_BG, BLUE),
             ("Bạn mở file, điền\ntài khoản (+ Basic Auth)\nghi ENV=TEST → lưu", ORANGE_BG, ORANGE),
             ("Script tự đăng nhập\n(AI không đọc file)", GREEN_BG, GREEN),
             ("Quét toàn bộ màn\nbị đá phiên →\ntự đăng nhập lại", GREEN_BG, GREEN)]
    for i, (t, fc, ec) in enumerate(steps):
        x = 0.2 + i * 3.2
        _box(ax, P, x, 2.3, 2.8, 1.6, t, fc, ec, size=10)
        if i < len(steps) - 1:
            _arrow(ax, x + 2.8, 3.1, x + 3.2, 3.1, GREEN)
    ax.text(0.2, 1.65, "Production / chưa chắc", fontsize=12, weight="bold", color=RED)
    _box(ax, P, 0.2, 0.2, 6.0, 1.15, "AI mở cửa sổ trình duyệt → BẠN tự đăng nhập\nAI chỉ lưu phiên vào .auth/ — không thấy mật khẩu",
         RED_BG, RED, size=10)
    ax.add_patch(P((6.8, 0.2), 6.0, 1.75, boxstyle="round,pad=0.02,rounding_size=0.06", fc="#24292F", ec="#24292F"))
    tmpl = ("# .auth/credentials.local.env  (template)\nWEB-01.URL=https://staging.shopdemo.example\n"
            "WEB-01.ENV=TEST\nWEB-01.admin.USER=\nWEB-01.admin.PASS=")
    ax.text(6.95, 1.08, tmpl, fontsize=8.5, family="monospace", color="#E6EDF3", va="center")
    _save(plt, fig, path)


def img_outputs(path):
    plt, P, fig, ax = _canvas(12, 7.5)
    ax.text(0.2, 7.2, "outputs/ver1_011026_baseline/", fontsize=13, weight="bold", color=GREEN)
    items = [
        ("README.md", "Mục lục: mọi output · số lượng · kết quả kiểm tra", GREY_BG, GREY),
        ("01_Overview/", "O1  Tài liệu tổng hợp — docx: nghiệp vụ chính + bảng tổng màn hình / API / DB", GREEN_BG, GREEN),
        ("02_API/", "O2  API Documentation — xlsx", BLUE_BG, BLUE),
        ("03_DB/", "O3  Database Documentation — xlsx + png ERD", BLUE_BG, BLUE),
        ("04_Figma/", "O4  Link Figma: Flow tổng quan + Screen flow", ORANGE_BG, ORANGE),
        ("05_Basic_Design/", "O5  Danh sách màn hình — xlsx, 1 file / website, cột \"API gọi\"", BLUE_BG, BLUE),
        ("06_Design_System/", "O6  Design System (tuỳ chọn) — folder + link artifact claude.ai", ORANGE_BG, ORANGE),
        ("07_Bug_List/", "O7  Bug mức High trở lên ảnh hưởng thao tác — xlsx 1 sheet (nếu chọn)", RED_BG, RED),
        ("08_Huong_dan_chay_local/", "O8  Hướng dẫn chạy local cho dev — md (chỉ tên key cấu hình)", GREY_BG, GREY),
    ]
    for i, (f, d, fc, ec) in enumerate(items):
        y = 6.3 - i * 0.66
        _box(ax, P, 0.3, y, 2.8, 0.52, f, fc, ec, size=11, bold=True)
        ax.text(3.35, y + 0.26, d, fontsize=11, va="center")
    _save(plt, fig, path)


def img_flow2(path):
    plt, P, fig, ax = _canvas(12, 4.4)
    ways = [("File trong inputs/cr/", "/change-request inputs/cr/yc.docx"),
            ("Dán trong Claude Code", "/change-request  + dán nội dung"),
            ("Link Backlog/Drive/Figma", "/change-request <link>")]
    for i, (a, b) in enumerate(ways):
        y = 3.3 - i * 1.1
        _box(ax, P, 0.2, y, 2.6, 0.8, a, RED_BG, RED, bold=True)
        ax.text(0.25, y - 0.18, b, fontsize=8.5, color=GREY)
        _arrow(ax, 2.8, y + 0.4, 3.6, 2.2, RED)
    _box(ax, P, 3.6, 1.6, 2.4, 1.2, "Tìm baseline mới nhất\n+ hỏi chỗ chưa rõ", ORANGE_BG, ORANGE)
    _arrow(ax, 6.0, 2.2, 6.6, 2.2)
    _box(ax, P, 6.6, 1.6, 2.2, 1.2, "Phân tích\n6 trục impact", ORANGE_BG, ORANGE, bold=True)
    _arrow(ax, 8.8, 2.2, 9.4, 2.2)
    _box(ax, P, 9.4, 0.7, 2.4, 3.0,
         "ver<N>_…_CR-001/\n\nCR-001_Impact.xlsx\n(7 sheet: Summary · Estimation …)\nFigma view CR mới", GREEN_BG, GREEN)
    _save(plt, fig, path)


def img_six_axes(path):
    plt, P, fig, ax = _canvas(12, 4.6)
    _box(ax, P, 4.7, 1.8, 2.6, 1.0, "CR-001", RED_BG, RED, size=13, bold=True)
    axes = [("Hệ thống", "site · module · repo · batch nào?"), ("Database", "thêm gì? xung đột cái cũ?"),
            ("Nghiệp vụ", "sửa gì? ảnh hưởng nghiệp vụ cũ?"), ("Màn hình", "thêm / sửa / xoá màn nào?"),
            ("Bên thứ 3", "liên kết mới? ảnh hưởng cái cũ?"), ("Mockup", "nhất quán Design System cũ?")]
    pos = [(0.3, 3.4), (4.4, 3.6), (8.5, 3.4), (0.3, 0.4), (4.4, 0.2), (8.5, 0.4)]
    for (t, d), (x, y) in zip(axes, pos):
        _box(ax, P, x, y, 3.2, 0.9, t + "\n" + d, BLUE_BG, BLUE, size=10)
        _arrow(ax, 6.0, 2.8 if y > 2 else 1.8, x + 1.6, y if y > 2 else y + 0.9, GREY)
    _save(plt, fig, path)


BADGES = [("NEW", "thứ mới", GREEN_BG, GREEN, False), ("UPD", "thứ sửa: cũ → mới", ORANGE_BG, ORANGE, True),
          ("DEL", "thứ xoá", RED_BG, RED, True), ("IMPACT", "không sửa, bị ảnh hưởng", PURPLE_BG, PURPLE, True),
          ("AS-IS", "màn bên cạnh, không đổi", GREY_BG, LINE, False)]


def img_badges(path):
    plt, P, fig, ax = _canvas(12, 2.4)
    for i, (t, d, fc, ec, dash) in enumerate(BADGES):
        _box(ax, P, 0.2 + i * 2.4, 0.6, 2.2, 1.2, t + "\n" + d, fc, ec, size=10, dashed=dash)
    _save(plt, fig, path)


# ---------------------------------------------------------------- anh mau tong hop (du lieu gia ShopDemo)
def img_bug_list(path):
    plt, P, fig, ax = _canvas(15, 4.6)
    ax.text(0.1, 4.35, "BUG LIST — ShopDemo (ver1)  ·  lỗi ảnh hưởng thao tác — code + website  ·  High / Urgent",
            fontsize=11, weight="bold", color=XL_HEAD)
    widths = [0.8, 2.3, 1.1, 2.0, 1.1, 0.95, 3.4, 1.25, 1.1]
    rows = [["Bug ID", "Title", "Screen", "URL", "Category", "Severity", "Repro Steps", "Evidence", "Reproduced"],
            ["BUG-001", "Nút Thanh toán báo lỗi 500", "SC-013", "/checkout", "Chức năng", "Urgent",
             "1. Thêm 1 sản phẩm  2. Mở giỏ hàng\n3. Bấm Thanh toán → trang lỗi", "EV-0142.png", "Yes — 3/3"],
            ["BUG-002", "Danh sách sản phẩm trắng trang", "SC-010", "/products?page=2", "JS error", "High",
             "1. Mở Danh sách sản phẩm\n2. Bấm trang 2 → màn trắng", "EV-0155.png", "Yes — 3/3"],
            ["BUG-003", "Ảnh sản phẩm không hiển thị", "SC-011", "/products/123", "Giao diện", "High",
             "1. Mở chi tiết sản phẩm bất kỳ\n→ ảnh chính hỏng", "EV-0161.png", "Yes — 2/2"],
            ["BUG-004", "Layout tràn che nút Lưu", "SC-021", "/account/profile", "Giao diện", "High",
             "1. Đăng nhập  2. Mở Hồ sơ\nở 1366px → nút Lưu bị che", "EV-0170.png", "Yes — 2/2"]]
    sev = {"Urgent": "#FFD8D3", "High": "#FFE8CC", "Medium": "#FFF6CC"}
    fills = {(r, 5): sev[rows[r][5]] for r in range(1, len(rows))}
    fills.update({(r, 7): "#E8F4FD" for r in range(1, len(rows))})
    _grid(ax, 0.1, 4.05, widths, rows, rh=0.4, size=8.2, fills=fills)
    _tabs(ax, 0.1, 0.05, ["Bug List"], "Bug List", sum(widths))
    _save(plt, fig, path)


def img_cr_figma(path):
    plt, P, fig, ax = _canvas(15, 9.6)
    ax.add_patch(P((0.15, 0.15), 14.7, 9.3, boxstyle="round,pad=0,rounding_size=0.12", fc="#FAFBFC", ec="#8C959F", lw=1.2))
    ax.text(0.45, 9.0, "CR-001 — Thêm mã giảm giá (baseline ver1)", fontsize=15, weight="bold", color=INK)
    ax.text(0.45, 8.55, "CR-2 Screen Flow — chỉ màn thay đổi / bị ảnh hưởng + hàng xóm 1 bước", fontsize=10, color=GREY)
    W, H = 3.0, 1.25
    nodes = {
        "a": (0.5, 6.7, "AS-IS · SC-010\nDanh sách sản phẩm", GREY_BG, LINE, False),
        "u": (4.1, 6.7, "UPD · SC-012 · Giỏ hàng\ncũ: Tổng tiền →\nmới: + ô mã giảm giá", ORANGE_BG, ORANGE, True),
        "n": (7.7, 6.7, "NEW · IMP-002\nPopup nhập mã giảm giá", GREEN_BG, GREEN, False),
        "c": (11.3, 6.7, "AS-IS · SC-013\nThanh toán", GREY_BG, LINE, False),
        "d": (4.1, 4.6, "DEL · SC-015\nBanner khuyến mãi cũ", RED_BG, RED, True),
        "i": (11.3, 4.6, "IMPACT · SC-020 · Lịch sử đơn\nbị ảnh hưởng qua API-002", PURPLE_BG, PURPLE, True),
    }
    for k, (x, y, t, fc, ec, dash) in nodes.items():
        faded = fc == GREY_BG
        _box(ax, P, x, y, W, H, t, fc, ec, size=9.5, dashed=dash, alpha=0.6 if faded else 1.0,
             bold=not faded)
        if k == "d":
            ax.plot([x + 0.35, x + W - 0.35], [y + H / 2 - 0.02, y + H / 2 - 0.02], color=RED, lw=1.4)
    mid = 6.7 + H / 2
    _arrow(ax, 3.5, mid, 4.1, mid, GREY)
    _arrow(ax, 7.1, mid, 7.7, mid, ORANGE)
    _arrow(ax, 10.7, mid, 11.3, mid, GREEN)
    _arrow(ax, 2.0, 6.7, 4.1, 5.2, RED, dashed=True)
    _arrow(ax, 9.2, 6.7, 11.3, 5.4, PURPLE, dashed=True)
    ax.text(9.55, 5.85, "API-002", fontsize=8.5, color=PURPLE)
    ax.text(0.45, 3.95, "CR Change Table", fontsize=11, weight="bold", color=INK)
    rows = [["Impact ID", "Badge", "Baseline Ref", "Nội dung", "MD"],
            ["IMP-001", "UPD", "SC-012", "Giỏ hàng thêm ô nhập mã + dòng giảm giá", "1.5"],
            ["IMP-002", "NEW", "—", "Popup nhập / kiểm tra mã giảm giá", "1.0"],
            ["IMP-003", "DEL", "SC-015", "Bỏ banner khuyến mãi cũ", "0.25"],
            ["IMP-004", "IMPACT", "SC-020", "Lịch sử đơn hiển thị số tiền đã giảm (qua API-002)", "0.5"]]
    bf = {"UPD": ORANGE_BG, "NEW": GREEN_BG, "DEL": RED_BG, "IMPACT": PURPLE_BG}
    fills = {(r, 1): bf[rows[r][1]] for r in range(1, 5)}
    _grid(ax, 0.45, 3.75, [1.1, 0.95, 1.25, 4.6, 0.6], rows, rh=0.55, head_fc="#24292F", size=9, fills=fills)
    ax.text(9.6, 3.95, "Chú thích", fontsize=11, weight="bold", color=INK)
    for i, (t, d, fc, ec, dash) in enumerate(BADGES):
        y = 3.2 - i * 0.6
        ax.add_patch(P((9.6, y), 1.15, 0.42, boxstyle="round,pad=0.01,rounding_size=0.06", fc=fc, ec=ec,
                       lw=1.4, ls="--" if dash else "-"))
        ax.text(10.175, y + 0.21, t, ha="center", va="center", fontsize=8.5, weight="bold")
        ax.text(10.95, y + 0.21, d, va="center", fontsize=9, color=GREY)
    _save(plt, fig, path)


def img_cr_summary(path):
    plt, P, fig, ax = _canvas(15, 10.4)
    ax.text(0.1, 10.1, "CR-001 — Thêm mã giảm giá  ·  Summary", fontsize=13, weight="bold", color=XL_HEAD)
    info = [["Mục", "Giá trị"], ["Baseline", "ver1_011026_baseline"], ["Nguồn", "FILE — inputs/cr/yc-ma-giam-gia.docx"],
            ["Người yêu cầu", "PM phía khách (vai trò)"], ["Mức ảnh hưởng", "Medium"],
            ["Đề xuất", "Làm trong 1 sprint, chốt CQ-001 trước khi code"]]
    _grid(ax, 0.1, 9.8, [2.0, 5.2], info, rh=0.36, size=8.5)
    ax.text(0.1, 7.35, "① Vì sao đây là Change Request", fontsize=11, weight="bold", color=RED)
    why = [["Tiêu chí", "Hệ thống hiện tại (baseline)", "Yêu cầu CR", "Kết luận"],
           ["C1 Chức năng mới", "Giỏ hàng SC-012 không có ô mã giảm giá", "Nhập mã → trừ tiền", "CR"],
           ["C3 Đổi dữ liệu", "Chưa có bảng mã giảm giá (O3)", "Thêm bảng coupons", "CR"],
           ["C4 Đổi màn đã có", "SC-015 banner khuyến mãi đang chạy", "Bỏ banner", "CR"]]
    _grid(ax, 0.1, 7.15, [2.3, 4.6, 3.2, 1.2], why, rh=0.38, size=8.5,
          fills={(r, 3): RED_BG for r in range(1, 4)})
    ax.text(0.1, 5.25, "② Tổng MD — Trục × Loại", fontsize=11, weight="bold", color=XL_HEAD)
    md = [["Trục", "NEW", "UPD", "DEL", "IMPACT", "Tổng"],
          ["Hệ thống", "—", "—", "—", "—", "0"], ["Database", "0.5", "—", "—", "—", "0.5"],
          ["Nghiệp vụ", "1.0", "—", "—", "—", "1.0"], ["Màn hình", "1.0", "1.5", "0.25", "0.5", "3.25"],
          ["Bên thứ 3", "—", "—", "—", "—", "0"], ["Mockup", "0.5", "—", "—", "—", "0.5"],
          ["Tổng", "3.0", "1.5", "0.25", "0.5", "5.25"]]
    fills = {(7, c): "#DDEBF7" for c in range(6)}
    end = _grid(ax, 0.1, 5.05, [1.8, 0.9, 0.9, 0.9, 1.0, 0.9], md, rh=0.36, size=8.5, fills=fills)
    ax.text(0.1, end - 0.25, "Đơn giá DRAFT → ước lượng sơ bộ, PM / Tech Lead duyệt trước khi gửi khách",
            fontsize=8.5, color=ORANGE, style="italic")
    ax.text(7.2, 5.25, "③ Câu hỏi cần khách trả lời", fontsize=11, weight="bold", color=XL_HEAD)
    q = [["ID", "Câu hỏi", "Trục"],
         ["CQ-001", "1 đơn được dùng tối đa mấy mã?", "Nghiệp vụ"],
         ["CQ-002", "Mã có hạn dùng / giới hạn số lượt?", "Database"],
         ["CQ-003", "Đơn đã giảm có hoàn tiền theo giá gốc?", "Nghiệp vụ"]]
    _grid(ax, 7.2, 5.05, [0.9, 4.6, 1.3], q, rh=0.38, size=8.5)
    ax.text(7.2, 3.15, "Trục không ảnh hưởng: Bên thứ 3 — không thêm / đổi liên kết nào", fontsize=8.5, color=GREY)
    _tabs(ax, 0.1, 0.05, ["Summary", "Impact"], "Summary", 14.0)
    _save(plt, fig, path)


# ---------------------------------------------------------------- anh lay tu huong dan requirement-to-flow
# media trong docx nguon -> ten trong docs/images (chi anh buoc chung, khong mang noi dung du an khac)
SOURCE_IMAGES = {
    "word/media/image5.png": ("src_tao-folder.png", None),
    "word/media/image3.png": ("src_tra-loi-cau-hoi.png", None),
    "word/media/image15.png": ("src_cai-claude-code.png", None),
    "word/media/image19.png": ("src_dang-nhap-claude.png", None),
    "word/media/image14.png": ("src_figma-connected.png", None),
    # nen phia sau hop thoai co chu cua du an khac -> chi giu hop thoai
    "word/media/image18.jpg": ("src_figma-needs-auth.png", (38, 57, 471, 350)),
}


def extract_source_images(docx_path, img_dir):
    from PIL import Image
    import io
    with zipfile.ZipFile(docx_path) as z:
        for member, (name, crop) in SOURCE_IMAGES.items():
            im = Image.open(io.BytesIO(z.read(member))).convert("RGB")
            if crop:
                im = im.crop(crop)
            im.save(os.path.join(img_dir, name))
    print("Da lay %d anh tu huong dan nguon" % len(SOURCE_IMAGES))


# ---------------------------------------------------------------- che anh chup output that (chay 1 lan)
# toa do theo anh hien thi (x0, y0, x1, y1) * scale = pixel goc. Che: ten he thong/du an, mo ta nghiep vu,
# API path, ten bang DB, dich vu ngoai, nhan man hinh, avatar/ten nguoi dung, URL/domain.
_R1 = [(141, 302), (325, 486), (509, 670), (693, 854), (877, 1038), (1061, 1222), (1246, 1407)]
_ERDX = [(64, 248), (314, 498), (565, 749), (816, 1000), (1066, 1250), (1317, 1501)]
_O3 = [(10, 4, 305, 52), (60, 84, 300, 112), (500, 782, 1905, 812)]
_O3 += [(a, y0, b, y1) for (y0, y1) in ((153, 276), (331, 404), (460, 549), (605, 663)) for a, b in _ERDX]
_O3 += [(64, 719, 248, 776)]
_O5 = [(85, 5, 210, 36), (1672, 2, 1712, 40), (135, 76, 860, 107), (135, 708, 860, 740),
       (1428, 266, 1595, 316), (1826, 118, 2000, 595), (1826, 750, 2000, 942)]
_O5 += [(a, 279, b, 314) for a, b in _R1] + [(a, 376, b, 410) for a, b in _R1[:4]]
_O5 += [(a, 830, b, 864) for a, b in _R1[:2]] + [(a, 925, b, 960) for a, b in _R1[:2]]
ANON_SPEC = {
    "output_1.png": (1.47, "output_O1.png", [(383, 208, 579, 815)]),
    "output_2.png": (1.45, "output_O2.png", [(192, 4, 346, 26), (95, 42, 346, 58), (346, 305, 453, 785),
                                             (577, 305, 1540, 785), (176, 787, 1905, 818)]),
    "output_3.png": (1.46, "output_O3.png", _O3),
    "ouptut_4.png": (1.47, "output_O4.png", [
        (0, 0, 2000, 16), (38, 24, 190, 52), (1750, 24, 1782, 52), (1464, 116, 1620, 146),
        (925, 420, 1015, 450), (1190, 420, 1285, 450), (872, 498, 1065, 529), (900, 571, 1005, 602),
        (1145, 571, 1230, 602), (1350, 571, 1500, 602), (910, 641, 995, 672), (1075, 708, 1135, 744),
        (836, 800, 1600, 982)]),
    "output_5.png": (1.47, "output_O5.png", _O5),
    "ouput_6.png": (1.0, "output_O6.png", [
        (505, 20, 1415, 60), (292, 340, 1566, 362), (300, 508, 1585, 762), (1143, 816, 1563, 902),
        (294, 1194, 712, 1574), (1143, 1194, 1563, 1574), (719, 1488, 1138, 1574), (300, 1628, 1585, 1808)]),
}


def anonymize_shots(shots_dir, img_dir):
    from PIL import Image, ImageDraw, ImageFont
    fonts = ["/Library/Fonts/Arial Unicode.ttf", "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
             "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
    font_path = next((f for f in fonts if os.path.isfile(f)), None)
    for fn, (scale, out, rects) in ANON_SPEC.items():
        src = os.path.join(shots_dir, fn)
        if not os.path.isfile(src):
            print("Bo qua (khong co): %s" % fn, file=sys.stderr)
            continue
        im = Image.open(src).convert("RGB")
        d = ImageDraw.Draw(im)
        for r in rects:
            x0, y0, x1, y1 = [int(v * scale) for v in r]
            d.rectangle((x0, y0, x1, y1), fill="#D0D7DE", outline="#8C959F", width=2)
            fs = max(10, min(22, int((y1 - y0) * 0.5)))
            f = ImageFont.truetype(font_path, fs) if font_path else ImageFont.load_default()
            if x1 - x0 > fs * 3:
                d.text((x0 + 4, y0 + 2), "đã che", fill="#57606A", font=f)
        im.save(os.path.join(img_dir, out))
    print("Da che %d anh chup output" % len(ANON_SPEC))


# ---------------------------------------------------------------- docx
class Guide:
    def __init__(self):
        from docx import Document
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        from docx.shared import Pt, RGBColor, Cm
        self.Pt, self.RGB, self.Cm, self.CENTER = Pt, RGBColor, Cm, WD_ALIGN_PARAGRAPH.CENTER
        self.doc = Document()
        for s in self.doc.sections:
            s.left_margin = s.right_margin = Cm(2.0)
            s.top_margin = s.bottom_margin = Cm(1.8)
        st = self.doc.styles["Normal"]
        st.font.name = FONT
        st.font.size = Pt(10.5)
        self.n_img = 0
        self.missing = []

    def title(self, text, sub, goal):
        p = self.doc.add_paragraph()
        p.alignment = self.CENTER
        r = p.add_run(text)
        r.bold = True
        r.font.size = self.Pt(19)
        p = self.doc.add_paragraph()
        p.alignment = self.CENTER
        r = p.add_run(sub)
        r.italic = True
        r.font.color.rgb = self.RGB(0x57, 0x60, 0x6A)
        p = self.doc.add_paragraph()
        r = p.add_run("Mục tiêu: ")
        r.bold = True
        p.add_run(goal)

    def h1(self, t):
        self.doc.add_heading(t, level=1)

    def h3(self, t):
        self.doc.add_heading(t, level=3)

    def p(self, t):
        self.doc.add_paragraph(t)

    def bullets(self, items):
        for it in items:
            p = self.doc.add_paragraph(style="List Bullet")
            head, sep, rest = it.partition(" — ") if it.startswith("**") else ("", "", it)
            if head:
                r = p.add_run(head.strip("*"))
                r.bold = True
                p.add_run(" — " + rest)
            else:
                p.add_run(it)

    def bold_line(self, t):
        p = self.doc.add_paragraph()
        r = p.add_run(t)
        r.bold = True
        r.font.color.rgb = self.RGB(0xCF, 0x22, 0x2E)

    def note(self, t):
        p = self.doc.add_paragraph()
        r = p.add_run("Lưu ý: ")
        r.bold = True
        p.add_run(t)

    def code(self, t):
        p = self.doc.add_paragraph()
        r = p.add_run(t)
        r.font.name = "Roboto Mono"
        r.font.size = self.Pt(9.5)
        r.font.color.rgb = self.RGB(0x1A, 0x7F, 0x37)

    def table(self, header, rows):
        t = self.doc.add_table(rows=1, cols=len(header))
        t.style = "Table Grid"
        for i, h in enumerate(header):
            c = t.rows[0].cells[i]
            c.text = h
            for r in c.paragraphs[0].runs:
                r.bold = True
        for row in rows:
            cells = t.add_row().cells
            for i, v in enumerate(row):
                cells[i].text = v
        for row in t.rows:
            for c in row.cells:
                for para in c.paragraphs:
                    for r in para.runs:
                        r.font.size = self.Pt(9.5)
        self.doc.add_paragraph()

    def image(self, path, caption, width_cm=15):
        if not os.path.isfile(path):
            self.missing.append(os.path.basename(path))
            return
        self.n_img += 1
        self.doc.add_picture(path, width=self.Cm(width_cm))
        self.doc.paragraphs[-1].alignment = self.CENTER
        p = self.doc.add_paragraph()
        p.alignment = self.CENTER
        r = p.add_run("Hình minh họa — " + caption)
        r.italic = True
        r.font.size = self.Pt(9)

    def save(self, path):
        self.doc.save(path)


def build(kit, samples, source_guide, shots):
    out_dir = os.path.join(kit, "docs")
    img = os.path.join(out_dir, "images")
    os.makedirs(img, exist_ok=True)
    I = lambda n: os.path.join(img, n)
    if source_guide:
        extract_source_images(source_guide, img)
    if shots:
        anonymize_shots(shots, img)
    img_two_flows(I("01_hai-luong.png"))
    img_folder(I("02_thu-muc.png"))
    img_flow1_steps(I("03_luong1-cac-buoc.png"))
    img_outputs(I("04_outputs.png"))
    img_flow2(I("05_luong2.png"))
    img_six_axes(I("06_sau-truc.png"))
    img_badges(I("07_badge-cr.png"))
    img_credentials(I("08_tai-khoan-test.png"))
    img_bug_list(I("mau_O7_bug-list.png"))
    img_cr_figma(I("mau_CR_figma-view.png"))
    img_cr_summary(I("mau_CR_impact-summary.png"))

    g = Guide()
    g.title("HƯỚNG DẪN SỬ DỤNG — SYSTEM TO DOC",
            "Hệ thống đang chạy → AI khảo sát → Bộ tài liệu baseline → Phân tích Change Request",
            "nhận 1 hệ thống đang chạy → AI dựng bộ tài liệu baseline (Luồng 1); "
            "khi khách gửi yêu cầu thay đổi → AI phân tích ảnh hưởng dựa trên baseline (Luồng 2).")
    g.image(I("01_hai-luong.png"), "Hai luồng của kit")

    # ---- BUOC 1
    g.h1("BƯỚC 1 — CHUẨN BỊ (LÀM 1 LẦN)")
    g.h3("1.1 Tạo folder dự án và đặt kit vào")
    g.bullets(["Tạo 1 folder riêng cho mỗi hệ thống cần khảo sát, VD: my-project.",
               "Tải kit và giải nén, copy toàn bộ nội dung folder system-to-doc vào my-project."])
    g.bold_line("Link tải kit (Google Drive): " + DRIVE_LINK)
    g.p("Kit đã có sẵn các folder để bỏ file vào (mỗi folder có README.md hướng dẫn riêng):")
    g.table(["Folder", "Bỏ gì vào"],
            [["inputs/repo/", "Source code hệ thống — mỗi repo 1 folder con (web-fe/, api/, batch/…). Không bỏ .env, key, node_modules."],
             ["inputs/db/", "File schema.sql CHỈ cấu trúc (mysqldump --no-data / pg_dump --schema-only)."],
             ["inputs/cr/", "File yêu cầu thay đổi của khách (.docx .pdf .xlsx .md, ảnh) — dùng ở Luồng 2."],
             [".auth/credentials.local.env", "Tài khoản test website: copy từ .auth/credentials.example.env rồi điền (xem Bước 3)."]])
    g.note("Folder inputs/ và .auth/ đã được .gitignore — file bạn bỏ vào không bị commit. "
           "Có folder nào để trống, AI hỏi đường dẫn khác ở bước 2.")
    g.note("phải có folder .claude/ nằm ngay trong my-project. Trên Mac folder này bị ẩn — "
           "bấm Shift + Command + . để hiện, hoặc mở bằng VS Code.")
    g.image(I("src_tao-folder.png"), "Tạo folder dự án trên máy", width_cm=6.5)
    g.image(I("02_thu-muc.png"), "Cấu trúc folder dự án sau khi đặt kit", width_cm=13)
    g.h3("1.2 Mở Claude Code")
    g.bullets(["VS Code → Extensions → tìm Claude Code for VS Code (Anthropic) → Install.",
               "Mở panel Claude Code → Sign in bằng tài khoản Claude trả phí (Pro / Max / Team / Enterprise).",
               "Hoặc dùng Terminal: cd my-project rồi gõ claude."])
    g.image(I("src_cai-claude-code.png"), "Cài extension Claude Code trên VS Code", width_cm=10)
    g.image(I("src_dang-nhap-claude.png"), "Đăng nhập Claude Code", width_cm=6)
    g.h3("1.3 Không cần cài thư viện — kit tự lo")
    g.p("Khi chạy /analyze-system hoặc /change-request, AI tự kiểm tra và tự cài những gì còn thiếu: "
        "thư viện Python, bộ đọc code ts-morph (giai đoạn 1, khoảng 15 MB, chỉ cài trong thư mục kit), "
        "Playwright + trình duyệt (khi quét website ở giai đoạn 2), kết nối Figma MCP (khi vẽ Figma).")
    g.note("máy cần có sẵn Node.js (cài 1 lần, nodejs.org). Chưa có thì AI báo BLOCKED và dừng; "
           "mạng công ty chặn npm thì cấu hình npm theo hướng dẫn của IT.")
    g.note("việc duy nhất bạn có thể được nhờ: gõ /mcp → chọn figma → Authenticate, đăng nhập Figma "
           "bằng tài khoản công ty cấp (liên hệ QA) có quyền EDIT file cần vẽ.")

    # ---- BUOC 2
    g.h1("BƯỚC 2 — CHẠY PHASE 1 (ĐỌC SOURCE CODE) VÀ TRẢ LỜI CÂU HỎI")
    g.p("Luồng 1 chạy bằng 1 lệnh, chia 2 giai đoạn để bạn có output nhanh và xem trước. Giai đoạn 1 chỉ đọc source code "
        "(BE, FE, Mobile), chưa mở website. Xong Giai đoạn 1, AI dừng lại báo kết quả và hỏi có chạy tiếp Giai đoạn 2 không: "
        "AI Playwright mở website để kiểm tra lại và bổ sung.")
    g.table(["", "Giai đoạn 1 — đọc source code", "Giai đoạn 2 — AI Playwright"], [
        ["Lệnh", "/analyze-system", "cùng lệnh — sau điểm dừng bạn chọn chạy tiếp (ngay, hoặc lần gọi sau)"],
        ["Ra", "O1 Tổng hợp · O2 API · O3 DB · O4 Figma · O5 Basic Design · O8 Hướng dẫn chạy local",
         "Kiểm tra lại O1–O5 (thêm ảnh màn hình) · thêm O6 Design System · O7 Bug list"],
        ["Ghi chú", "Tốn token (đọc code)", "Chạy lâu nhưng ít token — máy thao tác trên màn hình, bạn xem được"],
    ])
    g.note("phần mềm là app (không mở bằng trình duyệt được) → không có Giai đoạn 2; AI ghi rõ O6, O7 không chạy.")
    g.p("Trong Claude Code (đang mở folder my-project), gõ lệnh:")
    g.code("/analyze-system")
    g.p("Lệnh tự chạy bằng model Opus. Ở Giai đoạn 1 AI chỉ hỏi về phạm vi, source code, database, Figma — "
        "chưa hỏi tài khoản website. AI hỏi bằng hộp chọn (mỗi lượt tối đa 4 câu cùng chủ đề) — chọn đáp án hoặc gõ vào ô Other:")
    g.table(["Nhóm", "AI hỏi", "Bạn chuẩn bị"], [
        ["Phạm vi", "Tên hệ thống, khảo sát tới đâu, phần mềm là website hay app", ""],
        ["Source code", "Repo nào (AI tự liệt kê từ inputs/repo/), FE hay BE, repo FE thuộc website nào", "Repo đã bỏ vào inputs/repo/"],
        ["Database (tuỳ chọn)", "File schema / chỉ có migration / không có",
         "File .sql chỉ cấu trúc trong inputs/db/ (mysqldump --no-data / pg_dump --schema-only)"],
        ["Figma (tuỳ chọn)", "Link design hiện tại; link file để AI vẽ flow; có publish Design System không",
         "Link figma.com/design/..."],
        ["Khác", "Ngôn ngữ tài liệu, ai đọc", ""],
    ])
    g.note("chưa có thông tin nào (ví dụ chưa có link Figma) → chọn \"Chưa có — chạy v1 trước, bổ sung sau\". "
           "Bổ sung sau thì AI cập nhật lại ver1.")
    g.h3("AI nhớ câu trả lời")
    g.bullets(["Câu bạn đã trả lời được lưu ở outputs/_project/preflight-memory.json (không lưu mật khẩu, không commit).",
               "Lần chạy sau AI không hỏi lại — chỉ in 1 bảng \"Tôi đang dùng các thông tin sau — có gì đổi không?\" để bạn xác nhận 1 lần.",
               "4 câu an toàn luôn được hỏi lại gọn: \"vẫn như lần trước chứ?\"."])
    g.image(I("src_tra-loi-cau-hoi.png"), "Trả lời các câu hỏi của Claude", width_cm=10)

    # ---- BUOC 3
    g.h1("BƯỚC 3 — XÁC NHẬN BẢNG TỔNG HỢP, REVIEW KẾT QUẢ PHASE 1")
    g.bullets(["AI đọc code, rồi in Bảng tổng hợp: repo, DB, Figma, output dự kiến.",
               "Kèm các quyết định lớn có đề xuất, ví dụ: \"2 website khác nhau về cỡ chữ, bo góc nút → đề xuất 2 bộ quy "
               "chuẩn giao diện riêng\", \"thư mục cũ không còn dùng → không khảo sát\", \"đồng ý vẽ sơ đồ database / "
               "lên Figma (dịch vụ bên ngoài)?\".",
               "Đúng → gõ OK. Sai chỗ nào → sửa ngay chỗ đó.",
               "Phát hiện dữ liệu nhạy cảm (.env, key, dump có dữ liệu thật…) → AI cảnh báo và DỪNG chờ bạn.",
               "Xong, AI báo \"Giai đoạn 1 đã chạy xong\" kèm bảng output (xem Bước 5) và hỏi: chạy tiếp Giai đoạn 2 ngay, "
               "dừng để bạn xem trước, hay không chạy Giai đoạn 2.",
               "Báo cáo luôn liệt kê giai đoạn 2 sẽ làm gì: (1) đăng nhập bằng tài khoản thử nghiệm, hỏi lại 4 câu an toàn; "
               "(2) đi qua từng màn, đối chiếu với giai đoạn 1; (3) chụp ảnh, đánh số các mục, chèn vào Basic Design; "
               "(4) bổ sung phần code không đọc được; (5) lập Design System; (6) lập Bug list; (7) cập nhật Tài liệu tổng hợp. "
               "Danh sách này cũng nằm trong README.md của thư mục version.",
               "Chọn dừng → mở các file xem trước; góp ý thì AI sửa và ghi lại vào ver1. Khi sẵn sàng, gọi lại /analyze-system "
               "— AI nhận ra Giai đoạn 1 đã xong và đề xuất chạy tiếp Giai đoạn 2."])
    g.image(I("03_luong1-cac-buoc.png"), "Các bước AI chạy ở Luồng 1")

    # ---- BUOC 4
    g.h1("BƯỚC 4 — PHASE 2 (AI PLAYWRIGHT) VÀ ĐĂNG NHẬP WEBSITE")
    g.p("Chọn \"chạy tiếp\" ở điểm dừng (hoặc gọi lại /analyze-system sau khi xem trước) — AI sang Giai đoạn 2:")
    g.bullets(["AI hỏi về website: URL, môi trường thử nghiệm hay thật, tài khoản role nào và có được phép quét không, "
               "chỉ ĐỌC hay được ghi, vùng cấm, có làm Bug list không, website có dữ liệu thật không. "
               "4 câu an toàn luôn được hỏi lại.",
               "AI Playwright mở website, đi qua từng màn: đối chiếu với kết quả Giai đoạn 1, chụp ảnh màn hình và đánh số "
               "từng mục trên ảnh trong Basic Design, sửa chỗ khác code (ghi thành câu hỏi), thêm O6 Design System và O7 Bug list.",
               "Xong, AI báo \"Giai đoạn 2 đã chạy xong\" và những gì đã đổi so với Giai đoạn 1."])
    g.p("Mật khẩu không bao giờ gõ vào chat. AI chọn cách đăng nhập theo môi trường bạn đã xác nhận:")
    g.bullets(["**Môi trường TEST** — điền sẵn file .auth/credentials.local.env (copy từ credentials.example.env; chưa có thì AI tạo với chỗ trống) → bạn mở file, "
               "điền URL, tài khoản (+ Basic Auth nếu có), ghi ENV=TEST, lưu rồi trả lời \"xong\".",
               "**Sau đó** — script tự đăng nhập và quét toàn bộ màn, tự đăng nhập lại khi bị app đá phiên. "
               "AI chỉ truyền đường dẫn file cho script, không đọc nội dung.",
               "**Production / chưa chắc** — AI mở cửa sổ trình duyệt, bạn tự đăng nhập; AI chỉ lưu phiên vào .auth/."])
    g.note(".auth/ không commit, không nằm trong output. Khảo sát xong thì xoá file và đổi mật khẩu test. "
           "Mặc định AI chỉ ĐỌC — mọi thao tác ghi bị chặn.")
    g.image(I("08_tai-khoan-test.png"), "Hai cách đăng nhập — TEST và production")

    # ---- BUOC 5
    g.h1("BƯỚC 5 — NHẬN KẾT QUẢ LUỒNG 1")
    g.p("Kết thúc, AI in đường dẫn folder version và bảng từng output. Mở README.md trong folder version "
        "để xem lại bất cứ lúc nào.")
    g.image(I("04_outputs.png"), "Các output trong 1 folder version", width_cm=13)
    g.table(["Output", "Phase", "Loại", "Nơi lưu"], [
        ["O1 Tài liệu tổng hợp", "1 (cập nhật ở 2)", "docx (hình luồng nghiệp vụ + nghiệp vụ chính + bảng tổng)", "01_Overview/Overview_….docx"],
        ["O2 API Documentation", "1", "xlsx", "02_API/"],
        ["O3 Database Documentation", "1", "xlsx + png ERD", "03_DB/"],
        ["O4 Figma flow", "1", "link Figma", "04_Figma/figma-links.md"],
        ["O5 Basic Design", "1 · ảnh ở 2", "xlsx (1 file / website)", "05_Basic_Design/BasicDesign_WEB-01_ver<N>.xlsx"],
        ["O6 Design System (tuỳ chọn)", "2", "link artifact claude.ai + folder", "06_Design_System/ (STATUS.md + project/)"],
        ["O7 Bug list (tuỳ chọn)", "2", "xlsx 1 sheet", "07_Bug_List/BugList_….xlsx"],
        ["O8 Hướng dẫn chạy local", "1", "md (dev)", "08_Huong_dan_chay_local/DevSetup_….md"],
        ["CR (Luồng 2)", "—", "xlsx (7 sheet) + 見積書 + link Figma view CR", "CR-<id>_<ngày>_<tên>/"],
    ])
    g.note("ảnh O1–O6 dưới đây chụp từ 1 dự án thật, phần thông tin dự án đã được che. "
           "Ô ghi “Cần xác nhận — Q-xxx” là chỗ AI chưa có bằng chứng — không phải lỗi; danh sách câu hỏi Q-xxx AI báo ở cuối phiên chạy.")

    g.h3("O1 — Tài liệu tổng hợp (docx)")
    g.bullets(["Dùng để: đọc nhanh hệ thống làm gì, các luồng nghiệp vụ chính (bước đánh số), trạng thái đối tượng chính.",
               "Ngay phần \"Tổng quan hệ thống\" có hình luồng nghiệp vụ (AI vẽ bằng Archify từ source code) — xem được luôn, không cần mở link.",
               "Màn hình, API, database chỉ có bảng tổng; danh sách chi tiết ở O5 / O2 / O3. Sơ đồ DB là link Figma.",
               "Mở: 01_Overview/Overview_….docx bằng Word."])
    g.image(I("output_O6.png"), "O1 — tài liệu tổng hợp", width_cm=11)
    g.h3("O2 — API Documentation (xlsx)")
    g.bullets(["Dùng để: tra mọi API / batch theo group — làm gì, method, request, response, màn nào gọi.",
               "Mở: sheet 00_Index → bấm API ID để tới block chi tiết."])
    g.image(I("output_O2.png"), "O2 — sheet 00_Index")
    g.h3("O3 — Database Documentation (xlsx + ERD)")
    g.bullets(["Dùng để: xem các bảng, quan hệ, từng cột (kiểu, format, giới hạn, mục đích).",
               "Mở: sheet 00_Overview → 02_ERD (sơ đồ) → mỗi bảng 1 sheet T_…"])
    g.image(I("output_O3.png"), "O3 — sheet 02_ERD")
    g.h3("O4 — Figma flow")
    g.bullets(["Dùng để: xem Flow tổng quan + Screen flow (màn nào dẫn tới màn nào, nhánh lỗi / edge).",
               "Mở: link trong 04_Figma/figma-links.md."])
    g.image(I("output_O5.png"), "O4 — Screen flow trên Figma")
    g.h3("O5 — Basic Design (xlsx)")
    g.bullets(["Dùng để: biết mỗi website có bao nhiêu màn, mỗi màn có những ô nhập / nút / bảng nào, bấm vào thì chuyển sang màn nào, "
               "thông báo lỗi nào hiện ra.",
               "Mỗi màn 1 sheet, tên sheet là tên màn dễ hiểu (ví dụ 「予約編集」), không dùng mã như SC-007.",
               "Giai đoạn 1: AI đọc code bằng AST (lấy nguyên văn nhãn, thông báo lỗi, bắt buộc nhập, độ dài tối đa), "
               "rồi viết lại theo nghiệp vụ. Chỗ code không cho biết ghi \"Cần xác nhận — Q-xxx\".",
               "Bắt buộc nhập, độ dài tối đa lấy từ source code; mô tả viết theo nghiệp vụ (\"bấm → chuyển sang màn 「…」\"), "
               "không ghi kiểu \"gọi API GET/POST\". Thông báo lỗi không để trống ô nào.",
               "Giai đoạn 1 lấy từ source code; Giai đoạn 2 thêm ảnh chụp màn hình có đánh số từng mục, và bổ sung phần code không đọc được.",
               "Mở: Excel, sheet Screen Index → bấm tên màn để tới sheet của màn; theo template Basic Design công ty."])
    g.image(I("output_O1.png"), "O5 — sheet Screen Index")
    g.h3("O6 — Design System (tuỳ chọn, link artifact claude.ai)")
    g.bullets(["Dùng để: tra màu, chữ, spacing, component có preview của hệ thống cũ — dùng lại khi làm màn mới "
               "(cùng chuẩn với designer-kit).",
               "Sinh ở Giai đoạn 2 (đo trên màn hình thật). Mở: link artifact private AI in ra (VD " + DS_LINK_EXAMPLE + "); bản file nằm ở 06_Design_System/.",
               "Nhiều website: chỉ khác màu → 1 Design System mỗi site 1 theme; khác cả phong cách → mỗi site 1 link riêng."])
    g.image(I("output_O4.png"), "O6 — trang Components của artifact Design System")
    g.h3("O7 — Bug list (xlsx, tuỳ chọn)")
    g.bullets(["Sinh ở Giai đoạn 2: đọc code trước (nút nào gọi xử lý gì, thiếu kiểm tra lỗi ở đâu), rồi AI Playwright thao tác thử trên website để xác nhận.",
               "Chỉ lỗi mức High / Urgent làm người dùng thao tác không được hoặc sai; mỗi bug có màn SC-xxx, bước tái hiện, bằng chứng (ảnh / dòng code).",
               "1 sheet duy nhất \"Bug List\". Không có lỗi mức cao → sheet trống.",
               "Mở: 07_Bug_List/BugList_….xlsx."])
    g.image(I("mau_O7_bug-list.png"), "O7 — sheet Bug List (dữ liệu giả ShopDemo)")
    g.h3("O8 — Hướng dẫn chạy local (md, cho dev)")
    g.bullets(["Lệnh cài / chạy, database local, môi trường, pipeline deploy, lịch batch — gom tự động từ source.",
               "Cấu hình chỉ ghi TÊN key (lấy từ .env.example) — không bao giờ có giá trị, AI không đọc .env thật.",
               "Mở: 08_Huong_dan_chay_local/DevSetup_….md."])

    # ---- BUOC 6
    g.h1("BƯỚC 6 — KHI CÓ 1 YÊU CẦU THAY ĐỔI (LUỒNG 2)")
    g.p("Đưa yêu cầu vào theo 1 trong 3 cách, rồi gọi lệnh:")
    g.table(["Cách", "Làm gì"], [
        ["File (khuyến nghị)", "Bỏ file (.docx .pdf .xlsx .md, ảnh chụp) vào inputs/cr/ → "
                               "/change-request inputs/cr/<tên-file>"],
        ["Dán trực tiếp", "/change-request rồi dán nội dung yêu cầu vào Claude Code"],
        ["Link", "/change-request <link Backlog / Drive / Figma> — AI không đọc được thì nhờ bạn tải về inputs/cr/"],
    ])
    g.note("phải có baseline (đã chạy Luồng 1). Che tên / email người gửi trước khi đưa vào.")
    g.image(I("05_luong2.png"), "Luồng 2 — từ yêu cầu tới kết quả")
    g.image(I("06_sau-truc.png"), "6 câu hỏi AI trả lời cho mỗi yêu cầu")

    # ---- BUOC 7
    g.h1("BƯỚC 7 — NHẬN KẾT QUẢ LUỒNG 2")
    g.h3("CR-<id>_Impact.xlsx — 7 sheet")
    g.bullets(["**Summary** — công số thay đổi (実装 MD · 総工数 人日 · 人月, link sang Estimation) · số màn / API / "
               "bảng DB … thêm / sửa / xoá / bị ảnh hưởng · link tới từng sheet.",
               "**Estimation** — đúng khung 見積書 của công ty (templates/template_estimation.xlsx), 1 dòng / hạng mục.",
               "**Screen · API · Database · Figma** — từng hạng mục của trục: vì sao phải sửa, xung đột, rủi ro, MD.",
               "**Q&A** — vì sao đây là CR · câu hỏi cần khách trả lời · mục không thuộc CR."])
    g.note("MD = đơn giá trong .claude/config/md-unit-rates.json × số lượng — AI không tự gõ số. "
           "Bảng đơn giá đang DRAFT, PM / Tech Lead duyệt trước khi gửi khách.")
    g.image(I("mau_CR_impact-summary.png"), "Sheet Summary của CR-001 (dữ liệu giả ShopDemo)")
    g.h3("Figma — view CR mới")
    g.bullets(["1 section mới đặt dưới bản baseline — bản cũ giữ nguyên.",
               "CR-1 Flow theo khung Output 1, CR-2 Screen Flow theo khung Output 2 (mũi tên thật); chỉ phần thay đổi "
               "+ phần bị ảnh hưởng + màn bên cạnh 1 bước; tô màu theo badge.",
               "CR Change Table = thống kê số màn / API / bảng thay đổi + công số (không liệt kê chi tiết).",
               "CR-3 màn đề xuất dựng từ Design System của baseline — AI đọc Design System trước, hỏi phạm vi."])
    g.image(I("07_badge-cr.png"), "Ký hiệu trên Figma view CR", width_cm=13)
    g.image(I("mau_CR_figma-view.png"), "Figma view CR-001 (dữ liệu giả ShopDemo)")

    # ---- BUOC 8
    g.h1("BƯỚC 8 — VERSION VÀ CHẠY LẠI (AI TỰ LÀM)")
    g.p("Bạn không phải chỉ version, không phải mở run-log.md. AI tự quản lý version:")
    g.bullets(["Mỗi lần chạy, AI tự đọc version mới nhất: baseline mới nhất, CR đang mở, góp ý chưa xử lý.",
               "Khảo sát lần đầu luôn là ver1. Chạy lại / bổ sung nguồn / sửa theo góp ý → AI ghi vào ver1, "
               "trước khi ghi đè thì cất bản cũ vào _internal/history/<ngày-giờ>/.",
               "Có yêu cầu thay đổi đầu tiên → folder CR-001_<ngày>_<tên>/ trỏ về ver1, ver1 bị khoá (không ghi đè nữa).",
               "CR đã được khách duyệt và đã code xong: nói \"CR-001 đã duyệt, đã code xong\" (hoặc chạy /analyze-system) — "
               "AI hỏi xác nhận rồi tạo ver2 = ver1 + CR đó. ver3, ver4… cũng chỉ sinh theo cách này.",
               "Muốn góp ý: nói thẳng trong chat (VD \"MD màn coupon cao quá\") — AI sửa và ghi vào run-log.md."])
    if os.path.isfile(os.path.join(out_dir, "lifecycle-system-to-doc.png")):
        g.image(os.path.join(out_dir, "lifecycle-system-to-doc.png"), "Vòng đời version: ver1 → CR → duyệt + code xong → ver2")

    # ---- LOI
    g.h1("MỘT SỐ LỖI KHI DÙNG")
    g.h3("1- AI nhờ xác thực Figma")
    g.bullets(["AI đã tự thêm kết nối Figma, chỉ còn bước đăng nhập phải do người bấm.",
               "Gõ /mcp → chọn figma. Thấy Needs Auth → bấm vào → Allow trên trình duyệt. "
               "Kết quả figma ✔ Connected là OK. Không thấy figma trong /mcp → khởi động lại Claude Code.",
               "Còn lỗi → kiểm tra Figma đã đăng nhập đúng tài khoản công ty cấp (liên hệ QA), có quyền EDIT chưa."])
    g.image(I("src_figma-needs-auth.png"), "Figma MCP chưa xác thực (Needs Auth)", width_cm=8)
    g.image(I("src_figma-connected.png"), "Figma MCP đã kết nối", width_cm=7)
    g.h3("2- AI báo không tự cài được môi trường (BLOCKED)")
    g.p("Thường do máy chưa có Node.js (cần khi quét website) hoặc mạng chặn tải thư viện. "
        "Gửi nguyên thông báo của AI cho người phụ trách kit / IT; phần không phụ thuộc vẫn chạy tiếp.")
    g.h3("3- AI báo \"dump có dữ liệu\" và dừng")
    g.p("Xuất lại chỉ cấu trúc: mysqldump --no-data … hoặc pg_dump --schema-only …")
    g.h3("4- AI dừng vì phát hiện .env / key trong repo")
    g.p("Đây là chủ đích. Gỡ file nhạy cảm khỏi bản copy repo đưa cho AI (hoặc xác nhận là dữ liệu giả), rồi chạy lại.")
    g.h3("5- AI không tự đăng nhập được")
    g.p("AI không thử mãi: sau 2 lần (hoặc quá thời gian) AI dừng, mở cửa sổ trình duyệt và nhắn "
        "\"Bạn đăng nhập tay giúp tôi, xong trả lời 'xong'\". Bạn đăng nhập trong cửa sổ đó → AI lưu phiên và quét tiếp. "
        "Trang đăng nhập 1 URL (SPA): báo AI phần tử chỉ hiện sau khi đăng nhập (VD tên menu) để AI dùng --success-selector.")
    g.h3("6- Claude Code chặn khi dùng tài khoản test")
    g.p("Không gõ tài khoản vào chat. Dùng file .auth/credentials.local.env: copy từ mẫu (hoặc AI tạo template) → bạn điền, "
        "ghi ENV=TEST → script tự đăng nhập (xem Bước 3).")

    path = os.path.join(out_dir, "Hướng dẫn sử dụng System to Doc.docx")
    g.save(path)
    print("Da tao %s (%d hinh)" % (path, g.n_img))
    if g.missing:
        print("Thieu anh (chay lai voi --source-guide / --anonymize-shots): " + ", ".join(g.missing),
              file=sys.stderr)
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kit", required=True)
    ap.add_argument("--samples", default=None, help="giu de tuong thich, khong con dung")
    ap.add_argument("--source-guide", default=None, help="docx huong dan requirement-to-flow -> lay anh buoc chung")
    ap.add_argument("--anonymize-shots", default=None, help="folder anh chup output that -> che va luu docs/images")
    a = ap.parse_args()
    try:
        import docx  # noqa: F401
        import matplotlib  # noqa: F401
    except ImportError:
        print("Thieu python-docx / matplotlib", file=sys.stderr)
        return 2
    return build(a.kit, a.samples, a.source_guide, a.anonymize_shots)


if __name__ == "__main__":
    sys.exit(main())
