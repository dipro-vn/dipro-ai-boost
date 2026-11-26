# Basic Design Skill

> **Load skill này** (Read file này) **BẮT BUỘC trước khi tạo file Basic Design xlsx**.
> Áp dụng cho cả lệnh `/analyze-system` (G2 bước 4) lẫn `/basic-design` (standalone).
> Skill giải quyết các lỗi thực tế đã xảy ra: tên sheet SC-xxx, item rỗng, B1/B4 không có nội dung thật.

**Companion spec** (đọc khi cần chi tiết):
- `sys-agent/basic-design/workbook-structure.md` — cell map, style, 8 nhóm nội dung, bảng ERROR SCENARIOS
- `sys-agent/basic-design/workbook-structure.md §2.8b` — ví dụ P/Q đầy đủ theo 12 type
- `sys-agent/outputs/o5-basic-design.md` — workflow, nguồn, gate V-BD, anti-patterns

---

## §1 Luồng tạo file — 4 bước bắt buộc theo thứ tự

```
Bước 1 — Trích AST từ code FE
  ast/extract-screen.mjs → _internal/ast/WEB-xx/WEB-xx.json
  build-bd-skeleton.py → _internal/bd/skeleton-WEB-xx.json

Bước 2 — LLM viết spec + build file
  LLM điền _internal/bd/spec-WEB-xx.json (title · P/Q · Step 1 · errors)
  build-basic-design.py --skeleton … --spec … → xlsx

Bước 3 — Crawl ảnh + đánh số (chỉ G2, có Playwright)
  Lấy screenshots từ crawl-site.js (đã chạy trước đó)
  annotate-ui-image.py đánh badge đỏ từng màn
  build-basic-design.py --crawl chèn ảnh đã đánh số

Bước 4 — Gate + Review
  verify-basic-design.py (31 check) → FAIL = 0
  sub-agent basic-design-reviewer (round 1 → 2)
```

**Thông báo bắt buộc trước Bước 1:**
> *"Bắt đầu tạo O5 Basic Design — gồm 4 việc: (1) trích AST từ code FE, (2) build file xlsx với tên màn đọc được + nội dung P/Q đầy đủ theo type, (3) chụp ảnh Playwright từng màn, (4) đánh số item trên ảnh (badge đỏ, không che nội dung) + chèn vào file."*

---

## §2 Tên sheet và B1 — ⛔ KHÔNG dùng SC-xxx

**Lỗi thực tế:** 92/93 sheet tên `SC-001`, `SC-002`... → V-BD check 24 FAIL.

**Quy tắc:**

