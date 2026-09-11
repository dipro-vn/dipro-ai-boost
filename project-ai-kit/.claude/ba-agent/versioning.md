# BA Agent — Versioning & Snapshot (Bước 3)

> **Scope:** Folder structure + 5 rule versioning + template `ba-outputs-log.md`.
> **Dùng ở:** `ba-agent.md` Bước 3 và Output section (snapshot trước Report cuối). Agent body chỉ giữ 3-5 dòng note + reference file này.

---

## Folder structure (canonical + versions)

**Canonical path (LATEST)** cho mọi feature: `<DOCS_ROOT>/features/<feature-name>/`

```
<DOCS_ROOT>/features/<feature-name>/
├── SPEC.md                         ← latest (downstream agent Read từ đây)
├── prototype/index.html            ← latest HTML prototype
└── versions/                       ← snapshot mỗi lần BA chạy (feedback + so sánh lịch sử)
    ├── v1_<DDMMYYYY>/
    │   ├── SPEC.md                 ← snapshot SPEC lần chạy này
    │   ├── ba-outputs-log.md       ← record 5 outputs (path SPEC + 3 Figma URL + HTML path + ghi chú)
    │   └── prototype/index.html    ← snapshot HTML (nếu có change)
    ├── v2_<DDMMYYYY>/
    │   └── ...
    └── ...
```

---

## Rule versioning (BẮT BUỘC — không skip)

### Rule 1 — Trước khi bắt đầu BA workflow

Check `versions/` folder:
- Nếu CHƯA có → sẽ tạo `versions/v1_<DDMMYYYY>/` sau khi hoàn thành
- Nếu ĐÃ có → xác định `N` version tiếp theo (VD đã có `v3_...` → lần này là `v4_...`)

### Rule 2 — Sau khi hoàn thành 5 outputs (trước Report cuối)

Snapshot vào `versions/v<N>_<DDMMYYYY>/`:
- `cp SPEC.md versions/v<N>_<DDMMYYYY>/SPEC.md`
- Tạo `versions/v<N>_<DDMMYYYY>/ba-outputs-log.md` với bảng 5-row (path SPEC + 3 Figma URL + HTML path) + ghi chú thay đổi so với version trước (nếu có)
- Copy `prototype/index.html` → `versions/v<N>_<DDMMYYYY>/prototype/index.html` (nếu HTML có thay đổi so với version trước)

### Rule 3 — Format `<DDMMYYYY>`

- Dùng convention `DDMMYYYY` theo user quy định (VD `09092026`, `11092026`)
- Lấy today's date từ system context, KHÔNG tự đoán ngày

### Rule 4 — Template `ba-outputs-log.md` per version

```markdown
# BA Outputs Log — v<N> (<DDMMYYYY>)

> Snapshot output BA cho feature `<feature-name>` lần chạy v<N>. Mọi feedback từ user đối với version này ghi vào section "Feedback" cuối file (không sửa các bảng bên trên).

## 5 Outputs

| # | Output | Status | Path / URL | Note |
|---|---|---|---|---|
| 0 | SPEC.md | ... | `versions/v<N>_<DDMMYYYY>/SPEC.md` | ... |
| 1 | Figma Flow Tổng Quan | ... | `<URL>` | ... |
| 2 | Figma Screen Flow | ... | `<URL>` | ... |
| 3 | Figma Screens + Items | ... | `<URL>` | ... |
| 4 | HTML Prototype | ... | `versions/v<N>_<DDMMYYYY>/prototype/index.html` | ... |

## Diff so với version trước (v<N-1>)

- <thay đổi cụ thể: VD "thêm Non-Happy Case 'mất mạng khi submit'", "sửa Actor 'User' → 'Admin'">
- Nếu là v1 → ghi "Version đầu tiên — không có diff"

## Feedback từ user (điền sau khi user review)

- <để trống, user điền sau khi review>
```

### Rule 5 — KHÔNG được

- ❌ Overwrite version cũ (không xóa `versions/v1_...` khi tạo `v2_...`)
- ❌ Skip snapshot vì "nhỏ nhặt" — mọi lần chạy đều snapshot
- ❌ Đặt tên version tự chế (`v-final`, `v-latest`) — chỉ dùng `v<N>_<DDMMYYYY>` với N tăng dần

---

## Reference note khác

Số lượng actor / repo bị ảnh hưởng được ghi trong section **Actors & Preconditions** của SPEC — đó là tín hiệu để PM biết có cần Contract Lock trước Phase 3 hay không (xem `.claude/context/doc-structure.md`).
