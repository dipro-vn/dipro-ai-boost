# ba-kit — BA-only Agent Kit

> Bộ kit chuyên biệt cho Business Analyst — pull ra từ `project-ai-kit` gốc, chỉ chứa những gì BA agent cần để phân tích requirement + tạo SPEC + Figma output + HTML prototype.
> Dùng khi bạn KHÔNG cần full pipeline BMAD (Tech Lead / PM / Dev / QC / QA / Designer), chỉ muốn 1 BA agent tự chạy độc lập.

---

## Khi nào dùng ba-kit thay vì `project-ai-kit`?

| Trường hợp | Dùng kit nào |
|---|---|
| Cần đủ pipeline BMAD (BA → TL → PM → Dev → QC → QA → Designer) | `project-ai-kit` |
| Chỉ cần BA phân tích 1 requirement → SPEC + Figma flow + HTML prototype | **`ba-kit`** (nhẹ hơn, ít file, không nhiễu context) |
| Freelance BA nhận job clarify requirement + wireframe cho khách | **`ba-kit`** |
| Team đã có Tech Lead / PM / Dev riêng — chỉ muốn BA AI hỗ trợ | **`ba-kit`** |

---

## Features có sẵn trong ba-kit

Mỗi folder con là 1 use-case BA riêng. Chọn 1 tùy nhu cầu:

| Folder | Use-case | Input | Output |
|---|---|---|---|
| [`requirement-to-flow/`](./requirement-to-flow/) | Tạo flow cho requirement từ file estimation, docs, excel, md, meeting note... | Bất kỳ (docs / xlsx / md / pdf / user chat) | SPEC.md + 3 Figma frames (Flow / Screen Flow / Screens+Items) + HTML Prototype |

> Sẽ có thêm feature folders khi mở rộng scope BA (ví dụ: `spec-to-testcase/`, `flow-to-mermaid/`, `interview-to-spec/`...).

---

## Cách dùng nhanh

1. Chọn feature folder phù hợp (ví dụ `requirement-to-flow/`)
2. Đọc `<feature>/README.md` để biết cách setup + trigger BA agent
3. Copy folder `.claude/` + `CLAUDE.md` + `POLICIES.md` + `AGENTS.md` từ feature folder đó vào dự án của bạn
4. Mở Claude Code trong dự án đó → chạy `"hãy là BA, làm SPEC cho <requirement>"`

---

## Cấu trúc kit

```
ba-kit/
├── README.md                            ← file này
└── requirement-to-flow/
    ├── README.md                        ← hướng dẫn feature này
    ├── CLAUDE.md                        ← bootstrap load POLICIES + AGENTS
    ├── POLICIES.md                      ← AI behavior rules
    ├── AGENTS.md                        ← project-specific rules (template)
    └── .claude/
        ├── agents/
        │   └── ba-agent.md              ← canonical BA workflow
        ├── ba-agent/                    ← support docs (spec template, versioning, self-check...)
        ├── skills/
        │   ├── business-analyst/        ← BA domain skill
        │   └── ba-figma-output/         ← Figma output skill
        ├── context/                     ← project context (specification, doc-structure...)
        ├── rules/                       ← POLICY, RELIABILITY, SECURITY, security-rules, stack-constraints
        └── commands/
            ├── create-spec.md
            └── create-feature.md
```

---

## Liên hệ / Đóng góp

Kit này pull từ [`project-ai-kit`](../project-ai-kit/) — nếu cần feature mới cho BA, đề xuất add vào ba-kit hoặc sync ngược về project-ai-kit.
