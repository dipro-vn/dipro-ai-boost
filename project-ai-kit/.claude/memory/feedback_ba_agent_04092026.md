---
name: feedback-ba-agent-04092026
description: Feedback từ demo 04/09/2026 — BA agent thiếu flow tổng quan, screen details, UX review, post-meeting workflow
metadata:
  type: feedback
---

BA agent phải output 9 điểm bổ sung sau demo 04/09/2026 (file: `feedbacks/feedback_04092026_BA.md`).

**Why:** Output cũ chỉ có bảng Screens đơn giản — stakeholder không hình dung được flow, Designer thiếu context để vẽ Figma, QC thiếu non-happy cases.

**How to apply:** Khi chạy `/create-spec`, ba-agent.md đã được cập nhật với các section và bước mới. Không cần can thiệp thêm trừ khi user báo vẫn thiếu.

**Các thay đổi đã apply vào `.claude/agents/ba-agent.md`:**
1. SPEC template thêm `## Flow Tổng Quan` — ASCII flow toàn bộ luồng (happy + non-happy branches)
2. SPEC template thêm `## Screen Details` — per-screen: components, positions, actions, Non-Happy Case table
3. `## Screens` bổ sung cột `Transition To` (screen chuyển đi đâu) + tổng số màn hình ở đầu section
4. SPEC template thêm `## Responsive Requirements` — breakpoints iPad/Mobile/MacBook/Wide
5. Bước 4.5: AI UX Self-Review (UX usability / information design / performance risk)
6. Bước 4.6: Completeness Self-Check — checklist trước khi output
7. Post-Meeting Workflow: tạo `customer_feedback_DDMMYY.md` + `meeting_note_DDMMYY.md` với 3 sections (decided/undecided/feedback) + impact analysis table
8. Output section: ghi rõ Designer output ưu tiên ảnh Figma + text document bên cạnh (không dùng HTML)
9. Output section: hiển thị tổng screen count

[[feedback-designer-04092026]]
