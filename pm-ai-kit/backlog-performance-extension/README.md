# Backlog Performance Extension

**Chrome extension** để quản lý performance dự án trực tiếp trên giao diện Backlog:
Theo Tuần / Tháng → Hiệu suất Nhân viên / Hiệu suất Sprint.

Hỗ trợ PM và các bộ phận cần lấy số liệu nhanh từ Backlog mà không cần chạy script.

## Khi nào dùng

- Cần xem nhanh hiệu suất member trên chính trang Backlog, không cần export Excel.
- Cần số liệu Sprint để họp retrospective ngay lập tức.
- Đối chiếu nhanh vs báo cáo từ [`performance-report`](../performance-report/) (chạy Python).

## Version

**v1.0** — nguồn từ Backlog API, render trực tiếp trên browser.

## Cài đặt & sử dụng

Xem tài liệu chi tiết: `AI_Source/HDSD_Backlog_Performance_Extension.docx`
(hoặc liên hệ team AI để nhận file `.crx` / hướng dẫn cài Chrome extension từ source).

## Quan hệ với các tool khác trong kit

| Tool | Vai trò |
|---|---|
| **Backlog Performance Extension** (đây) | Xem nhanh trên UI Backlog |
| [`performance-report`](../performance-report/) | Xuất Excel chi tiết (5 sheets) qua Claude Code |

Hai tool dùng cùng nguồn Backlog API — số liệu phải khớp nhau. Nếu lệch → kiểm tra config allocation, filter status, hoặc project scope.
