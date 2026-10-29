#!/usr/bin/env python3
"""O8 — Huong dan chay local + moi truong cho dev moi (R12 · D7). CHI DOC repo.

  python3 build-devsetup.py --repo REPO-01=/path/fe --repo REPO-02=/path/api [--inventory <_internal>/inventory.xlsx] \
          --system <sys> --version ver<N> --out <ver>/08_DevSetup/DevSetup_<sys>_ver<N>.md

Gom tu dong (moi dong ghi file nguon <REPO-xx>:<path>):
  1 Repo va cong cu  : package.json (engines, package manager theo lockfile) · composer / requirements / pyproject /
                       Gemfile / go.mod · README (chi duong dan)
  2 Cai dat va chay  : lenh cai + TEN script (npm run <ten>) · target Makefile — KHONG chep than script
  3 Database local   : service trong docker-compose*.yml (image + port), khong chep `environment:`
  4 Cau hinh         : CHI TEN key trong .env.example / .env.sample / .env.template (KHONG BAO GIO mo .env that)
  5 Moi truong       : hau to cua file env mau / docker-compose.<env>.yml / workflow
  6 Pipeline         : Dockerfile*, docker-compose*, .github/workflows/*, .gitlab-ci.yml, Jenkinsfile, bitbucket-pipelines,
                       buildspec, serverless, appspec (ten file + dong `name:` dau tien)
  7 Lich batch       : 07_API Kind=BATCH cua inventory (lich + handler + code-ref)
Cho khong tim thay -> "Cần xác nhận — <can hoi gi>". Gate: verify-devsetup.py.
"""
import argparse
import importlib.util
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import inv_schema as S  # noqa: E402

_spec = importlib.util.spec_from_file_location("scan_repo", os.path.join(HERE, "scan-repo.py"))
SR = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(SR)

