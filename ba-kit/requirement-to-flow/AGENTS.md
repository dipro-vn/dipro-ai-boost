# BA Kit — Requirement to Flow

> **Kit ad-hoc cho BA** — mỗi lần chạy = 1 requirement do Human đưa vào (file docs / xlsx / md / pdf / meeting note / user chat), KHÔNG gắn với 1 dự án cụ thể. Không cần `/init-kit`, không cần khai báo repo / actor / stack.

---

## BA Agent làm gì

**1 agent duy nhất:** [`ba-agent`](.claude/agents/ba-agent.md) — canonical workflow.

**Input** (Human đưa vào lúc chạy):
- File requirement: `.docx` / `.md` / `.xlsx` / `.pdf` / meeting note
- Hoặc paste text trực tiếp trong chat
- Hoặc chỉ nói bằng ngôn ngữ tự nhiên → BA sẽ hỏi thêm

**Output** (5 artifacts per lần chạy):

| # | Output | Path / URL |
|---|---|---|
| 0 | `SPEC.md` (14 sections chuẩn) | `<output-folder>/SPEC.md` |
| 1 | Figma Frame — **Flow Tổng Quan** (Business Logic + Tech Table + Sitemap) | Node trên Figma page user cung cấp |
| 2 | Figma Frame — **Screen Flow** (N groups + bảng Index) | Node Figma |
| 3 | Figma Frame — **Screens + Items** (mockup + bảng ITEMS + ERROR SCENARIOS) | Node Figma |
| 4 | **HTML Prototype** (standalone, mở bằng `open index.html`) | `<output-folder>/prototype/index.html` |

**Snapshot:** Mỗi lần chạy tự lưu vào `<output-folder>/versions/v<N>_<DDMMYYYY>/` để user feedback + so sánh version.

---

## Trigger

**Cách A — Natural language:**
```
Hãy là BA, đọc file <path-to-requirement> và làm SPEC cho <feature>
```

**Cách B — Slash command:**
```
/create-spec <feature>
```

---

## 3 câu Preflight (BA sẽ hỏi mỗi lần chạy)

BA **không tự đoán** — luôn hỏi 3 câu trước khi bắt tay vào việc:

1. **Scope** — Chức năng đơn lẻ / Cụm chức năng / Toàn hệ thống?
2. **Platform** — Mobile app / Web app / Website / iPad-Tablet?
3. **Figma URL** — paste URL `figma.com/design/...` (nếu có, để BA vẽ Figma frames)

Chi tiết trong `.claude/ba-agent/preflight-questions.md`.

---

## Ràng buộc quan trọng

- BA chỉ tạo/sửa file `.md` + Figma nodes — **tuyệt đối không sửa source code**
- BA không thiết kế kỹ thuật (DB schema, API contract, coding pattern) — đó là việc Tech Lead
- Multi-flow feature → BA hỏi Gate B1/B2 để user chọn vẽ toàn bộ hay 1 flow
- Nếu user "có" Figma URL mà chưa paste → BA DỪNG chờ, KHÔNG tự skip
- Mọi lần chạy đều snapshot vào `versions/` — không overwrite version cũ

---

## Files quan trọng (đọc khi cần chi tiết)

| File | Vai trò |
|---|---|
| `.claude/agents/ba-agent.md` | Canonical BA workflow — sửa quy trình BA chỉ sửa file này |
| `.claude/ba-agent/spec-template.md` | Template 14 sections cho SPEC.md |
| `.claude/ba-agent/preflight-questions.md` | 3 câu Preflight + 10 câu chuẩn |
| `.claude/ba-agent/clarify-ambiguity.md` | Template hỏi khi request mơ hồ |
| `.claude/ba-agent/versioning.md` | Rule snapshot `versions/v<N>_<DDMMYYYY>/` |
| `.claude/ba-agent/figma-outputs/*` | Chi tiết từng Figma output + gate rules |

AI behavior policy chung + companion rules → `./POLICIES.md`.
