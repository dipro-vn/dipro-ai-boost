# AI Agent Policies — system-to-doc

> Always-loaded qua `CLAUDE.md`. Sửa policy thì chỉ sửa file này.
>
> **Companion rules** (đọc khi cần chi tiết): `.claude/rules/DATA-PRIVACY.md` (dữ liệu KH) · `.claude/rules/SECURITY.md` (file cấm đọc) · `.claude/rules/RELIABILITY.md` (không bịa) · `.claude/rules/POLICY.md` (tài sản, AI tool, sự cố). Các file rules copy từ kit `requirement-to-flow`; chỗ nào nói "BA / SPEC.md" thì hiểu là "System Analyst / tài liệu O1–O7 + CR".

---

## 1. Năm nguyên tắc cốt lõi

| Policy | Nội dung | Vi phạm dẫn tới |
|---|---|---|
| **Bằng chứng trước, kết luận sau** | Mọi `Confirmed` phải có `EV ID` phân giải được | Tài liệu sai, khách mất niềm tin vào cả bộ |
| **Không đoán mò** | Thiếu thông tin → hỏi bằng `AskUserQuestion`; không có → `UNKNOWN` + Open Question, **chạy tiếp phần khác** | Giả định biến thành spec |
| **Read-only mặc định** | Không thao tác ghi trên hệ thống thật khi chưa qua P3 | Hỏng dữ liệu production — không hoàn tác được |
| **Stateless + versioned** | Mọi context đọc từ folder version; mỗi lần chạy 1 folder mới, không sửa version cũ | Tự cho là đã được duyệt · mất baseline |
| **Gate bằng máy** | PASS/FAIL do script, không do cảm nhận | Gate rỗng, báo xong khi chưa xong |

---

## 2. Tuyệt đối không làm với hệ thống của khách

- ❌ Sửa source code / cấu hình / dữ liệu của hệ thống đang phân tích — kit **chỉ đọc**
- ❌ Kết nối DB của khách, chạy bất kỳ câu SQL nào, đọc dòng dữ liệu (kể cả "xem thử")
- ❌ Bấm nút xoá / thanh toán / gửi mail khi chưa qua G9; vào vùng `forbidden_zones`
- ❌ Dùng tài khoản khi user chưa xác nhận **được phép** dùng nó để quét tự động (P2b)
- ❌ Khai thác / thử lỗ hổng bảo mật (kể cả để lấy PoC trên production)
- ❌ Vượt budget (200 URL / 30 phút / site) mà không báo — hết budget thì **dừng và báo phần đã phủ**

---

## 3. Dữ liệu nhạy cảm & bảo mật — CẢNH BÁO + DỪNG

> **Nguyên tắc:** KHÔNG đưa 秘密情報・個人情報 của khách hàng vào AI hay vào output. Phát hiện → **dừng việc đang làm, cảnh báo user ngay**, chỉ tiếp tục khi nguồn đã được xử lý (gỡ, thay bằng bản an toàn, hoặc user phân loại là không nhạy cảm).

| # | Nhóm | Ví dụ ở kit này |
|---|---|---|
| 1 | Thông tin cá nhân | Tên/email/SĐT người dùng hiện trên màn hình, trong dump, trong CR |
| 2 | Dữ liệu production | DB dump có dữ liệu, log, export, screenshot màn có dữ liệu thật |
| 3 | Credential | `.env`, private key, API key/token hardcode, connection string, mật khẩu tài khoản quét |
| 4 | Giao dịch / hợp đồng | Đơn hàng, thanh toán, hợp đồng thật |
| 5 | KH xác định confidential | 社外秘 / NDA |

### 3.1 Bốn lớp phát hiện

| Lớp | Cơ chế | Khi nào | Bắt nhóm |
|---|---|---|---|
| **S1** | `scan-sensitive.py` (exit 3 = dừng) · `read-schema.py` từ chối dump có dữ liệu | **Trước khi đọc** repo / dump / file input / CR | ②③ + ① dạng hàng loạt |
| **H06** | Hook `detect-pii.js` chặn ở `Write`/`Edit`/`Bash`/MCP Figma·Backlog·Slack·Drive | **Trước khi ghi / đẩy ra ngoài** | ①③④ |
| **Scan** | `node .claude/hooks/detect-pii.js --scan <ver>` | Trước khi đóng version | ①③④ |
| **Khai báo** | Câu P11 (nguồn có dữ liệu thật không) · P2b (tài khoản được phép không) | Preflight | ②⑤ — máy không nhận ra |

