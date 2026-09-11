# Ba Agent — Post-Meeting Workflow (on-demand)

> Không thuộc luồng chính. Kích hoạt khi user nói: "vừa có cuộc họp", "KH feedback", "có meeting note cần xử lý".

**Bước 1 — Tạo document ghi nhận:**

```
<DOCS_ROOT>/meetings/customer_feedback_<DDMMYY>.md   ← feedback trực tiếp từ KH
<DOCS_ROOT>/meetings/meeting_note_<DDMMYY>.md         ← note đầy đủ từ Gemini / ghi tay
```

Template `meeting_note_DDMMYY.md`:
```markdown
# Meeting Note — <DD/MM/YY>

## Participants
- <tên / role>

## Các điểm đã quyết định
- <quyết định 1>

## Các điểm chưa quyết định
- <vấn đề còn open + owner + deadline trả lời>

## Các điểm khách hàng đang feedback
- <feedback + screen / feature liên quan>
```

**Bước 2 — Impact Analysis:**

Sau khi có meeting note, BA đánh giá impact lên SPEC/DESIGN hiện có:

```
tilth_files(pattern: "**/SPEC.md")   ← tìm các SPEC liên quan
```

Với mỗi feedback item → xác định:
- Ảnh hưởng section nào trong SPEC? (Happy Path / AC / Screens / Screen Details)
- Có cần thêm/sửa/xóa screen không?
- Cần thông báo Tech Lead (Design-Technical.md bị ảnh hưởng)?

Trình user bảng impact trước khi sửa:

| Feedback | Ảnh hưởng | SPEC section | Action |
|---|---|---|---|
| <feedback text> | <screen code> | <section name> | Cần update / Cần hỏi lại |

**Bước 3 — Update đồng bộ:**
Chỉ update sau khi user confirm bảng impact ở Bước 2. Cập nhật đồng bộ tất cả màn hình liên quan trong cùng 1 lần edit.
