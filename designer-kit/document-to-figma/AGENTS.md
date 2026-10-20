# Designer Kit — Document to Figma

> **Kit ad-hoc cho Designer** — mỗi lần chạy = 1 bộ tài liệu (prototype HTML · SPEC · Basic Design · ảnh…) do người dùng đưa vào. Dùng cho **mọi dự án**: design system lấy từ nguồn của chính dự án (link Figma / tài liệu / 1–5 màn Figma mẫu); dự án chưa có → user chọn **Base Design System** chuẩn UI Nhật có sẵn trong kit (`.claude/base-design-system/`).

## Agent

**1 agent duy nhất:** [`designer-agent`](.claude/agents/designer-agent.md)

| Trigger | Cách gọi |
|---|---|
| Natural language | `Hãy là Designer, chuyển tài liệu trong folder input sang Figma` |
| Slash command | `/document-to-figma [document-path] [figma-output-url] [design-system-url]` |

**Input** (hỏi bằng `AskUserQuestion` nếu thiếu):

| Gate | Hỏi gì | Không đạt |
|---|---|---|
| G1 — Design system | Có link Figma / file / artifact / codebase quy định màu, font, size, component… chưa? **Có link artifact Design System đúng định dạng → dùng luôn, không tạo mới.** Còn lại: phân tích → Design System artifact đủ D1–D8 chưa? | Chưa có → dùng **Base Design System** (user chọn) hoặc **dừng** · Thiếu → xin 1–5 màn Figma để agent tự đo, hoặc bù từ base (nhãn `[base]`) |
| G2 — Tài liệu & phạm vi | Tài liệu ở đâu (prototype / SPEC / ảnh…) · muốn vẽ toàn bộ / chọn màn / chỉ phân tích / 1 luồng | Không có tài liệu nào → **dừng** |
| G3 — Figma đầu ra | Link Figma (file / section) có quyền EDIT · tên output | Không có link và không cho tạo file → **dừng** |
| — | Platform · ngôn ngữ tên (vi + ja + en) | — |

**Output:**

| # | Output | Vị trí |
|---|---|---|
| 1 | **Design System artifact** của dự án (định dạng type "Design System": README brand book · tokens · component + preview · Logos / Icons · Cover), user duyệt | Link claude.ai/artifact + `design-system/project/` |
| 2 | Figma frames HIGH-FIDELITY | Link Figma đầu ra user cung cấp |
| 3 | **Screen Index** — frame trên Figma mô tả đã vẽ gì (hyperlink tới từng frame) + bản markdown | Frame cùng page với các section · `output/<feature>/screen-index.md` |
| 4 | **Field Description Table** — bảng mô tả từng trường của mỗi màn hình (JP\|VI), lấy nguyên văn từ tài liệu/SPEC | Section `Mô tả trường` dưới section màn hình trong Figma |
| 5 | Báo cáo: Screen Inventory + Figma link + Design notes | `output/<feature>/figma-screens.md` |

## File hỗ trợ

| File | Nội dung |
|---|---|
| `.claude/designer-agent/design-system-intake.md` | G1 — câu hỏi nguồn, phân tích đầy đủ từng loại nguồn, dựng + publish artifact |
| `.claude/designer-agent/design-system-format.md` | Chuẩn định dạng Design System (cây file, tokens.json, README, component, cover, token vai trò D1–D8, checklist) |
| `.claude/designer-agent/document-intake.md` | G2 — câu hỏi tài liệu đầu vào, phạm vi |
| `.claude/designer-agent/naming-rule.md` | Tên đa ngôn ngữ xuống dòng, không bị cắt |
| `.claude/designer-agent/output-template.md` | Template figma-screens.md |
| `.claude/designer-agent/field-table-spec.md` | Đặc tả Field Description Table (bảng mô tả trường JP\|VI, nguồn nguyên văn) — Bước 5.6 |
| `.claude/designer-agent/screen-index-spec.md` | Đặc tả frame Screen Index trên Figma (vị trí, cột, style, DoD) — Bước 5.5 |
| `.claude/designer-agent/flow-connector-spec.md` | Đặc tả đường nối + nhãn giữa các màn hình (style đo, hình học, legend, DoD) — Bước 5.7 |
| `.claude/designer-agent/design-system-template/` | Skeleton `design-system/` (`STATUS.md` + `project/`) |
| `.claude/base-design-system/` | **Base Design System** chuẩn UI Nhật (DADS + tên vai trò chuẩn công ty) — design system tạm khi dự án chưa có, khung khi dựng từ nguồn dự án (intake §2.6). Bản copy từ `AI_Source/base-design-system/`, giống bản trong ba-kit (sửa ở gốc rồi copy lại cả 3 kit) |
| `.claude/skills/figma-design/` | Đọc / ghi Figma MCP, map token, checklist chất lượng |
| `.claude/rules/` | DATA-PRIVACY · POLICY · RELIABILITY · SECURITY |
| `.claude/hooks/detect-pii.js` | Hook H06 — chặn dữ liệu cá nhân thật khi ghi file / Figma |

## Không có trong kit

BA / Tech Lead / Dev / QC agent. Cần SPEC + flow từ requirement → dùng `ba-kit/requirement-to-flow`.
