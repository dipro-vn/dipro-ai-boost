---
description: Sinh TC Implementation Plan — xác định chiến lược theo Screen archetype, phân rã Screen → Component, gắn Component Type/Risk Level, Permission Matrix, Luồng E2E chính. Bước tiền xử lý của /gen-tcs (tự chạy nếu chưa có plan, không dừng hỏi); chạy riêng khi muốn duyệt cấu trúc trước.
skills:
  - rbt_manual_testing
  - screen_strategy
---

Thực hiện **Section 3: TC Implementation Plan** từ skill `rbt_manual_testing`.

## Hướng dẫn

1. Đọc `testing/[module]/analysis.md` (Summary + AC + Screen Inventory nếu có) + `CLAUDE.md` (platform).

2. **Xác định Screen (đơn vị màn hình)** — tổng quát, không giới hạn CRUD. 1 Screen = 1 **màn hình điều hướng chính** user đi tới được (VD List, Detail, Create/Edit). **Form wizard nhiều step = 1 Screen** (lấy cả form làm đơn vị, mỗi step là nhóm Component/Function Name trong cùng sheet, không tách step thành Screen) — mỗi Screen = 1 sheet trong file `.xlsx`. **Popup, dialog, modal, submenu, bottom sheet, toast, tab con KHÔNG phải Screen riêng**: chúng thuộc Screen đã mở ra chúng, được liệt kê là Component (Component Type = Dialog/Popup...) của Screen đó và TC nằm cùng sheet. Overlay dùng chung ở nhiều Screen → gắn vào Screen mở nó đầu tiên, các Screen còn lại chỉ test phần khác biệt.
   - Có Screen Inventory trong `analysis.md` → dùng làm nguồn, **nhưng frame Figma của popup/dialog/submenu phải gộp vào Screen cha** theo định nghĩa trên (Inventory liệt kê frame, không phải danh sách sheet).
   - Không có → suy luận từ Summary/luồng trong AC, tự flag rõ: "Phân rã dựa trên suy luận từ text, chưa có design xác nhận."
   - **Thứ tự Screen và Component** (áp dụng cho cả plan và thứ tự sinh TC ở `/gen-tcs`):

     | | Chỉ có spec | Có design |
     |---|---|---|
     | Screen | Theo luồng chính trong spec (từ lúc vào đến kết thúc) | Theo thứ tự frame trong luồng điều hướng của design |
     | Component | Theo thứ tự spec mô tả: field theo danh sách trong spec, rồi action theo thứ tự luồng. Ghi rõ "thứ tự suy luận từ spec" | Theo thứ tự đọc trên frame (trên xuống dưới, trái sang phải); popup/dialog nằm ngay sau component mở ra nó |
     | Spec và design ghi thứ tự khác nhau | — | Theo design, ghi vào DIF nếu spec nêu thứ tự khác |

3. Với mỗi Screen:
   a. Ghi nhận **UI chung (layout tổng thể)** — 1 dòng mô tả ngắn ở cấp Screen.
   b. Liệt kê **từng Component theo đúng thứ tự xuất hiện trên UI** (không xáo trộn, để dễ đối chiếu với màn hình thật). Có design → thứ tự đọc trên frame; chỉ có spec → thứ tự spec mô tả (xem "Thứ tự Screen và Component" ở bước 2).

4. **Xác định Archetype & viết Strategy Summary cho Screen:**
   - Xác định archetype của Screen (List/Search, Form Create/Edit, Detail/View, hoặc Khác) dựa trên Summary + AC trong `analysis.md`.
   - Đọc `.claude/skills/screen_strategy/SKILL.md` — section khớp archetype, hoặc Fallback nếu không khớp archetype nào.
   - Viết **Strategy Summary** 2-5 bullet cho Screen đó. **Chỉ ghi quyết định chiến lược** mà `/gen-tcs` không thể đọc ra trực tiếp từ bảng AC: (a) **phạm vi** — điều **không** test và lý do (VD "không test tổ hợp với filter khác", "không có site doctor ở phase này"); (b) **ưu tiên và tổ hợp** cần test kết hợp (chỉ 1-2 tổ hợp rủi ro cao); (c) **cách xử lý điểm TBD** (VD "trạng thái khác chưa chốt, Q-XXX-NNN, chỉ 1 TC đại diện"); (d) **lưu ý kiểm thử không hiển nhiên** (VD biên làm tròn, quy đổi, multi-byte, liên kết dữ liệu giữa các Screen). **Không** lặp lại ánh xạ AC → hành vi (VD "contracted → nút enable (AC-01)") vì `analysis.md` đã có; AC ID chỉ để nêu nguồn của quyết định. Bắt buộc tham chiếu tên component thật đã liệt kê ở bước 3b. Không paste nguyên khung mẫu chưa điều chỉnh.
   - Self-check trước khi lưu: bullet nào chỉ lặp lại AC, hoặc không gắn với component/AC cụ thể của Screen đang xử lý → tự viết lại hoặc xoá, không hỏi user.

5. Với mỗi Component, xác định:
   - **Component Type** (Textbox/Dropdown/Checkbox/Radio/Table/Dialog/Button/File Upload/...) — dùng để tra thẳng `.claude/skills/component_checklist/SKILL.md` (Section A/B/C) ở bước `/gen-tcs`, không đoán qua keyword AC text nữa.
   - **Risk Level** (High/Medium/Low) — dùng làm đầu vào để suy ra Bảng 1 "High Risk & E2E" ở `/gen-tcs`, **không** xuất thành cột trong bảng TC:
     - High: nghiệp vụ quan trọng, liên quan tiền/bảo mật/phân quyền
     - Medium: luồng chính nhưng không critical
     - Low: UI validation, happy path đơn giản

