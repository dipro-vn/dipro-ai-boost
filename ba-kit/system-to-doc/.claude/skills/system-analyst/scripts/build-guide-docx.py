#!/usr/bin/env python3
"""Sinh file huong dan su dung kit (docx + anh so do).

  python3 build-guide-docx.py --kit <kit root> [--samples <requirement-to-flow/sample>]

Output: <kit>/docs/Hướng dẫn sử dụng System to Doc.docx + <kit>/docs/images/*.png
Anh so do ve bang matplotlib. Cho can anh chup that (terminal Claude Code, Figma that)
-> chen khung "CHÈN ẢNH" de nguoi viet huong dan dan sau.
"""
import argparse
import os
import sys

BLUE, BLUE_BG = "#0969DA", "#E8F4FD"
ORANGE, ORANGE_BG = "#F4860C", "#FFF9EB"
GREEN, GREEN_BG = "#1A7F37", "#EDFDF0"
RED, RED_BG = "#CF222E", "#FFF6F5"
GREY, GREY_BG = "#57606A", "#F6F8FA"
FONT = "Arial"


# ---------------------------------------------------------------- so do
def _plt():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyBboxPatch
    plt.rcParams["font.family"] = ["Arial Unicode MS", "Arial", "DejaVu Sans"]
    return plt, FancyBboxPatch


def _box(ax, P, x, y, w, h, text, fc, ec, size=10, bold=False, dashed=False):
    ax.add_patch(P((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08",
                   fc=fc, ec=ec, lw=1.6, ls="--" if dashed else "-"))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=size,
            weight="bold" if bold else "normal", color="#1F2328", wrap=True)


def _arrow(ax, x1, y1, x2, y2, color=BLUE):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="-|>", color=color, lw=1.6))


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


def img_two_flows(path):
    plt, P, fig, ax = _canvas(12, 5.2)
    ax.text(0.2, 4.9, "LUỒNG 1 — Baseline  (/analyze-system)", fontsize=12, weight="bold", color=BLUE)
    srcs = ["Website", "Source code", "Database\n(tuỳ chọn)", "Figma\n(tuỳ chọn)"]
    for i, s in enumerate(srcs):
        _box(ax, P, 0.2, 3.7 - i * 0.9, 1.9, 0.7, s, BLUE_BG, BLUE)
        _arrow(ax, 2.1, 4.05 - i * 0.9, 3.0, 2.6)
    _box(ax, P, 3.0, 2.1, 2.3, 1.0, "AI khảo sát\n(chỉ đọc)", ORANGE_BG, ORANGE, bold=True)
    _arrow(ax, 5.3, 2.6, 6.0, 2.6)
    _box(ax, P, 6.0, 1.6, 2.6, 2.0, "outputs/\nver1_…_baseline/\n\nO1 … O7", GREEN_BG, GREEN, bold=True)
    ax.text(8.9, 4.9, "LUỒNG 2 — Change Request  (/change-request)", fontsize=12, weight="bold", color=RED)
    _box(ax, P, 9.2, 3.7, 2.6, 0.8, "Yêu cầu thay đổi\n(file · chat · link)", RED_BG, RED)
    _arrow(ax, 10.5, 3.7, 10.5, 3.05, RED)
    _box(ax, P, 9.2, 2.1, 2.6, 0.95, "AI đối chiếu baseline\nphân tích 6 trục", ORANGE_BG, ORANGE, bold=True)
    _arrow(ax, 8.6, 2.6, 9.2, 2.6, GREEN)
    ax.text(8.62, 2.75, "đọc", fontsize=9, color=GREEN)
    _arrow(ax, 10.5, 2.1, 10.5, 1.4, RED)
    _box(ax, P, 9.2, 0.4, 2.6, 1.0, "outputs/\nver2_…_CR-001-…/", GREEN_BG, GREEN, bold=True)
    _save(plt, fig, path)


