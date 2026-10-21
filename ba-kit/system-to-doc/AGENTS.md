# BA Kit — System to Doc

> **Kit ad-hoc** — mỗi dự án = 1 hệ thống đã có sẵn. Không cần khai báo trước; mọi thông tin hỏi lúc chạy.

---

## Agent

**1 agent duy nhất:** [`system-analyst`](.claude/agents/system-analyst.md) — canonical workflow cho cả 2 luồng.

**Văn phong:** mọi câu trả lời trong phiên và mọi chữ khách đọc theo [`sys-agent/writing-style.md`](.claude/sys-agent/writing-style.md) — vai PM / BrSE chuẩn Nhật, đúng trọng tâm, ngắn, dễ hiểu, không chào hỏi / tóm tắt cuối.

| Luồng | Lệnh | Spec |
|---|---|---|
| **1 — Baseline** | `/analyze-system` | `system-analyst.md` §3 |
| **2 — Change Request** | `/change-request <file / link / nội dung>` | `.claude/sys-agent/flow-2-change-request.md` |

**Môi trường — kit tự cài:** đầu Luồng 1 / Luồng 2 agent chạy `ensure-env.py` (thư viện Python · Playwright + Chromium · Figma MCP), thiếu thì tự cài. User **không** cài tay; chỉ bấm Authenticate Figma (`/mcp`) khi agent nhờ.

**Input Luồng 1** (hỏi bằng `AskUserQuestion`, không đoán): Website (URL · tài khoản + quyền được dùng · READ/WRITE) · Source code (repo · FE/BE · FE↔website) · DB (tuỳ chọn, schema-only) · Figma (tuỳ chọn: design hiện tại + link để vẽ flow).

**Output Luồng 1** → `outputs/ver<N>_<DDMMYY>_<slug>/`:

| # | Output | Gate |
|---|---|---|
| O1 | Danh sách màn hình theo website (Basic Design xlsx, 1 file / site) | V-BD |
| O2 | API Documentation xlsx (+ batch) + Code map | V-API |
| O3 | Database Documentation xlsx + ERD | V-DB |
| O4 | Design System — chuẩn chung với designer-kit (= format Artifact type "Design System" của claude.ai), **dựng trên Base Design System chuẩn Nhật** `.claude/base-design-system/` (giá trị hệ thống thắng; phần không quan sát được lấy base, nhãn `[base]`), publish khi user đồng ý. Hệ thống không có DS → CR-3 dùng base tạm | V-DS |
| O5 | Figma Output 1 (**use case**: Actor → đường đi → kết thúc, non-happy hàng dưới · Technology Stack · Sitemap Site → Actor → Nhóm → Màn) + Output 2 (**site → use case → section**) · không chữ `UNKNOWN` trên hình | recheck bbox · phủ SC |
| O6 | docx tổng hợp | V3 · V5 |
| O7 | Bug list màn hình (quét Playwright) mức Urgent–High (tuỳ chọn) | V8 |

