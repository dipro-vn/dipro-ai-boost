---
name: screen_strategy
description: Khung chiến lược test theo Screen archetype (List/Form/Detail...) — dùng trong /plan-tcs để viết Strategy Summary trước khi phân rã Component. Không dùng độc lập.
---

# Screen Strategy

## Cách dùng

Skill này **không dùng độc lập** — chỉ được `/plan-tcs` gọi tới, sau khi đã liệt kê Component (bước 3b) và trước khi gắn Component Type/Risk Level.

**Quy trình:**
1. Xác định archetype của Screen từ Summary + AC trong `analysis.md`: **List/Search**, **Form (Create/Edit)**, **Detail/View**, hoặc không khớp archetype nào → dùng **Fallback**.
2. Đọc section tương ứng bên dưới.
3. Viết Strategy Summary 3-5 bullet cho Screen đó — **bắt buộc tham chiếu tên component hoặc AC ID thật** đã xác định cho Screen này. Không paste nguyên bullet mẫu bên dưới mà không điều chỉnh.
4. Self-check trước khi lưu: nếu bullet nào không gắn với component/AC cụ thể nào của Screen đang xử lý → viết lại, không hỏi user.

---

## Archetype: List / Search

Screen hiển thị danh sách bản ghi, thường có Search/Filter/Sort/Pagination/Row Action.

**Nguyên tắc:**
- Test độc lập từng chức năng trước: Search, mỗi Filter riêng, Sort, Pagination, Row Action, Bulk Action — **không** test toàn bộ tổ hợp giữa chúng (tăng theo cấp số nhân, khó bảo trì).
- Chỉ chọn **1-2 tổ hợp có rủi ro/nghiệp vụ cao** để test kết hợp (VD: Filter theo trạng thái quan trọng + Sort theo cột tiền tệ) — không cần test mọi tổ hợp.
- **Permission:** dùng Permission Matrix (Role × Action) thay vì lặp lại toàn bộ TC cho từng Role.
- **Data Display:** verify đúng số lượng bản ghi, đúng cột, mapping đúng dữ liệu, đúng định dạng ngày/số/tiền tệ/trạng thái.
- **Boundary data:** 0 record, 1 record, vừa đủ 1 trang, nhiều hơn 1 trang.
- **Search:** áp EP/BVA — tìm chính xác, tìm 1 phần, ký tự đặc biệt/SQL/script.
- **Screen State:** Loading, Empty Data, Error, Permission Denied.
- **Refresh sau thao tác:** danh sách cập nhật đúng sau Create/Update/Delete hoặc quay lại từ Detail.

**Ví dụ bullet Strategy Summary (điều chỉnh theo component thật của Screen đang xử lý):**
```
- Test độc lập [tên Search field], [tên Filter A], [tên Filter B], Sort theo [tên cột], Pagination — không test toàn bộ tổ hợp
- Tổ hợp ưu tiên: [Filter A] + Sort [cột tiền tệ] — do liên quan số liệu tài chính hiển thị (AC-XX)
- Permission Matrix cho [Role A/B/C] trên [Row Action tên thật] thay vì lặp TC theo role
- Boundary data cho [tên bảng/danh sách]: 0 record, 1 record, đủ 1 trang, nhiều trang
```

---

## Archetype: Form (Create/Edit)

Screen nhập liệu để tạo mới hoặc chỉnh sửa bản ghi.

**Nguyên tắc:**
- Test **field-level trước** (mỗi field độc lập, xem `component_checklist` Section A) — chỉ sau đó mới xét **cross-field validation** (field phụ thuộc field khác, VD Confirm Password phụ thuộc Password).
- Phân biệt rõ **Create vs Edit** nếu hành vi khác nhau (VD: Edit có sẵn giá trị cũ, field nào bị khóa không cho sửa).
- **Submit/Cancel/Dirty state:** rollback đúng khi Cancel, cảnh báo khi rời trang có thay đổi chưa lưu, double-submit không tạo 2 bản ghi.
- **Không** test tổ hợp toàn bộ field sai cùng lúc — mỗi field 1 nhóm TC validation riêng (đã có `component_checklist`), Strategy Summary chỉ nêu field nào có phụ thuộc chéo cần test riêng.

**Ví dụ bullet Strategy Summary:**
```
- Field-level validation riêng cho [tên field 1], [tên field 2]... theo component_checklist
- Cross-field: [Field B] phụ thuộc [Field A] — test A đổi thì B reset/validate lại đúng
- Create vs Edit khác nhau ở: [nêu khác biệt thật, VD field X bị khóa khi Edit]
- Dirty-state: rời trang khi chưa lưu → confirm dialog; Cancel → không lưu thay đổi
```

---

## Archetype: Detail / View

Screen hiển thị chi tiết 1 bản ghi, có thể kèm action.

**Nguyên tắc:**
- **Data mapping:** mọi field hiển thị đúng nguồn dữ liệu, đúng định dạng, không thiếu/thừa so với bản ghi gốc.
- **Related-data consistency:** nếu Detail hiển thị data từ bảng/module liên quan, verify đúng đồng bộ khi data gốc thay đổi.
- **Action theo quyền:** action trên Detail (Edit/Delete/Approve...) chỉ hiện/enable đúng theo Role — dùng Permission Matrix nếu nhiều role.
- **Không tồn tại/đã xóa:** truy cập Detail của record không tồn tại hoặc đã bị xóa → error rõ ràng, không crash.

**Ví dụ bullet Strategy Summary:**
```
- Data mapping đúng cho toàn bộ field trên [tên Screen], đối chiếu [tên AC/nguồn dữ liệu]
- Related-data: [tên data liên quan] đồng bộ đúng khi bản ghi gốc thay đổi
- Permission Matrix cho action [tên action thật] theo Role [A/B/C]
- Record không tồn tại/đã xóa → error rõ ràng, không crash
```

---

## Fallback — Screen không khớp archetype nào

Dùng khi Screen không phải List/Form/Detail rõ ràng (Dashboard, Wizard nhiều bước, Settings...).

**Nguyên tắc chung:**
1. Liệt kê các nhóm chức năng độc lập của Screen (không gộp chung).
2. Test từng nhóm độc lập trước — không test toàn bộ tổ hợp giữa các nhóm.
3. Chỉ chọn tổ hợp có **rủi ro nghiệp vụ cao** hoặc luồng sử dụng phổ biến để test kết hợp.
4. Nếu có yếu tố phân quyền lặp lại nhiều nơi trên Screen → dùng Permission Matrix thay vì lặp TC theo role.

**Ví dụ bullet Strategy Summary:**
```
- Nhóm chức năng độc lập của [tên Screen]: [nhóm 1], [nhóm 2], [nhóm 3]
- Test độc lập từng nhóm trước, chỉ kết hợp [nhóm X] + [nhóm Y] do [lý do rủi ro/nghiệp vụ thật]
- Permission Matrix cho [Role thật] nếu phân quyền lặp ở nhiều nhóm chức năng
```
