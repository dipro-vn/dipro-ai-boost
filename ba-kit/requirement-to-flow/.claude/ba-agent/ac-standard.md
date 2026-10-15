# BA Agent — Chuẩn Acceptance Criteria (`## Acceptance Criteria`)

> **Scope:** cách viết section `## Acceptance Criteria` của SPEC.md. Được reference từ Bước 4 và Bước 4.6 của `ba-agent.md`.
> **BẮT BUỘC Read** trước khi viết section này. Ví dụ minh họa đầy đủ: `.claude/ba-agent/examples/spec-sample.md`.
>
> ⚠️ **Chưa có script gate cho AC.** Mọi quy tắc dưới đây được kiểm bằng **checklist ở §9** (Bước 4.6 + Self-Feedback Bước 5.6) — do chính BA tự rà. Đừng báo "AC đạt chuẩn" như thể đã có công cụ kiểm.

---

## 1. Vị trí & ràng buộc cấu trúc SPEC

- AC nằm trong `## Acceptance Criteria` của SPEC.md. **KHÔNG tạo heading `##` riêng cho AC / User Story / Trace** — AC chỉ là các `###` bên trong section này. Các heading `##` bắt buộc khác của SPEC (`BA Deliverables`, `Source Register`, `UX Review Notes`, `Open Questions`… theo `spec-template.md` và `ba-agent.md` Bước 4.5) vẫn giữ nguyên.
- AC là **nguồn duy nhất** của tiêu chí nghiệm thu. Danh sách User Story (`user-stories.md`) chỉ **tham chiếu ID** AC, không chép nội dung AC.
- AC **không chép message lỗi**. Message thật chỉ nằm ở `## Screen Details` (bảng Non-Happy 5 cột, cột `ID` = `E-nnn`, cố định — `spec-template.md`) — AC tham chiếu `E-nnn`. Chép ra 3 nơi (Screen Details · AC · Figma Output 3) là nguồn trôi lệch.

## 2. Nguồn của AC — chỉ từ `FACT`

Theo `RELIABILITY.md` §3 và `spec-template.md`:

| Classification trong `## Source Register` | Được viết thành AC? |
|---|---|
| `FACT` | ✅ Viết bình thường |
| `PROPOSAL` | ⚠️ Chỉ khi gắn badge `[PROPOSAL — chờ BRSE approve]` ngay dòng `Then` |
| `INFERENCE` | ❌ Không đưa vào AC — list ở `## Alternative Flows & Edge Cases` |
| `UNKNOWN` / `CONFLICT` | ❌ Không bịa. Ghi **placeholder**: `AC-nn — PENDING-OQ-yy` (xem §6) |

CR chưa được KH chốt → **KHÔNG** viết vào AC (`versioning.md` Rule 2c).

## 3. Format bắt buộc — Given / When / Then

```markdown
## Acceptance Criteria

> Tổng: <n> AC · Happy <a> · Edge <b> · Negative <c> · PENDING-OQ <d>

### AC-01 — <tên scenario, danh từ + kết quả> `[Happy]`
- **Trace:** FR #12,13 · AX_LEAV_003 · Flow 2
- **Given** <tiền điều kiện cụ thể — vai trò, trạng thái dữ liệu>
- **And** <tiền điều kiện thứ 2, nếu có>
- **When** <MỘT hành động của actor hoặc 1 sự kiện hệ thống>
- **Then** <kết quả quan sát/đo lường được>
- **And** <kết quả phụ, nếu có>
```

| Phần | Quy tắc |
|---|---|
| **Tiêu đề** | `AC-<NN>` + tên scenario + tag loại: `[Happy]` · `[Edge]` · `[Negative]` |
| **Trace** | BẮT BUỘC. `FR #<n>` (khớp FR Register / cột `FR No.` của `## Screens`) · `Screen Code` · `Flow <N>`. Không trace được → AC chưa chín, đưa về OQ. `Flow <N>` = số business flow ở Output 1; **chưa chạy Output 1** thì dùng nhãn nhóm nghiệp vụ tạm (`Flow Đổi trả`) và đổi sang số khi Output 1 chốt |
| **Given** | Trạng thái cụ thể (ai, đang ở đâu, dữ liệu thế nào). Không viết "hệ thống hoạt động bình thường" |
| **When** | **1 hành động duy nhất.** Có chữ "rồi / sau đó / và" nối 2 hành động → tách AC |
| **Then** | Quan sát được: trạng thái, số liệu, màn đích (`→ AX_LEAV_004`), hoặc `E-nnn` |
| **ID** | `AC-<NN>` tăng dần, **không đánh lại số giữa các version** (giống OQ ID). AC bị bỏ → ghi `AC-06 — (đã bỏ ở v3)`, không xoá số |
| **Đếm ở dòng `> Tổng:`** | AC `PENDING-OQ` **giữ tag loại** của nó (`[Negative]`…) nhưng chỉ được đếm vào ô `PENDING-OQ`, **không** đếm lại ở Happy/Edge/Negative. Luôn có `Happy + Edge + Negative + PENDING-OQ = tổng số AC` |