def img_folder(path):
    plt, P, fig, ax = _canvas(10, 5.6)
    lines = [
        ("my-project/", 0, True), ("CLAUDE.md · POLICIES.md · AGENTS.md", 1, False),
        (".claude/ · templates/ · docs/            ← kit, không sửa", 1, False),
        ("inputs/", 1, True), ("db/schema.sql        ← (tuỳ chọn) dump CHỈ cấu trúc", 2, False),
        ("cr/                  ← bỏ file yêu cầu thay đổi vào đây (Luồng 2)", 2, False),
        (".auth/                ← phiên đăng nhập, AI tự tạo — KHÔNG commit", 1, False),
        ("outputs/              ← AI tự tạo, mỗi lần chạy 1 folder", 1, True),
        ("ver1_011026_baseline/", 2, False), ("ver2_151026_CR-001-them-coupon/", 2, False),
    ]
    for i, (t, lvl, bold) in enumerate(lines):
        name, _, note = t.partition("←")
        y = 5.2 - i * 0.5
        color = BLUE if bold else "#1F2328"
        ax.text(0.3 + lvl * 0.5, y, ("├─ " if lvl else "") + name.strip(), fontsize=12,
                weight="bold" if bold else "normal", color=color)
        if note:
            ax.text(4.6, y, "← " + note.strip(), fontsize=11, color=GREY)
    _save(plt, fig, path)


def img_flow1_steps(path):
    plt, P, fig, ax = _canvas(13, 3.2)
    steps = [("1", "Hỏi input\n(4 nhóm)", BLUE_BG, BLUE), ("2", "Bảng tổng hợp\n→ bạn OK", BLUE_BG, BLUE),
             ("3", "Quét nhạy cảm\n(cảnh báo + dừng)", RED_BG, RED), ("4", "Khảo sát\nchỉ đọc", ORANGE_BG, ORANGE),
             ("5", "Sinh O1–O7\n+ tự kiểm tra", ORANGE_BG, ORANGE), ("6", "Báo cáo:\nfile ở đâu", GREEN_BG, GREEN)]
    for i, (n, t, fc, ec) in enumerate(steps):
        x = 0.2 + i * 2.15
        _box(ax, P, x, 0.8, 1.8, 1.4, t, fc, ec, size=10)
        ax.text(x + 0.15, 2.35, "Bước " + n, fontsize=9, weight="bold", color=ec)
        if i < len(steps) - 1:
            _arrow(ax, x + 1.8, 1.5, x + 2.15, 1.5)
    _save(plt, fig, path)


def img_outputs(path):
    plt, P, fig, ax = _canvas(12, 6.2)
    ax.text(0.2, 5.9, "outputs/ver1_011026_baseline/", fontsize=13, weight="bold", color=GREEN)
    items = [
        ("README.md", "Mục lục: mọi output · số lượng · kết quả kiểm tra", GREY_BG, GREY),
        ("01_Screens/", "O1  Danh sách màn hình theo website (Basic Design xlsx)", BLUE_BG, BLUE),
        ("02_API/", "O2  API Documentation xlsx + sơ đồ map code", BLUE_BG, BLUE),
        ("03_DB/", "O3  Database Documentation xlsx + ERD", BLUE_BG, BLUE),
        ("04_DesignSystem/", "O4  Design System (artifact claude.ai)", ORANGE_BG, ORANGE),
        ("05_Figma/", "O5  Link Figma: Flow tổng quan + Screen flow", ORANGE_BG, ORANGE),
        ("06_Overview/", "O6  Tài liệu tổng hợp (docx)", GREEN_BG, GREEN),
        ("07_BugList/", "O7  Bug hiện trạng Medium–High (nếu chọn)", RED_BG, RED),
    ]
    for i, (f, d, fc, ec) in enumerate(items):
        y = 5.0 - i * 0.66
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
         "ver<N>_…_CR-001/\n\nCR-001_Impact.xlsx\nCR-001_Summary.md\nFigma view CR mới", GREEN_BG, GREEN)
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


def img_badges(path):
    plt, P, fig, ax = _canvas(12, 2.4)
    for i, (t, d, fc, ec, dash) in enumerate([
            ("NEW", "thứ mới", GREEN_BG, GREEN, False), ("UPD", "thứ sửa: cũ → mới", ORANGE_BG, ORANGE, True),
            ("DEL", "thứ xoá", RED_BG, RED, True), ("AS-IS", "màn bên cạnh, không đổi", GREY_BG, "#D0D7DE", False)]):
        _box(ax, P, 0.2 + i * 3.0, 0.6, 2.6, 1.2, t + "\n" + d, fc, ec, size=11, dashed=dash)
    _save(plt, fig, path)


