# Naming — group_name · section_name · screen_name đa ngôn ngữ

> Áp dụng theo lựa chọn ở Bước 0.5. Mặc định đề xuất **vi + ja + en**, thứ tự dòng vi → ja → en.

Tên layer / Section / frame trên canvas Figma chỉ hiển thị **1 dòng** → tên dài bị cắt `…`. Tách 2 lớp:

## 1. Tên layer (`node.name`) — 1 dòng, nối ` | `

| Loại | 1 ngôn ngữ | vi + ja + en |
|---|---|---|
| group_name | `Luồng đăng ký` | `Luồng đăng ký \| 登録フロー \| Registration flow` |
| section_name | `AI_Generate_Đăng ký` | `AI_Generate_Đăng ký \| 登録 \| Registration` |
| screen_name | `XX_REGI_001 Danh sách` | `XX_REGI_001 \| Danh sách \| 一覧 \| List` |

Screen Code luôn đứng đầu screen_name, không dịch.

## 2. Nhãn hiển thị (TEXT node) — bắt buộc khi ≥ 2 ngôn ngữ

- Đặt ngay **phía trên** group / section / frame (cách 16–24px), mỗi ngôn ngữ **1 dòng**.
- `textAutoResize = "HEIGHT"` + `resize(width_của_node, …)` → tự xuống dòng, không bao giờ bị cắt. Không set height cố định.
- Dòng 1 (Screen Code hoặc ngôn ngữ chính) chữ đậm 18; các dòng sau 16 thường, màu chữ phụ theo design system.
- Label là con của Section / group cha, không nằm trong frame màn hình.

```js
const label = figma.createText();
await figma.loadFontAsync(label.fontName);
label.characters = "XX_REGI_001\nDanh sách\n一覧\nList";
label.textAutoResize = "HEIGHT";
label.resize(frame.width, label.height);
label.x = frame.x; label.y = frame.y - label.height - 16;
label.name = "label · XX_REGI_001";
```

## 3. Checklist
- [ ] Đúng ngôn ngữ đã chọn cho từng cấp.
- [ ] Mọi tên ≥ 2 ngôn ngữ có label nhiều dòng, không chữ nào bị cắt (xác nhận bằng screenshot).
- [ ] Label không chồng frame khác.
- [ ] Bản dịch lấy từ prototype / tài liệu; thuật ngữ không chắc → ghi `[Design]` cần xác nhận.
