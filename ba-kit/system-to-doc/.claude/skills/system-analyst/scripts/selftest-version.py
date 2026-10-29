#!/usr/bin/env python3
"""Self-test version-tool.py (R5 · D3 · D4): khao sat lan dau luon la ver1, ver<N+1> chi qua promote.

  python3 selftest-version.py [--keep]

Ca: 3 lan `next` khong CR -> cung ver1 · snapshot giu file cu trong _internal/history · CR moi dat ten
CR-<id>_<DDMMYY>_<slug> + tro baseline -> ver1 khoa (next exit 3) · promote thieu --coded bi tu choi ·
promote -> ver2 · sau promote next -> ver2 (CR-001 khong con open) · doc duoc layout cu ver<N>_..._CR-...
In `N ca · N PASS`. Exit 0 tat ca PASS · 1 co ca FAIL.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
TOOL = os.path.join(HERE, "version-tool.py")


def vt(*args):
    p = subprocess.run([sys.executable, TOOL] + list(args), capture_output=True, text=True)
    try:
        return p.returncode, json.loads(p.stdout) if p.stdout.strip() else {}, p.stderr
    except ValueError:
        return p.returncode, {"_raw": p.stdout}, p.stderr


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--keep", action="store_true")
    a = ap.parse_args()
    tmp = tempfile.mkdtemp(prefix="selftest-version-")
    res = []

    def case(name, ok, detail=""):
        res.append(bool(ok))
        print("%s  %s%s" % ("PASS" if ok else "FAIL", name, ("  — " + str(detail)[:300]) if detail and not ok else ""))

    try:
        out = os.path.join(tmp, "outputs")
        os.makedirs(out)
        # --- 3 lan next khong CR -> cung ver1
        folders = []
        for i, d in enumerate(("011026", "051026", "091026")):
            rc, j, err = vt("next", "--outputs", out, "--slug", "baseline", "--date", d, "--create")
            folders.append((rc, j.get("folder"), j.get("reuse")))
        case("3 lan next khong CR -> cung ver1_011026_baseline (lan 2-3 reuse)",
             [f[1] for f in folders] == ["ver1_011026_baseline"] * 3 and [f[2] for f in folders] == [False, True, True]
             and all(f[0] == 0 for f in folders) and len(os.listdir(out)) == 1, folders)
        v1 = os.path.join(out, "ver1_011026_baseline")

        # --- snapshot truoc khi ghi de
        doc = os.path.join(v1, "02_API", "API_Doc_T_ver1.xlsx")
        os.makedirs(os.path.dirname(doc))
        open(doc, "w").write("ban cu")
        rc, j, _ = vt("snapshot", "--ver", v1, "--files", "02_API/API_Doc_T_ver1.xlsx")
        open(doc, "w").write("ban moi")
        kept = os.path.join(j.get("dir") or "", "02_API", "API_Doc_T_ver1.xlsx")
        case("snapshot -> _internal/history/<YYYYMMDD-HHMM>/ giu ban cu, file moi ghi de tai cho",
             rc == 0 and j.get("files") == 1 and os.path.isfile(kept) and open(kept).read() == "ban cu"
             and open(doc).read() == "ban moi" and os.sep + os.path.join("_internal", "history") + os.sep in kept, j)
        rc, j2, _ = vt("snapshot", "--ver", v1)
        case("snapshot mac dinh (moi file) khong chep lai history cu",
             rc == 0 and j2.get("dir") != j.get("dir") and j2.get("files") == 2   # API doc + version-meta.json
             and not os.path.isdir(os.path.join(j2.get("dir") or "", "_internal", "history")), j2)
        rc, j3, _ = vt("snapshot", "--ver", v1, "--files", "../outside.txt", doc)
        case("snapshot bo duong dan ngoai folder version, nhan duong dan tuyet doi trong folder",
             rc == 0 and j3.get("files") == 1, j3)
        rc, ctx, _ = vt("context", "--outputs", out, "--flow", "1")
        case("context: chua CR -> flow1_action rerun_in_place vao ver1, co history",
             ctx.get("suggest", {}).get("flow1_action") == "rerun_in_place"
             and ctx["suggest"].get("flow1_target") == "ver1_011026_baseline"
             and not ctx["latest_baseline"]["locked"] and len(ctx["latest_baseline"]["history"]) == 3, ctx.get("suggest"))
        # Giai đoạn 1 xong, dung lai review -> lan sau de xuat chay tiep Giai đoạn 2
        json.dump({"outputs": [{"id": "O6", "status": "skip", "reason": "chờ Giai đoạn 2"}]},
                  open(os.path.join(v1, "_internal", "index.json"), "w", encoding="utf8"), ensure_ascii=False)
        rc, ctx2, _ = vt("context", "--outputs", out, "--flow", "1")
        os.remove(os.path.join(v1, "_internal", "index.json"))
        case("context: index.json co 'chờ Giai đoạn 2' -> flow1_phase = 2",
             ctx2.get("suggest", {}).get("flow1_phase") == 2 and "flow1_phase" not in ctx.get("suggest", {}), ctx2.get("suggest"))

        # --- CR moi -> ten CR-<id>_<DDMMYY>_<slug>, tro ver1 -> ver1 khoa
        rc, j, _ = vt("next", "--outputs", out, "--cr-id", "1", "--slug", "Thêm coupon", "--date", "151026", "--create")
        crdir = os.path.join(out, "CR-001_151026_them-coupon")
        meta = json.load(open(os.path.join(crdir, "_internal", "version-meta.json"))) if os.path.isdir(crdir) else {}
        case("next --cr-id -> folder CR-001_151026_them-coupon, meta baseline = ver1",
             rc == 0 and j.get("folder") == "CR-001_151026_them-coupon" and meta.get("baseline") == "ver1_011026_baseline"
             and os.path.isdir(os.path.join(crdir, "_internal", "gates")), j)
        rc, j, _ = vt("next", "--outputs", out, "--cr-id", "CR-001", "--slug", "khac", "--date", "201026", "--create")
        case("chay lai cung CR -> reuse folder CR cu, khong tao folder moi",
             rc == 0 and j.get("reuse") is True and j.get("folder") == "CR-001_151026_them-coupon"
             and not os.path.exists(os.path.join(out, "CR-001_201026_khac")), j)
        rc, j, _ = vt("next", "--outputs", out, "--slug", "baseline", "--date", "201026", "--create")
        case("co CR tro ver1 -> next Luong 1 bao khoa (exit 3), khong tao folder",
             rc == 3 and j.get("locked") is True and j.get("locked_by") == ["CR-001"]
             and sorted(os.listdir(out)) == ["CR-001_151026_them-coupon", "ver1_011026_baseline"], (rc, j))
        rc, ctx, _ = vt("context", "--outputs", out, "--flow", "1")
        case("context: ver1 locked, open_crs = CR-001, flow1_action locked",
             ctx["latest_baseline"]["locked"] and ctx["suggest"].get("flow1_action") == "locked"
             and [c["cr_id"] for c in ctx["open_crs"]] == ["CR-001"], ctx.get("suggest"))

        # --- promote
        rc, j, err = vt("promote", "--outputs", out, "--cr", "CR-001", "--approved", "--create")
        case("promote thieu --coded -> tu choi (exit 1), khong tao ver2",
             rc == 1 and not any(n.startswith("ver2") for n in os.listdir(out)), (rc, err))
        rc, j, err = vt("promote", "--outputs", out, "--cr", "CR-009", "--approved", "--coded", "--create")
        case("promote CR khong tro baseline hien hanh -> tu choi", rc == 1, (rc, err))
        rc, j, err = vt("promote", "--outputs", out, "--cr", "CR-001", "--approved", "--coded", "--date", "251026", "--create")
        v2 = os.path.join(out, "ver2_251026_baseline")
        m2 = json.load(open(os.path.join(v2, "_internal", "version-meta.json"))) if os.path.isdir(v2) else {}
        case("promote --cr CR-001 --approved --coded -> ver2_251026_baseline (previous ver1, promoted CR-001)",
             rc == 0 and j.get("folder") == "ver2_251026_baseline" and m2.get("previous_version") == "ver1_011026_baseline"
             and m2.get("promoted_crs") == ["CR-001"], (rc, j, err))
        case("ver1 + history van con nguyen sau promote",
             open(doc).read() == "ban moi" and os.path.isfile(kept), kept)
        rc, j, _ = vt("next", "--outputs", out, "--slug", "baseline", "--date", "261026")
        rc2, ctx, _ = vt("context", "--outputs", out, "--flow", "1")
        case("sau promote: next Luong 1 -> ver2 (reuse), CR-001 khong con open",
             rc == 0 and j.get("folder") == "ver2_251026_baseline" and j.get("reuse") is True
             and ctx["latest_baseline"]["folder"] == "ver2_251026_baseline" and ctx["open_crs"] == [], (j, ctx.get("open_crs")))

        # --- layout cu
        old = os.path.join(tmp, "old")
        for f in ("ver1_011026_baseline", "ver2_151026_CR-001-otp", "ver3_201026_baseline"):
            os.makedirs(os.path.join(old, f, "_internal"))
        json.dump({"meta": {"cr_id": "CR-001", "baseline_version": "ver1_011026_baseline"}},
                  open(os.path.join(old, "ver2_151026_CR-001-otp", "_internal", "cr.json"), "w"))
        rc, lst, _ = vt("list", "--outputs", old, "--json")
        types = {v["folder"]: (v["type"], v["cr_id"], v["baseline_ref"]) for v in lst.get("versions", [])}
        case("layout cu: ver<N>_..._CR-... doc la CR tro ver1, ver<N> la BASELINE",
             types.get("ver2_151026_CR-001-otp") == ("CR", "CR-001", "ver1_011026_baseline")
             and types.get("ver1_011026_baseline", ("",))[0] == "BASELINE"
             and lst.get("latest_baseline") == "ver3_201026_baseline" and lst.get("open_crs") == [], lst)
        rc, j, _ = vt("next", "--outputs", old, "--slug", "baseline", "--date", "271026")
        case("layout cu: ver3 chua co CR tro toi -> next tra ve ver3 (reuse)",
             rc == 0 and j.get("folder") == "ver3_201026_baseline" and j.get("reuse") is True, j)
        os.makedirs(os.path.join(old, "ver4_221026_CR-002-x", "_internal"))   # CR cu khong ghi baseline, sau ver3
        rc, j, _ = vt("next", "--outputs", old, "--slug", "baseline")
        case("layout cu: CR ver4 (khong ghi baseline, sau ver3) -> ver3 khoa", rc == 3 and j.get("locked_by") == ["CR-002"], (rc, j))
        case("next --cr-id khi chua co baseline -> exit 1",
             vt("next", "--outputs", os.path.join(tmp, "empty"), "--cr-id", "CR-001", "--slug", "x")[0] == 1)
    finally:
        if a.keep:
            print("Giu thu muc: %s" % tmp)
        else:
            shutil.rmtree(tmp, ignore_errors=True)
    total, passed = len(res), sum(res)
    print("\n%d ca · %d PASS" % (total, passed))
    print("SUMMARY: %d ca · %d PASS · %d FAIL" % (total, passed, total - passed), file=sys.stderr)
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