# ---------------------------------------------------------------- docx
class Guide:
    def __init__(self):
        from docx import Document
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        from docx.shared import Pt, RGBColor, Cm
        self.Pt, self.RGB, self.Cm, self.CENTER = Pt, RGBColor, Cm, WD_ALIGN_PARAGRAPH.CENTER
        self.doc = Document()
        st = self.doc.styles["Normal"]
        st.font.name = FONT
        st.font.size = Pt(10.5)
        self.fig = 0

    def title(self, text, goal):
        p = self.doc.add_paragraph()
        p.alignment = self.CENTER
        r = p.add_run(text)
        r.bold = True
        r.font.size = self.Pt(19)
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
            self.doc.add_paragraph(it, style="List Bullet")

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
        self.doc.add_paragraph()

    def image(self, path, caption, width_cm=16):
        self.fig += 1
        self.doc.add_picture(path, width=self.Cm(width_cm))
        self.doc.paragraphs[-1].alignment = self.CENTER
        self._caption("Hình %d — %s" % (self.fig, caption))

    def placeholder(self, what):
        self.fig += 1
        t = self.doc.add_table(rows=1, cols=1)
        t.style = "Table Grid"
        c = t.rows[0].cells[0]
        c.text = ""
        r = c.paragraphs[0].add_run("[ CHÈN ẢNH: %s ]" % what)
        r.bold = True
        r.font.color.rgb = self.RGB(0x57, 0x60, 0x6A)
        c.paragraphs[0].alignment = self.CENTER
        for _ in range(3):
            c.add_paragraph("")
        self._caption("Hình %d — %s" % (self.fig, what))

    def _caption(self, t):
        p = self.doc.add_paragraph()
        p.alignment = self.CENTER
        r = p.add_run(t)
        r.italic = True
        r.font.size = self.Pt(9)

    def save(self, path):
        self.doc.save(path)


def _to_png(src, dst):
    """python-docx khong doc duoc mot so JPG -> chuyen PNG qua matplotlib."""
    import matplotlib.image as mpimg
    plt, _ = _plt()
    mpimg.imsave(dst, mpimg.imread(src))


