# DATA PRIVACY — Dữ liệu bí mật & cá nhân của khách hàng (秘密情報・個人情報)

> **Bản rút gọn cho BA kit.** Nguồn đầy đủ: `POLICIES.md` §3.6 (canonical, dùng chung mọi kit).
> File này chỉ giữ phần **liên quan tới công việc BA**: input là tài liệu/họp/ảnh của khách, output là SPEC + Figma + prototype.
>
> **Đọc on-demand khi:** nhận file KH cung cấp · xử lý meeting note/transcript · nhận screenshot hệ thống thật · trước khi vẽ Figma · trước khi bàn giao.

---

## 1. Nguyên tắc

> **KHÔNG đưa trực tiếp 秘密情報・個人情報 của khách hàng vào AI.**

| # | Nhóm dữ liệu | Ví dụ |
|---|---|---|
| 1 | Thông tin định danh cá nhân | Tên, email, SĐT, địa chỉ, thông tin member/user thực tế |
| 2 | Dữ liệu production | DB dump, export, log, bản ghi nghiệp vụ thật |
| 3 | Credential | Password, API key, token, connection string |
| 4 | Giao dịch / hợp đồng xác định cá nhân | Đơn hàng, thanh toán, hợp đồng, bảng lương |
| 5 | Dữ liệu KH xác định là confidential | 社外秘 / confidential / thuộc NDA |

Không chắc → **mặc định coi là confidential**, hỏi PM.

---

## 2. Bản đồ rủi ro của BA kit — nguồn nào hay chứa PII

Đối chiếu với **8 loại source** ở `.claude/ba-agent/preflight-questions.md`:

| Loại source | PII thường gặp | Cách xử lý |
|---|---|---|
| **Simple Estimate** (.xlsx) | Giá, man-month, thông tin hợp đồng | Chỉ lấy **function inventory**. ❌ Không copy số tiền vào SPEC |
| **Detailed Spec / tài liệu KH** | Tên người phụ trách, email liên hệ, ví dụ dữ liệu thật | Trích đúng đoạn cần; thay danh từ riêng bằng placeholder |
| **Meeting Note** | Tên người dự họp, email, tên khách hàng cuối | Trong SPEC dùng **vai trò** (`BrSE A`, `PM phía KH`), không dùng tên thật |
| **Full Transcript** | Rất cao — tên, SĐT, chuyện nội bộ ngoài lề | Trích đúng đoạn làm evidence. ❌ Không paste nguyên transcript vào SPEC/Figma |
| **BRSE Raw Flow** | Thường thấp | — |
| **Approved FigJam** | Có thể chứa ảnh chụp màn hình thật | Kiểm trước khi trích |
| **Figma Design / UI Image / Screenshot** | **Rất cao** — màn hình chụp từ hệ thống đang chạy chứa dữ liệu member thật | Yêu cầu bản chụp bằng **tài khoản test**; không có thì che vùng nhạy cảm trước khi dùng |
| **Source Code / Existing System / URL production** | Credential trong config, dữ liệu thật trên màn | ❌ Không đọc `.env`/config secret — **không có hook chặn chiều đọc**, chỉ rule `SECURITY.md` §1 ngăn. Không đăng nhập bằng tài khoản thật của khách |

---

## 3. Bản đồ rủi ro — output nào hay làm rò rỉ

| Output | Rủi ro | Bắt buộc |
|---|---|---|
| **SPEC.md** | Dán ví dụ dữ liệu thật vào Business Rules / AC / Screen Details | Dùng dữ liệu mẫu ở §4 |
| **`## Source Register`** | Ghi tên người thật làm evidence locator | Dùng vai trò + timestamp: `[00:14:32] BrSE A`, không ghi họ tên đầy đủ |
| **Figma Frame 1/2/3** | ⚠️ **Figma là dịch vụ cloud bên ngoài** — mọi thứ vẽ lên đó là đã đưa ra ngoài | ❌ Không vẽ dữ liệu thật lên mockup. Mọi label/list/record trên frame dùng dữ liệu mẫu |
| **HTML Prototype** | Hard-code dữ liệu thật vào mock data | Dùng dữ liệu mẫu |
| **Basic Design (.xlsx)** | Ảnh UI chèn vào sheet chứa dữ liệu member thật | Như hàng Screenshot ở §2 |
| **`versions/` snapshot** | PII bị đóng băng vĩnh viễn trong lịch sử | Rà trước khi snapshot — sửa sau khi snapshot là đã muộn |
| **Backlog / MCP** | Đẩy nội dung có PII lên service ngoài | Chỉ gửi nội dung đã làm sạch |

---

## 4. Bộ dữ liệu mẫu chuẩn — dùng nhất quán trong mọi output

