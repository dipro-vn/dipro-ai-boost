#!/usr/bin/env python3
"""Recon source code — trich route / job / integration. CHI DOC, khong sua gi.

  python3 scan-repo.py <repo_root> --out ./recon [--ext .ts,.js,.py,.php,.rb,.java]

Output:
  recon/code/routes.txt        1 route / dong  (input cho verify-inventory.py --routes)
  recon/code/routes.json       route + file#Lxx  (dung lam Locator cua EV code-ref)
  recon/code/jobs.json         cron / schedule / queue
  recon/code/integrations.json SDK / API ngoai phat hien duoc
  recon/code/stack.json        framework + version doc tu manifest

⚠ Ket qua cua script nay la GOI Y, khong phai ket luan. Moi route o day van phai
duoc doi chieu voi quan sat UI truoc khi ghi Status=Confirmed.
"""
import argparse
import json
import os
import re
import sys

ROUTE_PATTERNS = [
    # express / koa / fastify / nest
    (r"""\b(?:app|router|server)\.(get|post|put|patch|delete|all)\(\s*['"`]([^'"`]+)""", 2, 1),
    (r"""@(Get|Post|Put|Patch|Delete)\(\s*['"`]?([^'"`)]*)""", 2, 1),
    # laravel / symfony
    (r"""Route::(get|post|put|patch|delete|any)\(\s*['"]([^'"]+)""", 2, 1),
    (r"""@Route\(\s*['"]([^'"]+)""", 1, None),
    # django / flask
    (r"""\bpath\(\s*['"]([^'"]*)['"]""", 1, None),
    (r"""@(?:app|bp)\.route\(\s*['"]([^'"]+)""", 1, None),
    # spring
    (r"""@(?:Request|Get|Post|Put|Delete)Mapping\(\s*(?:value\s*=\s*)?['"]([^'"]+)""", 1, None),
    # next.js / nuxt file-based duoc xu ly rieng ben duoi
]

JOB_PATTERNS = [
    r"""@Cron\(\s*['"]([^'"]+)""",
    r"""\bcron\s*[:=]\s*['"]([^'"]+)""",
    r"""schedule\.(?:scheduleJob|every)\(\s*['"]([^'"]+)""",
    r"""(?m)^\s*([\d*/,\-]+\s+[\d*/,\-]+\s+[\d*/,\-]+\s+[\d*/,\-]+\s+[\d*/,\-]+)\s+\S""",
]

INTEGRATION_HINTS = {
    "stripe": "Payment", "paypal": "Payment", "gmo": "Payment",
    "sendgrid": "Email", "nodemailer": "Email", "ses": "Email",
    "firebase": "Push/Auth", "fcm": "Push", "onesignal": "Push",
    "s3": "Storage", "cloudinary": "Storage",
    "redis": "Cache", "elasticsearch": "Search", "algolia": "Search",
    "twilio": "SMS", "slack": "Chat", "line": "Chat",
    "oauth": "Auth", "saml": "Auth", "keycloak": "Auth",
}

SKIP_DIRS = {".git", "node_modules", "vendor", "dist", "build", ".next",
             "__pycache__", ".venv", "venv", "target", "coverage", ".idea"}

MANIFESTS = ["package.json", "composer.json", "requirements.txt", "pom.xml",
             "build.gradle", "Gemfile", "go.mod", "pyproject.toml"]