def build(kit, samples):
    out_dir = os.path.join(kit, "docs")
    img = os.path.join(out_dir, "images")
    os.makedirs(img, exist_ok=True)
    I = lambda n: os.path.join(img, n)
    img_two_flows(I("01_hai-luong.png"))
    img_folder(I("02_thu-muc.png"))
    img_flow1_steps(I("03_luong1-cac-buoc.png"))
    img_outputs(I("04_outputs.png"))
    img_flow2(I("05_luong2.png"))
    img_six_axes(I("06_sau-truc.png"))
    img_badges(I("07_badge-cr.png"))
    sample_imgs = {}
    for key, fn in (("bd", "output5_sample.png"), ("o2", "output2_sample.jpg")):
        src = os.path.join(samples, fn) if samples else ""
        if src and os.path.isfile(src):
            dst = I("mau_" + os.path.splitext(fn)[0] + ".png")
            _to_png(src, dst)
            sample_imgs[key] = dst

    g = Guide()
    g.title("HƯỚNG DẪN SỬ DỤNG — SYSTEM TO DOC",
            "nhận 1 hệ thống đang chạy → AI dựng bộ tài liệu baseline (Luồng 1); "
            "khi khách gửi yêu cầu thay đổi → AI phân tích ảnh hưởng dựa trên baseline (Luồng 2).")
    g.image(I("01_hai-luong.png"), "Hai luồng của kit")

    g.h1("BƯỚC 1 — Chuẩn bị (làm 1 lần)")
    g.bullets(["Tạo folder dự án, copy toàn bộ folder system-to-doc vào.",
               "Tạo inputs/db/ (nếu có file schema) và inputs/cr/ (để bỏ yêu cầu thay đổi sau này).",
               "Cài thư viện (1 lần trên máy):"])
    g.code("pip install openpyxl python-docx matplotlib\n"
           "npm i -D playwright && npx playwright install chromium")
    g.bullets(["Muốn AI vẽ Figma: kết nối Figma MCP (xem mục Lỗi thường gặp)."])
    g.image(I("02_thu-muc.png"), "Cấu trúc folder dự án")

    g.h1("BƯỚC 2 — Chạy Luồng 1 và trả lời câu hỏi")
    g.code("cd my-project\nclaude\n/analyze-system")
    g.p("AI hỏi lần lượt bằng hộp chọn — chọn đáp án hoặc gõ vào ô Other:")
    g.table(["Nhóm", "AI hỏi", "Bạn chuẩn bị"], [
        ["Website", "Bao nhiêu site, URL, staging hay production; tài khoản role nào, ai cấp, có được phép "
                    "dùng để quét không; chỉ ĐỌC hay được CREATE/UPDATE; vùng cấm", "URL + tài khoản TEST"],
        ["Source code", "Bao nhiêu repo, đường dẫn, FE hay BE, repo FE thuộc website nào", "Đường dẫn repo trên máy"],
        ["Database (tuỳ chọn)", "File schema / quyền đọc DB / chỉ có migration / không có",
         "mysqldump --no-data hoặc pg_dump --schema-only"],
        ["Figma (tuỳ chọn)", "Link design hiện tại; link file để AI vẽ flow; có publish Design System lên claude.ai không", "Link figma.com/design/..."],
        ["Khác", "Có làm bug list không; ngôn ngữ; nguồn có dữ liệu người dùng thật không", ""],
    ])
    g.note("không gõ mật khẩu vào chat. Khi cần đăng nhập, AI mở trình duyệt để bạn tự đăng nhập; "
           "AI chỉ lưu phiên vào .auth/. Mặc định AI chỉ ĐỌC — mọi thao tác ghi bị chặn.")
    g.placeholder("Claude Code đang hỏi nhóm câu Website (hộp chọn AskUserQuestion)")

    g.h1("BƯỚC 3 — Xác nhận bảng tổng hợp, chờ AI chạy")
    g.bullets(["AI in Bảng tổng hợp (Discovery Brief): website, tài khoản, quyền, repo, DB, Figma, output dự kiến.",
               "Đúng → gõ OK. Sai chỗ nào → sửa ngay chỗ đó.",
               "Thiếu thứ gì (không có DB, chưa có Figma…) → AI ghi lại và chạy tiếp phần còn lại.",
               "Phát hiện dữ liệu nhạy cảm (.env, key, dump có dữ liệu thật, website hiện dữ liệu thật) → "
               "AI cảnh báo và DỪNG, chờ bạn xử lý."])
    g.image(I("03_luong1-cac-buoc.png"), "Các bước AI chạy ở Luồng 1")

    g.h1("BƯỚC 4 — Nhận kết quả Luồng 1")
    g.p("Kết thúc, AI in đường dẫn folder version và bảng từng output (file · số lượng · kết quả kiểm tra). "
        "Mở README.md trong folder version để xem lại bất cứ lúc nào.")
    g.image(I("04_outputs.png"), "Các output trong 1 folder version")
    g.table(["Output", "Trả lời câu hỏi gì"], [
        ["O1 Danh sách màn hình", "Mỗi website có bao nhiêu màn; mỗi màn có item gì, xử lý thế nào, lỗi hiện gì, "
                                 "liên kết với màn nào"],
        ["O2 API Documentation", "Có những API/batch nào theo group; mỗi API làm gì, method, request, response"],
        ["O3 Database Documentation", "Có những bảng nào, quan hệ ra sao, từng cột: kiểu, format, giới hạn, mục đích"],
        ["O4 Design System", "Cùng chuẩn với designer-kit = format artifact Design System của claude.ai: brand book, màu theo theme, thang chữ, spacing/bo góc/đổ bóng, component có preview chạy thật, logo/icon. Đồng ý thì AI publish thành link private — dùng lại khi làm màn mới"],
        ["O5 Figma", "Flow tổng quan + Screen flow vẽ trên Figma"],
        ["O6 Tài liệu tổng hợp", "Đã chạy gì, có gì, nằm ở đâu, còn câu hỏi gì"],
        ["O7 Bug list", "Lỗi Medium–High đang tồn tại trên website"],
    ])
    if "bd" in sample_imgs:
        g.image(sample_imgs["bd"], "Ví dụ định dạng O1 — sheet Screen Index của Basic Design (dữ liệu mẫu)")
    if "o2" in sample_imgs:
        g.image(sample_imgs["o2"], "Ví dụ định dạng O5 — Screen flow trên Figma (dữ liệu mẫu)")
    g.note("cột/ô ghi UNKNOWN hoặc \"cần xác minh\" là chỗ AI chưa có bằng chứng — không phải lỗi. "
           "Danh sách câu cần hỏi khách nằm ở Phụ lục A của O6.")

    g.h1("BƯỚC 5 — Khi có 1 yêu cầu thay đổi (Luồng 2)")
    g.p("Đưa yêu cầu vào theo 1 trong 3 cách, rồi gọi lệnh:")
    g.table(["Cách", "Làm gì"], [
        ["File (khuyến nghị)", "Bỏ file (.docx .pdf .xlsx .md, ảnh chụp email/mockup) vào inputs/cr/ → "
                               "/change-request inputs/cr/<tên-file>"],
        ["Dán trực tiếp", "/change-request rồi dán nội dung yêu cầu vào Claude Code"],
        ["Link", "/change-request <link Backlog / Drive / Figma> — AI không đọc được thì nhờ bạn tải file về inputs/cr/"],
    ])
    g.image(I("05_luong2.png"), "Luồng 2 — từ yêu cầu tới kết quả")
    g.note("phải có baseline (đã chạy Luồng 1) thì mới phân tích được. Che tên/email người gửi trước khi đưa vào.")

    g.h1("BƯỚC 6 — Nhận kết quả Luồng 2")
    g.image(I("06_sau-truc.png"), "6 câu hỏi AI trả lời cho mỗi yêu cầu")
    g.bullets(["CR-<id>_Impact.xlsx — chi tiết từng trục, xung đột, mức rủi ro, câu hỏi cần khách trả lời.",
               "CR-<id>_Summary.md — tóm tắt ≤ 1 trang, gửi khách được.",
               "Figma — 1 view CR MỚI, chỉ vẽ phần thay đổi và phần bị ảnh hưởng; bản cũ giữ nguyên."])
    g.image(I("07_badge-cr.png"), "Ký hiệu trên Figma view CR", width_cm=14)
    g.placeholder("Figma view CR thực tế (section CR-xxx đặt dưới bản baseline)")

    g.h1("BƯỚC 7 — Version và chạy lại")
    g.bullets(["Mỗi lần chạy = 1 folder mới ver<N>_<ngày>_<tên>. Không bao giờ sửa folder cũ.",
               "Muốn góp ý: ghi vào mục Feedback trong run-log.md của version rồi chạy lại.",
               "CR đã code xong → /analyze-system chọn Delta để có baseline mới cho các CR sau."])

    g.h1("MỘT SỐ LỖI THƯỜNG GẶP")
    g.h3("1- Kết nối với FIGMA")
    g.code("claude mcp add --transport http figma https://mcp.figma.com/mcp")
    g.h3("2- Thiếu Playwright / trình duyệt")
    g.code("npm i -D playwright && npx playwright install chromium")
    g.h3("3- AI báo \"dump có dữ liệu\" và dừng")
    g.p("Xuất lại chỉ cấu trúc: mysqldump --no-data … hoặc pg_dump --schema-only …")
    g.h3("4- AI dừng vì phát hiện .env / key trong repo")
    g.p("Đây là chủ đích. Gỡ file nhạy cảm khỏi bản copy repo đưa cho AI (hoặc xác nhận là dữ liệu giả), rồi chạy lại.")
    g.h3("5- Đăng nhập không được (trang 1 URL, SPA)")
    g.p("Báo AI phần tử hiển thị sau khi đăng nhập (VD tên menu) để AI dùng --success-selector.")

    path = os.path.join(out_dir, "Hướng dẫn sử dụng System to Doc.docx")
    g.save(path)
    print("Da tao %s (%d hinh)" % (path, g.fig))
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kit", required=True)
    ap.add_argument("--samples", default=None)
    a = ap.parse_args()
    try:
        import docx  # noqa: F401
        import matplotlib  # noqa: F401
    except ImportError:
        print("Thieu python-docx / matplotlib", file=sys.stderr)
        return 2
    return build(a.kit, a.samples)


if __name__ == "__main__":
    sys.exit(main())
