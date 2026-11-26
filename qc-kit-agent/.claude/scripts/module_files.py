#!/usr/bin/env python3
"""
Quy ước tên file và version của một module (xem skill `rbt_manual_testing`, mục "Quy ước file và version").

Trong thư mục module `testing/<module>/` (tên module = tên thư mục):
    <module>-analysis-vN.md
    <module>-testcases-vN.md
    <module>-testcases-vN.xlsx
    <module>-review-vN.md             (sản phẩm phái sinh của /review-tcs, N = version TC được review)
    <module>-review-detail-vN.md      (phụ lục của review-vN: bằng chứng, vế, trạng thái tiêu chí)
    <module>-automation-report-vN.md  (sản phẩm phái sinh của /gen-automation, N = version TC được chạy)
    <module>-uicompare-vN.md          (sản phẩm phái sinh của /ui-compare, N = version TC mới nhất của module, v1 nếu chưa có TC)
    <module>-spec-vN.md               (bản chụp spec dạng text mà /update-tcs dùng cho version N)
N = số lần spec đổi. Tên cũ vẫn đọc được: `analysis.md`, `test-cases.md`,
`test-cases.xlsx`, `automation-report.md` tính là v1; `test-cases_vN.*` / `test-cases-vN.*` tính là vN.
Cùng N thì tên mới được ưu tiên hơn tên cũ.

Lệnh (`python3 -I module_files.py ...`):
  info <dir>
      In file analysis / testcases (md, xlsx) mới nhất và version lớn nhất của module.
  latest <dir> analysis|testcases|review|review-detail|automation-report|uicompare|spec [md|xlsx]
      In đường dẫn file mới nhất của loại đó. Không có thì không in gì, exit code 1.
      Không nêu đuôi file: lấy đuôi `.md` (analysis luôn là `.md`).
  next-version <dir>
      In số version kế tiếp = (version lớn nhất của mọi file analysis và testcases) + 1,
      hoặc 1 nếu module chưa có file nào. review và automation-report KHÔNG tính vào
      (chúng chỉ đi theo version của TC). uicompare cũng không tính.
  path <dir> analysis|testcases|review|review-detail|automation-report|uicompare|spec <N> [md|xlsx]
      In đường dẫn đúng quy ước cho version N (không kiểm tra file có tồn tại hay không).
  version <file>
      In version suy ra từ tên file (hậu tố -vN / _vN ở cuối tên, VD `HRD_Testcase_v2.xlsx` -> 2).
      Không có hậu tố -> 1.

  check <dir>
      Cảnh báo (mỗi dòng một vấn đề, exit code 1 nếu có): xlsx và md testcases mới nhất lệch
      version; analysis mới hơn testcases; file có dạng version nhưng không đúng quy ước
      (VD `analysis-v1.1.md`, `*-testcases-v2-final.md`). Không có vấn đề thì in `OK`.

Chỉ nhìn các file nằm trực tiếp trong <dir>, không đi vào thư mục con.
"""
import re
import sys
from pathlib import Path

KINDS = ("analysis", "testcases", "review", "review-detail", "automation-report", "uicompare", "spec")
CORE = ("analysis", "testcases")  # quyết định version của module
CANON = re.compile(r"^(?P<mod>.+)-(?P<kind>analysis|testcases|review-detail|review|automation-report|uicompare|spec)-v(?P<n>\d+)\.(?P<ext>md|xlsx)$", re.I)
LEGACY_REPORT = re.compile(r"^automation-report\.md$", re.I)
LOOKS_VERSIONED = re.compile(r"(analysis|testcases?|test-cases|review|automation-report|uicompare|spec).*v\d", re.I)
LEGACY_ANALYSIS = re.compile(r"^analysis\.md$", re.I)
LEGACY_TCS = re.compile(r"^test-cases(?:[_-]v(?P<n>\d+))?\.(?P<ext>md|xlsx)$", re.I)


