# -*- coding: utf-8 -*-
"""Sinh 3 hinh minh hoa cho muc CR trong file huong dan (.docx)."""
from PIL import Image, ImageDraw, ImageFont

R = "/System/Library/Fonts/Supplemental/Arial.ttf"
B = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
f = lambda p, s: ImageFont.truetype(p, s)

INK = (36, 41, 47)
GREY = (87, 96, 106)
LINE = (208, 215, 222)
WHITE = (255, 255, 255)
BLUE = ((232, 244, 253), (9, 105, 218))
GREEN = ((237, 253, 240), (26, 127, 55))
AMBER = ((255, 249, 235), (244, 134, 12))
RED = ((255, 246, 245), (207, 34, 46))
PURPLE = ((251, 238, 255), (102, 57, 186))
GRAY = ((246, 248, 250), (140, 149, 159))


def wrap(dr, text, font, maxw):
    out, line = [], ""
    for w in text.split():
        t = (line + " " + w).strip()
        if dr.textlength(t, font=font) <= maxw:
            line = t
        else:
            if line:
                out.append(line)
            line = w
    if line:
        out.append(line)
    return out


def box(dr, xy, fill, stroke, w=3, rad=14, dash=False):
    x1, y1, x2, y2 = xy
    dr.rounded_rectangle(xy, rad, fill=fill, outline=None)
    if dash:
        step, on = 16, 9
        for x in range(x1, x2, step):
            dr.line([(x, y1), (min(x + on, x2), y1)], fill=stroke, width=w)
            dr.line([(x, y2), (min(x + on, x2), y2)], fill=stroke, width=w)
        for y in range(y1, y2, step):
            dr.line([(x1, y), (x1, min(y + on, y2))], fill=stroke, width=w)
            dr.line([(x2, y), (x2, min(y + on, y2))], fill=stroke, width=w)
    else:
        dr.rounded_rectangle(xy, rad, outline=stroke, width=w)


def text_block(dr, x, y, lines, font, fill=INK, lh=1.35, center_w=None):
    for ln in lines:
        tx = x if center_w is None else x + (center_w - dr.textlength(ln, font=font)) / 2
        dr.text((tx, y), ln, font=font, fill=fill)
        y += int(font.size * lh)
    return y


def arrow(dr, p1, p2, color=(140, 149, 159), w=3, head=11):
    dr.line([p1, p2], fill=color, width=w)
    x1, y1 = p1
    x2, y2 = p2
    if abs(x2 - x1) >= abs(y2 - y1):
        s = 1 if x2 > x1 else -1
        dr.polygon([(x2, y2), (x2 - s * head, y2 - head + 2), (x2 - s * head, y2 + head - 2)], fill=color)
    else:
        s = 1 if y2 > y1 else -1
        dr.polygon([(x2, y2), (x2 - head + 2, y2 - s * head), (x2 + head - 2, y2 - s * head)], fill=color)


def dot(dr, cx, cy, r, fill, stroke):
    dr.ellipse([cx - r, cy - r, cx + r, cy + r], fill=fill, outline=stroke, width=3)


# ────────────────────────────── HINH 1 — Triage ──────────────────────────────
def img1(path):
    W, H = 2200, 1180
    im = Image.new("RGB", (W, H), WHITE)
    dr = ImageDraw.Draw(im)
    fT, fH, fN, fS = f(B, 46), f(B, 32), f(R, 27), f(R, 23)

    dr.text((60, 48), "Bước 7 — Claude phân định: CR hay feedback về luồng hiện tại?", font=fT, fill=INK)
    dr.line([(60, 118), (W - 60, 118)], fill=LINE, width=3)

    # input
    box(dr, (60, 480, 420, 690), BLUE[0], BLUE[1])
    text_block(dr, 60, 528, ["Meeting note /", "Feedback của KH"], fH, INK, center_w=360)
    text_block(dr, 60, 620, ["dán vào session mới"], fS, GREY, center_w=360)

    # triage
    box(dr, (500, 430, 900, 740), PURPLE[0], PURPLE[1])
    text_block(dr, 500, 470, ["TRIAGE"], f(B, 38), PURPLE[1], center_w=400)
    text_block(dr, 500, 540, ["So từng item với", "BASELINE", "(version đã chốt)"], fN, INK, center_w=400)
    text_block(dr, 500, 672, ["bắt buộc trích bằng chứng"], fS, GREY, center_w=400)
    arrow(dr, (430, 585), (492, 585))

    rows = [
        (170, RED, "CR — ChangeRequest", "Ngoài scope đã chốt",
         ["1. Giải trình vì sao là CR (trích baseline)", "2. Hỏi lại bạn (AskUserQuestion)",
          "3. Vẽ CR view MỚI — không vẽ chồng Output 1/2/3", "4. Tạo output_cr.md để trao đổi KH",
          "5. Snapshot version mới v<N+1>"]),
        (560, AMBER, "FEEDBACK — trong scope", "BA vẽ sai/thiếu, chốt Open Question, wording",
         ["1. Bảng Impact Analysis", "2. Hỏi lại bạn (AskUserQuestion)",
          "3. Scoped update — không regenerate toàn bộ", "4. Snapshot version mới v<N+1>"]),
        (860, GRAY, "CHƯA RÕ", "Không trích được bằng chứng từ baseline",
         ["Hỏi lại bạn, không tự chọn nhánh"]),
    ]
    for y, col, title, sub, steps in rows:
        dot(dr, 975, y + 46, 17, col[1], col[1])
        box(dr, (1010, y, 1500, y + (210 if len(steps) > 1 else 110)), col[0], col[1])
        text_block(dr, 1035, y + 22, [title], f(B, 30), col[1])
        text_block(dr, 1035, y + 64, wrap(dr, sub, fS, 440), fS, GREY)
        arrow(dr, (908, y + 46), (962, y + 46), col[1])
        box(dr, (1545, y, 2140, y + (210 if len(steps) > 1 else 110)), WHITE, LINE, w=2)
        text_block(dr, 1570, y + 22, steps, fS, INK, lh=1.55)
        arrow(dr, (1505, y + 46), (1538, y + 46), col[1])

    box(dr, (60, 1050, W - 60, 1140), (246, 248, 250), LINE, w=2, rad=10)
    dr.text((90, 1078), "1 meeting note thường có CẢ HAI loại → Claude gán nhãn cho TỪNG ITEM, "
                        "không gán 1 nhãn cho cả note. Version cũ luôn được giữ nguyên làm baseline.",
            font=fN, fill=GREY)
    im.save(path)


