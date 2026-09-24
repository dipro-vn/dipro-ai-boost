# BA Kit — System to Doc

> **Kit ad-hoc** — mỗi lần chạy = 1 hệ thống đã có sẵn do Human chỉ định (website / source code / DB / file khách hàng). Không gắn với repo cụ thể, không cần khai báo trước.

---

## Agent làm gì

**1 agent duy nhất:** [`system-analyst`](.claude/agents/system-analyst.md) — canonical workflow.

**Input:**

| Nguồn | Bắt buộc | Ghi chú |
|---|---|---|
| Website đang chạy | ⬜ | Có thể nhiều site. Ưu tiên staging |
| Source code | ⬜ | Repo path |
| Database | ⬜ | Dump / schema / connection read-only |
| File khách hàng cung cấp | ⬜ | `.pdf` / `.docx` / `.xlsx` |

Không có nguồn nào cả → agent không chạy được. Có ít nhất 1 nguồn → chạy được, phần thiếu được ghi rõ là thiếu.

**Output:**

| # | Output | Bắt buộc | Nơi lưu |
|---|---|---|---|
| **O1** | High Level System Analysis (Word) | ✅ | `latest/01_HighLevel_<system>_v<N>.docx` |
| **O1-INV** | Inventory workbook — **artifact nội bộ của agent** | ✅ | `latest/01_Inventory_<system>_v<N>.xlsx` |
| **O2A** | Basic Design → master Excel công ty | ⬜ on-demand | master workbook do user chỉ định |
| **O2B** | Bug List | ⬜ on-demand | `latest/02_BugList_<system>_v<N>.xlsx` |

> **O1-INV không phải deliverable cho khách/user.** Đây là bộ nhớ dài hạn của agent: gate script đọc vào, Output 2 lấy nguồn ra, lần chạy sau đọc lại để làm tiếp. Không đưa vào README hay hướng dẫn sử dụng. Schema: [`inventory-spec.md`](.claude/sys-agent/inventory-spec.md).

---

## Cấu trúc kit

```
.claude/
├── agents/system-analyst.md          ← canonical workflow (sửa quy trình thì sửa file này)
├── commands/
│   ├── analyze-system.md             /analyze-system
│   ├── basic-design.md               /basic-design
│   └── bug-list.md                   /bug-list
├── sys-agent/
│   ├── preflight-questions.md        G-R · G0-G14: wording + xử lý từng câu trả lời
│   ├── source-rules.md               RE1-RE4: nguồn nào cho phép kết luận gì
│   ├── evidence-ledger.md            xương sống chống bịa
│   ├── inventory-spec.md             schema 7 sheet (hợp đồng với script)
│   ├── versioning.md                 snapshot + resume
│   ├── basic-design/
│   │   └── workbook-structure.md     map cell master workbook (copy từ requirement-to-flow)
│   └── outputs/
│       ├── output-1-highlevel.md
│       ├── output-2a-basic-design.md
│       └── output-2b-bug-list.md
└── skills/system-analyst/
    ├── SKILL.md                      chỉ mục script
    └── scripts/                      recon · render · 6 gate · 2 self-test
```

---

## Hai loại gate

| Loại | Ký hiệu | Công cụ | Nguyên tắc |
|---|---|---|---|
| **Hỏi người** | G-R · G0–G14 | `AskUserQuestion` | Cấm in text rồi tự suy ra câu trả lời |
| **Máy chấm** | V1–V10 | script trong `skills/system-analyst/scripts/` | Cấm chấm bằng mắt. Script không chạy được → `❌ Blocked` |

Chi tiết: [`preflight-questions.md`](.claude/sys-agent/preflight-questions.md) và bảng gate trong [`system-analyst.md`](.claude/agents/system-analyst.md).

---

## Quan hệ với `requirement-to-flow`

| | requirement-to-flow | system-to-doc |
|---|---|---|
| Chiều | requirement → tài liệu → hệ thống | hệ thống → tài liệu |
| Loại tài liệu | TO-BE | AS-IS |
| Nguồn sự thật | con người nói ra | hiện vật quan sát được |
| Chống sai | Source Register + R1–R8 | Evidence Ledger + RE1–RE4 |

**Phần dùng chung đã copy sang (self-contained):** `verify-basic-design.py` · `bd_styles.py` · `selftest-basic-design.py` · `workbook-structure.md`, đều mang header `SOURCE: ... @ 447770e`. Sửa logic chung thì **sửa cả hai nơi**.
