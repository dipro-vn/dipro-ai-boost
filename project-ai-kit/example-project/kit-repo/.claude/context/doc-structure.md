# Doc Structure — BMAD

> **Một path duy nhất cho mọi feature** — `<DOCS_ROOT>/features/<feature-name>/` (thay `<DOCS_ROOT>` bằng path thật đã điền trong `AGENTS.md` section `<ecosystem>`).
> Folder này đóng vai trò **long-memory** của dự án (tất cả SPEC/DESIGN/tasks đều ở đây) — không tách riêng theo "epic" hay giai đoạn.

---

## Single-repo feature

Khi feature chỉ ảnh hưởng **1 repo duy nhất** (ví dụ: 1 tính năng chỉ chạm backend, hoặc chỉ chạm 1 web app) — DESIGN.md có thể nằm thẳng trong subfolder repo:

```
<DOCS_ROOT>/features/<feature-name>/
├── SPEC.md                  ← BA tạo (nghiệp vụ + Screens table); Designer điền cột Figma Link
└── <backend-repo>/
    ├── DESIGN.md            ← Tech Lead tạo
    └── tasks/
        ├── task-1-1.md
        └── task-2-1.md
```

> **Designer không tạo file `.md` nào trong folder feature.** Output Designer = Figma frames (cloud) + URL điền vào cột `Figma Link` của bảng `## Screens` trong SPEC.md. FE/Mobile/QC/QA agents tự gọi Figma MCP để đọc design khi cần.

---

## Cross-repo feature

Khi feature ảnh hưởng **nhiều repo** (BE + FE, BE + Mobile, hoặc cả 3 — theo bảng Ecosystem trong `AGENTS.md`):

```
<DOCS_ROOT>/features/<feature-name>/
├── SPEC.md                          ← BA tạo (1 file, nghiệp vụ + Screens table); Designer điền cột Figma Link
├── <backend-repo>/
│   ├── DESIGN.md                    ← Tech Lead (kỹ thuật BE)
│   └── tasks/
│       ├── task-1-1.md              ← Phase 1: DB migration
│       ├── task-2-1.md              ← Phase 2: Service
│       └── task-2-2.md              ← Phase 2: API endpoint
├── <web-repo-a>/                    ← nếu repo này liên quan
│   ├── DESIGN.md
│   └── tasks/
│       └── task-3-1.md
├── <web-repo-b>/                    ← nếu repo này liên quan
│   ├── DESIGN.md
│   └── tasks/
│       └── task-3-2.md
└── <mobile-repo>/                   ← nếu Mobile liên quan
    ├── DESIGN.md
    └── tasks/
        └── task-3-3.md
```

> Sự khác biệt single-repo vs cross-repo **không nằm ở path** (cùng `<DOCS_ROOT>/features/`) mà nằm ở **metadata trong SPEC** (số lượng Actors/repo trong section Actors & Preconditions) — quyết định PM có cần `Contract Lock` trước Phase 3 hay không.

---

## Phân công

| Role | Trách nhiệm |
|---|---|
| BA | Tạo **1 SPEC** — nghiệp vụ, actors, flow, AC, **Screens table**. Không cần biết ranh giới repo. |
| Designer | Đọc SPEC (section `## Screens`) → tạo Figma frames → **điền Figma URL vào cột Figma Link** trong `## Screens` của SPEC.md. Không viết file `.md` riêng. |
| Tech Lead | Đọc SPEC (gồm Figma URLs) → xác định repo (theo bảng Ecosystem trong `AGENTS.md`) → tạo **DESIGN per repo** + tasks (truyền Figma URL vào task Context cho FE/Mobile) |
| Dev | Implement task của repo mình |

---

## Khi nào Mobile cần DESIGN riêng?

Repo mobile cần subfolder + DESIGN.md khi SPEC có:

- Người dùng thao tác trên mobile app
- WebSocket event mới
- Push notification
- API endpoint mới mà Mobile gọi

---

## Khi nào cần Contract Lock?

**Cần** khi feature ảnh hưởng từ **2 repo trở lên** (cross-repo).
**Không cần** khi feature chỉ ảnh hưởng 1 repo (single-repo).

Contract Lock = confirm trước Phase 3:

- REST API endpoints (method/path/DTO/error codes)
- WebSocket events (nếu có)
- Push notification payload (nếu có)
</content>
