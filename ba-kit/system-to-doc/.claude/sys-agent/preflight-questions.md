# Gate hỏi người — wording + cách xử lý từng câu trả lời

> **Mọi gate dưới đây PHẢI gọi tool `AskUserQuestion`.** In bảng text rồi tự suy ra câu trả lời là anti-pattern nghiêm cấm.
>
> `AskUserQuestion` tối đa 4 câu / lần → hỏi theo **5 lượt** dưới đây. Câu cần nhập tự do (URL, đường dẫn) → để option gợi ý + user nhập ở ô **Other**. Câu trả lời mơ hồ → hỏi lại đúng câu đó, **không đoán**.
>
> **Thứ tự bắt buộc:** G-R → Lượt 1 (P0) → Lượt 2 (Website P1–P4) → Lượt 3 (Source P5 · DB P6) → Lượt 4 (Figma P7–P8) → Lượt 5 (P9–P11) → **Discovery Brief** → (recon) → G9/G10 khi phát sinh.
>
> Lưu mọi câu trả lời vào `_internal/inventory.xlsx` sheet `00_Meta` (key ở cột phải). **Không bao giờ lưu mật khẩu.**

---

## G-R — Resume (chỉ khi `version-tool.py latest-baseline` tìm thấy baseline)

```
Đã có baseline ver<K> (<DD/MM/YYYY>): <a> site · <m> màn · <p> API · <t> bảng · <q> câu hỏi còn mở.
Lần này bạn muốn:
  [A] Delta — quét bổ sung phần thiếu + kiểm lại phần cũ   (mặc định)
  [B] Chạy lại toàn bộ — hệ thống đã đổi nhiều
  [C] Không quét — chỉ đọc lại ver<K> để trả lời câu hỏi
  [D] Thực ra tôi có 1 yêu cầu thay đổi (CR) → chuyển Luồng 2
```

| Chọn | `run_mode` | Hành vi |
|---|---|---|
| `[A]` | `DELTA` | Giữ dòng cũ + `Note = Carried from ver<K>`; evidence > 30 ngày → chụp lại nếu dòng đó `Confirmed`. Câu trả lời P0–P11 cũ làm **mặc định đề xuất** |
| `[B]` | `FULL` | Bỏ dữ liệu cũ, vẫn đề xuất câu trả lời cũ |
| `[C]` | `READ_ONLY_REVIEW` | Không crawl, **không** tạo version mới |
| `[D]` | — | Đọc `flow-2-change-request.md`, chạy Luồng 2 |

---

## Lượt 1 — P0 Tên & phạm vi

```
P0a. Tên hệ thống (dùng trong tên file)?            → system_name   (Other: nhập tên)
P0b. Tên ngắn cho version này?                       → slug           [baseline] [khao-sat-lan-dau] (Other)
P0c. Phạm vi?                                         → scope
     [A] Toàn hệ thống  [B] Một số module — liệt kê  [C] Một luồng nghiệp vụ
```
**Chưa trả lời P0a/P0c → DỪNG.** Không đoán `[A]`.

---

## Lượt 2 — Website (P1–P4) ⚠️ lượt quan trọng nhất về an toàn

### P1 — Website hiện tại
```
Hệ thống có bao nhiêu website cần khảo sát? Liệt kê URL + môi trường.
  [A] 1 website        [B] Nhiều website (user / admin / ...)   [C] Không có website để quét
  → Other: "WEB-01 user https://stg.abc.jp (staging); WEB-02 admin https://stg-admin.abc.jp (staging)"
```
→ `websites` (`WEB-01=<url>;WEB-02=<url>`) + sheet `10_Site`. Mỗi site có `Site ID` cố định `WEB-01, WEB-02…`.

- Có staging mà chọn production → hỏi lại 1 lần: *"Staging an toàn hơn. Bạn chắc chắn muốn quét production?"*
- `[C]` → O1 = ⬜ (`không có website`), O4 chỉ chạy nếu có Figma. **Chạy tiếp** các phần khác.

