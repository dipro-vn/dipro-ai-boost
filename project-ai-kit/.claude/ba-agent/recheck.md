# Ba Agent — Bước 5.5 Visual Recheck

> Sau khi Bước 5 xong (Output 1 + 2 + 3), BA **phải chụp screenshot từng frame** rồi tự đánh giá theo checklist. KHÔNG được báo user "đã xong" nếu chưa qua bước này.

**Quy trình:**

```
For each frame in [Output 1, Output 2, Output 3]:
  1. Call get_screenshot(nodeId, maxDimension=1400, enableBase64Response=true)
  2. Đọc screenshot → tự đánh giá theo checklist 5 tiêu chí bên dưới
  3. Nếu FAIL 1 tiêu chí → fix ngay (viết use_figma call sửa) → chụp lại
  4. Chỉ khi PASS toàn bộ mới sang frame tiếp theo
```

**Checklist 5 tiêu chí (mỗi frame):**

| # | Tiêu chí | PASS khi... | Cách kiểm tra |
|---|---|---|---|
| 1 | **Đủ nội dung theo yêu cầu** | Đã đủ tất cả sections theo skill (VD Output 1: 5 columns + Tech Stack + Sitemap; Output 2: 4 zones; Output 3: mockup + bảng ĐẦY ĐỦ item) | So sánh checklist section trong `ba-figma-output/SKILL.md` |
| 2 | **KHÔNG chồng đè** | Không có node nào overlap lên node khác (text, arrow, box) | Zoom screenshot xem từng khu vực. Đặc biệt check: giao điểm zones, cross-actor connectors, arrows đi qua nodes |
| 3 | **Text đầy đủ, không bị crop** | Mọi label đọc được đầy đủ, không bị cắt cuối câu | Zoom screenshot check text nodes có `...` cuối hoặc content ngắn bất thường |
| 4 | **Đúng vùng (không lệch cột)** | Node của Zone X nằm gọn trong `Z<X>_X` đến `Z<X>_X + Z<X>_W` | Verify X-coordinate của mỗi node ≥ Zone X boundary |
| 5 | **Số lượng item khớp bảng** (chỉ Output 3) | Số badge trên mockup = số dòng trong bảng | Đếm badge trên phone → đếm rows trong table → phải khớp |

**Format báo cáo recheck (in ra cho user):**

```
🔍 AI Recheck Report — Output <N>

✅ Tiêu chí 1: Đủ nội dung        (đã đủ 4 zones + Tech Stack)
✅ Tiêu chí 2: Không chồng đè      (đã zoom check 5 điểm giao)
✅ Tiêu chí 3: Text đầy đủ         (tất cả nodes readable)
❌ Tiêu chí 4: Đúng vùng           (CA_VOIP_001 tràn sang Non-Happy zone)
   → Fix: dời CA column sang phải 200px, mở rộng frame width
✅ Tiêu chí 5: N/A cho Output này

Kết quả: FAIL → tiến hành fix rồi chụp lại
```

**Nếu FAIL → không được bỏ qua:** phải fix bằng `use_figma` call sửa layout, sau đó chụp lại và recheck.

**Common overlap patterns cần đặc biệt check:**

- Cross-actor arrow đi ngang qua node column khác
- CA column overlap với Non-Happy zone (như đã từng xảy ra)
- Decision node "Accept?" bị đè bởi label "Yes/No"
- Numbered badge (bên trái node) đè lên border của Zone trước
- Text purpose 1 dòng bị crop vì width không đủ
- Cross-session connector chồng lên In-Call node của phía đối diện
- Non-happy flow trigger box overlap với error node bên dưới
- **Output 3 phone đè bảng dưới nếu dùng grid layout** — dùng layout DỌC
- **Output 1 Tech Stack ngang đè Sitemap** — chuyển Tech thành TABLE bên phải Flow

**Khi tất cả 3 Outputs PASS → mới báo user thành công.**
