#!/usr/bin/env python3
"""Self-test bo trich AST (ast/extract-screen.mjs) + ghep --ast-spec cua build-basic-design.py.

  python3 selftest-ast.py

Dung 1 repo Next.js gia (tsconfig baseUrl, ROUTE const, yup schema dung qua yupResolver, Label htmlFor isRequired,
inputProps maxLength, header chung, file S1) -> chay bo trich -> kiem tung mau. Can Node + ts-morph (ensure-env.py --flow 1).
"""
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
EXTRACT = os.path.join(HERE, "ast", "extract-screen.mjs")

FILES = {
    "package.json": '{"dependencies": {"react": "18.2.0", "next": "13.0.0"}}',
    "tsconfig.json": '{"compilerOptions": {"baseUrl": "./src", "jsx": "preserve"}}',
    "src/constants/route.ts": 'export const ROUTE = { STAFF_LIST: "/admin/staff", HOME: "/" };',
    "src/libs/validation/schemas.ts": '''import * as yup from "yup";
export const staffSchema = yup.object().shape({
  lastName: yup.string().required("姓を入力してください").max(50),
  code: yup.string().test("is-code", "コードは半角で入力してください", (v) => !!v),
});
export const otherSchema = yup.object().shape({ unrelated: yup.string().required("関係ない画面のメッセージ") });''',
    "src/components/common/Header/index.tsx": '''export default function Header() {
  return <header><a href="/news">お知らせ</a></header>;
}''',
    "src/components/Secret/index.tsx": 'export const KEY = "x"; export default function S() { return <button>秘密</button>; }',
    "src/components/StaffForm/index.tsx": '''import { useRouter } from "next/router";
import { yupResolver } from "@hookform/resolvers/yup";
import { staffSchema } from "libs/validation/schemas";
import { ROUTE } from "constants/route";
import Header from "components/common/Header";
import S from "components/Secret";
export default function StaffForm({ errorMsg, setErrorDialogMsg }) {
  const router = useRouter();
  const form = useForm({ resolver: yupResolver(staffSchema) });
  const handleBack = () => { router.push(ROUTE.STAFF_LIST); };
  const onSave = () => { setErrorDialogMsg("保存に失敗しました"); };
  return (
    <div>
      <Header />
      <h1>従業員登録</h1>
      <Label htmlFor="lastName" isRequired={true}>姓</Label>
      <TextInputField id="lastName" name="lastName" inputProps={{ maxLength: 50 }} placeholder="山田" />
      <label>メモ</label>
      <TextField name="memo" placeholder="自由入力" />
      {errorMsg && <p>{errorMsg}</p>}
      <Button onClick={handleBack}>戻る</Button>
      <Button onClick={onSave}>保存する</Button>
      <S />
    </div>
  );
}''',
    "src/pages/admin/staff/create.tsx": '''import StaffForm from "components/StaffForm";
export default function Page() { return <StaffForm />; }''',
}


def run(args, cwd=None):
    p = subprocess.run(args, capture_output=True, text=True, cwd=cwd)
    return p.returncode, p.stdout, p.stderr