def walk(root, exts):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if exts and not any(fn.endswith(e) for e in exts):
                continue
            yield os.path.join(dirpath, fn)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("repo")
    ap.add_argument("--out", default="./recon")
    ap.add_argument("--ext", default=".ts,.tsx,.js,.jsx,.py,.php,.rb,.java,.go,.kt")
    a = ap.parse_args()

    exts = [e.strip() for e in a.ext.split(",") if e.strip()]
    outdir = os.path.join(a.out, "code")
    os.makedirs(outdir, exist_ok=True)

    routes, jobs, integrations = [], [], {}
    compiled = [(re.compile(p), gi, mi) for p, gi, mi in ROUTE_PATTERNS]
    job_rx = [re.compile(p) for p in JOB_PATTERNS]

    for fp in walk(a.repo, exts):
        rel = os.path.relpath(fp, a.repo)
        try:
            text = open(fp, encoding="utf8", errors="ignore").read()
        except OSError:
            continue
        lines = text.split("\n")

        for rx, gi, mi in compiled:
            for m in rx.finditer(text):
                line_no = text[:m.start()].count("\n") + 1
                routes.append({
                    "route": m.group(gi),
                    "method": (m.group(mi).upper() if mi else "ANY"),
                    "locator": "%s#L%d" % (rel, line_no),
                })

        for rx in job_rx:
            for m in rx.finditer(text):
                line_no = text[:m.start()].count("\n") + 1
                jobs.append({"schedule": m.group(1).strip(),
                             "locator": "%s#L%d" % (rel, line_no)})

        low = text.lower()
        for key, kind in INTEGRATION_HINTS.items():
            if key in low:
                integrations.setdefault(key, {"kind": kind, "hits": []})
                if len(integrations[key]["hits"]) < 3:
                    idx = low.find(key)
                    integrations[key]["hits"].append(
                        "%s#L%d" % (rel, text[:idx].count("\n") + 1))

        # next.js / nuxt file-based routing
        if re.search(r"(^|/)(pages|app)/", rel.replace(os.sep, "/")) and \
                fn_ext_ok(rel) and "_" not in os.path.basename(rel)[:1]:
            r = file_route(rel)
            if r:
                routes.append({"route": r, "method": "PAGE", "locator": rel + "#L1"})

        del lines

    # stack tu manifest
    stack = {}
    for mf in MANIFESTS:
        p = os.path.join(a.repo, mf)
        if os.path.isfile(p):
            try:
                if mf.endswith(".json"):
                    d = json.load(open(p, encoding="utf8"))
                    stack[mf] = {k: d.get(k) for k in ("name", "dependencies", "devDependencies")
                                 if k in d}
                else:
                    stack[mf] = open(p, encoding="utf8", errors="ignore").read()[:4000]
            except Exception as e:
                stack[mf] = "khong doc duoc: %s" % e

    uniq = {}
    for r in routes:
        uniq.setdefault(r["route"], r)
    routes = sorted(uniq.values(), key=lambda x: x["route"])

    W = lambda n, s: open(os.path.join(outdir, n), "w", encoding="utf8").write(s)
    W("routes.txt", "\n".join(r["route"] for r in routes) + "\n")
    W("routes.json", json.dumps(routes, indent=2, ensure_ascii=False))
    W("jobs.json", json.dumps(jobs, indent=2, ensure_ascii=False))
    W("integrations.json", json.dumps(integrations, indent=2, ensure_ascii=False))
    W("stack.json", json.dumps(stack, indent=2, ensure_ascii=False)[:200000])

    print(json.dumps({"routes": len(routes), "jobs": len(jobs),
                      "integrations": sorted(integrations), "out": outdir},
                     indent=2, ensure_ascii=False))
    print("\nLUU Y: day la GOI Y tu code. Route chua quan sat duoc tren UI "
          "phai ghi Status='To verify', khong duoc ghi 'Confirmed'.", file=sys.stderr)
    return 0


def fn_ext_ok(rel):
    return rel.endswith((".tsx", ".jsx", ".vue", ".js", ".ts"))


def file_route(rel):
    p = rel.replace(os.sep, "/")
    m = re.search(r"(?:^|/)(?:pages|app)/(.*)$", p)
    if not m:
        return None
    r = m.group(1)
    r = re.sub(r"\.(tsx|jsx|vue|js|ts)$", "", r)
    r = re.sub(r"/(index|page)$", "", r)
    r = re.sub(r"\[([^\]]+)\]", r":\1", r)
    if any(x in r for x in ("_app", "_document", "api/_", "components/")):
        return None
    return "/" + r.lstrip("/")


if __name__ == "__main__":
    sys.exit(main())
