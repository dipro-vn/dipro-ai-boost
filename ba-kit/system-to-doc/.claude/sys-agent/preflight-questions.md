# Gate hỏi người — wording + cách xử lý từng câu trả lời

> **Mọi gate dưới đây PHẢI gọi tool `AskUserQuestion`.** In bảng text rồi tự suy ra câu trả lời là anti-pattern nghiêm cấm.
>
> Mã câu (P0a, P2b, B1…) chỉ để agent tra cứu: nằm ở **tiêu đề mục** và **comment `<!-- -->`**, **không bao giờ** xuất hiện trong câu hỏi / option người dùng đọc. Câu chữ trong khối ``` ``` là chữ hiển thị — viết theo `writing-style.md` (điều người dùng thấy và làm, không mã nội bộ, thuật ngữ buộc dùng thì giải thích 1 câu).

---

## 0. Quy tắc hỏi — chỗ DUY NHẤT trong kit (R9 · R11)

| Quy tắc | Chi tiết |
|---|---|
| **Gom theo chủ đề** | Mỗi lượt `AskUserQuestion` = **1 chủ đề**, tối đa **4 câu** (giới hạn của tool). Không hỏi từng câu lẻ, không trộn 2 chủ đề trong 1 lượt. Chủ đề: Tên & phạm vi · Website · Source code & database · Figma · Tài liệu & dữ liệu · Quyết định lớn (trong Discovery Brief) |
| **Chỉ hỏi cái chưa biết** | Đầu lần chạy: `preflight-memory.py missing --outputs outputs` → chỉ hỏi câu trong `ask` (chưa có · đang bỏ qua · quá 90 ngày). Câu đã có → **1 bảng** (mục 1) chờ 1 xác nhận |
| **4 câu an toàn — luôn xác nhận lại, không cho bỏ qua** (D8) | Môi trường thử nghiệm hay thật (P1-env) · tài khoản có được phép quét tự động (P2b) · mức thao tác (P3) · có dữ liệu thật của người dùng (P11). Đã có câu trả lời → hỏi gọn "vẫn như lần trước chứ?" (mục 1b). Không có option "chạy trước, bổ sung sau" |
| **Cho phép chạy trước** | Mọi câu **không** an toàn có thêm 1 option: **"Chưa có — chạy v1 trước, bổ sung sau"** → `preflight-memory.py set --code <mã> --pending --by-role <vai trò>`. Lần sau người dùng bổ sung → `set` lại, chạy lại phần liên quan **ghi vào v1** (`version-tool.py snapshot` trước khi ghi đè, `versioning.md`) |
| **Nhập tự do** | URL, đường dẫn, tên → để option gợi ý, người dùng gõ ở ô **Other** |
| **Mơ hồ** | Hỏi lại đúng câu đó, **không đoán** |
| **Ghi nhớ** | Mỗi câu trả lời: `preflight-memory.py set --code <mã> --answer "<câu trả lời>" --by-role "<vai trò người trả lời>" [--source user\|code\|meta]` (nguồn: người dùng trả lời / đọc từ code / kế thừa 00_Meta) + ghi `00_Meta` của inventory như cũ. **Không bao giờ lưu mật khẩu / token** — chỉ tên role, đường dẫn file (script từ chối, exit 2) |

**Thứ tự:** G-R (khi đã có baseline) → bảng "đang dùng" + xác nhận an toàn (mục 1) → các lượt còn thiếu (Lượt 1–5) → Pha A đọc code + so token nháp (R10) → **Discovery Brief** có mục *Quyết định lớn* (mục 7) → recon → G9 / G10 khi phát sinh.

Memory: `outputs/_project/preflight-memory.json` — ngoài folder version, dùng chung cho ver1 / CR / ver<N+1>, gitignore (`.gitignore` của kit). Xem nhanh: `preflight-memory.py list --outputs outputs`.

---

## 1. Câu đã có — 1 bảng, 1 xác nhận

Agent tự chạy `missing`; mục `confirm_table` in thành bảng (cột: Hạng mục · Đang dùng · Nguồn · Ngày), rồi 1 câu `AskUserQuestion`:

