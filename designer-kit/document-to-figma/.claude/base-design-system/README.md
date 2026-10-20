> **SOURCE:** `AI_Source/base-design-system/` (bản gốc, gitignored) — bản copy self-contained cho kit. Sửa ở bản gốc (chạy `tools/add-company-layer.py` ở đó) rồi copy lại vào **cả 3 kit** (`ba-kit/requirement-to-flow`, `ba-kit/system-to-doc`, `designer-kit/document-to-figma`); selftest `selftest-design-system.py` của system-to-doc báo lệch bản.

# Base Design System — chuẩn UI Nhật dùng chung cho ba-kit và designer-kit

Design system nền cho các màn **đề xuất** trong `ba-kit`. Gồm 2 nguồn, dùng cùng nhau:

| Nguồn | File | Vai trò |
|---|---|---|
| **Nguyên tắc thiết kế** | `prompt_design_system.md` | Luật thiết kế cho thị trường Nhật: đơn giản, dễ dùng, nhất quán, chức năng hơn trang trí; đủ trạng thái loading / rỗng / thành công / lỗi; chỉ vẽ chức năng có trong yêu cầu; điều chưa rõ thì hỏi |
| **Design system** | `project/` | デジタル庁デザインシステム (DADS) v2.18.0: token màu / chữ / bo góc / bóng / lưới, 46 component (React, `window.DADS`), giọng văn UI tiếng Nhật. Copy từ artifact https://claude.ai/artifact/WCjMDsToWAsjADJBWjHQwe ngày 20/10/2026 |

`project/` đúng format Artifact type "Design System" — cùng chuẩn với `ba-kit/system-to-doc/.claude/sys-agent/design-system/design-system-format.md`.

## Cây thư mục

```
base-design-system/
├── README.md                    ← file này (cách dùng — không publish)
├── STATUS.md                    ← trạng thái, nguồn, phần thiếu (TBD), changelog
├── prompt_design_system.md      ← nguyên tắc thiết kế (tiếng Nhật)
├── tools/add-company-layer.py   ← thêm lớp tên chuẩn công ty lên DADS (chạy lại được)
└── project/                     ← DADS + lớp chuẩn công ty
    ├── design-system.json · tokens.json · README.md (brand book DADS, tiếng Anh)
    └── components/<Comp>/README.md + preview.html · bundle.js · bundle.css · index.d.ts · lib/ (React 18.3.1)
```

## Lớp tên chuẩn công ty

DADS dùng tên gốc (`key-900`, `solid-gray-800`, `Std-16N-170`, `InputText`). Các kit bind theo **tên vai trò** của chuẩn công ty (D1–D7). `tools/add-company-layer.py` thêm vào `project/` (không xoá tên gốc):

| Thêm gì | Ví dụ | Nhận biết |
|---|---|---|
| Token vai trò = alias tới token DADS | `primary` = `{key-900}` · `text-high` = `{solid-gray-800}` · `negative-500` = `{error-1}` · `radius-md` = `{radius-8}` · `shadow-popout` = `{elevation-3}` | `usage` mở đầu `[Vai trò chuẩn]` + tên DADS gốc |
| `spacing` / `size` đọc từ README / CSS DADS | `control-md` 48px · `modal-width` 480px · `viewport-web` 1280px · `content-max` 1120px | giá trị suy ra ghi rõ cách tính trong `usage` |
| Type group `Heading` / `Text` | `text-16` = `Std-16N-170` · `heading-20-bold` = `Std-20B-150` | |
| Component tên chuẩn = alias DADS | `TextField` = `InputText` · `Select` = `SelectBox` · `Badge` = `ChipLabel` · `Modal` = `ModalDialog` · `Pagination` = `PageNavigation` · `PageHeader` = `Heading` · `AppHeader` = `HeaderContainer` · `InlineMessage` = `NoticeBlock` | folder `components/<Tên chuẩn>/`, khối `company-layer` cuối `bundle.js` / `index.d.ts` |