6. **Rule tương tác chéo component:** khi xác định Logic của 1 component, luôn tự hỏi "component này có phụ thuộc/ảnh hưởng component nào khác trên cùng màn hình không?" (VD: Confirm Password phụ thuộc Password, Dropdown B phụ thuộc Dropdown A). Ghi vào cột "Ghi chú phụ thuộc" của component chịu trách nhiệm chính — không tạo category riêng.

6b. **Permission Matrix (nếu Screen có action phân quyền):** lưu thành **bảng thật** trong `plan-tcs.md` (không chỉ viết một bullet nhắc "Permission Matrix"). Quy tắc:
   - **Chép đủ mọi hàng** của ma trận Actor × Action trong `analysis.md` vào Screen chứa action đó — không bỏ hàng nào (kể cả hàng chỉ có ô ❌ hoặc ?, VD "Tạo đơn"). Hàng không gắn với Screen nào thì đặt vào Screen đầu tiên liên quan. Sau khi xong, đối chiếu: số hàng của `analysis.md` = tổng số hàng các Permission Matrix trong plan.
   - **Thêm chiều sở hữu:** action nào chỉ áp dụng cho đối tượng của chính actor (đơn của mình, đơn được gán cho mình, record do mình tạo) thì thêm một hàng riêng `[Action] — của người khác`, ô ❌ cho cùng loại actor (VD Driver khác với Driver được gán; Customer khác với Customer chủ đơn). Đây là hàng riêng, không chỉ ghi trong cột Ghi chú.
   - Ô ? ghi kèm mã Q&A.
   - Mục đích: `/gen-tcs` dùng bảng này để phủ từng ô ❌ và `/review-tcs` đối chiếu.

7. **Xác định Assumption môi trường test** — liệt kê ngắn các điều kiện hạ tầng/bên ngoài mà TC ở bước `/gen-tcs` sẽ ngầm dựa vào để chạy được (VD: API bên thứ 3 available lúc test, cronjob/background job chạy đúng chu kỳ thật, không bị mock/stub). Đây KHÔNG phải câu hỏi cho PM/BA (khác Q-MOD-XXX) — chỉ là lưu ý cho người chạy test. Để trống nếu module không phụ thuộc hạ tầng ngoài.

7b. **Luồng E2E chính:** từ luồng chính và các nhánh có ý nghĩa nghiệp vụ trong `analysis.md` (vòng đời, nhánh lỗi/hủy, luồng qua nhiều actor/thiết bị), liệt kê **3-6 luồng E2E** (luồng chính trước). Đây là nguồn cho Bảng 2 của mục `## High Risk & E2E` ở `/gen-tcs`; user xác nhận cùng plan. Không gộp biến thể dữ liệu thành luồng riêng.

8. Lưu ra `testing/[module]/plan-tcs.md`.

9. **Khi chạy riêng `/plan-tcs`:** show cho user, hỏi:

> Đây là plan triển khai TC cho module [tên]. Bạn muốn điều chỉnh gì không?
> *(Nếu không, tôi sẽ dùng plan này làm cơ sở sinh Test Case ở bước `/gen-tcs`.)*

   **Khi `/gen-tcs` tự chạy bước này (chưa có plan):** **không dừng hỏi**. Lưu `plan-tcs.md` rồi tiếp tục sinh TC; `/gen-tcs` in tóm tắt plan không chặn ở đầu output (xem Bước 0 trong `/gen-tcs`).

## Input cần thiết

- `testing/[module]/analysis.md`

## Output

`testing/[module]/plan-tcs.md`

```markdown
# TC Implementation Plan: [Module Name]

## [Screen 1 Name]
- **Archetype:** [List / Form / Detail / Khác]
- **Chiến lược Test Case:**
  - [Bullet 1 — tham chiếu component/AC thật của Screen này]
  - [Bullet 2]
  - [Bullet 3]
- **UI chung:** [mô tả ngắn layout tổng thể]

| Component | Component Type | Risk Level | Ghi chú phụ thuộc |
|---|---|---|---|
| [Tên component] | [Loại] | High/Medium/Low | [phụ thuộc component nào, — nếu không] |

### Permission Matrix *(chỉ khi Screen có action phân quyền)*
| Action | [Actor 1] | [Actor 2] | [Actor 3] | Ghi chú |
|---|---|---|---|---|
| [Action] | ✅ / ❌ / ? (Q-MOD-XXX) | ... | ... | [điều kiện trạng thái] |
| [Action] — của người khác | ❌ (Customer khác) | ❌ | ❌ (Driver khác) | [chỉ khi action giới hạn theo sở hữu] |

## [Screen 2 Name]
...

## Luồng E2E chính
| # | Luồng | Các bước chính (actor) | Nguồn (AC) |
|---|---|---|---|
| 1 | [Luồng chính — happy path] | [Bước 1 (Actor) → Bước 2 (Actor) → ...] | [AC-NN] |

## Ghi chú tổng quát
- **Assumption môi trường test:** [điều kiện hạ tầng/bên ngoài TC sẽ dựa vào — để trống nếu không có]
```

## Bước tiếp theo

Sau khi user confirm `plan-tcs.md`, chạy `/gen-tcs` để sinh Test Case chi tiết.

> Nếu user gọi thẳng `/gen-tcs` mà module chưa có `plan-tcs.md`, bước này được `/gen-tcs` tự động chạy trước (sau khi có `analysis.md`) và **không dừng hỏi**; plan vẫn được lưu thành file `plan-tcs.md` để các lần chạy lại một Screen dùng lại cùng cấu trúc.