## 4. Phân loại & độ phủ

| Tag | Là gì | Nguồn thường lấy |
|---|---|---|
| `[Happy]` | Đường chính hoàn thành mục tiêu | `## Happy Path` |
| `[Edge]` | Biên / điều kiện hiếm nhưng hợp lệ (đầu cuối khoảng, rỗng, trùng, đồng thời) | `## Alternative Flows & Edge Cases` |
| `[Negative]` | Lỗi, bị từ chối, vi phạm business rule | bảng Non-Happy của `## Screen Details` |

**Độ phủ — tính theo FLOW, không ép số cứng theo Story:**
- Mỗi business flow (Output 1) có ≥ 1 `[Happy]` + ≥ 1 `[Edge]` + ≥ 1 `[Negative]`.
- Loại nào thực sự không có → ghi `N/A — <lý do>` cho flow đó. **Cấm** để trống im lặng.
- Mỗi dòng Non-Happy có `Hiển thị` ∈ {`Modal` · `Popup` · `Full screen` · `Toast` · `Banner` · `Empty state`} phải có AC `[Negative]` hoặc `[Edge]` tương ứng (đã có ở checklist Bước 4.6 — đây là chuẩn của nó).
- `Inline error` · `Button disabled` · `Tooltip` · `Chặn UI`: gom vào 1 AC theo màn khi cùng cách xử lý (xem §5), không cần mỗi dòng 1 AC. State không có hành động kích hoạt riêng (VD `Button disabled` khi thiếu dữ liệu) viết **trong AC của hành động liên quan**, không tạo AC "When xem màn".
- Dòng Non-Happy `Hiển thị = UNKNOWN` (chưa có `E-ID`, kể cả Empty state mà nguồn không mô tả) **không** viết AC; nó đã nằm trong OQ. Chỉ khi OQ được trả lời và dòng có `E-ID` thì mới bổ sung AC.

## 5. Tránh AC bùng nổ — dùng `Examples`

Nhiều dòng Non-Happy **cùng nhóm, cùng cách hiển thị, cùng hành vi** chỉ khác dữ liệu (VD 5 field bắt buộc) → **1 AC + bảng Examples**, không viết 5 AC:

```markdown
### AC-07 — Từ chối gửi khi thiếu trường bắt buộc `[Negative]`
- **Trace:** FR #12 · AX_LEAV_002 · Flow 2
- **Given** actor đang ở form gửi yêu cầu
- **When** actor nhấn "Gửi" khi bỏ trống <trường>
- **Then** hệ thống không gửi yêu cầu và hiển thị <lỗi>

| trường | lỗi |
|---|---|
| Loại nghỉ | E-004 |
| Ngày bắt đầu | E-005 |
| Lý do | E-006 |
```

Khác cách xử lý (VD 1 case Toast, 1 case Full screen) → **không** gộp.

## 6. Chưa chốt được → `PENDING-OQ`

Open Question (Output OQ) sinh ra **trong giai đoạn Output 1** — sau Bước 4. Nên lúc viết AC (Bước 4) nhiều rule còn `UNKNOWN`. Quy ước:

```markdown
### AC-09 — Hạn mức nghỉ tối đa mỗi năm `[Negative]`
- **PENDING-OQ-03** — chờ KH trả lời: "Mỗi nhân viên được nghỉ tối đa bao nhiêu ngày/năm?"
- **Trace:** FR #14 · Flow 2
- _Given/When/Then: chưa viết — UNKNOWN. Không suy diễn._
```

- Mã `OQ-yy` phải **tồn tại** trong `OQ-REGISTER.md` (hoặc sẽ được thêm ở Bước 5.4 cùng lần chạy).
- Khi OQ được trả lời → Bước 7 nhánh FEEDBACK: đổi `UNKNOWN → FACT` ở Source Register, **viết đủ Given/When/Then thay placeholder**, giữ nguyên `AC-09`.
- `PENDING-OQ` không được tính là AC "đủ" khi báo kết quả: ghi riêng trong dòng `> Tổng:` (`PENDING-OQ <d>`).

## 7. Ngôn ngữ — cấm / tránh

| ❌ Không viết | ✅ Viết |
|---|---|
| "nhanh", "mượt", "kịp thời", "ngay lập tức" | số: "trong vòng 3 giây" (chỉ khi nguồn có số — không có thì OQ, **không tự bịa số**) |
| "thân thiện", "trực quan", "hợp lý", "phù hợp", "thích hợp" | hành vi quan sát được |
| "v.v.", "etc.", "…", "các trường hợp khác" | liệt kê đủ, hoặc ghi rõ phạm vi |
| "hiển thị thông báo lỗi" | tham chiếu `E-nnn` |
| "nút chuyển màu xanh", vị trí pixel, font | (thuộc Screen Details / Figma, không thuộc AC) |
| "gọi API /…", tên bảng DB, tên framework | "hệ thống lưu yêu cầu với trạng thái `Chờ duyệt`" |

