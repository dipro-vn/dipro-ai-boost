#!/usr/bin/env python3
"""GATE V-DEV — O8 DevSetup md (R12 · D7).

  python3 verify-devsetup.py <ver>/08_Huong_dan_chay_local/DevSetup_<sys>_ver<N>.md [--out report.md]

Chan: thieu muc 1-7 · con chu cu · H06 (detect-pii.js --scan) bat duoc PII / credential · co dang KEY=gia tri
hoac `KEY: gia tri` cho key cua muc 4 · nguon cua muc 4 khong phai file mau (.env.example/.sample/.template) ·
o trong trong bang.
"""
import argparse
import importlib.util
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import inv_schema as S  # noqa: E402
from gate_report import Gate  # noqa: E402

_spec = importlib.util.spec_from_file_location("dev", os.path.join(HERE, "build-devsetup.py"))
DEV = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(DEV)
PII = os.path.abspath(os.path.join(HERE, "..", "..", "..", "hooks", "detect-pii.js"))
ASSIGN_RX = re.compile(r"\b([A-Z][A-Z0-9_]{2,})\s*=\s*[^\s|`]")


def section(lines, head):
    out, grab = [], False
    for ln in lines:
        if ln.startswith("## "):
            grab = ln.strip() == head
            continue
        if grab:
            out.append(ln)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("md")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    text = open(a.md, encoding="utf8").read()
    lines = text.splitlines()
    g = Gate("GATE V-DEV — DevSetup (O8)")

    g.check(1, "Du muc 1-7", [h for h in DEV.SECTIONS if h not in lines])
    g.check(2, "Khong con chu '%s'" % S.LEGACY_WORD, ["md"] if S.has_legacy(text) else [])
    p = subprocess.run(["node", PII, "--scan", a.md], capture_output=True, text=True)
    g.check(3, "H06 detect-pii --scan sach (khong PII / credential)",
            [] if p.returncode == 0 else [ln.strip() for ln in p.stdout.splitlines() if ln.strip()][:5])
    rows = [ln for ln in section(lines, DEV.SECTIONS[3]) if ln.startswith("| ") and not ln.startswith("| Repo")]
    keys = [re.sub(r"[`\s]", "", r.split("|")[2]) for r in rows]
    bad = ["%s=..." % m.group(1) for m in ASSIGN_RX.finditer(text)]
    bad += ["%s: <gia tri>" % k for k in keys if k and re.search(r"\b%s\b\s*:\s*\S" % re.escape(k), text)]
    g.check(4, "Chi TEN key cau hinh — khong co gia tri (KEY=..., KEY: ...)", bad)
    srcs = [r.split("|")[3].strip() for r in rows]
    g.check(5, "Nguon muc 4 chi la file mau (.env.example / .sample / .template)",
            [s_ for s_ in srcs if s_ != "—" and not DEV.ENV_SAMPLE_RX.match(os.path.basename(s_.split(":", 1)[-1]))])
    blanks = [ln for ln in lines if ln.startswith("|") and re.search(r"\|\s*\|", ln) and not ln.startswith("|---")]
    g.check(6, "Khong o trong trong bang", blanks)
    return g.emit(a.out)


if __name__ == "__main__":
    sys.exit(main())