```
Tôi đang dùng các thông tin sau từ lần trước (bảng trên). Có gì thay đổi không?
  [A] Không đổi — dùng tiếp
  [B] Có đổi — tôi ghi ở ô bên dưới (ví dụ: "website admin đổi địa chỉ thành https://…")
```
`[A]` → `preflight-memory.py confirm --outputs outputs --codes all --by-role <vai trò>`. `[B]` → `set` lại đúng các mục bị đổi; mục đổi kéo theo câu khác (đổi website → hỏi lại tài khoản) thì hỏi tiếp trong cùng chủ đề.

### 1b. Bốn câu an toàn — hỏi lại gọn mỗi lần (cùng 1 lượt, 4 câu)
<!-- P1-env · P2b · P3 · P11 — confirm_safety. Không có option bỏ qua. Trả lời khác lần trước → hỏi lại câu đầy đủ ở Lượt 2 / 5 -->
```
1. Lần trước bạn cho biết website là bản thử nghiệm (không phải bản khách đang dùng thật). Vẫn như lần trước chứ?   [Đúng] [Đã đổi]
2. Tài khoản đăng nhập là tài khoản thử nghiệm, được phép để tôi tự mở từng trang. Vẫn như lần trước chứ?            [Đúng] [Đã đổi]
3. Tôi chỉ được xem, không bấm lưu / gửi / xoá. Vẫn như lần trước chứ?   (ghi đúng mức đã chọn lần trước)          [Đúng] [Đã đổi]
4. Website không có dữ liệu thật của người dùng. Vẫn như lần trước chứ?                                                [Đúng] [Đã đổi]
```
"Đã đổi" → hỏi lại câu đầy đủ tương ứng (P1 / P2b / P3 / P11). Chưa trả lời → **coi là môi trường thật**, chỉ đăng nhập tay, chỉ xem.

---

## G-R — Đã có bản khảo sát trước (chỉ khi `version-tool.py context` có `latest_baseline`)

Agent **tự** chạy `context`, Read file trong `read`, rồi mới hỏi — không bắt người dùng chỉ version.

```
Đã có bản khảo sát ngày <DD/MM/YYYY>: <a> website · <m> màn hình · <p> chức năng phía máy chủ · <t> bảng dữ liệu · <q> điểm còn chờ xác nhận.
Yêu cầu thay đổi đang mở: <tên yêu cầu> | không có. Góp ý chưa xử lý: <n> | không có.
Lần này bạn muốn:
  [A] Cập nhật phần còn thiếu, kiểm lại phần cũ và làm theo góp ý   (đề xuất)
  [B] Khảo sát lại từ đầu — hệ thống đã đổi nhiều
  [C] Không khảo sát — chỉ đọc lại bản cũ để trả lời câu hỏi
  [D] Thực ra tôi có 1 yêu cầu thay đổi → chuyển sang phân tích yêu cầu thay đổi
```
<!-- [A] DELTA (mặc định = suggest.flow1_mode) · [B] FULL · [C] READ_ONLY_REVIEW · [D] Luồng 2 -->

| Chọn | `run_mode` | Hành vi |
|---|---|---|
| `[A]` | `DELTA` | Giữ dòng cũ + `Note = Carried from ver<K>`; evidence > 30 ngày → chụp lại nếu dòng đó `Confirmed`. Baseline chưa khoá (`suggest.flow1_action = rerun_in_place`) → ghi vào chính baseline đó, `snapshot` trước khi ghi đè. Baseline đã khoá (`locked`) → hỏi thêm (multiSelect) *"Yêu cầu thay đổi nào khách đã duyệt và đã đưa lên hệ thống?"* → `version-tool.py promote --cr … --approved --coded --create` → quét lại phần yêu cầu đó chạm vào ver<N+1>; không có → báo "bản khảo sát ngày … đã khoá", chỉ đọc lại. Có `pending_feedback` → áp dụng + ghi **Feedback đã xử lý** |
| `[B]` | `FULL` | Bỏ dữ liệu cũ, vẫn dùng memory làm đề xuất |
| `[C]` | `READ_ONLY_REVIEW` | Không quét, **không** tạo version mới |
| `[D]` | — | Đọc `flow-2-change-request.md`, chạy Luồng 2 |

---

## Lượt 1 — Tên & phạm vi (P0a · P0b · P0c)

