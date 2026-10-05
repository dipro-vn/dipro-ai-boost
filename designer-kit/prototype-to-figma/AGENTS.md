# Designer Kit — Prototype to Figma

> **Kit ad-hoc cho Designer** — mỗi lần chạy = 1 prototype HTML do người dùng đưa vào. Dùng cho **mọi dự án**: design system lấy từ nguồn của chính dự án (link Figma / tài liệu / 1–5 màn Figma mẫu), không có mặc định.

## Agent

**1 agent duy nhất:** [`designer-agent`](.claude/agents/designer-agent.md)

| Trigger | Cách gọi |
|---|---|
| Natural language | `Hãy là Designer, chuyển prototype trong folder input sang Figma` |
| Slash command | `/prototype-to-figma [prototype-path] [figma-output-url]` |

**Input** (hỏi bằng `AskUserQuestion` nếu thiếu):

| Gate | Hỏi gì | Không đạt |
|---|---|---|
| G1 — Design system | Có link Figma / file / artifact / codebase quy định màu, font, size, component… chưa? Phân tích → Design System artifact đủ D1–D8 chưa? | Chưa có → **dừng** · Thiếu → xin 1–5 màn Figma để agent tự đo, bổ sung |
| G2 — Prototype & phạm vi | Prototype ở đâu · tài liệu khác · muốn vẽ toàn bộ / chọn màn / chỉ phân tích / 1 luồng | Không có prototype và tài liệu → **dừng** |
| G3 — Figma đầu ra | Link Figma (file / section) có quyền EDIT · tên output | Không có link và không cho tạo file → **dừng** |
| — | Platform · ngôn ngữ tên (vi + ja + en) | — |

**Output:**

| # | Output | Vị trí |
|---|---|---|
| 1 | **Design System artifact** của dự án (định dạng type "Design System": README brand book · tokens · component + preview · Logos / Icons · Cover), user duyệt | Link claude.ai/artifact + `design-system/project/` |
| 2 | Figma frames HIGH-FIDELITY | Link Figma đầu ra user cung cấp |
| 3 | Báo cáo: Screen Inventory + Figma link + Design notes | `output/<feature>/figma-screens.md` |

## File hỗ trợ

| File | Nội dung |
|---|---|
| `.claude/designer-agent/design-system-intake.md` | G1 — câu hỏi nguồn, phân tích đầy đủ từng loại nguồn, dựng + publish artifact |
| `.claude/designer-agent/design-system-format.md` | Chuẩn định dạng Design System (cây file, tokens.json, README, component, cover, token vai trò D1–D8, checklist) |
| `.claude/designer-agent/prototype-intake.md` | G2 — câu hỏi prototype, phạm vi, tài liệu |
| `.claude/designer-agent/naming-rule.md` | Tên đa ngôn ngữ xuống dòng, không bị cắt |
| `.claude/designer-agent/output-template.md` | Template figma-screens.md |
| `.claude/designer-agent/design-system-template/` | Skeleton `design-system/` (`STATUS.md` + `project/`) |
| `.claude/skills/figma-design/` | Đọc / ghi Figma MCP, map token, checklist chất lượng |
| `.claude/rules/` | DATA-PRIVACY · POLICY · RELIABILITY · SECURITY |
| `.claude/hooks/detect-pii.js` | Hook H06 — chặn dữ liệu cá nhân thật khi ghi file / Figma |

## Không có trong kit

BA / Tech Lead / Dev / QC agent. Cần SPEC + flow từ requirement → dùng `ba-kit/requirement-to-flow`.
