---
description: Sinh Playwright spec từ SPEC.md + Figma (+ TC.md nếu có) và chạy E2E test. Dùng: /qc-automation <feature-path> <figma-url> [testcases]
---

Đọc `.claude/agents/qc-automation-agent.md` rồi đóng vai **QC Automation Tester** để sinh Playwright spec và chạy E2E test.

Arguments: **$ARGUMENTS**

Parse arguments theo thứ tự:
1. `feature-path` — path đến folder feature (ví dụ: `docs/features/company-account`)
2. `figma-url` — Figma node URL (ví dụ: `https://www.figma.com/file/xxx/...`)
3. `testcases` _(tùy chọn)_ — path đến file TC thủ công từ qc-agent. Khi có → ưu tiên đọc TC file thay vì tự suy từ SPEC.md.

`target-app`: tự suy từ context (tên feature, repo, app được đề cập). Nếu không rõ → hỏi 1 câu trước khi chạy.
`website-url`: đọc tự động từ `.env.test` (biến `<APP>_URL` tương ứng với target app — xem bảng Ecosystem trong AGENTS.md để map app → biến env) — không hỏi user.

Nếu thiếu argument 1–2 → hỏi user trước khi bắt đầu.

Toàn bộ workflow (Bước 1→7), ràng buộc selector, cấu trúc report nằm trong `qc-automation-agent.md` — tuân thủ đầy đủ.