# ─────────────────────── HINH 2 — CR view badges ───────────────────────
def img2(path):
    W, H = 2200, 1240
    im = Image.new("RGB", (W, H), WHITE)
    dr = ImageDraw.Draw(im)
    fT, fN, fS = f(B, 46), f(R, 27), f(R, 23)

    dr.text((60, 48), "CR view — view RIÊNG, phân định chỗ tạo mới và chỗ sửa cái cũ", font=fT, fill=INK)
    dr.line([(60, 118), (W - 60, 118)], fill=LINE, width=3)

    cards = [
        (GREEN, "NEW", "Tạo mới hoàn toàn", "Viền liền, màu xanh", False, False),
        (AMBER, "UPD", "Sửa cái đã có", "Viền nét đứt + ghi: cũ → mới", True, False),
        (RED, "DEL", "Bỏ khỏi luồng", "Viền nét đứt, chữ gạch ngang", True, True),
        (GRAY, "AS-IS", "Giữ nguyên, vẽ làm ngữ cảnh", "Viền mảnh, làm mờ", False, False),
    ]
    x = 60
    for col, code, mean, note, dash, strike in cards:
        box(dr, (x, 170, x + 500, 470), col[0], col[1], w=4, dash=dash)
        dr.rounded_rectangle((x + 28, 200, x + 28 + 150, 252), 8, fill=col[1])
        t = code
        dr.text((x + 28 + (150 - dr.textlength(t, font=f(B, 30))) / 2, 211), t, font=f(B, 30), fill=WHITE)
        ty = text_block(dr, x + 28, 282, wrap(dr, mean, f(B, 29), 440), f(B, 29), INK)
        if strike:
            dr.line([(x + 28, 296), (x + 28 + dr.textlength(mean, font=f(B, 29)), 296)], fill=col[1], width=3)
        text_block(dr, x + 28, ty + 14, wrap(dr, note, fS, 440), fS, GREY)
        text_block(dr, x + 28, 402, ["Ghi kèm Screen Code gốc"] if code in ("UPD", "DEL", "AS-IS")
                   else ["Chưa có trong baseline"], fS, col[1])
        x += 520

    dr.text((60, 530), "Mỗi node trong CR view bắt buộc có đúng 1 badge + 1 bảng CR Change Table đi kèm:",
            font=f(B, 30), fill=INK)

    # table
    hdr = ["#", "Đối tượng", "Loại", "Baseline ref", "Nội dung thay đổi", "Artifact cần sửa"]
    wcol = [70, 420, 180, 420, 540, 450]
    rowsd = [
        ("1", "AX_FEAT_007 — Màn Xác nhận OTP", "NEW", "— (chưa có)", "Thêm bước xác thực OTP", "SPEC, O2, O3, prototype"),
        ("2", "AX_FEAT_003 — Màn Đăng ký", "UPD", "SPEC v2 ## Screen Details", "Nút Gửi → sang màn OTP", "SPEC, O2, O3"),
        ("3", "BR-04 — Auto approve", "DEL", "SPEC v2 ## AC — AC-06", "Bỏ rule auto-approve", "SPEC"),
    ]
    colmap = {"NEW": GREEN, "UPD": AMBER, "DEL": RED}
    y = 590
    x = 60
    dr.rectangle([60, y, 60 + sum(wcol), y + 62], fill=(9, 105, 218))
    for w_, h_ in zip(wcol, hdr):
        dr.text((x + 16, y + 16), h_, font=f(B, 26), fill=WHITE)
        x += w_
    y += 62
    for r in rowsd:
        x = 60
        hgt = 76
        dr.rectangle([60, y, 60 + sum(wcol), y + hgt], fill=WHITE, outline=LINE, width=2)
        for i, (w_, val) in enumerate(zip(wcol, r)):
            if i == 2:
                c = colmap[val]
                dr.rounded_rectangle((x + 16, y + 18, x + 16 + 130, y + 58), 7, fill=c[0], outline=c[1], width=3)
                dr.text((x + 16 + (130 - dr.textlength(val, font=f(B, 24))) / 2, y + 27), val, font=f(B, 24), fill=c[1])
            else:
                ls = wrap(dr, val, fS, w_ - 32)[:2]
                text_block(dr, x + 16, y + (24 if len(ls) == 1 else 12), ls, fS, INK)
            dr.line([(x, y), (x, y + hgt)], fill=LINE, width=2)
            x += w_
        y += hgt

    box(dr, (60, y + 36, W - 60, y + 150), (255, 246, 245), RED[1], w=3, rad=10)
    dr.text((92, y + 60), "KHÔNG vẽ chồng lên Output 1 / 2 / 3 đã giao, cũng không sửa màu hay nhãn của chúng.",
            font=f(B, 28), fill=RED[1])
    dr.text((92, y + 102), "CR luôn là view mới nằm bên dưới, để so được “trước CR” và “sau CR”.",
            font=fN, fill=GREY)
    im.save(path)