### P2 — Tài khoản đăng nhập + quyền được dùng ⚠️
Hỏi **2 ý riêng**, không gộp:
```
P2a. Mỗi website đăng nhập bằng tài khoản role nào?
     [A] Có tài khoản cho mọi role — liệt kê role   [B] Chỉ 1 số role   [C] Không có — chỉ màn public
P2b. Tài khoản đó do ai cấp, và bạn có được PHÉP dùng nó để agent tự động quét hệ thống không?
     [A] Tài khoản TEST do KH/PM cấp cho mục đích khảo sát — được phép
     [B] Tài khoản thật / dùng chung — CHƯA rõ được phép
     [C] Không được phép quét tự động
```
→ `accounts` (chỉ **tên role**, không tên người, không mật khẩu) · `access_approved_by` (vai trò người cấp, VD `PM phía KH`).

| P2b | Hành vi |
|---|---|
| `[A]` | Đăng nhập bằng `login-site.js` (xem dưới) |
| `[B]` | ⛔ **Không đăng nhập.** Chỉ quét màn public. Mọi màn sau login = `To verify` + Open Q "cần tài khoản test được phép" |
| `[C]` | Như `[B]`, ghi rõ lý do |

**Cách đăng nhập — phụ thuộc môi trường (`POLICIES.md` §3.2):**

| Môi trường | Cách |
|---|---|
| **TEST đã xác nhận** (T1 dev/staging/test · T2 = P2b `[A]` · T3 = P11 `[A]`) | Agent được dùng tài khoản user dán vào chat hoặc file tài khoản user chỉ định: `login-site.js --form --user-env … --pass-env …` (+ `--http-user-env/--http-pass-env` khi có Basic Auth), giá trị đặt vào biến môi trường, không in ra |
| **PRODUCTION / chưa chắc** | Chỉ `--manual` — user tự gõ. Không dùng mật khẩu trong chat / file |

- `--manual`: `node login-site.js --manual --url <login> --save .auth/WEB-01.json` → mở trình duyệt, **user tự gõ** tài khoản, script lưu phiên.
- Hoặc user tự `export SITE_USER=... SITE_PASS=...` trong terminal rồi agent chạy `--form --user-env SITE_USER --pass-env SITE_PASS`.
- User dán mật khẩu vào chat → TEST đã xác nhận: được dùng để đăng nhập, **không ghi ra file**; PRODUCTION / chưa chắc: **không dùng**. Cả hai: nhắc user đổi mật khẩu sau khảo sát.
- Môi trường chưa rõ là TEST hay PRODUCTION → hỏi lại P1 (phân loại). Vẫn chưa chắc → coi là PRODUCTION.
- Role không đăng nhập được → mọi chức năng của role đó `To verify` + Open Q, **cấm** đoán theo tên menu.

### P3 — Quyền thao tác ⚠️ gate an toàn
```
Agent được thao tác tới mức nào trên website?
  [A] Chỉ ĐỌC — không submit form, không bấm nút ghi/xoá            (mặc định)
  [B] ĐỌC + CREATE/UPDATE trên STAGING bằng tài khoản test
  [C] ĐỌC + CREATE/UPDATE cả PRODUCTION — tôi chịu trách nhiệm
  [D] Không quét — tôi tự gửi screenshot
```
| Chọn | `crawl_mode` | `crawl-site.js --mode` | Thực thi |
|---|---|---|---|
| `[A]` | `READ_ONLY` | `read-only` | **Chặn ở tầng network** mọi request khác GET/HEAD |
| `[B]` | `SUBMIT_STAGING` | `submit-staging` | Cho POST, **vẫn** chặn nút xoá/thanh toán/gửi mail |
| `[C]` | `SUBMIT_PROD` | `submit-prod` | Như `[B]` + in cảnh báo trước mỗi thao tác ghi |
| `[D]` | `NO_CRAWL` | — | Không chạy crawler |

DELETE **không bao giờ** được cấp qua câu này — gặp nút xoá luôn đi qua G9. Chưa trả lời → `[A]` + in: `Đang chạy READ-ONLY — mọi thao tác ghi bị chặn ở tầng network.`

