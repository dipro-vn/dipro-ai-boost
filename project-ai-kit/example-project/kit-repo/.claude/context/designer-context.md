# Designer Context — \<PROJECT_NAME\>

> Context bắt buộc cho `designer-agent` mỗi lần chạy. Tổng hợp UI components, theme, naming conventions từ source code thực tế của các repo frontend/mobile.
> **File này rỗng trong kit gốc** — `designer-agent` (hoặc BA/Tech Lead lần đầu setup) cần **auto-extract từ source code** của dự án rồi điền vào đây trước khi Designer có thể reuse component thay vì vẽ lại từ đầu.

---

## 1. Tech Stack — Map per repo

_(điền theo bảng Ecosystem trong `AGENTS.md`, bổ sung UI stack chi tiết hơn: version AntD/shadcn/component lib, icon set, form lib...)_

| Repo | UI Stack | Trạng thái |
|---|---|---|
| _(tên repo)_ | _(vd: React 19 · AntD v6 · TanStack Query v5 · RTK v2 · TailwindCSS v4)_ | |

> ⚠️ Nếu có repo dùng UI library khác biệt hẳn (vd 1 repo dùng shadcn/ui thay vì AntD trong khi các repo khác dùng AntD) — ghi rõ cảnh báo ở đây để Designer không áp nhầm component style.

---

## 2. Color Theme thực tế per repo

_(điền màu primary thật đọc từ code/theme config của từng repo — có thể lệch với `rules/design_rule.md` nếu code chưa migrate theo token mới, ghi chú rõ)_

| Repo | Primary color (code) | Mapping token (nếu có) | Note |
|---|---|---|---|

---

## 3. Shared Components — Library catalog

_(liệt kê component dùng chung đã có sẵn trong codebase — Designer PHẢI reuse, không vẽ lại. Extract bằng cách đọc thư mục `src/components/` hoặc tương đương của từng repo)_

| Component | Folder | Variants / Props chính | Có ở repo nào |
|---|---|---|---|

---

## Cách cập nhật file này

1. Đọc `src/components/**` (hoặc thư mục UI component chung) của từng repo frontend/mobile
2. Đọc theme config (`tailwind.config`, theme provider, design token file...) để lấy màu primary thật
3. Điền lại 3 bảng trên
4. Cập nhật dòng "Updated: \<ngày\>" ở đầu file khi có thay đổi lớn về UI stack
</content>