ENV_SAMPLE_RX = re.compile(r"^\.env(\.[\w-]+)*\.(example|sample|template)$|^\.env\.(example|sample|template)(\.[\w-]+)*$")
KEY_RX = re.compile(r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=")
COMPOSE_RX = re.compile(r"^(docker-)?compose(\.[\w-]+)?\.ya?ml$")
CI_RX = re.compile(r"^(Dockerfile(\.[\w-]+)?|Jenkinsfile|\.gitlab-ci\.ya?ml|bitbucket-pipelines\.yml|buildspec\.ya?ml|"
                   r"serverless\.ya?ml|appspec\.ya?ml|app\.ya?ml|cloudbuild\.ya?ml|Procfile)$")
LOCKS = (("pnpm-lock.yaml", "pnpm install"), ("yarn.lock", "yarn install"), ("package-lock.json", "npm ci"),
         ("bun.lockb", "bun install"))
OTHER = (("composer.json", "composer install"), ("requirements.txt", "pip install -r requirements.txt"),
         ("pyproject.toml", "pip install -e . (hoặc poetry install)"), ("Gemfile", "bundle install"),
         ("go.mod", "go mod download"), ("pom.xml", "mvn install"), ("build.gradle", "./gradlew build"))
MAX_DEPTH = 3
NC = S.NEED_CONFIRM


def files(root):
    """(rel, name) — bo SKIP_DIRS, toi da MAX_DEPTH cap; file nhay cam va .env that khong bao gio tra ve."""
    for dp, dns, fns in os.walk(root):
        depth = os.path.relpath(dp, root).count(os.sep) + (0 if dp == root else 1)
        dns[:] = sorted(d for d in dns if d not in SR.SKIP_DIRS and (d == ".github" or d == "workflows"
                                                                      or not d.startswith(".")) and depth < MAX_DEPTH)
        for fn in sorted(fns):
            if fn.startswith(".env") and not ENV_SAMPLE_RX.match(fn):
                continue   # .env that: khong mo (rules/SECURITY.md)
            yield os.path.relpath(os.path.join(dp, fn), root).replace(os.sep, "/"), fn


def read(root, rel):
    try:
        return open(os.path.join(root, rel), encoding="utf8", errors="replace").read()
    except OSError:
        return ""


def scan(rid, root):
    r = {"tools": [], "install": [], "run": [], "db": [], "keys": [], "envs": set(), "ci": []}
    all_files = list(files(root))
    names = {rel for rel, _ in all_files}
    ref = lambda rel: "%s:%s" % (rid, rel)
    if "package.json" in names:
        try:
            pj = json.loads(read(root, "package.json"))
        except ValueError:
            pj = {}
        eng = pj.get("engines") or {}
        r["tools"].append(("Node.js %s" % eng.get("node", "— (package.json không ghi engines.node)"), ref("package.json")))
        inst = next((cmd for lock, cmd in LOCKS if lock in names), "npm install")
        r["install"].append((inst, ref("package.json")))
        mgr = {"npm": "npm run", "yarn": "yarn", "pnpm": "pnpm", "bun": "bun run"}[inst.split()[0]]
        for name in (pj.get("scripts") or {}):
            r["run"].append(("%s %s" % (mgr, name), ref("package.json")))
    for f, cmd in OTHER:
        if f in names:
            r["tools"].append((f, ref(f)))
            r["install"].append((cmd, ref(f)))
    if "Makefile" in names:
        for t in re.findall(r"^([A-Za-z][\w-]*):(?!=)", read(root, "Makefile"), re.M):
            r["run"].append(("make %s" % t, ref("Makefile")))
    for rel, fn in all_files:
        if fn.lower().startswith("readme"):
            r["tools"].append(("README (đọc phần cài đặt)", ref(rel)))
        if ENV_SAMPLE_RX.match(fn):
            for line in read(root, rel).splitlines():
                m = KEY_RX.match(line)
                if m:
                    r["keys"].append((m.group(1), ref(rel)))
            env = [p for p in fn.split(".")[2:] if p not in ("example", "sample", "template")]
            r["envs"].update(env)
        if COMPOSE_RX.match(fn):
            m = re.match(r"^(?:docker-)?compose\.([\w-]+)\.ya?ml$", fn)
            if m:
                r["envs"].add(m.group(1))
            r["ci"].append((rel, ""))
            svc = None
            in_services = False
            for line in read(root, rel).splitlines():
                if re.match(r"^services:\s*$", line):
                    in_services = True
                    continue
                if in_services and re.match(r"^\S", line):
                    in_services = False
                mm = re.match(r"^  ([\w.-]+):\s*$", line) if in_services else None
                if mm:
                    svc = mm.group(1)
                im = re.match(r"^\s+image:\s*['\"]?([^'\"\s]+)", line)
                if in_services and svc and im:
                    r["db"].append((svc, im.group(1), ref(rel)))
                pm = re.match(r"^\s+-\s*['\"]?(\d+(?::\d+)?)['\"]?\s*$", line)
                if in_services and svc and pm and r["db"] and r["db"][-1][0] == svc:
                    r["db"][-1] = (svc, r["db"][-1][1] + " · port " + pm.group(1), r["db"][-1][2])
        if CI_RX.match(fn) or rel.startswith(".github/workflows/"):
            nm = re.search(r"^name:\s*['\"]?([^'\"\n]+)", read(root, rel), re.M)
            r["ci"].append((rel, nm.group(1).strip() if nm else ""))
            if rel.startswith(".github/workflows/"):
                r["envs"].update(re.findall(r"^\s+environment:\s*['\"]?([\w-]+)", read(root, rel), re.M))
    return r


def table(head, rows):
    out = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    out += ["| " + " | ".join(str(c).replace("|", "/") for c in row) + " |" for row in rows]
    return out


SECTIONS = ["## 1. Repo và công cụ", "## 2. Cài đặt và chạy", "## 3. Database local", "## 4. Cấu hình (chỉ tên key)",
            "## 5. Môi trường", "## 6. Pipeline / deploy", "## 7. Lịch batch"]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", action="append", required=True, help="REPO-01=/path")
    ap.add_argument("--inventory", default=None)
    ap.add_argument("--system", required=True)
    ap.add_argument("--version", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    repos = []
    for spec in a.repo:
        rid, _, path = spec.partition("=")
        if not re.match(r"^REPO-\d{2,}$", rid) or not os.path.isdir(path):
            print("--repo phai dang REPO-01=/path (thu muc ton tai): %s" % spec, file=sys.stderr)
            return 1
        repos.append((rid, scan(rid, path)))
    batches = []
    if a.inventory:
        batches = [r for r in S.load(a.inventory).get("07_API", []) if r.get("Kind") == "BATCH"]

    L = ["# Hướng dẫn chạy local và môi trường — %s %s" % (a.system, a.version), "",
         "> Người đọc: dev mới vào dự án. Máy tự gom từ source (chỉ đọc). Cấu hình chỉ ghi **tên key** — giá trị "
         "lấy từ Tech Lead / secret manager, không bao giờ ghi vào file này.", ""]
    L += [SECTIONS[0], ""] + table(["Repo", "Công cụ / file", "Nguồn"],
                                   [(rid, t, src) for rid, r in repos for t, src in r["tools"]]
                                   or [("—", NC + " — repo không có file khai báo công cụ", "—")]) + [""]
    L += [SECTIONS[1], ""] + table(["Repo", "Bước", "Lệnh", "Nguồn"],
                                   [(rid, "Cài", c, src) for rid, r in repos for c, src in r["install"]]
                                   + [(rid, "Chạy", "`%s`" % c, src) for rid, r in repos for c, src in r["run"]]
                                   or [("—", "—", NC + " — không thấy lệnh cài / chạy", "—")]) + [""]
    L += [SECTIONS[2], ""] + table(["Repo", "Service", "Image · port", "Nguồn"],
                                   [(rid, s_, im, src) for rid, r in repos for s_, im, src in r["db"]]
                                   or [("—", "—", NC + " — không có docker-compose; hỏi Tech Lead cách dựng DB local", "—")]) + [""]
    L += [SECTIONS[3], ""] + table(["Repo", "Tên key", "Nguồn"],
                                   [(rid, "`%s`" % k, src) for rid, r in repos for k, src in r["keys"]]
                                   or [("—", NC + " — không có .env.example; hỏi Tech Lead danh sách key", "—")]) + [""]
    envs = sorted({e for _, r in repos for e in r["envs"]})
    L += [SECTIONS[4], "", "- " + (", ".join(envs) if envs else NC + " — không thấy tên môi trường trong file mẫu / pipeline"), ""]
    L += [SECTIONS[5], ""] + table(["Repo", "File", "Tên"],
                                   [(rid, f, n or "—") for rid, r in repos for f, n in r["ci"]]
                                   or [("—", NC + " — không thấy file pipeline; hỏi cách deploy", "—")]) + [""]
    L += [SECTIONS[6], ""] + table(["Batch", "Lịch", "Xử lý", "Nguồn"],
                                   [(b.get("API ID"), b.get("Path / Schedule") or NC, b.get("Handler") or NC,
                                     b.get("Evidence") or NC) for b in batches]
                                   or [("—", "—", "Không thấy batch trong source đã khảo sát" if a.inventory
                                        else NC + " — chưa truyền --inventory", "—")]) + [""]
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    open(a.out, "w", encoding="utf8").write("\n".join(L))
    print(json.dumps({"out": a.out, "repos": len(repos), "keys": sum(len(r["keys"]) for _, r in repos),
                      "envs": envs, "batches": len(batches)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
