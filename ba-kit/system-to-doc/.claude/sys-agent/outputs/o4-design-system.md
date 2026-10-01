# O4 — Design System của hệ thống cũ

> **Yêu cầu:** chỉ tạo khi **có đọc từ website hoặc Figma** · nguồn gồm website + source code (+ Figma nếu có) · cấu trúc theo `designer-kit` · lưu lại để **sau này phát triển / đề xuất màn mới thì reference tới file này** (Luồng 2 trục Mockup, kit `designer-kit` khi vẽ màn mới).
>
> Thành phẩm: `04_DesignSystem/` — đúng cấu trúc `designer-kit/prototype-to-figma/design-system/`, để copy thẳng sang kit đó dùng được.

---

## 1. Điều kiện

| Có | O4 |
|---|---|
| Website đã crawl (P1) **hoặc** Figma input (P7) | ✅ chạy |
| Chỉ có source code | ⬜ **không chạy** — token trong CSS chưa chắc là cái đang hiển thị. `--skip "O4=chỉ có source code, chưa quan sát UI"` |

---

## 2. Thu nguồn — chỉ ghi cái **quan sát được**

| Nguồn | Lấy gì | Cách |
|---|---|---|
| **Website** | màu nền/chữ/nút/viền/link, font, cỡ chữ, radius, padding, viewport | `crawl-site.js` ghi `styles.json` → `extract-design-tokens.py` tổng hợp theo tần suất |
| **Source code** | tên token (CSS variable, SCSS var, Tailwind theme), font khai báo | `extract-design-tokens.py --css-root REPO-xx=<path>` |
| **Figma** (P7) | variable, style, component library | Figma MCP: `get_variable_defs` · `get_metadata` · `search_design_system` · `get_screenshot` (theo `designer-kit/.../design-system-intake.md` §2) |

```bash
python3 $S/extract-design-tokens.py --crawl $I/recon/crawl --css-root REPO-01=<fe-repo> --out $I/recon/design
# → $I/recon/design/tokens-draft.json + tokens-draft.md (xếp hạng theo tần suất, kèm nguồn)
```

**Thứ tự ưu tiên khi mâu thuẫn** (ghi vào README mục "Mâu thuẫn cần xác nhận"):
1. Giá trị **đo trên website đang chạy** (cái người dùng đang thấy)
2. Variable / style trong Figma
3. Khai báo trong source code (có thể là code chết)

---

## 3. Dựng folder

Copy `.claude/sys-agent/design-system-template/` → `$V/04_DesignSystem/`, **đổi tên `platform.md` → `platform-<WEB-xx>.md`** (1 file / site), rồi điền. Mục "Thứ tự ưu tiên nguồn" trong `README.md` của template (viết cho designer-kit, Figma đứng đầu) → **thay bằng thứ tự ở §2** (website đứng đầu):

| File | Checklist designer-kit | Điền từ |
|---|---|---|
| `README.md` | nguồn · platform · trạng thái · mâu thuẫn · changelog | Nguồn: `WEB-01 (<n> trang)`, `REPO-01`, `Figma <link>` · **Trạng thái: `DRAFT`** |
| `foundation.md` | D1 primary · D2 nền/chữ · D3 trạng thái · D4 typography · D5 spacing/radius/shadow · D8 icon & ngôn ngữ UI | `tokens-draft.json` (màu → vai trò theo `roles`), message lỗi O1 cho màu error |
| `platform-<WEB-xx>.md` | D7 viewport + khung màn + page pattern (List/Detail/Form/Modal) | 1 file / website; pattern lấy từ `02_Screen.Type` + screenshot |
| `components.md` | D6 component | Có Figma library → key component. Không có → liệt kê component **quan sát được** (Button, Input, Select, Table, Badge, Modal, Pagination) kèm style đo được + màn ví dụ `SC-xxx` |
| `tokens.json` | giữ đúng key của template | giá trị từ draft |
| `refs/` | screenshot màn đại diện | copy từ `_internal/evidence/` — **chỉ** ảnh không có dữ liệu thật (P11) |

Thiếu một mục D1–D8 → ghi `TBD — <lý do>` (VD `TBD — không quan sát được trạng thái warning trên UI`). **Không chế màu cho đủ bộ.**

---

## 4. Gate V-DS

```bash
python3 $S/verify-design-system.py $V/04_DesignSystem --draft $I/recon/design/tokens-draft.json \
    [--figma-used] --out $I/gates/v-ds.md
```
Chặn: thiếu file · placeholder template còn sót · **màu / font không có trong dữ liệu quan sát** (bịa token) · trạng thái `APPROVED` (AI không được tự duyệt — người duyệt sửa thành `APPROVED <ngày>`) · nguồn không có website/Figma.

---

## 5. Dùng lại về sau

| Ai | Dùng thế nào |
|---|---|
| Luồng 2 — trục `06_Mockup` | Màn NEW/UPD phải trỏ `DS:<token>` / `DS-component:<tên>` của folder này |
| Luồng 2 — Figma CR mockup | Vẽ bằng màu/font/component trong folder này |
| `designer-kit/prototype-to-figma` | Copy `04_DesignSystem/` → `design-system/` của kit đó; designer duyệt → `APPROVED <ngày>` |

Version sau (DELTA) giữ token cũ, chỉ cập nhật cái đo lại khác đi + ghi Changelog.
