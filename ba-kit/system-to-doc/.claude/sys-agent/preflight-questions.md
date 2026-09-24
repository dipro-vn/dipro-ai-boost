# Gate hỏi người — wording chính xác + cách xử lý từng câu trả lời

> **Mọi gate dưới đây PHẢI gọi tool `AskUserQuestion`.** In bảng text rồi tự suy ra câu trả lời là anti-pattern nghiêm cấm — agent stateless, không có state machine nào lưu "user đã đồng ý" giữa các session.
>
> **Thứ tự bắt buộc:** G-R → G0 → G1 → G2 → G3 → G4 → G5 → G6 → G7 → **Discovery Brief** → (recon) → G9/G9b/G10 khi phát sinh → **Proposal Gate G11–G14**.

---

## G-R — Resume (chỉ khi đã tồn tại version trước)

```
Đã có tài liệu v<N-1> chạy ngày <DD/MM/YYYY> (<n> function · <m> screen · <k> câu hỏi còn treo).
Lần này bạn muốn:
  [A] Delta — chỉ quét phần chưa phủ + kiểm lại phần đã có   (mặc định)
  [B] Chạy lại toàn bộ từ đầu — hệ thống đã thay đổi nhiều
  [C] Không quét — chỉ đọc lại v<N-1> và trả lời câu hỏi của tôi
```

| Chọn | `00_Meta.run_mode` | Hành vi |
|---|---|---|
| `[A]` | `DELTA` | Giữ dòng cũ + `Note = Carried from v<N-1>`; evidence > 30 ngày đánh `STALE` và chụp lại nếu dòng đó `Confirmed` |
| `[B]` | `FULL` | Bỏ qua dữ liệu cũ nhưng **vẫn giữ câu trả lời G0–G8 làm mặc định đề xuất** |
| `[C]` | `READ_ONLY_REVIEW` | Không crawl, không sinh version mới |

Chưa trả lời → mặc định `[A]`, **in rõ chữ "mặc định"**.

---

## G0 — Scope (hỏi ĐẦU TIÊN)

```
Phạm vi tài liệu hoá lần này?
  [A] Toàn hệ thống — mọi module
  [B] Một số module — tôi sẽ liệt kê
  [C] Một luồng nghiệp vụ cụ thể
```
Lưu `g0_scope`. **Chưa trả lời → DỪNG.** Không đoán `[A]` vì "chắc khách muốn đủ".

---

## G1 — Website & môi trường

```
Hệ thống có website nào để quan sát?
  [A] 1 site production — URL: ?
  [B] Nhiều site (user/admin/api docs...) — tôi sẽ liệt kê
  [C] Có staging — ưu tiên quét staging  (an toàn nhất)
  [D] Không quét được — tôi sẽ cung cấp screenshot
```
Lưu `g1_websites`. **Chưa trả lời → DỪNG.**

> Có staging mà vẫn chọn production → hỏi lại 1 lần: *"Staging an toàn hơn. Bạn chắc chắn muốn quét production?"*

---

## G2 — Quyền thao tác trên site ⚠️ **gate an toàn**

```
Agent được phép thao tác tới đâu trên site?
  [A] Chỉ đọc — không submit form, không bấm nút ghi/xoá   (mặc định)
  [B] Được submit trên staging bằng tài khoản test
  [C] Được submit cả production — tôi chịu trách nhiệm
  [D] Không crawl — tôi tự thao tác và gửi screenshot
```

| Chọn | `g2_crawl_mode` | `crawl-site.js --mode` | Thực thi |
|---|---|---|---|
| `[A]` | `READ_ONLY` | `read-only` | **Chặn ở tầng network:** mọi request khác GET/HEAD bị abort |
| `[B]` | `SUBMIT_STAGING` | `submit-staging` | Cho POST, **vẫn** chặn selector phá dữ liệu |
| `[C]` | `SUBMIT_PROD` | `submit-prod` | Như `[B]`; agent PHẢI in cảnh báo trước mỗi thao tác ghi |
| `[D]` | `NO_CRAWL` | — | Không chạy crawler |

Chưa trả lời → **mặc định `[A]`** và in: `Đang chạy chế độ READ-ONLY — mọi thao tác ghi bị chặn ở tầng network.`

⛔ Đây là gate duy nhất có thể gây hậu quả không hoàn tác được trên hệ thống thật. **Không bao giờ tự nâng quyền.**

---

## G3 — Tài khoản / role

```
Tài khoản nào để quan sát hệ thống?
  [A] Có đủ mọi role (list role + ai cấp)
  [B] Chỉ 1 role — role nào?
  [C] Không có tài khoản — chỉ xem được màn public
```
Lưu `g3_accounts`.

**Enforcement:** role không có tài khoản → mọi chức năng của role đó `Status = To verify` + 1 dòng Open Question `Type = Unknown`, **cấm** đoán theo tên menu.

---

## G4 — Database

```
Database?
  [A] Có dump / file schema — đường dẫn?
  [B] Có connection read-only — thông tin kết nối?
  [C] Không có → bỏ chương 3, liệt kê entity suy từ code ở Appendix A
```
Lưu `g4_db` ∈ `DUMP` / `READONLY_CONN` / `NONE`. **Chưa trả lời → DỪNG** (quyết định cả một chương).

Gate V2 check 12 và gate V3 check 5/6 đối chiếu trực tiếp giá trị này.

---

## G5 — Source code

```
Source code?
  [A] Có full repo — đường dẫn?
  [B] Chỉ một phần (frontend / backend / module cụ thể)
  [C] Không có
```
Lưu `g5_source`. **Chưa trả lời → DỪNG.**

