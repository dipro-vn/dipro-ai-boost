#!/usr/bin/env python3
"""Ve so do flow tong quan tu flow.json -> PNG (chen vao chuong 7 cua Overview O6).

  python3 render-flow.py <_internal>/flow/flow.json --out <_internal>/flow/flow.png [--width 12] [--dpi 150]

Schema flow.json + quy tac ref: xem verify-flow-png.py (gate V5).

Layout theo lop: node.row = so hang (0 tren cung). Trong 1 hang, node xep theo thu tu
xuat hien. Edge ve mui ten thang. Khong phu thuoc graphviz — chi can matplotlib.
"""
import argparse
import json
import sys

KIND_STYLE = {
    "actor":    dict(fc="#FFFFFF", ec="#222222"),
    "site":     dict(fc="#F2F6FC", ec="#222222"),
    "screen":   dict(fc="#F2F6FC", ec="#222222"),
    "api":      dict(fc="#FFFFFF", ec="#222222"),
    "db":       dict(fc="#F7F7F7", ec="#222222"),
    "external": dict(fc="#FFFFFF", ec="#666666"),
    "batch":    dict(fc="#FFFFFF", ec="#666666"),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("flow")
    ap.add_argument("--out", required=True)
    ap.add_argument("--width", type=float, default=12.0)
    ap.add_argument("--dpi", type=int, default=150)
    a = ap.parse_args()

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
    except ImportError:
        print("Thieu matplotlib. Chay: pip install matplotlib", file=sys.stderr)
        return 2

    flow = json.load(open(a.flow, encoding="utf8"))
    nodes = flow.get("nodes", [])
    edges = flow.get("edges", [])
    if not nodes:
        print("flow.json khong co node", file=sys.stderr)
        return 1

    rows = {}
    for n in nodes:
        rows.setdefault(int(n.get("row", 0)), []).append(n)
    n_rows = max(rows) + 1
    n_cols = max(len(v) for v in rows.values())

    BW, BH = 2.6, 1.0
    GX, GY = 1.2, 1.4
    pos = {}
    for r, items in rows.items():
        total = len(items) * BW + (len(items) - 1) * GX
        x0 = -total / 2
        for i, n in enumerate(items):
            cx = x0 + i * (BW + GX) + BW / 2
            cy = -r * (BH + GY)
            pos[n["id"]] = (cx, cy)

    fig_w = a.width
    fig_h = max(3.0, n_rows * (BH + GY) * 0.9)
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    ax.set_axis_off()

    for n in nodes:
        cx, cy = pos[n["id"]]
        st = KIND_STYLE.get(n.get("kind"), KIND_STYLE["api"])
        ax.add_patch(FancyBboxPatch(
            (cx - BW / 2, cy - BH / 2), BW, BH,
            boxstyle="round,pad=0.02,rounding_size=0.12",
            linewidth=1.6, **st))
        ax.text(cx, cy, n.get("label", n["id"]), ha="center", va="center",
                fontsize=10, wrap=True)

    for e in edges:
        if e.get("from") not in pos or e.get("to") not in pos:
            continue
        x1, y1 = pos[e["from"]]
        x2, y2 = pos[e["to"]]
        dx, dy = x2 - x1, y2 - y1
        if abs(dy) < 0.01:
            sx, sy = x1 + BW / 2, y1
            tx, ty = x2 - BW / 2, y2
        elif abs(dx) < 0.01:
            sx, sy = x1, y1 - BH / 2
            tx, ty = x2, y2 + BH / 2
        else:
            sx, sy = x1 + (BW / 2 if dx > 0 else -BW / 2), y1
            tx, ty = x2, y2 + (BH / 2 if dy < 0 else -BH / 2)
        ax.add_patch(FancyArrowPatch((sx, sy), (tx, ty),
                                     arrowstyle="-|>", mutation_scale=14,
                                     linewidth=1.3, color="#222222",
                                     shrinkA=0, shrinkB=0))
        if e.get("label"):
            ax.text((sx + tx) / 2, (sy + ty) / 2 + 0.12, e["label"],
                    ha="center", fontsize=8, color="#444444")

    if flow.get("title"):
        ax.set_title(flow["title"], fontsize=15, fontweight="bold", pad=18)

    xs = [p[0] for p in pos.values()]
    ys = [p[1] for p in pos.values()]
    ax.set_xlim(min(xs) - BW, max(xs) + BW)
    ax.set_ylim(min(ys) - BH, max(ys) + BH)
    ax.set_aspect("equal")
    fig.tight_layout()
    fig.savefig(a.out, dpi=a.dpi, bbox_inches="tight", facecolor="white")
    print("Da ve %s (%d node, %d edge)" % (a.out, len(nodes), len(edges)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
