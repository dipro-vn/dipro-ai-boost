# Understand-Anything

> Nguồn: https://github.com/Egonex-AI/Understand-Anything · Cài đặt: xem `guideline/step1-install-source-map.md`.

Trong các repo đã cài Understand-Anything (tồn tại thư mục `.understand-anything/` ở root repo), dùng công cụ này TRƯỚC khi grep/find thủ công để tìm hiểu hoặc định vị code — đây là lựa chọn thay thế cho [CodeGraph](codegraph.md), phù hợp với dự án legacy/thiếu tài liệu.

Nếu không có thư mục `.understand-anything/`, bỏ qua công cụ này hoàn toàn — việc cài đặt do người dùng quyết định.

## Lệnh chính

- `/understand-chat [câu hỏi]` — hỏi đáp trực tiếp về codebase, dùng thay cho việc đọc nhiều file thủ công.
- `/understand-explain [file/function]` — giải thích chi tiết 1 file hoặc 1 function cụ thể.
- `/understand-dashboard` — xem tổng quan knowledge graph của dự án.
- `/understand-diff` — xem các thay đổi so với lần phân tích trước.
- `/understand-domain` — xem phân tích theo domain nghiệp vụ.
- `/understand src/frontend` — chỉ phân tích lại 1 phần cụ thể của repo (ví dụ 1 thư mục).

## Đồng bộ sau khi code (bắt buộc theo bước 6 của Workflow)

- `/understand` — chạy lại, mặc định incremental (chỉ phân tích lại các file đã thay đổi).
- `/understand --auto-update` — bật post-commit hook để tự động patch graph sau mỗi commit (chỉ bật nếu người dùng yêu cầu, không tự ý bật).

## Ghi chú

- Output nằm trong `.understand-anything/` (gồm `knowledge-graph.json`, `config.json`) — không commit `intermediate/` và `diff-overlay.json` (scratch/local-only).
- Nếu dự án cần output đa ngôn ngữ, dùng `--language <mã>` (`en`, `zh`, `zh-TW`, `ja`, `ko`, `ru`), ví dụ `/understand --language ja`.