def classify(p):
    """Trả (kind, n, ext, canonical) hoặc None."""
    name = p.name
    m = CANON.match(name)
    if m:
        return m["kind"].lower(), int(m["n"]), m["ext"].lower(), True
    if LEGACY_ANALYSIS.match(name):
        return "analysis", 1, "md", False
    if LEGACY_REPORT.match(name):
        return "automation-report", 1, "md", False
    m = LEGACY_TCS.match(name)
    if m:
        return "testcases", int(m["n"] or 1), m["ext"].lower(), False
    return None


def scan(d):
    files = []
    for p in sorted(Path(d).iterdir()):
        if p.is_file():
            c = classify(p)
            if c:
                files.append((p,) + c)
    return files


def latest(d, kind, ext="md"):
    best = None
    for p, k, n, e, canon in scan(d):
        if k == kind and e == ext:
            key = (n, canon)
            if best is None or key > best[0]:
                best = (key, p)
    return best[1] if best else None


def max_version(d):
    return max((n for _, k, n, _, _ in scan(d) if k in CORE), default=0)


def module_name(d):
    return Path(d).resolve().name


def build_path(d, kind, n, ext="md"):
    return Path(d) / f"{module_name(d)}-{kind}-v{n}.{ext}"


def file_version(f):
    m = re.search(r"[-_]v(\d+)$", Path(f).stem, re.I)
    return int(m.group(1)) if m else 1


def check(d):
    problems = []
    md, xl = latest(d, "testcases", "md"), latest(d, "testcases", "xlsx")
    vmd = classify(md)[1] if md else None
    vxl = classify(xl)[1] if xl else None
    if vmd and vxl and vmd != vxl:
        problems.append(f"testcases md mới nhất là v{vmd} nhưng xlsx mới nhất là v{vxl}")
    an = latest(d, "analysis")
    if an and vmd and classify(an)[1] > vmd:
        problems.append(f"analysis v{classify(an)[1]} mới hơn testcases v{vmd} (TC chưa theo kịp spec?)")
    for p in sorted(Path(d).iterdir()):
        if p.is_file() and classify(p) is None and LOOKS_VERSIONED.search(p.name):
            problems.append(f"tên không đúng quy ước, script bỏ qua: {p.name}")
    print("\n".join(problems) if problems else "OK")
    return 1 if problems else 0


def usage():
    print(__doc__)
    sys.exit(2)


def main(argv):
    if len(argv) < 2:
        usage()
    cmd = argv[1]
    if cmd == "version" and len(argv) == 3:
        print(file_version(argv[2]))
        return 0
    if len(argv) < 3:
        usage()
    d = argv[2]
    if not Path(d).is_dir():
        print(f"Không phải thư mục: {d}", file=sys.stderr)
        return 2
    if cmd == "info":
        for kind in KINDS:
            for ext in ("md", "xlsx"):
                if kind != "testcases" and ext == "xlsx":
                    continue
                p = latest(d, kind, ext)
                print(f"{kind}.{ext}: {p if p else '(chưa có)'}")
        print(f"version lớn nhất: {max_version(d)}")
        return 0
    if cmd == "latest" and len(argv) in (4, 5):
        kind = argv[3]
        if kind not in KINDS:
            usage()
        p = latest(d, kind, argv[4].lower() if len(argv) == 5 else "md")
        if p:
            print(p)
            return 0
        return 1
    if cmd == "check" and len(argv) == 3:
        return check(d)
    if cmd == "next-version" and len(argv) == 3:
        print(max_version(d) + 1)
        return 0
    if cmd == "path" and len(argv) in (5, 6):
        kind = argv[3]
        if kind not in KINDS or not argv[4].isdigit():
            usage()
        print(build_path(d, kind, int(argv[4]), argv[5].lower() if len(argv) == 6 else "md"))
        return 0
    usage()


if __name__ == "__main__":
    sys.exit(main(sys.argv))