```
1. Hệ thống tên là gì? (dùng đặt tên file)                                           → gõ ở ô Other
2. Đặt tên ngắn cho lần khảo sát này?                    [baseline] [khao-sat-lan-dau] (Other)
3. Lần này khảo sát tới đâu?
   [A] Toàn bộ hệ thống  [B] Chỉ một số phần — ghi tên phần  [C] Chỉ một luồng nghiệp vụ, ví dụ "đặt hàng → thanh toán"
```
<!-- P0a system_name · P0b slug/version_label · P0c scope. P0a và P0c KHÔNG có option "chạy trước": chưa trả lời → DỪNG, không đoán [A]. P0b có thể mặc định "baseline" -->

---

## Lượt 2 — Website (P1 · P1-env · P2a · P2b) và (P3 · P4) ⚠️ lượt quan trọng nhất về an toàn

Lượt 2a (4 câu):
```
1. Có những website nào cần khảo sát? Ghi địa chỉ từng website.
   [A] 1 website  [B] Nhiều website (ví dụ trang người dùng + trang quản trị)  [C] Không có website để mở
   [D] Chưa có — chạy v1 trước, bổ sung sau
   → Other: "Trang người dùng https://stg.abc.jp; Trang quản trị https://stg-admin.abc.jp"
2. Các website đó là bản thử nghiệm hay bản khách hàng đang dùng thật?
   [A] Bản thử nghiệm (dev / staging / test)  [B] Bản đang dùng thật  [C] Chưa rõ
3. Tôi đăng nhập bằng những loại tài khoản nào?
   [A] Có tài khoản cho mọi loại người dùng — ghi tên loại (quản trị, nhân viên…)  [B] Chỉ một số loại
   [C] Không có — chỉ xem trang không cần đăng nhập  [D] Chưa có — chạy v1 trước, bổ sung sau
4. Tài khoản này có phải tài khoản thử nghiệm mà khách hàng / PM cấp, và cho phép tôi tự động mở từng trang để xem không?
   [A] Đúng — tài khoản thử nghiệm, được phép  [B] Tài khoản thật hoặc dùng chung — chưa rõ có được phép không  [C] Không được phép
```
<!-- 1=P1 websites (WEB-01=<url>;… + sheet 10_Site) · 2=P1-env (AN TOÀN, T1; [C] → coi là thật) · 3=P2a accounts (chỉ TÊN role) · 4=P2b (AN TOÀN, T2) + access_approved_by = vai trò người cấp -->

Lượt 2b (2 câu):
```
5. Trên website, tôi được thao tác tới mức nào?
   [A] Chỉ xem — không bấm lưu / gửi / xoá   (đề xuất)
   [B] Xem + được thêm / sửa dữ liệu trên bản thử nghiệm, bằng tài khoản thử nghiệm
   [C] Xem + được thêm / sửa cả trên bản đang dùng thật — tôi chịu trách nhiệm
   [D] Không mở website — tôi tự gửi ảnh chụp màn hình
6. Có trang / chức năng nào tuyệt đối không được đụng vào không? (ví dụ gửi mail hàng loạt, thanh toán)
   [A] Không có   → Other: liệt kê
```
<!-- 5=P3 (AN TOÀN) → crawl_mode · 6=P4 forbidden_zones → crawl-site.js --forbid -->

- Có bản thử nghiệm mà vẫn chọn bản thật → hỏi lại 1 lần: *"Bản thử nghiệm an toàn hơn. Bạn chắc muốn tôi mở bản đang dùng thật?"*
- Câu 1 `[C]` → O1 = ⬜ (`không có website`), O4 chỉ chạy nếu có Figma. Chạy tiếp phần khác.

| Câu 4 (P2b) | Hành vi |
|---|---|
| `[A]` | Đăng nhập bằng `login-site.js` (xem dưới) |
| `[B]` | ⛔ **Không đăng nhập.** Chỉ quét trang không cần đăng nhập. Mọi màn sau login = `To verify` + Open Q "cần tài khoản thử nghiệm được phép" |
| `[C]` | Như `[B]`, ghi rõ lý do |