# ─────────────────── HINH 3 — output_cr.md ───────────────────
def img3(path):
    W, H = 2000, 1180
    im = Image.new("RGB", (W, H), WHITE)
    dr = ImageDraw.Draw(im)
    fT, fN, fS = f(B, 46), f(R, 27), f(R, 23)
    dr.text((60, 48), "output_cr.md — tài liệu trao đổi khách hàng “vì sao đây là CR”", font=fT, fill=INK)
    dr.line([(60, 118), (W - 60, 118)], fill=LINE, width=3)

    # paper
    box(dr, (60, 170, 1180, 1030), WHITE, LINE, w=3, rad=12)
    dr.rounded_rectangle((60, 170, 1180, 240), 12, fill=(251, 238, 255))
    dr.text((92, 188), "CR-01 — Thêm bước xác thực OTP", font=f(B, 32), fill=PURPLE[1])
    secs = [
        ("1. Yêu cầu của KH", "1–3 gạch đầu dòng, sát ý KH, không diễn giải thêm"),
        ("2. Vì sao chúng tôi xem đây là CR", "mỗi bullet = 1 lý do + trích dẫn baseline (SPEC section, version)"),
        ("3. Ảnh hưởng nếu thực hiện", "scope +N màn mới · artifact phải sửa · effort: cần Dev estimate"),
        ("4. Phương án đề xuất", "[A] … [B] … + khuyến nghị 1 dòng"),
        ("5. Cần KH xác nhận", "checklist câu hỏi chờ KH trả lời"),
        ("Reference", "meeting note · baseline SPEC · CR view Figma · triage"),
    ]
    y = 276
    for t, s in secs:
        dr.rounded_rectangle((92, y, 104, y + 56), 6, fill=PURPLE[1])
        dr.text((128, y + 2), t, font=f(B, 29), fill=INK)
        text_block(dr, 128, y + 44, wrap(dr, s, fS, 1000), fS, GREY)
        y += 124

    rules = [
        ("≤ 1 trang (~40 dòng)", "đọc trong 2 phút, toàn bộ là gạch đầu dòng / bảng"),
        ("Có reference file", "chỉ ghi file / URL có thật; không có thì ghi “chưa vẽ”"),
        ("Giọng văn trung tính", "CR là việc bình thường của dự án — không phán xét KH"),
        ("Không con số thương mại", "BA không tự đưa man-day / giá / kết luận tính thêm tiền"),
        ("Không dữ liệu thật", "người yêu cầu ghi bằng role, không ghi họ tên"),
    ]
    dr.text((1240, 180), "Ràng buộc bắt buộc", font=f(B, 34), fill=INK)
    y = 258
    for t, s in rules:
        box(dr, (1240, y, W - 60, y + 136), (246, 248, 250), LINE, w=2, rad=10)
        dot(dr, 1282, y + 40, 13, GREEN[0], GREEN[1])
        dr.text((1312, y + 20), t, font=f(B, 27), fill=INK)
        text_block(dr, 1282, y + 64, wrap(dr, s, fS, 600), fS, GREY)
        y += 154
    im.save(path)


d = "/private/tmp/claude-501/-Users-longtd-Desktop-WORK-AI-AGENTS-dipro-ai-boots/1aca595c-58c8-47cf-831e-f8969fdaa29d/scratchpad/cr-img/"
img1(d + "cr-1-triage.png")
img2(d + "cr-2-view-badge.png")
img3(d + "cr-3-output-cr.png")
print("done")
