#!/usr/bin/env python3
"""Tự chuẩn bị môi trường chạy kit — agent gọi ở đầu Luồng 1 / Luồng 2, người dùng KHÔNG phải tự cài.

    python3 ensure-env.py --flow 1 [--browser] [--figma] [--check-only] [--out <file.md>]
    python3 ensure-env.py --flow 2 [--figma]

Việc làm (idempotent — đã có thì bỏ qua):
  · Thư viện Python   Luồng 1: openpyxl python-docx matplotlib · Luồng 2: openpyxl
                      thiếu → `python -m pip install --user …` (môi trường externally-managed → thử thêm --break-system-packages)
  · --browser         Playwright + Chromium cho login-site.js / crawl-site.js (Luồng 1 có website)
                      thiếu → `npm i -D playwright` + `npx playwright install chromium`
  · --figma           Figma MCP (vẽ O5 / view CR). Chưa có server nào tên *figma* → `claude mcp add --transport http figma https://mcp.figma.com/mcp`
                      Server có nhưng chưa xác thực → trạng thái NEED_AUTH (phiên đã có tool mcp__*figma* gọi được thì bỏ qua): việc DUY NHẤT user phải làm là `/mcp` → figma → Authenticate
                      (OAuth phải do người bấm; vừa add mà /mcp chưa thấy → khởi động lại Claude Code)

Exit: 0 = đủ (OK / INSTALLED, có thể kèm NEED_AUTH) · 2 = có mục BLOCKED (cài không được) → output phụ thuộc = ❌ Blocked.
Không bao giờ in / đọc credential. Không cần quyền admin (cài --user, npm cục bộ trong folder dự án).
"""
import argparse
import importlib.util
import os
import shutil
import subprocess
import sys

FIGMA_URL = "https://mcp.figma.com/mcp"
PY_DEPS = {  # module import name -> tên gói pip
    1: [("openpyxl", "openpyxl"), ("docx", "python-docx"), ("matplotlib", "matplotlib")],
    2: [("openpyxl", "openpyxl")],
}

rows = []  # (hạng mục, trạng thái, ghi chú)


def run(cmd, timeout=900, cwd=None):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=cwd)
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    except FileNotFoundError:
        return 127, f"không tìm thấy lệnh {cmd[0]}"
    except subprocess.TimeoutExpired:
        return 124, f"quá {timeout}s"


def missing_py(flow):
    importlib.invalidate_caches()
    return [(m, pkg) for m, pkg in PY_DEPS[flow] if importlib.util.find_spec(m) is None]


def ensure_python(flow, check_only):
    miss = missing_py(flow)
    if not miss:
        rows.append(("Python: " + " ".join(p for _, p in PY_DEPS[flow]), "OK", sys.executable))
        return
    pkgs = [p for _, p in miss]
    if check_only:
        rows.append(("Python: " + " ".join(pkgs), "MISSING", "chạy lại không có --check-only để tự cài"))
        return
    base = [sys.executable, "-m", "pip", "install", "--user", "--quiet", *pkgs]
    code, out = run(base)
    if code != 0 and "externally-managed" in out:
        code, out = run(base[:5] + ["--break-system-packages"] + base[5:])
    still = [p for _, p in missing_py(flow)] if code == 0 else pkgs
    if still:
        rows.append(("Python: " + " ".join(still), "BLOCKED", out.strip().splitlines()[-1][:160] if out.strip() else f"pip exit {code}"))
    else:
        rows.append(("Python: " + " ".join(pkgs), "INSTALLED", "pip --user"))


def node_ok(expr, cwd):
    code, out = run(["node", "-e", expr], timeout=60, cwd=cwd)
    return code == 0 and out.strip().endswith("YES")