| Câu 5 (P3) | `crawl_mode` | `crawl-site.js --mode` | Thực thi |
|---|---|---|---|
| `[A]` | `READ_ONLY` | `read-only` | **Chặn ở tầng network** mọi request khác GET/HEAD |
| `[B]` | `SUBMIT_STAGING` | `submit-staging` | Cho POST, **vẫn** chặn nút xoá / thanh toán / gửi mail |
| `[C]` | `SUBMIT_PROD` | `submit-prod` | Như `[B]` + in cảnh báo trước mỗi thao tác ghi |
| `[D]` | `NO_CRAWL` | — | Không chạy crawler |

DELETE **không bao giờ** được cấp qua câu này — gặp nút xoá luôn đi qua G9. Chưa trả lời → `[A]` + báo: `Tôi đang chỉ xem — mọi thao tác lưu / gửi / xoá đều bị chặn.`

**Cách đăng nhập — agent KHÔNG cầm mật khẩu (`POLICIES.md` §3.2):**

| Môi trường | Cách |
|---|---|
| **Thử nghiệm đã xác nhận** (câu 2 = `[A]` · câu 4 = `[A]` · Lượt 5 câu dữ liệu thật = `[A]`) | 1. Agent chạy `node $S/login-site.js --init-cred-file .auth/credentials.local.env --site WEB-01 --url <url> --accounts admin,user [--basic]` → tạo **file mẫu** (giá trị trống). 2. Nhờ người dùng: *"Bạn mở file `.auth/credentials.local.env`, điền tài khoản cho từng loại người dùng, ghi `WEB-01.ENV=TEST`, lưu lại rồi trả lời 'xong'."* 3. Agent chạy `login-site.js --form --cred-file .auth/credentials.local.env --site WEB-01 --account admin` và `crawl-site.js … --cred-file … --account admin` (mỗi role 1 lần). **Agent không Read / cat file đó** |
| **Bản thật / chưa chắc** | Chỉ `--manual` — người dùng tự gõ trong cửa sổ trình duyệt. Script từ chối `--cred-file` khi `ENV ≠ TEST` |

- `--manual`: `node $S/login-site.js --manual --url <login> --save .auth/WEB-01.json` → mở trình duyệt, **người dùng tự gõ**, script lưu phiên.
- Script không tự đăng nhập được (exit 4: quá 2 lần / quá thời gian) → dừng tự thử, nhắn: *"Tôi chưa đăng nhập được vào trang 「<tên site>」. Bạn đăng nhập tay giúp tôi trong cửa sổ trình duyệt sắp mở, xong trả lời 'xong'."* → `--manual` (`system-analyst.md` Bước 4).
- Người dùng dán mật khẩu vào chat → không dùng lại; hướng dẫn chuyển vào file mẫu, nhắc đổi mật khẩu đã dán.
- Đăng nhập qua trang của bên khác (SSO) → `--cred-file` không điền được (chỉ gửi tới đúng website đã khai) → dùng `--manual`.
- Mất phiên giữa chừng: crawler (có `--cred-file`) **tự đăng nhập lại**, ghi URL gây mất phiên (`sessionKiller`), không quay lại URL đó; thử lại 1 lần để xác định đúng màn (tối đa 5 lần đăng nhập lại). Kết quả: `crawl-summary.relogins`, `sessionKillers[]`, `stopped`; `blocked.json` kind `session-lost`.
- Kiểm người dùng đã điền xong: chạy lại `--init-cred-file` → `emptyKeys` (tên key còn trống, không có giá trị) + `envIsTest`. Giá trị có `#` / dấu cách → đặt trong ngoặc kép.
- Role không đăng nhập được → mọi chức năng của role đó `To verify` + Open Q, **cấm** đoán theo tên menu.

---

## Lượt 3 — Source code & database (P5a · P5b · P6)

> **Agent tự `Glob inputs/repo/*/` và `inputs/db/*.sql` trước khi hỏi.** Có folder / file → in danh sách để người dùng xác nhận thay vì bắt gõ lại đường dẫn.