| Loại | Dùng |
|---|---|
| Họ tên | `Nguyễn Văn A` · `Nguyễn Thị B` · `山田太郎` |
| Email | `user_a@example.com` |
| Điện thoại | `090-0000-0000` |
| Địa chỉ | `Số 1, Đường ABC, Quận 1, TP.HCM` |
| Mã đơn / mã giao dịch | `SO-0001` · `TXN-0001` |
| Số tiền | `1,000` (số tròn, không phải giá thật của KH) |
| Công ty | `Công ty ABC` |
| Tài khoản | `test_user` / `test_admin` |

Dùng đúng bộ này để người review nhận ra ngay đâu là dữ liệu giả.

---

## 5. Checklist trước khi bàn giao / snapshot version

- [ ] SPEC.md không còn tên thật, email thật, SĐT thật, địa chỉ thật
- [ ] SPEC.md không còn số tiền / điều khoản hợp đồng thật
- [ ] `## Source Register` dùng vai trò thay vì họ tên đầy đủ
- [ ] Figma frame không hiển thị dữ liệu thật của member/user
- [ ] HTML prototype dùng dữ liệu mẫu ở §4
- [ ] Không có file `.env` / dump / export nằm trong thư mục output
- [ ] Ảnh chèn vào output được chụp bằng tài khoản test, hoặc đã che vùng nhạy cảm

Có 1 ô chưa tick → **không snapshot, không bàn giao**.

---

## 6. Khi lỡ đưa dữ liệu thật vào

> Đây là **tóm tắt**. Phản ứng đúng phụ thuộc **đã lỡ tới đâu** → bảng 5 mức ở **§8** (và `POLICIES.md` §5).

1. **Dừng ngay**, không dùng tiếp output đó
2. **Báo user ngay** — nêu rõ: lỡ cái gì, ở output nào, đã ra ngoài chưa
3. **Chưa ra ngoài** (còn ở file local) → tự mask/xoá rồi báo 1 dòng, không cần hỏi
4. **Đã ra ngoài** (Figma cloud / Backlog / Slack / Drive / commit / snapshot `versions/`) → **KHÔNG tự xoá** node hay snapshot; dừng và hỏi cách khắc phục (§8)
5. Nói rõ với user: nghĩa vụ báo **người phụ trách / PM** theo `INCIDENT_REPORTING` (`.claude/rules/POLICY.md` §9) **vẫn còn nguyên** dù chọn phương án nào
6. ❌ Không tự xử lý im lặng

---

## 7. Làm sao biết đang vi phạm — 4 lớp phát hiện

Trước hết phải tách 5 nhóm làm hai loại, vì chúng cần cơ chế hoàn toàn khác nhau:

| Loại | Nhóm | Vì sao |
|---|---|---|
| **Máy nhìn ra được** | ① PII · ③ Credential · ④ Giao dịch | Có **hình dạng**: email, SĐT, số thẻ, JWT, `sk-`, `AKIA` |
| **Máy KHÔNG nhìn ra được** | ② Dữ liệu production · ⑤ KH xác định confidential | Không có hình dạng. `orders.csv` trông y hệt `mock_orders.csv` |

Viết regex để bắt nhóm ② và ⑤ là vô ích. Chúng phải chặn ở **cửa vào**, không phải cửa ra.

| Lớp | Cơ chế | Lúc nào | Tin được? | Bắt nhóm |
|---|---|---|---|---|
| **L1 — Hook H06** | `.claude/hooks/detect-pii.js` đọc `tool_input`, khớp pattern → `exit 2`, tool call bị huỷ | **Trước khi** ghi/gửi | ✅ Tất định, ngoài tầm LLM | ①③④ |
| **L2 — Quét trước bàn giao** | `node .claude/hooks/detect-pii.js --scan <thư mục output>` | Trước snapshot / bàn giao | ✅ Tất định | ①③④ |
| **L3 — Khai báo nguồn** | Cột `Chứa PII?` trong bảng phân loại source của Discovery Brief | Bước 1, trước khi đọc file | ✅ Vì **người** khai | **②⑤** |
| **L4 — AI tự soi** | Agent tự kiểm theo rule này | Bất kỳ lúc nào | ❌ **Yếu nhất** | — |

> ⚠️ Đừng dựa vào L4. Nó yếu vì **kẻ vi phạm tự chấm điểm mình**: AI dán email thật vào SPEC chính là AI phải tự nhận ra nó vừa dán email thật.

**H06 chặn ở đâu:**

| Matcher | Chặn gì |
|---|---|
| `Write` · `Edit` · `MultiEdit` · `NotebookEdit` | PII lọt vào SPEC.md / prototype |
| `mcp__*figma*` | ⚠️ **Đẩy PII lên Figma cloud** — ra khỏi công ty |
| `mcp__*backlog*` · `mcp__*slack*` · `mcp__*drive*` | Đẩy PII lên service ngoài |
| `Bash` | `cat khach_hang.csv`, `psql postgres://user:pass@...` |

