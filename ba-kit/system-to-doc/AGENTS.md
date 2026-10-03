# BA Kit — System to Doc

> **Kit ad-hoc** — mỗi dự án = 1 hệ thống đã có sẵn. Không cần khai báo trước; mọi thông tin hỏi lúc chạy.

---

## Agent

**1 agent duy nhất:** [`system-analyst`](.claude/agents/system-analyst.md) — canonical workflow cho cả 2 luồng.

| Luồng | Lệnh | Spec |
|---|---|---|
| **1 — Baseline** | `/analyze-system` | `system-analyst.md` §3 |
| **2 — Change Request** | `/change-request <file / link / nội dung>` | `.claude/sys-agent/flow-2-change-request.md` |

**Input Luồng 1** (hỏi bằng `AskUserQuestion`, không đoán): Website (URL · tài khoản + quyền được dùng · READ/WRITE) · Source code (repo · FE/BE · FE↔website) · DB (tuỳ chọn, schema-only) · Figma (tuỳ chọn: design hiện tại + link để vẽ flow).

**Output Luồng 1** → `outputs/ver<N>_<DDMMYY>_<slug>/`:

| # | Output | Gate |
|---|---|---|
| O1 | Danh sách màn hình theo website (Basic Design xlsx, 1 file / site) | V-BD |
| O2 | API Documentation xlsx (+ batch) + Code map | V-API |
| O3 | Database Documentation xlsx + ERD | V-DB |
| O4 | Design System — chuẩn chung với designer-kit (= format Artifact type "Design System" của claude.ai), publish khi user đồng ý | V-DS |
| O5 | Figma Output 1 + Output 2 (cách vẽ của requirement-to-flow) | recheck bbox |
| O6 | docx tổng hợp | V3 · V5 |
| O7 | Bug list màn hình (quét Playwright) mức Urgent–High (tuỳ chọn) | V8 |

**Output Luồng 2** → `outputs/ver<N>_<DDMMYY>_CR-<id>-<slug>/`: `CR-<id>_Impact.xlsx` (2 sheet: `Summary` giải trình CR + tổng MD · `Impact` từng hạng mục + vì sao sửa + MD) · Figma view CR mới (badge NEW/UPD/DEL/IMPACT/AS-IS, chỉ phần liên quan). Gate V-CR · V-CR-FIGMA. Đơn giá MD: `.claude/config/md-unit-rates.json`.

`_internal/inventory.xlsx` trong mỗi version = bộ nhớ máy đọc của agent (schema: [`inventory-spec.md`](.claude/sys-agent/inventory-spec.md)). Không phải deliverable, không nhắc trong tài liệu cho user.

---

## Cấu trúc kit

```
.claude/
├── agents/system-analyst.md          ← canonical workflow (sửa quy trình thì sửa file này)
├── commands/
│   ├── analyze-system.md             /analyze-system   (Luồng 1)
│   └── change-request.md             /change-request   (Luồng 2)
├── sys-agent/
│   ├── preflight-questions.md        G-R · P0–P11 · G9 · G10
│   ├── flow-2-change-request.md      Luồng 2: nhận CR, 6 trục impact, Figma view CR
│   ├── versioning.md                 folder ver<N>_<DDMMYY>_<slug>, README, run-log
│   ├── source-rules.md · evidence-ledger.md · inventory-spec.md
│   ├── outputs/o1-screens.md … o7-bug-list.md
│   ├── basic-design/workbook-structure.md      (copy từ requirement-to-flow)
│   ├── design-system/                          chuẩn design system + template (copy từ designer-kit)
│   └── figma/                                  (copy từ requirement-to-flow)
├── skills/
│   ├── system-analyst/               SKILL.md + scripts/ (recon · render · gate · self-test)
│   └── ba-figma-output/              (copy từ requirement-to-flow) quy tắc vẽ Figma
├── rules/                            DATA-PRIVACY · SECURITY · RELIABILITY · POLICY
├── hooks/detect-pii.js               H06 — chặn PII/credential trước khi ghi / đẩy lên Figma
├── config/pii-patterns.json
└── settings.json                     nối H06 vào PreToolUse
docs/                                 hướng dẫn sử dụng (docx)
templates/                            sample_basic_design.xlsx · high-level-template.docx
```

---

## Hai loại gate

| Loại | Ký hiệu | Công cụ | Nguyên tắc |
|---|---|---|---|
| **Hỏi người** | G-R · P0–P11 · G9 · G10 · CR-0…CR-2 | `AskUserQuestion` | Cấm in text rồi tự suy ra câu trả lời |
| **Máy chấm** | S1 · V1–V9 · V-BD · V-API · V-DB · V-DS · V-CR | script trong `skills/system-analyst/scripts/` | Cấm chấm bằng mắt. Script không chạy được → `❌ Blocked` |

---

## Quan hệ với kit khác

| | requirement-to-flow | system-to-doc |
|---|---|---|
| Chiều | requirement → tài liệu (TO-BE) | hệ thống → tài liệu (AS-IS) + impact CR |
| Chống sai | Source Register + R1–R8 | Evidence Ledger + RE1–RE4 |

O4 theo **chuẩn design system chung** với `designer-kit` (= format Artifact type **Design System** của claude.ai) → `04_DesignSystem/` copy thẳng sang `designer-kit/.../design-system/` dùng được.

**Phần copy self-contained** (file `.md`/`.py` mang header `SOURCE: …`; hook/config/settings copy nguyên — sửa logic chung thì **sửa cả hai nơi**):

| Từ | Sang |
|---|---|
| requirement-to-flow `scripts/{verify-basic-design,bd_styles,selftest-basic-design}.py` · `basic-design/workbook-structure.md` | `skills/system-analyst/scripts/` · `sys-agent/basic-design/` |
| requirement-to-flow `skills/ba-figma-output/` · `ba-agent/figma-outputs/{output-1-flow,output-2-screen-flow,shared-rules,code-patterns}.md` · `ba-agent/{granularity-principles,recheck}.md` | `skills/ba-figma-output/` · `sys-agent/figma/` |
| requirement-to-flow `rules/` · `hooks/detect-pii.js` · `config/pii-patterns.json` · `settings.json` | cùng đường dẫn |
| designer-kit `designer-agent/design-system-format.md` · `design-system-template/` | `sys-agent/design-system/design-system-format.md` · `sys-agent/design-system/template/` |