```
1. Tôi thấy các thư mục source sau trong inputs/repo/: <danh sách>. Đúng đủ chưa?
   [A] Đúng đủ  [B] Còn repo ở chỗ khác — ghi đường dẫn  [C] Không có source code  [D] Chưa có — chạy v1 trước, bổ sung sau
2. (khi có phần giao diện) Thư mục giao diện nào là của website nào?
   → Other: "web-fe → trang người dùng; admin-fe → trang quản trị"     [Chưa có — chạy v1 trước, bổ sung sau]
3. Có thông tin cấu trúc database không? (chỉ cấu trúc bảng, không có dữ liệu)
   [A] Có file cấu trúc (.sql) — tôi thấy: <inputs/db/…>   [B] Có quyền đọc database — tôi tự xuất cấu trúc theo lệnh bạn đưa
   [C] Không có, nhưng source code có định nghĩa bảng      [D] Không có gì   [E] Chưa có — chạy v1 trước, bổ sung sau
```
<!-- 1=P5a source_repos + sheet 11_Repo (REPO-01…) · 2=P5b For Site (không đoán theo tên folder; chưa gán → hỏi lại) · 3=P6 db_mode: [A] DUMP · [B] READONLY_CONN · [C] MIGRATION · [D] NONE -->

- Không có source → O2 = ⬜, chạy **chế độ chỉ website** (D9), ghi rõ trong Brief.
- Repo bị `scan-sensitive.py` báo HIGH → `system-analyst.md` §6.

| Câu 3 | `db_mode` | Hành vi |
|---|---|---|
| `[A]` | `DUMP` | `read-schema.py --dump`. File có dữ liệu → script exit 3 → yêu cầu file chỉ cấu trúc |
| `[B]` | `READONLY_CONN` | Agent đưa lệnh `mysqldump --no-data` / `pg_dump --schema-only`; **người dùng tự chạy** (agent không giữ mật khẩu DB) → như `[A]` |
| `[C]` | `MIGRATION` | Dựng bảng / cột từ code (`read-orm-schema.py`), evidence `code-ref` |
| `[D]` | `NONE` | O3 = ⬜, O6 chương DB ghi `Database not available.` |

---

## Lượt 4 — Figma (P7 · P7b · P8)

```
1. Có file Figma thiết kế của hệ thống hiện tại không? (dùng để bổ sung bộ quy chuẩn giao diện)
   [A] Có — dán link figma.com/design/…  [B] Không có  [C] Chưa có — chạy v1 trước, bổ sung sau
2. (khi làm bộ quy chuẩn giao diện) Có đăng bộ quy chuẩn lên claude.ai thành 1 trang riêng (chỉ bạn xem, tự chia sẻ khi cần) không?
   [A] Có  (đề xuất)   [B] Không — chỉ giữ file trong thư mục kết quả
3. Tôi vẽ luồng nghiệp vụ, luồng màn hình và sơ đồ dữ liệu ở file Figma nào?
   [A] Có file — dán link figma.com/design/… (trang sẽ vẽ)  [B] Chưa có link — tôi gửi sau  [C] Không vẽ Figma lần này
```
<!-- 1=P7 figma_input_url (O4) · 2=P7b ds_publish (không trả lời → không publish) · 3=P8 figma_output_url (O5 + sơ đồ DB cho O6, R4) -->
- Câu 3 `[B]` → làm các output khác trước, O5 + link sơ đồ O6 chờ link; cuối lượt nhắc lại 1 lần. Không tự bỏ.
- Link `/board/` (FigJam) → nói rõ kit vẽ mọi thứ (Output 1 / 2 và sơ đồ DB) trên **file Figma design**; xin link `figma.com/design/…`. Không tự tạo file mới.
- Nhắc 1 câu: *"Figma và claude.ai là dịch vụ bên ngoài công ty — tôi chỉ đưa lên tên màn, luồng, chữ trên giao diện, logo; không đưa dữ liệu thật."* Việc đưa **sơ đồ database** lên Figma được hỏi riêng ở Brief (B5, D5).

---

## Lượt 5 — Tài liệu & dữ liệu (P9 · P10 · P11)

```
1. Có lập danh sách lỗi hiện có của hệ thống không? (lỗi làm người dùng thao tác không được hoặc sai;
   tôi đọc code và mở thử website; chỉ ghi lỗi mức Cao trở lên, 1 sheet)
   [A] Có — nội bộ xem trước (đề xuất)  [B] Có — gửi thẳng khách hàng  [C] Không
2. Tài liệu viết bằng tiếng gì, ai đọc?
   [Tiếng Việt] [Tiếng Nhật] [Tiếng Anh] [Việt + Nhật]  ·  Nội bộ / khách hàng
3. Website có dữ liệu thật của người dùng không? (tên, email, đơn hàng của người thật)
   [A] Không — chỉ dữ liệu thử nghiệm  [B] Có dữ liệu thật (bản đang dùng, hoặc bản thử nghiệm chép từ bản thật)  [C] Chưa rõ
```
<!-- 1=P9 bug_list = YES/NO, bug_recipient. 1 sheet Bug List, chỉ High / Urgent, nguồn code + website (o7-bug-list.md)
     2=P10 lang, audience · 3=P11 (AN TOÀN, T3; [C] = [B]) -->