### P4 — Vùng cấm chạm
```
Có URL / chức năng nào tuyệt đối không được chạm? (VD /admin/batch, gửi mail hàng loạt, cổng thanh toán)
  [A] Không có   → Other: liệt kê
```
→ `forbidden_zones` → `crawl-site.js --forbid`.

---

## Lượt 3 — Source code (P5) + Database (P6)

### P5 — Source code
```
P5a. Có source code để quét không? Bao nhiêu repo, ở đâu?
     [A] 1 repo  [B] Nhiều repo (FE / BE / batch riêng)  [C] Không có
     → Other: "REPO-01 /path/web-fe (FE); REPO-02 /path/api (BE)"
P5b. (chỉ khi có repo FE) Repo FE nào là của website nào?
     → Other: "REPO-01 → WEB-01; REPO-03 → WEB-02"
```
→ `source_repos` + sheet `11_Repo` (`Kind`, `For Site`). Repo FE chưa gán site → hỏi lại, **không** đoán theo tên folder.

- `[C]` → O2 = ⬜ (`không có source`), mọi business rule chỉ `Inferred`. Chạy tiếp.
- Repo có trong đường dẫn nhưng `scan-sensitive.py` báo HIGH → xem §6 agent.

### P6 — Database (tuỳ chọn)
```
Có thông tin database không?
  [A] Có file schema-only (.sql) — đường dẫn?  (khuyến nghị đặt ở inputs/db/)
  [B] Có quyền đọc DB — tôi sẽ tự xuất schema-only theo lệnh agent đưa
  [C] Không có DB, nhưng source có migration / ORM model
  [D] Không có gì
```
| Chọn | `db_mode` | Hành vi |
|---|---|---|
| `[A]` | `DUMP` | `read-schema.py --dump`. Dump có dữ liệu → script exit 3 → yêu cầu dump schema-only |
| `[B]` | `READONLY_CONN` | Agent đưa lệnh `mysqldump --no-data` / `pg_dump --schema-only`; **user tự chạy** (agent không giữ mật khẩu DB) → như `[A]` |
| `[C]` | `MIGRATION` | Agent dựng `03/04` từ migration/ORM, evidence `code-ref` |
| `[D]` | `NONE` | O3 = ⬜, O6 chương DB ghi `Database not available.` |

---

## Lượt 4 — Figma (P7, P8)

```
P7. (tuỳ chọn) Có Figma design / design system của hệ thống hiện tại không?
    [A] Có — link figma.com/design/...   [B] Không có
    → dùng bổ sung O4 Design System. figma_input_url

P7b. (chỉ khi O4 sẽ chạy) Design System (O4) có publish thành artifact "Design System" trên claude.ai không?
    [A] Có — artifact private, tôi tự chia sẻ link khi cần   (khuyến nghị)
    [B] Không — chỉ giữ file trong 04_DesignSystem/project/ (publish sau được)
    → ds_publish

P8. Bạn muốn tôi vẽ Figma flow dự án (Output 1 Flow tổng quan + Output 2 Screen flow) ở đâu?
    [A] Có file Figma — link figma.com/design/... (page sẽ vẽ)
    [B] Chưa có link, tôi gửi sau
    [C] Không vẽ Figma lần này
    → figma_output_url
```
- P8 `[B]` → **DỪNG phần O5** chờ link, làm các output khác trước; cuối lượt nhắc lại 1 lần. Không tự skip.
- Link `/board/` (FigJam) → cảnh báo kit vẽ trên Design file, hỏi xác nhận.
- ⚠️ Nhắc user: **Figma và claude.ai là cloud bên ngoài** — chỉ đưa lên tên màn, ID, luồng, token, chữ UI, logo/icon; không dữ liệu thật.

---

## Lượt 5 — Output tuỳ chọn + an toàn dữ liệu