| Vị trí | Quy tắc | Ví dụ đúng | Ví dụ sai |
|---|---|---|---|
| **Tên tab sheet** | Tên màn đọc được (≤31 ký tự, bỏ `[]:*?/\`) | `ログイン`, `施設管理`, `Trang chủ` | `SC-001`, `/admin/login` |
| **`B1` Screen Name** | Giống tên tab | `施設管理` | `SC-031` |
| **`F1` Screen ID** | SC-xxx | `SC-031` | (đây mới đúng) |
| **Screen Index cột D** | Tên màn đọc được (= B1) | `施設管理` | `SC-031` |

**Nguồn tên màn** (ưu tiên theo thứ tự):
1. `spec.screens[sid].title` — LLM viết theo nghiệp vụ, tiếng Nhật hoặc VN
2. `02_Screen` cột `Screen Name` trong inventory (đã bỏ SC code / route)
3. `<h1>` / `<title>` trích được từ AST
4. ⚠️ Không có nguồn → ghi `Cần xác nhận — Q-xxx` (không để SC-xxx)

**Màn gom `merged_from`:** tên sheet = tên màn **cha** (không gộp tên con vào tab).

---

## §3 B4 (mục đích) và B5 (Step 1) — phải có nội dung thật

**Lỗi thực tế:** B4 = `"SC-001 (Error)"`, B5 = toàn `要確認 — Q-xxx`.

### B4 — ■目的 / ■アクセス方法

```
■目的
<1-2 câu: màn này làm gì, phục vụ ai>
Ví dụ: 「施設の基本情報を登録・編集し、料金プランやスタッフ情報を管理する」

■アクセス方法
<cách vào màn: menu, link từ màn nào, URL param>
Ví dụ: 「サイドメニュー「施設管理」→「施設を追加」ボタン押下」/ /admin/facilities/new

■トレーサビリティ / Traceability
SC-031 · FL-004 · SPEC ## Screen Details SC-031
```

⛔ Cấm: `"SC-031 (Other)"`, `"SC-031 (Form)"` — đây là type/mã, không phải mục đích.

### B5 — Step 1：画面共通 (6 dòng bắt buộc — V-BD check 32)

```
■初期表示・データ取得
<API load data lúc mở màn, sort mặc định, số item/trang>
Ví dụ: 「GET /api/facilities tải danh sách, sort 作成日降順, 20件/ページ」

■権限
<role nào thấy màn, role nào thấy nút nào>
Ví dụ: 「admin・staff xem; viewer ẩn nút「新規作成」・「削除」」

■データ範囲
<user thấy data của tenant nào, phạm vi lọc>
Ví dụ: 「ログイン中のテナントに属する施設のみ表示」

■状態保持
<filter/sort/trang có giữ khi back không, storage nào>
Ví dụ: 「検索キーワード・ページ番号をsessionStorageに保持（30分）」

■loading / 0件 / エラー
<skeleton loading, empty state text, toast khi 5xx>
Ví dụ: 「loading = skeleton 3行; 0件 = 「施設がありません」+ 追加ボタン; 5xx = toast「取得失敗」」

■URL tham số sai
<?page=abc → fallback gì, ID không tồn tại → 404 hay redirect>
Ví dụ: 「?page=abc → page=1 fallback; /facilities/9999 → 404ページ表示」
```

Chưa rõ → ghi `要確認 — Q-xxx` (hợp lệ, không để trống hoặc để SC-xxx).

---

## §4 Quy tắc gom màn — 1 sheet = 1 tính năng người dùng thấy

**Nguyên tắc:** 1 tab = 1 tính năng người dùng **cảm nhận được**, không phải 1 route.

| Rule | Gom khi | Ví dụ |
|---|---|---|
| **R1** | Màn kết quả/thành công (「〜しました」「〜完了」) chỉ có message + nút quay về | `パスワード変更しました` ⊂ `パスワード再設定` |
| **R2** | New + Edit cùng component form (code dùng chung, chỉ khác default value) | `新規施設登録` + `施設編集` ⊂ `施設管理` |
| **R3** | Detail chỉ đọc của list, không có action riêng | `施設詳細` ⊂ `施設管理` |
| **R4** | Modal confirm trước action / loading trung gian | Popup 「削除確認？」⊂ màn list có nút Xoá |

**Giữ riêng (KHÔNG gom):**
- Static page: 利用規約, プライバシーポリシー, エラー, メンテナンス中
- Màn kết quả phục vụ nhiều trigger khác nhau
- Màn có logic riêng (chọn, phân nhánh, tính toán)
- **Ngưỡng tối đa: 6 màn con / 1 parent** — vượt → tách thêm parent

**Khi gom:** đặt `merged_from` trong spec JSON → builder tự tạo group cho từng SC con trong sheet cha.

---

## §5 Quy tắc nội dung P/Q theo type

> **Đọc `workbook-structure.md §2.8b`** để lấy ví dụ cụ thể cho từng type.

**Format chung:**
```
P (JP):
・<mô tả item — item này là gì>
・初期表示：<trạng thái ban đầu>
・押下時の挙動：(Button/Link)
  1. <nhánh happy> → <đích 「màn」hoặc action>
  2. <nhánh lỗi> → E_xxx_001
・バリデーション：(Input)
  1. <rule> → E_xxx_001

Q (VN): khớp 1-1 với P — cùng số bullet, cùng thứ tự nhánh
```

**Trọng tâm bắt buộc theo type:**

| Type | Bắt buộc có | Hay bỏ sót |
|---|---|---|
| Button | Điều kiện active + mọi nhánh (happy/error/5xx) + đích rõ | Nhánh 5xx |
| Textbox/Input | Placeholder + maxlength enforcement + mọi validation rule | Ký tự không hợp lệ |
| Dropdown | Nguồn data + option mặc định + hành vi khi chọn | API load lỗi |
| Checkbox | Trạng thái mặc định + hành vi check/uncheck | Điều kiện enable nút sau |
| Radio | Danh sách option + mặc định + hành vi đổi | State persistence |
| Table | Tên cột theo thứ tự + sort + pagination + 0 item + action enable | Điều kiện action nút |
| Label | Nguồn data (API field cụ thể) + format + fallback | Loading / fallback khi lỗi |
| Tab | Danh sách tab + mặc định + nội dung từng tab + URL sync | URL param |
| DatePicker | Format + phạm vi + mặc định + validation range | Range check API |
| Image/File | Định dạng + dung lượng + preview + khi gửi server | Validation trùng file |
| Pagination | Items/trang + disable Prev/Next + scroll-to-top | Scroll behavior |
| SearchBox | Trigger (debounce timing) + 0 result + clear | Debounce ms |

**Ngôn ngữ theo cột (V-BD FAIL nếu sai):**
- Cột `P`, `I`, `K`, `L`, `M`, `N`, `O`: **JP thuần**
- Cột `Q`, `J`: **VN thuần**
- Cột `R`, `S`: VN (nội bộ)
- `Cần xác nhận` ở cột `P` → phải là `要確認 — Q-xxx`

**Cấm trong P/Q:**
- `/api/xxx`, `GET`, `POST` → đưa vào cột `S`
- `fetchData()`, `onSubmit()`, tên hàm → đưa vào cột `R`
- Nội dung không có bằng chứng → `要確認 — Q-xxx` + Q trong sheet 確認事項

---

## §6 Quy tắc đánh số ảnh — badge không che nội dung

**Yêu cầu:**
- Badge hình tròn đỏ `#C41230`, chữ trắng đậm, viền trắng 1px
- Đường kính: `max(18, round(W * 0.015))` px (≈22px với ảnh 1440px)
- Vị trí: **góc trên-phải** trong vùng item, **không che text/icon chính** của item đó
- Số trên badge = số `#` trong bảng item cùng sheet
- Item không hiện trên ảnh → không đặt badge, ghi cột `R`: `Không hiển thị trên ảnh`

**Lệnh:**
```bash
python3 $S/annotate-ui-image.py <ảnh gốc> <ảnh output> \
  --marks "1:0.5,0.18;2:0.93,0.22" --expect <N item hiển thị>
```

**Sau khi annotate:** mở ảnh xem lại — badge không được:
- Che text của item (chỉ cho phép che phần border/padding)
- Nằm ngoài vùng item tương ứng
- Chồng lên badge khác

**Nếu không có Playwright (G1 / app):** A9 = `Chưa có ảnh — bổ sung ở Giai đoạn 2 (Playwright)`, không để ô trống.

---

## §7 SELF-CHECK sau khi build — bắt buộc trước khi báo xong

Chạy sau mỗi lần `build-basic-design.py` hoàn thành, **trước khi chạy V-BD và trước khi báo user**.

Mỗi lỗi kèm **hướng dẫn sửa + link section trong SKILL.md** để agent biết đọc gì ngay:

```python
python3 - <<'PYEOF'
import openpyxl, re, sys

SKILL = "skills/basic-design/SKILL.md"
wb = openpyxl.load_workbook(sys.argv[1], data_only=True)
errors = []

for name in wb.sheetnames:
    ws = wb[name]
    if ws["F6"].value != "WORKING_SCREEN":
        continue

    # CHECK 1 — Tên sheet không là SC-xxx
    if re.match(r'^SC-\d+$', name):
        errors.append(
            f"[CHECK-24 | {SKILL} §2] Sheet '{name}': tên tab là SC-xxx.\n"
            f"  → Sửa: đổi tên tab thành tên màn đọc được (ví dụ: ログイン, 施設管理).\n"
            f"  → Nguồn tên: spec.screens[sid].title → inventory 02_Screen → <h1> AST."
        )

    # CHECK 2 — B1 phải là tên màn đọc được
    b1 = str(ws["B1"].value or "").strip()
    if not b1 or re.match(r'^SC-\d+$', b1):
        errors.append(
            f"[CHECK-24 | {SKILL} §2] Sheet '{name}': B1='{b1}' không phải tên màn.\n"
            f"  → Sửa: điền spec.screens[sid].title vào B1 (cùng giá trị với tên tab)."
        )

    # CHECK 3 — B4 phải có mục đích nghiệp vụ thật
    b4 = str(ws["B4"].value or "").strip()
    if not b4 or re.match(r'^SC-\d+', b4):
        errors.append(
            f"[CHECK-B4 | {SKILL} §3] Sheet '{name}': B4='{b4[:40]}' không có mục đích thật.\n"
            f"  → Sửa: điền ■目的 (1-2 câu: màn làm gì, phục vụ ai) + ■アクセス方法 vào B4.\n"
            f"  → Ví dụ: 「施設の基本情報を登録・編集し、料金プランを管理する」"
        )

    # CHECK 4 — B5 phải có 6 dòng Step 1
    b5 = str(ws["B5"].value or "")
    step1_headers = ["初期表示", "権限", "データ範囲", "状態保持", "loading", "URL"]
    missing = [h for h in step1_headers if h not in b5]
    if missing:
        errors.append(
            f"[CHECK-32 | {SKILL} §3] Sheet '{name}': B5 thiếu dòng Step 1: {missing}.\n"
            f"  → Sửa: điền đủ 6 ■ section. Chưa rõ → 要確認 — Q-xxx (hợp lệ)."
        )

    # CHECK 5 — Bảng item không được rỗng
    items = [r for r in ws.iter_rows(min_row=9, min_col=8, max_col=9, values_only=True)
             if r[1] is not None]
    if not items:
        errors.append(
            f"[CHECK-ITEM | {SKILL} §1] Sheet '{name}': bảng item rỗng (0 dòng).\n"
            f"  → Nguyên nhân thường gặp: AST extraction chưa chạy hoặc spec JSON thiếu items[].\n"
            f"  → Sửa: kiểm tra _internal/ast/WEB-xx.json và _internal/bd/spec-WEB-xx.json."
        )

    # CHECK 6 — Cột P/Q không được trống
    empty_pq = []
    for row in ws.iter_rows(min_row=9, min_col=8, max_col=17, values_only=True):
        if row[1] is None:
            continue
        p, q = str(row[8] or "").strip(), str(row[9] or "").strip()
        k = str(row[3] or "").strip()   # col K = type
        if not p or not q:
            empty_pq.append(f"'{row[1]}' (type={k})")
    if empty_pq:
        errors.append(
            f"[CHECK-19 | {SKILL} §5] Sheet '{name}': {len(empty_pq)} item có P hoặc Q trống:\n"
            f"  {', '.join(empty_pq[:5])}{'...' if len(empty_pq)>5 else ''}\n"
            f"  → Sửa: điền P/Q theo type. Chưa rõ → 要確認 — Q-xxx.\n"
            f"  → Xem ví dụ từng type tại {SKILL} §5 + workbook-structure.md §2.8b."
        )

    # CHECK 7 — Button/Hyperlink phải có cột S (API gọi)
    for row in ws.iter_rows(min_row=9, min_col=8, max_col=20, values_only=True):
        if row[1] is None:
            continue
        k = str(row[3] or "").strip()
        s = str(row[11] if len(row) > 11 else "") .strip()
        if k in ("Button", "Hyperlink") and not s:
            errors.append(
                f"[CHECK-17 | {SKILL} §5] Sheet '{name}': item '{row[1]}' (Button/Hyperlink) thiếu cột S.\n"
                f"  → Sửa: điền API gọi vào cột S. Không gọi → 'Không gọi API — chuyển trang'."
            )

if errors:
    print(f"\nSELF-CHECK FAIL — {len(errors)} lỗi:\n")
    for e in errors[:15]:
        print(f"  {e}\n")
    if len(errors) > 15:
        print(f"  ... và {len(errors)-15} lỗi khác")
    sys.exit(1)
else:
    ws_count = sum(1 for n in wb.sheetnames if wb[n]["F6"].value == "WORKING_SCREEN")
    print(f"SELF-CHECK PASS — {ws_count} working sheets OK")
PYEOF
```

**Thực thi:** `python3 <script trên> <path_to_xlsx>`

**Nếu SELF-CHECK FAIL:**
1. Đọc error message → link SKILL.md section được chỉ dẫn
2. Sửa `_internal/bd/spec-WEB-xx.json` theo hướng dẫn
3. Rebuild: `build-basic-design.py --skeleton … --spec …`
4. Chạy lại SELF-CHECK → PASS mới sang V-BD

**⛔ Không được chạy V-BD khi SELF-CHECK còn FAIL** — tránh tốn thời gian 31 check khi lỗi cơ bản chưa sửa.

**In kết quả bắt buộc:**
```
SELF-CHECK PASS — N working sheets OK
```
hoặc:
```
SELF-CHECK FAIL — X lỗi:
  [CHECK-24 | skills/basic-design/SKILL.md §2] Sheet 'SC-001': tên tab là SC-xxx.
  → Sửa: đổi tên tab thành tên màn đọc được...
→ Đang sửa spec JSON và rebuild...
```

---

## §8 Anti-patterns — lỗi đã xảy ra thực tế, không lặp lại

| ❌ Sai | ✅ Đúng |
|---|---|
| Tên sheet = `SC-001` | Tên sheet = `ログイン` / `施設管理` |
| B1 = `SC-001` | B1 = tên màn đọc được |
| B4 = `SC-001 (Error)` | B4 = mục đích nghiệp vụ bằng câu hoàn chỉnh |
| Bảng item rỗng (0 dòng) | Mỗi item trong màn phải có ≥1 dòng |
| P/Q để trống | `要確認 — Q-xxx` nếu chưa rõ |
| P viết `GET /api/orders` | Cột S viết API, P viết hành vi người dùng |
| P/Q mô tả 2 hành vi khác nhau | P và Q khớp 1-1 từng bullet và nhánh |
| Badge che text của item | Badge đặt góc trên-phải, không che text/icon chính |
| Gom >6 màn vào 1 sheet | Tối đa 6 màn con/parent, vượt → tách parent |
| Chạy build xong báo ngay | Chạy SELF-CHECK trước, PASS mới báo |