`[C]` → mọi business rule chỉ có thể `Inferred`, **không** dòng nào được `Confirmed` chỉ bằng ảnh.

---

## G6 — Mức chi tiết chương 2

```
Chương "Functional Overview" liệt kê ở mức nào?
  [A] Executive — 10-15 chức năng, gộp theo capability
  [B] Standard — 1 use-case = 1 dòng          (mặc định)
  [C] Detailed — tới từng thao tác
```
Lưu `g6_detail`. Chưa trả lời → `[B]` + **in rõ chữ "mặc định"**.

---

## G7 — Ngôn ngữ + audience

```
Tài liệu viết bằng ngôn ngữ nào, ai đọc?
  Ngôn ngữ: [VN] / [JP] / [EN] / [VN + JP]
  Audience: Nội bộ / BrSE / Khách hàng
```
Lưu `g7_lang` + `g7_audience`. Chưa trả lời → `VN` + `Nội bộ`.

Audience = `Khách hàng` → tránh thuật ngữ kỹ thuật trong văn xuôi (không viết "API trả 500", viết "hệ thống báo lỗi").

---

## Discovery Brief — in 1 lần, chờ 1 confirm

```
📋 DISCOVERY BRIEF — <system>

| # | Hạng mục | Giá trị | Nguồn |
|---|---|---|---|
| G-R | Run mode | <FULL/DELTA/READ_ONLY_REVIEW> | user / mặc định |
| G0 | Scope | ... | user |
| G1 | Website | ... | user |
| G2 | Quyền crawl | ... | user / **mặc định READ_ONLY** |
| G3 | Tài khoản | ... | user |
| G4 | Database | ... | user |
| G5 | Source code | ... | user |
| G6 | Chi tiết | ... | user / mặc định |
| G7 | Ngôn ngữ · Audience | ... | user / mặc định |

Phân loại nguồn (sửa nếu tôi gán nhầm):

| File / nguồn | Loại | Rule | Dùng để lấy |
|---|---|---|---|
| ... | Running Website / Source Code / Database / File KH | RE1-RE4 | ... |

Budget dự kiến: ≤ 200 URL · ≤ 30 phút
Hạng mục còn thiếu: <list hoặc "không thiếu">

→ Đúng chưa? (reply "OK" để bắt đầu recon, hoặc sửa hạng mục nào sai)
```

⛔ **Không được sang Bước 3 (recon) khi chưa có confirm.**

---

## G9 — Gặp hành động ghi khi crawl

Trigger: crawler gặp element khớp danh sách phá dữ liệu (`削除` · `Xoá` · `Thanh toán` · `Gửi mail`...).

```
Màn <SC-xxx> có nút「<nhãn>」— thao tác này có thể thay đổi dữ liệu thật.
  [A] Bỏ qua — ghi UNKNOWN cho hành vi của nút này   (mặc định)
  [B] Được bấm, đây là staging có dữ liệu test
  [C] Tôi tự thao tác và gửi screenshot cho bạn
```

`[A]` → item vẫn được ghi vào inventory, cột mô tả hành vi ghi `UNKNOWN — chưa quan sát được (thao tác ghi bị chặn theo G2)`, kèm 1 Open Question.

## G9b — Vùng cấm chạm (hỏi TRƯỚC khi crawl)

```
Có URL / chức năng nào tuyệt đối không được chạm không?
(VD: /admin/batch, trang gửi mail hàng loạt, cổng thanh toán)
```
Lưu `forbidden_zones` → truyền vào `crawl-site.js --forbid`.

## G10 — Tài liệu khách hàng mâu thuẫn hệ thống

Trigger: phát hiện ≥ 3 điểm lệch.

```
Tài liệu khách hàng lệch với hệ thống thật ở <n> điểm.
  [A] Hệ thống thật thắng, ghi CONFLICT vào Open Questions   (mặc định)
  [B] Dừng lại, tôi hỏi khách hàng trước
  [C] Cho tôi xem danh sách lệch trước khi quyết
```

---

## Proposal Gate — Output 2 (sau khi Output 1 qua mọi gate)

### Bước A — in bảng tình hình trước khi hỏi

```
✅ Output 1 hoàn thành — <n> function · <m> screen · <k> bảng DB · <j> câu hỏi treo
   Gate V1 <...> · V2 <...> · V3 <...> · V5 <...>
```

### Bước B — hỏi bằng `AskUserQuestion`

| Câu | Khi nào | Header | Options |
|---|---|---|---|
| **G11** | LUÔN LUÔN | `Output 2` | `[Dừng ở Output 1]` · `[+ Basic Design]` · `[+ Bug List]` · `[Làm cả hai]` |
| **G12** | Chỉ khi chọn Basic Design | `BD scope` | `[Toàn bộ <m> màn]` · `[Chỉ màn tôi chỉ định]` · `[Chưa làm bây giờ]` — kèm hỏi đường dẫn master workbook |
| **G13** | Chỉ khi chọn Bug List | `Bug scope` | Quét: `[Blackbox + Code + DB]` · `[Chỉ blackbox]` · `[Blackbox + Code]` — Gửi: `[Nội bộ review trước]` (mặc định) · `[Gửi thẳng KH]` |
| **G14** | Chỉ khi master workbook có sheet lạ | `Sheet lạ` | `[Xoá hết]` · `[Giữ lại — là screen thật]` · `[Cho tôi xem danh sách]` |

**Enforcement:**
- ⛔ Không có câu trả lời G11 → **không chạy gì thêm**, kết thúc ở Output 1.
- ⛔ G14: **không bao giờ tự xoá sheet** — xoá là thao tác không hoàn tác được.
- BA được phép đề nghị **1 lần duy nhất**. User nói "chưa" → không hỏi lại trong session.