def main():
    if not shutil.which("node") or not os.path.isdir(os.path.join(HERE, "ast", "node_modules", "ts-morph")):
        print("SKIP: chua co Node / ts-morph — chay ensure-env.py --flow 1")
        return 1
    tmp = tempfile.mkdtemp(prefix="selftest-ast-")
    fe = os.path.join(tmp, "repo")
    for rel, body in FILES.items():
        f = os.path.join(fe, rel)
        os.makedirs(os.path.dirname(f), exist_ok=True)
        open(f, "w", encoding="utf8").write(body)
    recon = os.path.join(tmp, "recon")
    os.makedirs(recon)
    json.dump({"/admin/staff/create": ["src/pages/admin/staff/create.tsx", "src/components/StaffForm/index.tsx"],
               "/admin/staff": ["src/pages/admin/staff/create.tsx"]}, open(os.path.join(recon, "fe-screen-files.json"), "w"))
    open(os.path.join(recon, "fe-api-calls.csv"), "w").write(
        "Screen Route,Screen File,Trigger,UI Label,Method,Path,API ID,Via,Trigger Ref,Code Ref,Confidence\n"
        "/admin/staff/create,REPO-01:src/components/StaffForm/index.tsx,onSave,—,POST,/api/staffs,API-001,x,"
        "REPO-01:src/components/StaffForm/index.tsx#L10,REPO-01:x#L1,static\n")
    s1 = os.path.join(tmp, "high-files.txt")
    open(s1, "w").write("src/components/Secret/index.tsx\n")
    out = os.path.join(tmp, "out")
    base = ["node", EXTRACT, "--frontend", fe, "--workspace", tmp, "--site", "WEB-01", "--repo-id", "REPO-09",
            "--screens", "SC-001=/admin/staff/create,SC-002=/admin/staff", "--only", "SC-001",
            "--screen-files", os.path.join(recon, "fe-screen-files.json"),
            "--api-calls", os.path.join(recon, "fe-api-calls.csv"), "--out", out]
    res, bad = [], 0

    def case(name, ok, detail=""):
        nonlocal bad
        res.append((name, ok, detail))
        bad += 0 if ok else 1

    rc, _, err = run(base)                                           # thieu --s1-list
    case("Thieu --s1-list -> exit 3, khong trich", rc == 3 and not os.path.exists(out), err[-120:])
    rc, so, err = run(base + ["--s1-list", s1])
    case("Chay du tham so -> exit 0", rc == 0, err[-300:])
    if rc != 0:
        for r in res:
            print(r)
        return 1
    stat = json.loads(so)
    sc = json.load(open(os.path.join(out, "WEB-01.json"), encoding="utf8"))["screens"]["SC-001"]
    items = {i["name_jp"]: i for i in sc["items"]}
    msgs = {e["msg_jp"]: e for e in sc["errors"]}
    case("Tieu de = <h1> cua man", sc["title"] == "従業員登録", sc["title"])
    li = items.get("姓", {})
    case("Nhan qua <Label htmlFor> (khong lay placeholder chu mau)", "姓" in items and "山田" not in items, list(items))
    case("Bat buoc: Label isRequired / yup required -> Yes", li.get("required") == "Yes", li.get("required"))
    case("Do dai: inputProps maxLength -> 50", li.get("maxlength") == "50", li.get("maxlength"))
    case("field = name trong code", li.get("field") == "lastName", li.get("field"))
    mi = items.get("メモ", {})
    case("O khong co luat -> required No, maxlength Cần xác nhận",
         mi.get("required") == "No" and mi.get("maxlength") == "Cần xác nhận", mi)
    back = items.get("戻る", {})
    case("Nut router.push(ROUTE.X) -> next = SC cua route", back.get("next") == "SC-002", back.get("next"))
    case("Nut co trong fe-api-calls -> api", items.get("保存する", {}).get("api") == "POST /api/staffs (API-001)",
         items.get("保存する", {}).get("api"))
    case("code-ref dung --repo-id", li.get("r", "").startswith("REPO-09:src/components/StaffForm/index.tsx#L"), li.get("r"))
    case("yup: required msg nguyen van", "姓を入力してください" in msgs, list(msgs))
    case("yup .test(ten, msg): lay msg, khong lay ten luat",
         "コードは半角で入力してください" in msgs and "is-code" not in msgs, list(msgs))
    case("yup chi schema man dung (yupResolver) — khong lay schema khac", "関係ない画面のメッセージ" not in msgs, list(msgs))
    e = msgs.get("保存に失敗しました", {})
    case("setErrorDialogMsg -> loi He thong, hien thi Dialog", e.get("display") == "Dialog" and "System" in e.get("category", ""), e)
    case("Header chung bi bo (khong phai item cua man)", "お知らせ" not in items, list(items))
    case("File S1 khong mo", "秘密" not in items and "src/components/Secret/index.tsx" in stat["skipped_s1"], stat["skipped_s1"])
    v = msgs.get("姓を入力してください", {})
    case("Loi validation co cach xu ly suy tu co che (sua noi dung nhap)", v.get("action_vn", "").startswith("Sửa"), v)
    # framework khong phai React -> exit 4
    open(os.path.join(fe, "package.json"), "w").write('{"dependencies": {"vue": "3"}}')
    rc4, _, _ = run(base + ["--s1-list", s1])
    case("Khong phai React JSX -> exit 4 (chua ho tro)", rc4 == 4)

    # ghep --ast-spec vao spec agent viet: lap cho trong, khong them dong, them loi chua co
    sp = importlib.util.spec_from_file_location("bdb", os.path.join(HERE, "build-basic-design.py"))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    llm = {"SC-001": {"title": "従業員登録", "items": [
        {"name_jp": "姓", "type": "Textbox", "required": "Cần xác nhận", "maxlength": "", "field": "lastName", "r": "x"}],
        "errors": [{"msg_jp": "姓を入力してください"}]}}
    n = m.merge_ast(llm, {"SC-001": sc})
    it = llm["SC-001"]["items"]
    case("merge: lap required / maxlength trong, khong them dong item, them loi moi",
         it[0]["required"] == "Yes" and it[0]["maxlength"] == "50" and len(it) == 1
         and len(llm["SC-001"]["errors"]) == len(sc["errors"]) and "AST:" in it[0]["r"], n)

    shutil.rmtree(tmp, ignore_errors=True)
    print("# Self-test bo trich AST\n\n| Ca | Ket qua | Chi tiet |\n|---|---|---|")
    for name, ok, detail in res:
        print("| %s | %s | %s |" % (name, "PASS" if ok else "**FAIL**", "" if ok else str(detail)[:160]))
    print("\n**%d ca · %d PASS · %d FAIL**" % (len(res), len(res) - bad, bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