Không có giá trị trong nguồn → **không thêm**, ghi ở `STATUS.md` § Thiếu (TBD) (`Toast`, `AppShell`, `SideNav` / `TabBar`, `sidebar-width`).

Cập nhật DADS từ artifact: tải lại `project/` → chạy `python3 tools/add-company-layer.py project` → script in phần còn thiếu và tự kiểm alias.

**Bản copy trong kit** (folder này gitignored, kit copy nguyên sang dự án khác): `ba-kit/requirement-to-flow/.claude/base-design-system/`, `ba-kit/system-to-doc/.claude/base-design-system/` và `designer-kit/document-to-figma/.claude/base-design-system/` — gồm `project/`, `STATUS.md`, `prompt_design_system.md`, `README.md` (thêm dòng `SOURCE:` đầu file), không gồm `tools/`. Sửa ở đây rồi copy lại **cả 3 kit**; `python3 ba-kit/system-to-doc/.claude/skills/system-analyst/scripts/selftest-design-system.py` FAIL khi 3 bản lệch nhau.

## Dùng ở đâu

| Kit / bước | Dùng thế nào |
|---|---|
| **requirement-to-flow — Output 3** (mockup màn đề xuất) | Mockup dựng từ token + component của `project/` theo nguyên tắc `prompt_design_system.md`. Chi tiết: `ba-kit/requirement-to-flow/.claude/ba-agent/figma-outputs/output-3-screens.md` § Design system |
| **system-to-doc — O4** (design system của hệ thống đã có) | Base = **khung chuẩn Nhật**: tên vai trò, thang chữ, trạng thái, giọng văn UI, danh mục component. Giá trị **quan sát được** từ hệ thống luôn thắng; token không quan sát được lấy từ base, đánh dấu "lấy từ base — chờ xác nhận". Chi tiết: `ba-kit/system-to-doc/.claude/sys-agent/outputs/o4-design-system.md` § 3b |
| **designer-kit / document-to-figma — G1** (design system cho màn Hi-Fi) | Dự án **chưa có** design system → user chọn "Dùng Base Design System" ở câu DS-1 → copy base làm `design-system/` của dự án (tạm, chờ duyệt). Dự án **có** nguồn (Figma / tài liệu / màn mẫu / codebase) → dựng theo khung tên + luật chuẩn Nhật của base, phần nguồn thiếu bù từ base có nhãn `[base]` (câu DS-2). Chi tiết: `designer-kit/document-to-figma/.claude/designer-agent/design-system-intake.md` §2.6 |
| **system-to-doc — CR-3** (màn đề xuất cho CR) | Dùng DS của baseline (O4). **Baseline không có DS** (hệ thống không cung cấp UI) → copy base làm DS tạm `04_DesignSystem/<WEB-xx>/` của version CR. Chi tiết: `ba-kit/system-to-doc/.claude/sys-agent/figma/cr-view.md` § Không có Design System |

Luật chung khi vẽ màn bằng base:
- Chỉ dùng token / component có trong `project/`. Thiếu thứ cần dùng → hỏi, không tự chế màu / component.
- Chữ UI theo `project/README.md` § Content fundamentals: tiếng Nhật lịch sự (です・ます), nhãn nút là cụm động từ ngắn, 「※必須」/「※任意」, lỗi 「＊…を入力してください。」 dưới ô, ngày 「2026年10月11日」, không emoji / dấu chấm than.
- Focus ring: viền đen 4px + dải `yellow-300` 2px. Trạng thái màu luôn đi kèm icon hoặc chữ.
- Theme `light` (デジタル庁, xanh) là mặc định. Theme `market` (đỏ, dày hơn) chỉ dùng khi yêu cầu nói rõ là trang thương mại.
- Dữ liệu mẫu theo `rules/DATA-PRIVACY.md` của kit, không dùng dữ liệu thật.