⚠️ Hook không đọc được nội dung ảnh — screenshot có dữ liệu thật vẫn lọt. Chặn bằng quy trình: tài khoản test / staging, P11 `[B]` → không chèn ảnh vào output gửi ngoài, không đẩy ảnh lên Figma.

### 3.2 Credential của chính việc khảo sát

- Mật khẩu tài khoản quét **không bao giờ** nằm trong file nào. Đăng nhập bằng `login-site.js --manual` (user tự gõ) hoặc biến môi trường.
- Phiên đăng nhập chỉ ở `.auth/` (gitignore, quyền 600), **không** copy vào `outputs/`.
- User dán mật khẩu vào chat → không ghi ra file, nhắc user đổi mật khẩu sau khảo sát.
- Không đọc `.env` / key store / `.git/config` của repo khách (`rules/SECURITY.md`). Cần biết cấu hình → chỉ ghi **tên key** từ `.env.example`.

---

## 4. Trung thực trong báo cáo

| Bắt buộc | Cấm |
|---|---|
| In số thật từ script: `N checks · X PASS · Y FAIL` | Gõ tay con số gate |
| `FAIL > 0` → sửa rồi chạy lại | Hạ ngưỡng gate cho dễ qua |
| Script lỗi → `❌ Blocked` | Tự chấm PASS bằng mắt |
| Output không chạy → ghi rõ trong README version + lý do | Im lặng thu hẹp scope |
| Báo cáo cuối: đường dẫn folder + từng output + số lượng | "Đã xong" chung chung |

Ba mức kết luận: `Confirmed` (≥ 1 evidence phân giải được) · `Inferred` / `To verify` (bắt buộc Open Question) · `UNKNOWN` (ghi rõ vì sao chưa quan sát được). **`UNKNOWN` không phải thất bại — ô trống mới là thất bại.**

---

## 5. Khi dính policy — phản ứng theo mức đã lỡ

> ⛔ **KHÔNG BAO GIỜ** dùng `AskUserQuestion` để xin phép tiếp tục vi phạm. Chỉ hỏi để **phân loại** (dữ liệu này có thật không?) hoặc **khắc phục** (đã lỡ, gỡ thế nào?).

| Mức | Tình huống | Agent làm gì | Hỏi user? |
|---|---|---|---|
| **0** | Hook chặn trước khi ghi | Thay dữ liệu mẫu (`DATA-PRIVACY.md` §4) rồi ghi lại | ❌ |
| **1** | S1 phát hiện secret / dữ liệu thật trong nguồn **trước khi đọc** | ⛔ **DỪNG đọc nguồn đó.** Báo: file nào, loại gì (không in giá trị). Hỏi cách xử lý: user gỡ file / đưa bản schema-only / xác nhận là dữ liệu giả | ✅ phân loại / khắc phục |
| **2** | Không chắc dữ liệu có thật không | Hỏi để phân loại; chưa rõ → coi là confidential | ✅ |
| **3** | Đã ghi vào file local, chưa bàn giao | Tự xoá/mask + **báo 1 dòng** | ❌ nhưng bắt buộc báo |
| **4** | **Đã đẩy ra ngoài** (Figma, Backlog, commit, version đã đóng) | **DỪNG TOÀN BỘ** + báo + hỏi cách khắc phục. **Không tự xoá** node Figma / version | ✅ — đây là sự cố |

Nghĩa vụ báo **PM / người phụ trách** thuộc về user — agent phải nói rõ nghĩa vụ đó còn nguyên (`rules/POLICY.md` §9).

---

## 6. Enforcement

| Lớp | File | Ghi chú |
|---|---|---|
| Rules | file này + `.claude/rules/*.md` | Ý định, ngoại lệ |
| Hook H06 | `.claude/hooks/detect-pii.js` · `.claude/settings.json` · `.claude/config/pii-patterns.json` | Self-test: `node .claude/hooks/selftest-detect-pii.js`. Dự án đã có `settings.json` riêng → **merge** khối `hooks`, đừng ghi đè |
| Script | `scan-sensitive.py` · `read-schema.py` · `crawl-site.js` (chặn ghi ở tầng network) | Gate máy |

Hai file nói ngược nhau → áp dụng bên **nghiêm hơn** + báo user để sửa file.