| Câu 3 (P11) | Hành vi |
|---|---|
| `[A]` | Chạy bình thường |
| `[B]` | ⚠️ Báo: *"Ảnh chụp màn hình sẽ có dữ liệu thật. Nên dùng tài khoản / bản thử nghiệm."* Vẫn giữ `[B]` → hỏi **ai duyệt** (vai trò), ghi `access_approved_by`, **không** chèn ảnh vào output gửi ra ngoài (O1 dùng `NO IMAGE — text only`), không đưa ảnh lên Figma |
| `[C]` | Như `[B]` |

---

## S1 — Phân loại kết quả quét dữ liệu nhạy cảm

`scan-sensitive.py` exit 3 → dừng, hỏi **phân loại / cách khắc phục** (không xin phép vi phạm — `POLICIES.md` §5). Trước khi hỏi: `preflight-memory.py missing --outputs outputs --sensitive-files <file bị báo…>` → chỉ hỏi file trong `sensitive_unclassified`; file đã phân loại lần trước → dùng lại, ghi 1 dòng trong run-log.
```
Tôi thấy <n> file có thể chứa thông tin nhạy cảm: <tên file — loại, không in nội dung>. Đây là:
  [A] Dữ liệu mẫu / giả do khách tạo — dùng bình thường
  [B] Dữ liệu thật — tôi bỏ qua file này, bạn gỡ hoặc thay bản an toàn
  [C] Chưa rõ — tôi tạm coi là dữ liệu thật và hỏi lại PM
```
Sau khi trả lời: `preflight-memory.py set-sensitive --classification "<lựa chọn>" --files <file…> --by-role <vai trò>`.
File chỉ bị chặn vì **tên** (chứa password / token / credential…) mà người dùng chọn `[A]` / "báo nhầm" → `scan-repo.py --sensitive-memory outputs/_project/preflight-memory.json` đọc lại; `.env`, key, dump, `.npmrc` / `.yarnrc.yml` vẫn luôn bị chặn.

---

## 7. Discovery Brief — in 1 lần, chờ 1 xác nhận (sau Pha A đọc code)

Trước Brief (R10): xong Pha A (`system-analyst.md` Bước 4) → so token nháp giữa các website **chỉ từ code**:
```bash
python3 $S/extract-design-tokens.py --code-only --css-root REPO-01@WEB-01=<fe-1> --css-root REPO-03@WEB-02=<fe-2> \
     --out $I/recon/design-draft          # dsLayout.mode: single | themes | per-site + diffs (font / radius / spacing)
```
(Chưa có folder version → `--out` tạm ở `outputs/_project/design-draft/`, chép vào `_internal/recon/` sau khi tạo version.)

