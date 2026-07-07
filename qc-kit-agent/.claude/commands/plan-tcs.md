---
description: Sinh TC Implementation Plan — phân rã module thành Screen → Component, gắn Component Type/Risk Level/Technique flag. Bắt buộc chạy trước /gen-tcs.
skills:
  - rbt_manual_testing
---

Thực hiện **Section 3: TC Implementation Plan** từ skill `rbt_manual_testing`.

## Hướng dẫn

1. Đọc `testing/[module]/analysis.md` (Summary + AC + Screen Inventory nếu có) + `context.md` (platform, auto-load).

2. **Xác định Screen (đơn vị màn hình)** — tổng quát, không giới hạn CRUD. 1 Screen = 1 đơn vị điều hướng riêng biệt user thực sự thấy (1 URL riêng, 1 dialog full-screen, 1 step trong wizard, 1 tab riêng).
   - Có Screen Inventory trong `analysis.md` → dùng trực tiếp, không đoán lại.
   - Không có → suy luận từ Summary/luồng trong AC, tự flag rõ: "Phân rã dựa trên suy luận từ text, chưa có design xác nhận."

3. Với mỗi Screen:
   a. Ghi nhận **UI chung (layout tổng thể)** — 1 dòng mô tả ngắn ở cấp Screen.
   b. Liệt kê **từng Component theo đúng thứ tự xuất hiện trên UI** (không xáo trộn, để dễ đối chiếu với màn hình thật).

4. Với mỗi Component, xác định:
   - **Component Type** (Textbox/Dropdown/Checkbox/Radio/Table/Dialog/Button/File Upload/...) — dùng để tra thẳng `component_checklist/SKILL.md` (Section A/B/C) ở bước `/gen-tcs`, không đoán qua keyword AC text nữa.
   - **Risk Level** (High/Medium/Low):
     - High: nghiệp vụ quan trọng, liên quan tiền/bảo mật/phân quyền
     - Medium: luồng chính nhưng không critical
     - Low: UI validation, happy path đơn giản
   - **Technique Flag** (nhẹ, optional) — nếu AC của component có dấu hiệu cần Decision Table/State Transition/Boundary Tier, ghi 1 dòng note ngắn (VD: "Decision Table — role × trạng thái"). **Không dựng bảng/diagram đầy đủ ở bước này** — việc đó để dành cho `/gen-tcs`.

5. **Rule tương tác chéo component:** khi xác định Logic của 1 component, luôn tự hỏi "component này có phụ thuộc/ảnh hưởng component nào khác trên cùng màn hình không?" (VD: Confirm Password phụ thuộc Password, Dropdown B phụ thuộc Dropdown A). Ghi vào cột "Ghi chú phụ thuộc" của component chịu trách nhiệm chính — không tạo category riêng.

6. Lưu ra `testing/[module]/plan-tcs.md`.

7. Show cho user, hỏi:

> Đây là plan triển khai TC cho module [tên]. Bạn muốn điều chỉnh gì không?
> *(Nếu không, tôi sẽ dùng plan này làm cơ sở sinh Test Case ở bước `/gen-tcs`.)*

## Input cần thiết

- `testing/[module]/analysis.md`

## Output

`testing/[module]/plan-tcs.md`

```markdown
# TC Implementation Plan: [Module Name]

## [Screen 1 Name]
- **UI chung:** [mô tả ngắn layout tổng thể]

| Component | Component Type | Risk Level | Technique Flag | Ghi chú phụ thuộc |
|---|---|---|---|---|
| [Tên component] | [Loại] | High/Medium/Low | [tên pattern nếu có, — nếu không] | [phụ thuộc component nào, — nếu không] |

## [Screen 2 Name]
...
```

## Bước tiếp theo

Sau khi user confirm `plan-tcs.md`, chạy `/gen-tcs` để sinh Test Case chi tiết. `/gen-tcs` sẽ từ chối chạy nếu module chưa có file này.