def ensure_browser(root, check_only):
    if not shutil.which("node") or not shutil.which("npm"):
        rows.append(("Node.js / npm", "BLOCKED", "máy chưa có Node.js — cài Node LTS (nodejs.org) 1 lần, cần quyền máy"))
        return
    has_pw = "try{require.resolve('playwright');console.log('YES')}catch(e){console.log('NO')}"
    has_chromium = ("try{const fs=require('fs');const p=require('playwright').chromium.executablePath();"
                    "console.log(fs.existsSync(p)?'YES':'NO')}catch(e){console.log('NO')}")
    if not node_ok(has_pw, root):
        if check_only:
            rows.append(("Playwright", "MISSING", "chạy lại không có --check-only để tự cài"))
            return
        code, out = run(["npm", "i", "-D", "--no-audit", "--no-fund", "playwright"], cwd=root)
        if code != 0 or not node_ok(has_pw, root):
            rows.append(("Playwright", "BLOCKED", (out.strip().splitlines() or [f"npm exit {code}"])[-1][:160]))
            return
        rows.append(("Playwright", "INSTALLED", "npm i -D playwright (trong folder dự án)"))
    else:
        rows.append(("Playwright", "OK", ""))
    if node_ok(has_chromium, root):
        rows.append(("Chromium cho Playwright", "OK", ""))
        return
    if check_only:
        rows.append(("Chromium cho Playwright", "MISSING", "chạy lại không có --check-only để tự cài"))
        return
    code, out = run(["npx", "playwright", "install", "chromium"], cwd=root)
    if code == 0 and node_ok(has_chromium, root):
        rows.append(("Chromium cho Playwright", "INSTALLED", "npx playwright install chromium"))
    else:
        rows.append(("Chromium cho Playwright", "BLOCKED", (out.strip().splitlines() or [f"exit {code}"])[-1][:160]))


def figma_lines(root):
    code, out = run(["claude", "mcp", "list"], timeout=120, cwd=root)
    if code == 127:
        return None, out
    return [ln for ln in out.splitlines() if "figma" in ln.lower()], out


def ensure_figma(root, check_only):
    lines, raw = figma_lines(root)
    if lines is None:
        rows.append(("Figma MCP", "UNKNOWN",
                     "không gọi được CLI `claude` — agent tự kiểm: có tool mcp__*figma* trong phiên thì coi là OK"))
        return
    if any("connected" in ln.lower() and "fail" not in ln.lower() for ln in lines):
        rows.append(("Figma MCP", "OK", "đã kết nối"))
        return
    if lines:
        rows.append(("Figma MCP", "NEED_AUTH",
                     "có server figma nhưng chưa xác thực. Phiên đã có tool mcp__*figma* gọi được (VD connector claude.ai Figma → whoami) thì coi là OK; "
                     "không có → nhờ user: gõ /mcp → chọn figma → Authenticate (tài khoản Figma có quyền EDIT)"))
        return
    if check_only:
        rows.append(("Figma MCP", "MISSING", "chạy lại không có --check-only để tự thêm"))
        return
    code, out = run(["claude", "mcp", "add", "--transport", "http", "figma", FIGMA_URL], timeout=120, cwd=root)
    if code != 0:
        rows.append(("Figma MCP", "BLOCKED", (out.strip().splitlines() or [f"exit {code}"])[-1][:160]))
        return
    rows.append(("Figma MCP", "NEED_AUTH",
                 "đã tự thêm server figma → nhờ user: gõ /mcp → chọn figma → Authenticate; /mcp chưa thấy figma → khởi động lại Claude Code"))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--flow", type=int, choices=[1, 2], required=True)
    ap.add_argument("--browser", action="store_true", help="cần Playwright + Chromium (Luồng 1 có website)")
    ap.add_argument("--figma", action="store_true", help="cần Figma MCP (O5 / view CR)")
    ap.add_argument("--check-only", action="store_true", help="chỉ kiểm, không cài")
    ap.add_argument("--root", default=os.getcwd(), help="folder dự án (mặc định: thư mục hiện tại)")
    ap.add_argument("--out", help="ghi bảng kết quả ra file .md (VD <ver>/_internal/gates/env.md)")
    a = ap.parse_args()

    ensure_python(a.flow, a.check_only)
    if a.browser:
        ensure_browser(a.root, a.check_only)
    if a.figma:
        ensure_figma(a.root, a.check_only)

    lines = [f"# Môi trường — Luồng {a.flow}", "", "| Hạng mục | Trạng thái | Ghi chú |", "|---|---|---|"]
    lines += [f"| {r[0]} | {r[1]} | {r[2]} |" for r in rows]
    blocked = [r for r in rows if r[1] in ("BLOCKED", "MISSING")]
    need = [r for r in rows if r[1] == "NEED_AUTH"]
    lines += ["", f"{len(rows)} mục · {len(rows) - len(blocked) - len(need)} sẵn sàng · "
              f"{len(need)} cần user xác thực · {len(blocked)} chặn"]
    text = "\n".join(lines)
    print(text)
    if a.out:
        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
        with open(a.out, "w", encoding="utf-8") as f:
            f.write(text + "\n")
    sys.exit(2 if blocked else 0)


if __name__ == "__main__":
    main()