```
P9. Có lập Bug list hiện trạng (lỗi giao diện/chức năng mức Medium–High phát hiện khi quét) không?
    [A] Có — nội bộ review trước (mặc định)  [B] Có — gửi thẳng KH  [C] Không
    → bug_list = YES/NO, bug_recipient

P10. Ngôn ngữ tài liệu + người đọc?
    [VN] [JP] [EN] [VN+JP]  ·  Nội bộ / BrSE / Khách hàng            → lang, audience

P11. Phân loại dữ liệu của nguồn (bắt buộc — máy không tự nhận ra được dữ liệu production):
    [A] Website staging, dữ liệu test — không có dữ liệu người dùng thật
    [B] Website có dữ liệu thật của người dùng (production / staging copy từ prod)
    [C] Chưa rõ
```
| P11 | Hành vi |
|---|---|
| `[A]` | Chạy bình thường |
| `[B]` | ⚠️ **Cảnh báo:** screenshot sẽ chứa dữ liệu thật → đề nghị tài khoản test / staging. User vẫn giữ `[B]` → hỏi **ai duyệt** việc này, ghi `access_approved_by`, **không** chèn screenshot vào output gửi ra ngoài (O1 dùng `NO IMAGE — text only`), không đẩy ảnh lên Figma |
| `[C]` | Coi như `[B]` |

---

## Discovery Brief — in 1 lần, chờ 1 confirm

```
📋 DISCOVERY BRIEF — <system_name> · ver<N>_<DDMMYY>_<slug>

| # | Hạng mục | Giá trị | Nguồn |
|---|---|---|---|
| P0 | Phạm vi | ... | user |
| P1 | Website | WEB-01 <url> (staging) · WEB-02 ... | user |
| P2 | Tài khoản | WEB-01: admin, user — test, PM KH cấp, được phép | user |
| P3 | Quyền thao tác | READ_ONLY | user / **mặc định** |
| P4 | Vùng cấm | ... | user |
| P5 | Source | REPO-01 <path> FE→WEB-01 · REPO-02 <path> BE | user |
| P6 | Database | DUMP inputs/db/schema.sql | user |
| P7 | Figma input | — | user |
| P7b | Publish Design System | Có (private) | user |
| P8 | Figma output | <link> | user |
| P9 | Bug list | Có — nội bộ trước | user |
| P10 | Ngôn ngữ · người đọc | VN · nội bộ | mặc định |
| P11 | Dữ liệu nguồn | staging, dữ liệu test | user |

Output dự kiến: O1 ✅ · O2 ✅ · O3 ✅ · O4 ✅ · O5 ✅ · O6 ✅ · O7 ✅
Không chạy: <Ox — lý do> hoặc "không"
Budget crawl: ≤ 200 URL · ≤ 30 phút / site
Folder: outputs/ver<N>_<DDMMYY>_<slug>/

→ Đúng chưa? ("OK" để bắt đầu, hoặc sửa hạng mục sai)
```
⛔ **Không quét gì khi chưa có confirm.** Confirm xong mới `version-tool.py next --create`.

---

## G9 — Gặp hành động ghi khi crawl

Trigger: crawler gặp element khớp danh sách phá dữ liệu (`削除` · `Xoá` · `Thanh toán` · `Gửi mail`…).
```
Màn <SC-xxx> có nút「<nhãn>」— thao tác này có thể thay đổi dữ liệu thật.
  [A] Bỏ qua — ghi UNKNOWN cho hành vi nút này   (mặc định)
  [B] Được bấm — đây là staging có dữ liệu test
  [C] Tôi tự thao tác và gửi screenshot
```
`[A]` → item vẫn vào O1, mô tả `UNKNOWN — chưa quan sát được (bị chặn theo P3)` + Open Question.

## G10 — Tài liệu KH mâu thuẫn hệ thống (≥ 3 điểm)
```
Tài liệu khách hàng lệch với hệ thống thật ở <n> điểm.
  [A] Hệ thống thật thắng, ghi CONFLICT vào Open Questions   (mặc định)
  [B] Dừng, tôi hỏi khách hàng trước
  [C] Cho tôi xem danh sách lệch trước khi quyết
```
