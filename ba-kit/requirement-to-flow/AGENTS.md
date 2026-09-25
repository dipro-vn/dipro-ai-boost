# BA Kit — Requirement to Flow

> **Kit ad-hoc cho BA** — mỗi lần chạy = 1 requirement do Human đưa vào (file docs / xlsx / md / pdf / meeting note / user chat), KHÔNG gắn với 1 dự án cụ thể. Không cần `/init-kit`, không cần khai báo repo / actor / stack.

---

## BA Agent làm gì

**1 agent duy nhất:** [`ba-agent`](.claude/agents/ba-agent.md) — canonical workflow.

**Input** (Human đưa vào lúc chạy):
- File requirement: `.docx` / `.md` / `.xlsx` / `.pdf` / meeting note
- Hoặc paste text trực tiếp trong chat
- Hoặc chỉ nói bằng ngôn ngữ tự nhiên → BA sẽ hỏi thêm

**Output** (5 artifacts per lần chạy + Output 5 on-demand):

| # | Output | Path / URL |
|---|---|---|
| 0 | `SPEC.md` (14 sections chuẩn) | `<output-folder>/SPEC.md` |
| 1 | Figma Frame — **Flow Tổng Quan** (Business Logic + Tech Table + Sitemap) | Node trên Figma page user cung cấp |
| 2 | Figma Frame — **Screen Flow** (Master Map + N groups nối bằng **arrow thật** + **Error-Screen Strip** + badge `⚠N` trên mỗi screen + **Combined Overview** + bảng Screen Index + **⑦ Error/Popup Index**) | Node Figma |
| 3 | Figma Frame — **Screens + Items** (mockup + bảng ITEMS + ERROR SCENARIOS) | Node Figma |
| 4 | **HTML Prototype** (standalone, mở bằng `open index.html`) | `<output-folder>/prototype/index.html` |
| 5 | **Basic Design** — ghi spec vào master Excel của công ty ⬜ **ON-DEMAND** | master workbook do user chỉ định |

> **Output 5 không tự chạy.** BA chỉ đề xuất khi Output 1 + Output 2 đã `APPROVED`, và phải hỏi user trước. Ảnh UI (từ Output 3 / Figma) là **tuỳ chọn** — không có ảnh vẫn tạo được sheet, chỉ cần khai báo `NO IMAGE — text only` ở `Screen Index`.

**Snapshot:** Mỗi lần chạy tự lưu vào `<output-folder>/versions/v<N>_<DDMMYYYY>/` để user feedback + so sánh version.

---

## Trigger

**Cách A — Natural language:**
```
Hãy là BA, đọc file <path-to-requirement> và làm SPEC cho <feature>
```

**Cách B — Slash command:**
```
/create-spec <feature>          ← Output 0→4
/basic-design [Screen ID...]    ← Output 5 (on-demand)
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
- ⛔ **KHÔNG đưa 秘密情報・個人情報 của khách hàng vào AI** — tên/email/SĐT/địa chỉ, member/user thực tế, dữ liệu production, password/API key/token, thông tin giao dịch/hợp đồng, dữ liệu KH xác định confidential. Mọi output dùng **dữ liệu mẫu**. Chi tiết: `.claude/rules/DATA-PRIVACY.md`

**5 rule cứng khi vẽ Figma (thêm sau khi audit thực tế — chi tiết trong `.claude/`):**

| Rule | Nội dung | File gốc |
|---|---|---|
| ⛔ **Gate ảnh mẫu** | Trước MỌI `use_figma`: phải mở ảnh mẫu trong `.claude/skills/ba-figma-output/examples/` **và mô tả lại bố cục bằng lời của mình**. Đọc rule dạng chữ mà không xem ảnh → vẽ sai bố cục (đã xảy ra) | `figma-outputs/shared-rules.md` |
| 🔗 **Connector thật** | Mọi screen node phải nối nhau bằng arrow vẽ thật. Liệt kê chip/card rời rạc không mũi tên → **FAIL** | `agents/ba-agent.md` |
| 📊 **Đếm màn lỗi** | `Toast` · `Modal` · `Popup` · `Banner` · `Full screen` · `Empty state` **ĐỀU tính là màn hình**, phải có trong thống kê tổng. Non-Happy bắt buộc dạng **bảng 4 cột** có message thật, cấm văn xuôi | `ba-agent/spec-template.md` |
| 📐 **Quét bbox** | Kết luận "không chồng đè" phải bằng **script quét toạ độ**, không bằng mắt nhìn screenshot | `ba-agent/recheck.md` Tiêu chí 7 |
| 🔢 **Gate FR Coverage** | Mốc đối chiếu "đã đủ" phải là **số dòng chức năng gốc trong nguồn**, không phải số nhóm / số flow do BA tự gom. Kiểm bằng **phép trừ tập hợp** có in `THIẾU: []`, không bằng phép so số lượng. Bảng `## Screens` bắt buộc có cột `FR No.` | `ba-agent/granularity-principles.md` § GATE FR COVERAGE · `recheck.md` Tiêu chí 8 |

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
| `.claude/ba-agent/basic-design/output-5-basic-design.md` | Output 5 — workflow, Input Gate, Proposal Gate, Quality Gate O5 |
| `.claude/ba-agent/basic-design/workbook-structure.md` | Map cell/cột thật của master Excel Basic Design |
| `.claude/rules/DATA-PRIVACY.md` | 秘密情報・個人情報 của KH — 5 nhóm cấm, bản đồ rủi ro theo source/output, bộ dữ liệu mẫu, checklist bàn giao |
| `.claude/hooks/detect-pii.js` | **Hook H06** — chặn cứng PII/credential ở `Write`/`Edit`/`Bash` + MCP (figma/backlog/slack/drive). Self-test: `node .claude/hooks/selftest-detect-pii.js` |
| `.claude/config/pii-patterns.json` | Pattern + allowlist dữ liệu mẫu — nguồn duy nhất, sửa 1 chỗ |
| `.claude/settings.json` | Nối hook vào `PreToolUse`. **Dự án đã có `settings.json` riêng → merge khối `hooks` vào, đừng ghi đè** |

AI behavior policy chung + companion rules → `./POLICIES.md`.