**Output Luồng 2** → `outputs/ver<N>_<DDMMYY>_CR-<id>-<slug>/`: `CR-<id>_Impact.xlsx` (7 sheet: `Summary` công số + số đối tượng thay đổi + link · `Estimation` = bản vi nội bộ của 見積書, 1 dòng / chức năng (`--estimate`) · `Screen` · `API` · `Database` · `Figma` · `Q&A` giải trình CR + câu hỏi KH) · Figma view CR mới (`sys-agent/figma/cr-view.md`): CR-1 Flow format Output 1 (**mỗi lane có NON-HAPPY**) · CR-2 Screen Flow format Output 2 (**màn / popup lỗi + Screen Index có Loại + ⑦ Error/Popup Index**) · CR Change Table thống kê · CR-3 màn đề xuất **format Output 3** (mockup trái · mô tả + ITEMS + ERROR SCENARIOS phải · NEW + UPD tô màu phần đổi + popup lỗi) bám Design System (badge NEW/UPD/DEL/IMPACT/AS-IS, chỉ phần liên quan). **> 1 site → mỗi site 1 Section riêng (CR-2 · CR-3 · Output 2 Luồng 1); trong section: site → flow nghiệp vụ → màn; section CR-3 nền `#9DA5AD`.** Gate V-CR-FIGMA check 11–14. **`CR-<id>_見積書.xlsx`** gửi KH (tiếng Nhật, 詳細見積書 + 前提条件・留意事項, theo `templates/template_mitsumori.xlsx`) sinh từ `_internal/estimate.json` — quy tắc `sys-agent/estimate-rules.md` + **văn phong cho khách `sys-agent/writing-style.md`** (gate V-EST E4 / E9 / E10), câu hỏi nghiệp vụ gửi khách sinh thành sheet 確認事項 / Câu hỏi nghiệp vụ, câu hỏi CR-4. Gate V-CR · V-EST · V-CR-FIGMA. Đơn giá: `.claude/config/function-rates.json` (見積書, theo chức năng) · `md-unit-rates.json` (impact nội bộ).

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
│   ├── flow-2-change-request.md      Luồng 2: nhận CR, 6 trục impact, xlsx 7 sheet, Figma view CR
│   ├── estimate-rules.md             Luồng 2: phân rã chức năng cho 見積書 (estimate.json, V-EST)
│   ├── versioning.md                 folder ver<N>_<DDMMYY>_<slug>, README, run-log
│   ├── source-rules.md · evidence-ledger.md · inventory-spec.md
│   ├── outputs/o1-screens.md … o7-bug-list.md
│   ├── basic-design/workbook-structure.md      (copy từ requirement-to-flow)
│   ├── design-system/                          chuẩn design system + template (copy từ designer-kit)
│   └── figma/                                  (copy từ requirement-to-flow) + cr-view.md (view CR Luồng 2 — riêng kit này)
├── skills/
│   ├── system-analyst/               SKILL.md + scripts/ (ensure-env · recon · render · gate · self-test)
│   └── ba-figma-output/              (copy từ requirement-to-flow) quy tắc vẽ Figma
├── base-design-system/                Base Design System chuẩn UI Nhật (DADS + tên chuẩn công ty) — O4 dựa vào, CR-3 dùng tạm khi hệ thống không có DS
├── rules/                            DATA-PRIVACY · SECURITY · RELIABILITY · POLICY
├── hooks/detect-pii.js               H06 — chặn PII/credential trước khi ghi / đẩy lên Figma
├── config/pii-patterns.json
└── settings.json                     nối H06 vào PreToolUse
inputs/                               có sẵn repo/ · db/ · cr/ — user bỏ file vào (AI tự tìm trước khi hỏi); README trong từng folder
.auth/                                credentials.example.env (mẫu) → credentials.local.env (user điền, AI không đọc) · KHÔNG commit
outputs/                              AI tự tạo mỗi lần chạy 1 folder ver<N>_...
docs/                                 hướng dẫn sử dụng (docx)
templates/                            sample_basic_design.xlsx · high-level-template.docx · template_estimation.xlsx (layout cũ) · template_mitsumori.xlsx (見積書 Luồng 2)
```

---

## Hai loại gate

| Loại | Ký hiệu | Công cụ | Nguyên tắc |
|---|---|---|---|
| **Hỏi người** | G-R · P0–P11 · G9 · G10 · CR-0…CR-4 | `AskUserQuestion` | Cấm in text rồi tự suy ra câu trả lời |
| **Máy chấm** | S1 · V1–V9 · V-BD · V-API · V-DB · V-DS · V-CR · V-EST | script trong `skills/system-analyst/scripts/` | Cấm chấm bằng mắt. Script không chạy được → `❌ Blocked` |

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
| `AI_Source/base-design-system/` (gốc, gitignored) — `project/` · `STATUS.md` · `prompt_design_system.md` · `README.md` | `.claude/base-design-system/` của **cả 3 kit** (requirement-to-flow + system-to-doc + designer-kit/document-to-figma). Lệch bản → `selftest-design-system.py` FAIL |
