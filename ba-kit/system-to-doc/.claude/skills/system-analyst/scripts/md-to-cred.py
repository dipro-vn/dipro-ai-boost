#!/usr/bin/env python3
"""Chuyen inputs/credentials.local.md -> .auth/credentials.local.env (format login-site.js nhan).

  python3 md-to-cred.py <inputs/credentials.local.md> <.auth/credentials.local.env> \
      --site WEB-01 --admin-section "Admin URL:" --role Super\\ Admin=super_admin ... \
      --site WEB-02 --user-section "User URL:" --role User=user ...

Nhan dang trong md:
  - "Admin URL: https://..."  /  "User URL: https://..."
  - "HTTP Basic Auth ...: <user> / <pass>"
  - Bang "| Vai tro | Email | Password |" nam ngay sau URL cua site.
Script ghi env, chmod 600, ENV=TEST. Agent khong doc gia tri; script in dong summary.
"""
import argparse, os, re, sys


def section_rows(text, header_rx, next_rx):
    """Doc bang markdown giua header_rx va next_rx. -> list[(role, email, pw)]."""
    h = re.search(header_rx, text, re.M)
    if not h: return []
    tail = text[h.end():]
    nxt = re.search(next_rx, tail, re.M) if next_rx else None
    block = tail[:nxt.start()] if nxt else tail
    rows = []
    for ln in block.splitlines():
        cells = [c.strip() for c in ln.split("|")]
        if len(cells) < 5: continue
        role, email, pw = cells[1], cells[2], cells[3]
        if not role or role.lower().startswith("vai") or set(role) <= set("- "): continue
        if "@" not in email: continue
        rows.append((role, email, pw))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src"); ap.add_argument("dst")
    ap.add_argument("--site", action="append", required=True, help="WEB-01|WEB-02")
    ap.add_argument("--url-key", action="append", required=True, help='"Admin URL:" / "User URL:"')
    ap.add_argument("--role-map", action="append", default=[],
                    help='"<site>:<role trong md>=<role script>" (vd WEB-01:Super Admin=super_admin)')
    a = ap.parse_args()
    assert len(a.site) == len(a.url_key)
    text = open(a.src, encoding="utf8").read()
    out = ["# auto-sinh tu %s (script, agent khong doc)" % a.src]
    # Basic Auth: lay cap "<user> / <pass>" sau "HTTP Basic Auth"
    bu = bp = None
    m = re.search(r"HTTP Basic Auth[^\n:]*:\s*([^\s/]+)\s*/\s*([^\s]+)", text)
    if m: bu, bp = m.group(1).strip(), m.group(2).strip()
    url_key_rx = [re.escape(k) for k in a.url_key]
    for i, s in enumerate(a.site):
        um = re.search(r"^%s\s*(https?://\S+)" % url_key_rx[i], text, re.M)
        if not um: sys.exit("khong tim thay '%s' trong %s" % (a.url_key[i], a.src))
        out += ["%s.URL=%s" % (s, um.group(1).strip()), "%s.ENV=TEST" % s]
        if bu: out.append("%s.BASIC_USER=%s" % (s, bu))
        if bp: out.append("%s.BASIC_PASS=%s" % (s, bp))
    role_map = {}   # {site: {md role: script role}}
    for tok in a.role_map:
        site, rest = tok.split(":", 1); md_role, sc_role = rest.split("=", 1)
        role_map.setdefault(site, {})[md_role.strip()] = sc_role.strip()
    for i, s in enumerate(a.site):
        nxt = url_key_rx[i+1] if i+1 < len(a.site) else r"\Z"
        rows = section_rows(text, r"^%s" % url_key_rx[i], nxt)
        for md_role, email, pw in rows:
            sc_role = role_map.get(s, {}).get(md_role)
            if not sc_role: continue
            out += ["%s.%s.USER=%s" % (s, sc_role, email), "%s.%s.PASS=%s" % (s, sc_role, pw)]
    os.makedirs(os.path.dirname(a.dst), exist_ok=True)
    with open(a.dst, "w") as f: f.write("\n".join(out) + "\n")
    os.chmod(a.dst, 0o600)
    print("Da ghi %s (%d dong, 0600)" % (a.dst, len(out)))
if __name__ == "__main__": main()
