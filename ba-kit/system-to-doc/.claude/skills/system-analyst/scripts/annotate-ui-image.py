#!/usr/bin/env python3
"""Danh so anh UI (badge do) truoc khi chen vao Basic Design (.xlsx).

So tren anh = cot `#` (H) cua bang item cung sheet. Anh goc KHONG bi sua —
script ghi ra file moi.

Dung:
  python3 annotate-ui-image.py <anh_goc.png> <anh_ra.png> \
      --marks "1:0.50,0.18;2:0.93,0.22;3:0.93,0.30" [--expect 6]
  python3 annotate-ui-image.py <anh_goc.png> <anh_ra.png> --marks-json marks.json

--marks      "<so>:<x>,<y>;..."  x,y = TAM badge. 0..1 = ti le theo anh, >1 = pixel
--marks-json {"marks":[{"n":1,"x":0.5,"y":0.18}, ...]}
--expect N   so item cua sheet; lech -> exit 1 (khong ghi file)
--size PX    duong kinh badge (mac dinh = 4.5% chieu rong anh, toi thieu 28)

Exit: 0 OK · 1 loi du lieu (thieu/thua so, toa do ngoai anh, trung so) · 2 thieu Pillow
"""
import argparse, json, os, sys

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Thieu Pillow: pip install Pillow", file=sys.stderr)
    sys.exit(2)

RED = (196, 18, 48, 255)
WHITE = (255, 255, 255, 255)
FONTS = [
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/Library/Fonts/Arial Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]


def load_font(px):
    for p in FONTS:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, px)
            except OSError:
                pass
    try:
        return ImageFont.load_default(size=px)
    except TypeError:
        return ImageFont.load_default()


def parse_marks(s):
    out = []
    for part in filter(None, (p.strip() for p in s.split(";"))):
        n, xy = part.split(":")
        x, y = xy.split(",")
        out.append({"n": int(n), "x": float(x), "y": float(y)})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--marks")
    ap.add_argument("--marks-json")
    ap.add_argument("--expect", type=int)
    ap.add_argument("--size", type=int)
    a = ap.parse_args()

    if a.marks_json:
        marks = json.load(open(a.marks_json, encoding="utf-8"))["marks"]
    elif a.marks:
        marks = parse_marks(a.marks)
    else:
        print("Can --marks hoac --marks-json", file=sys.stderr)
        return 1

    if os.path.abspath(a.src) == os.path.abspath(a.dst):
        print("dst phai khac src — khong ghi de anh goc", file=sys.stderr)
        return 1

    im = Image.open(a.src).convert("RGBA")
    W, H = im.size
    nums = [m["n"] for m in marks]
    errs = []
    if len(set(nums)) != len(nums):
        errs.append(f"trung so: {sorted(n for n in set(nums) if nums.count(n) > 1)}")
    if a.expect is not None:
        want = set(range(1, a.expect + 1))
        miss, extra = sorted(want - set(nums)), sorted(set(nums) - want)
        if miss:
            errs.append(f"thieu so {miss} (sheet co {a.expect} item)")
        if extra:
            errs.append(f"thua so {extra} (sheet chi co {a.expect} item)")
    pts = []
    for m in marks:
        x = m["x"] * W if 0 <= m["x"] <= 1 else m["x"]
        y = m["y"] * H if 0 <= m["y"] <= 1 else m["y"]
        if not (0 <= x <= W and 0 <= y <= H):
            errs.append(f"so {m['n']}: toa do ({x:.0f},{y:.0f}) ngoai anh {W}x{H}")
        pts.append((m["n"], x, y))
    if errs:
        print("LOI: " + "; ".join(errs), file=sys.stderr)
        return 1

    d = a.size or max(28, round(W * 0.045))
    r = d / 2
    font = load_font(int(d * 0.62))
    layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
    g = ImageDraw.Draw(layer)
    for n, x, y in sorted(pts):
        # giu badge nam tron trong anh
        x = min(max(x, r + 2), W - r - 2)
        y = min(max(y, r + 2), H - r - 2)
        g.ellipse([x - r, y - r, x + r, y + r], fill=RED, outline=WHITE, width=max(2, d // 14))
        g.text((x, y), str(n), fill=WHITE, font=font, anchor="mm")
    out = Image.alpha_composite(im, layer).convert("RGB")
    os.makedirs(os.path.dirname(os.path.abspath(a.dst)), exist_ok=True)
    out.save(a.dst, "PNG")
    print(f"OK: {len(pts)} badge -> {a.dst} ({W}x{H}px, badge {int(d)}px)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
