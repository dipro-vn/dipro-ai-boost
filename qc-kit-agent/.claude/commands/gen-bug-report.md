---
description: Chuẩn hóa bug report từ mô tả lỗi của QC — phân loại bug type/severity/priority, sinh steps to reproduce rõ ràng, format sẵn sàng paste vào Backlog.
skills:
  - bug_reporter
---

> **BẮT BUỘC (MANDATORY SKILL):** Bạn PHẢI nạp và đọc kỹ nội dung của skill **`bug_reporter`** (tại `.claude/skills/bug_reporter/SKILL.md`) trước khi bắt đầu.

# Workflow: Sinh Bug Report Chuẩn

Workflow này giúp QC chuyển mô tả lỗi thô thành bug report **đầy đủ, rõ ràng, sẵn sàng cho DEV** — không cần hỏi lại.

## Khi nào dùng

- QC vừa tìm được bug và muốn viết report nhanh
- Cần chuẩn hóa bug report đang viết dở
- Muốn kiểm tra severity/priority trước khi submit lên Backlog
- **Không dùng** workflow này để sinh test cases

## Input cần từ User

| Input | Bắt buộc | Mô tả |
|-------|----------|-------|
| **Mô tả bug** | ✅ | Mô tả lỗi bằng ngôn ngữ tự nhiên — viết sơ cũng được |
| **Environment** | ⚠️ Nên có | Browser, OS, URL, build, test account |
| **Evidence** | ⚠️ Nên có | Screenshot, video, console log |
| **Module/Tính năng** | ⚠️ Nên có | Để gán Bug ID đúng |
| **Mức Severity đề xuất** | ❌ Optional | Nếu không có → agent tự phân loại và giải thích |

## Các bước thực hiện

### Bước 1: Thu thập thông tin

1. Đọc mô tả bug từ user
2. Nếu thiếu thông tin quan trọng, hỏi **gộp 1 lần duy nhất**:
   - Environment (nếu chưa có)
   - Steps cụ thể để reproduce (nếu mô tả quá chung chung)
   - Expected behavior (nếu chưa rõ)
3. Nếu đủ thông tin → tiến hành luôn, không hỏi thêm

### Bước 2: Phân tích và phân loại

1. Xác định **Bug Type** theo bảng phân loại trong skill `bug_reporter` — giải thích lý do nếu có thể nhầm giữa 2 loại
2. Xác định **Severity** theo bảng trong skill `bug_reporter`
3. Xác định **Priority** đề xuất — giải thích lý do nếu khác với user
4. Đánh giá **Reproducibility** từ mô tả
5. Xác định **module** để sinh Bug ID

### Bước 3: Chuẩn hóa Steps to Reproduce

1. Viết lại steps theo quy tắc trong skill:
   - Precondition đầy đủ (tài khoản, trạng thái ban đầu, URL)
   - Mỗi step = 1 action
   - Test data cụ thể
   - Step cuối = action trigger lỗi
2. Phân biệt rõ Expected Result vs Actual Result

### Bước 4: Xuất Bug Report

Xuất theo Output Format trong skill `bug_reporter`. Nếu có nhiều bugs được mô tả cùng lúc → sinh **từng report riêng biệt**.

## Quy tắc quan trọng

- ❌ KHÔNG gộp nhiều bugs vào 1 report
- ❌ KHÔNG tự giả định steps nếu user chưa mô tả rõ → hỏi trước
- ✅ Nếu không có evidence → ghi rõ "Chưa có — QC cần bổ sung screenshot/video"
- ✅ Luôn giải thích lý do phân loại Severity/Priority nếu có thể gây tranh luận