**Giới hạn phải biết — đừng tưởng đã an toàn:**

- ❌ Hook **chỉ đọc text trong tool call**. Không mở được nội dung file `.png`/`.jpg`. **Screenshot chứa email thật vẫn lọt qua** — chặn bằng quy trình (tài khoản test / staging), không bằng script.
- ❌ Hook không quét được nội dung file mà agent chỉ *đọc* rồi tóm tắt trong đầu.
- ❌ Nhóm ② và ⑤ hoàn toàn nằm ngoài tầm của hook.

**Bảo trì:**

```bash
node .claude/hooks/selftest-detect-pii.js     # 15 ca — chạy lại sau MỖI lần sửa hook/pattern
node .claude/hooks/detect-pii.js --scan <thư mục output>   # quét trước khi bàn giao
node .claude/hooks/detect-pii.js --scan . --all           # quét cả .claude/ (mặc định bỏ qua)
```

Báo động giả → thêm giá trị vào `allowValues` trong `.claude/config/pii-patterns.json`.
⛔ **Không** thêm file output thật (`SPEC.md`, `prototype/`, `versions/`) vào `allowPathPatterns` để gate im lặng — đó là tắt gate, không phải sửa gate.

---

## 8. Phát hiện vi phạm rồi thì làm gì

**Không phải lúc nào cũng hỏi user.** Phân theo *đã lỡ tới đâu*:

| Tình huống | Hành động | `AskUserQuestion`? |
|---|---|---|
| Hook H06 chặn trước khi ghi | Tool call bị huỷ → **tự mask rồi ghi lại** | ❌ Chưa có gì xảy ra |
| AI tự nhận ra trước khi ghi | **Tự thay bằng dữ liệu mẫu** §4, ghi 1 dòng note trong report | ❌ Đây là việc **phải làm**, không phải lựa chọn |
| Không chắc dữ liệu này có confidential không | **Hỏi để phân loại** | ✅ Phân loại là quyền của user |
| Đã ghi vào file local, **chưa** bàn giao / chưa push | Tự xoá hoặc mask + **báo 1 dòng** cho user | ❌ Nhưng bắt buộc báo |
| **Đã đẩy ra ngoài** — Figma cloud, Backlog, commit, snapshot `versions/` | **DỪNG TOÀN BỘ** + báo + hỏi cách khắc phục | ✅ Đây là **incident** |

### Nguyên tắc vàng

> `AskUserQuestion` dùng để hỏi **cách khắc phục** hoặc **cách phân loại** — **không bao giờ** để xin phép vi phạm.

❌ **Sai** — biến policy thành thứ thương lượng được bằng một cú click:

```
Dữ liệu này là PII thật. Bạn muốn:
  [A] Tiếp tục dùng dữ liệu thật
  [B] Thay bằng dữ liệu mẫu
```

✅ **Đúng** — hỏi để phân loại, trước khi dùng:

```
File `members_2026.xlsx` có cột Email và SĐT. Đây là:
  [A] Dữ liệu thật của member → tôi chỉ đọc cấu trúc cột, không copy giá trị vào output
  [B] Dữ liệu mẫu do KH tạo → dùng bình thường
  [C] Chưa rõ → tôi tạm coi là confidential và hỏi lại PM
```

✅ **Đúng** — hỏi cách khắc phục, sau khi đã lỡ:

```
⛔ Frame "Screen Flow" trên Figma đang hiển thị 12 email thật lấy từ screenshot.
Figma là dịch vụ cloud — dữ liệu đã ra ngoài. Tôi đã dừng, chưa vẽ tiếp.
  [A] Xoá node đó khỏi Figma ngay, vẽ lại bằng dữ liệu mẫu
  [B] Giữ node, tôi che vùng email rồi upload lại
  [C] Để nguyên — tôi sẽ báo PM trước khi quyết
Dù chọn gì, việc này vẫn phải báo PM theo POLICY.md §9.
```

Khác biệt ở option `[C]`: nó **không phải** "được phép vi phạm", mà là "hoãn quyết định để hỏi người có thẩm quyền". Và dòng cuối nói rõ **nghĩa vụ báo cáo không mất đi** dù chọn gì.

### Khi user nói "cứ dùng dữ liệu thật đi"

Agent **không tự cấp phép cho mình**. Việc dùng dữ liệu thật là quyết định của **PM + khách hàng**, xảy ra ngoài session. Agent chỉ được:

1. Ghi nhận rằng user khai đã có phê duyệt — **hỏi rõ ai duyệt**
2. Ghi vào `versions/v<N>_.../ba-outputs-log.md`: ai duyệt · dùng cho việc gì · môi trường nào
3. Vẫn áp dụng least privilege: chỉ lấy đúng phần cần, không copy toàn bộ

❌ Không bao giờ tự thêm file output thật vào `allowPathPatterns` để hook thôi kêu.