```
📋 Thông tin khảo sát — <tên hệ thống> · <tên folder sẽ tạo>

| Hạng mục | Đang dùng | Nguồn |
|---|---|---|
| Phạm vi | Toàn bộ hệ thống | bạn trả lời |
| Website | Trang người dùng https://stg… (thử nghiệm) · Trang quản trị … | bạn trả lời |
| Tài khoản | quản trị, nhân viên — thử nghiệm, PM phía khách cấp, được phép | bạn trả lời |
| Mức thao tác | Chỉ xem | bạn trả lời / mặc định |
| Vùng không đụng | … | bạn trả lời |
| Source code | web-fe (giao diện trang người dùng) · api (máy chủ) | đọc từ thư mục |
| Database | File cấu trúc inputs/db/schema.sql + định nghĩa bảng trong code | bạn trả lời |
| Figma | Thiết kế: — · Vẽ sơ đồ: <link> | bạn trả lời |
| Danh sách lỗi | Có — nội bộ xem trước | bạn trả lời |
| Ngôn ngữ · người đọc | Tiếng Việt · nội bộ | mặc định |
| Dữ liệu thật | Không — dữ liệu thử nghiệm | bạn trả lời |
| Chưa có, chạy trước | <hạng mục đang bỏ qua> hoặc "không" | bạn chọn |

Quyết định lớn (tôi đề xuất, bạn chọn):
  1. Bộ quy chuẩn giao diện: <ví dụ "2 website khác nhau về chiều cao thanh đầu trang (56 / 64 px), độ bo góc nút (4 / 12 px), cỡ chữ
     → đề xuất làm 2 bộ riêng">. Đồng ý?
  2. Tài liệu sẽ làm: danh sách màn hình · tài liệu API · tài liệu database · bộ quy chuẩn giao diện · sơ đồ Figma · tài liệu tổng hợp ·
     hướng dẫn nghiệp vụ · hướng dẫn chạy local · danh sách lỗi. Bỏ cái nào?
  3. Thư mục <legacy-admin> có vẻ là bản cũ không còn dùng (<căn cứ: không có route nào trỏ tới / commit cuối 2019>) → đề xuất không khảo sát. Đồng ý?
  4. Phạm vi: <n> website · loại người dùng <…>. Đúng chưa?
  5. Sơ đồ database và API sẽ vẽ lên Figma (dịch vụ bên ngoài công ty; chỉ tên bảng, tên chức năng, không dữ liệu). Đồng ý?

Không làm: <tài liệu — lý do> hoặc "không"
Giới hạn quét: ≤ 200 trang · ≤ 30 phút mỗi website · mỗi kiểu trang lấy mẫu ≤ 3
Folder: outputs/ver1_<DDMMYY>_<slug>/

→ Đúng chưa? ("OK" để bắt đầu, hoặc sửa hạng mục sai)
```
<!-- Agent: Brief là 1 lượt AskUserQuestion — câu 1 "Thông tin trên đúng chưa?" + tối đa 3 câu cho Quyết định lớn chưa có trong memory
     (B1 DS 1/nhiều = dsLayout.mode, căn cứ = dsLayout.diffs · B2 O4 (tuỳ chọn) / O5 / O7 / O9 làm không · B3 repo legacy · B4 site/role · B5 D5 đưa sơ đồ DB lên Figma).
     > 3 quyết định chưa có → lượt 2 cùng chủ đề "Quyết định lớn". Mỗi quyết định: preflight-memory.py set --code B<n> …
     B5 = không → O6 ghi chú trỏ ảnh ERD trong 03_DB (o6-overview.md), không vẽ sơ đồ DB lên Figma.
     Không giao source (D9) → dòng Source ghi "chế độ chỉ website — API / database chỉ suy từ màn hình và request quan sát được". -->

⛔ **Không quét website khi chưa có xác nhận.** Xác nhận xong mới `version-tool.py next --create`.

---

## G9 — Gặp nút có thể thay đổi dữ liệu khi quét

Trigger: crawler gặp element khớp danh sách phá dữ liệu (`削除` · `Xoá` · `Thanh toán` · `Gửi mail`…).
```
Màn 「<tên màn>」 có nút 「<nhãn>」 — bấm nút này có thể thay đổi dữ liệu thật.
  [A] Bỏ qua — tôi mô tả nút này theo code; chỗ code không rõ ghi "Cần xác nhận"   (đề xuất)
  [B] Được bấm — đây là bản thử nghiệm có dữ liệu thử
  [C] Tôi tự thao tác và gửi ảnh chụp
```
`[A]` → item vẫn vào O1, hành vi mô tả từ handler trong code (code-ref ở cột R); code cũng không rõ → "Cần xác nhận — Q-xxx" + Open Question.

## G10 — Tài liệu của khách khác hệ thống thật (≥ 3 điểm)
```
Tài liệu khách hàng gửi khác với hệ thống đang chạy ở <n> điểm (ví dụ: tài liệu ghi có nút 「CSV出力」, màn hình thật không có).
  [A] Lấy hệ thống đang chạy làm chuẩn, ghi các điểm khác vào danh sách cần xác nhận   (đề xuất)
  [B] Dừng — tôi hỏi khách hàng trước
  [C] Cho tôi xem danh sách điểm khác trước khi quyết
```
<!-- [A] → CONFLICT trong 06_OpenQuestions -->