Quy tắc: **AC mô tả hệ thống làm gì, không mô tả làm thế nào** (ràng buộc cứng "không thiết kế kỹ thuật" của `ba-agent.md`).

## 8. Dữ liệu mẫu & thay đổi

- Mọi giá trị minh họa dùng bộ chuẩn `DATA-PRIVACY.md` §4 (`user_a@example.com`, `Nguyễn Văn A`, `SO-0001`…). Không dán dữ liệu thật của KH vào AC.
- Sửa AC = **scoped update** theo `POLICIES.md` §4.6 (không regenerate cả section; báo `Potential Impact` tới Screen Details / User Story có tham chiếu AC đó; SPEC về `WAITING_APPROVAL`).
- Đổi AC → danh sách User Story (nếu đã xuất) thành `STALE` — báo user, không tự xuất lại.

## 9. Checklist tự rà (BẮT BUỘC ở Bước 4.6 và Bước 5.6)

- [ ] Mọi AC có `Trace` (FR · Screen Code · Flow) và FR đó **có thật** trong FR Register
- [ ] Mỗi AC có đủ Given / When / Then; `When` chỉ 1 hành động
- [ ] Mỗi flow có Happy + Edge + Negative (hoặc `N/A — lý do`)
- [ ] Mỗi Non-Happy mức Modal/Popup/Full screen/Toast/Banner/Empty state đã có AC
- [ ] Không có AC nào chép message lỗi — chỉ `E-nnn`
- [ ] Không còn từ ở §7 cột trái
- [ ] Không AC nào dựa trên statement `INFERENCE`/`UNKNOWN`/`CONFLICT` (đã chuyển sang `PENDING-OQ`)
- [ ] Dòng `> Tổng:` khớp số AC thực tế (kể cả `PENDING-OQ`)
- [ ] Không tạo heading `##` riêng cho AC / User Story (AC chỉ là `###` trong `## Acceptance Criteria`)

Kết quả rà in vào report (Self-Feedback), liệt kê **từng mục đã kiểm** — không chỉ ghi "PASS".

## 10. Anti-pattern

- ❌ Viết AC từ "kiến thức chung" khi nguồn không nói (vd tự đặt "tối đa 3 lần sai thì khoá")
- ❌ 1 AC gộp 2 scenario ("đăng nhập thành công **và** đổi mật khẩu thành công")
- ❌ AC chỉ có Happy; lỗi để "xem bảng Non-Happy" mà không có AC
- ❌ AC trùng lặp message với Screen Details/Figma
- ❌ Đánh lại số AC khi sang version mới
- ❌ Điền `Given/When/Then` cho case `UNKNOWN` để cho "đủ"
- ❌ Báo "AC đã được verify" khi chỉ tự rà checklist

## 11. Hạ nguồn — ai đọc `## Acceptance Criteria`

| Nơi | Cách dùng | Lưu ý |
|---|---|---|
| **`qc-kit-agent`** (`/analyze-req` → `analysis.md`) | Đọc SPEC như một tài liệu requirement bất kỳ rồi **tự dựng lại** bảng `REQ ID · AC ID · AC Content · Status (Confirmed/Assumed/TBD)`. **Không parse** section này theo format cố định | (1) `AC-NN` của QC là **namespace riêng** — `AC-03` trong `analysis.md` **không** nhất thiết là `AC-03` của SPEC. Khi trao đổi, ghi rõ `SPEC AC-03` hoặc `QC AC-03`. (2) `PENDING-OQ-yy` ↔ `Status = TBD` của QC; `AMB-xx` của QC tương ứng `OQ-yy` ở đây |
| **`system-to-doc`** | Chỉ có dòng nhắc "QC agent dùng `## Acceptance Criteria`" trong khối Post-Delivery sao chép từ kit này. Kit đó viết tài liệu AS-IS, **không sinh AC** | Không bị ảnh hưởng |

- Kit này **không** sửa `qc-kit-agent`. Muốn QC giữ nguyên ID của SPEC thì sửa ở phía QC (ngoài phạm vi).
- Người đọc ngoài kit **không** nên hiểu `Tổng: n AC` là "đủ": phải đọc kèm `PENDING-OQ <d>` trong cùng dòng.

---

## Template trống

```markdown
### AC-<NN> — <tên scenario> `[Happy | Edge | Negative]`
- **Trace:** FR #<n> · <Screen Code> · Flow <N>
- **Given** <tiền điều kiện>
- **And** <tiền điều kiện phụ — bỏ nếu không có>
- **When** <1 hành động>
- **Then** <kết quả quan sát được>
- **And** <kết quả phụ — bỏ nếu không có>
```
