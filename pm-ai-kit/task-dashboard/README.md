# Task Dashboard (Burndown / Burnup)

Prompt AI tạo **1 ảnh dashboard infographic** phong cách PMO/Executive Report từ dữ liệu task của sprint — bao gồm Burndown, Burnup, phân bổ theo assignee/role, overdue.

Dùng **GPT free** (hoặc bất kỳ model nào có khả năng tạo ảnh) — không cần API key.

## Khi nào dùng

- Cần visual nhanh để gửi trong daily/weekly sync.
- Không muốn tự vẽ Burndown/Burnup bằng Excel.
- Có sẵn dữ liệu task theo assignee + số liệu Plan/Actual theo ngày.

## Cần chuẩn bị

- Dữ liệu task tổng hợp (Assignee → TOTAL task).
- Dữ liệu BURN DOWN theo ngày (PLAN & ACTUAL).
- Dữ liệu BURN UP theo ngày (TOTAL & COMPLETED — tùy chọn).
- Danh sách task overdue (tùy chọn).

Template dữ liệu đầu vào: xem `AI_Source/Nguon Daily Report bang hinh anh/Monitor template.xlsx`.

## Cách dùng

1. Mở ChatGPT (hoặc model bất kỳ hỗ trợ tạo ảnh).
2. Copy toàn bộ `prompt_task_dashboard.md` → paste.
3. Paste dữ liệu theo format ở cuối prompt (Assignee, BURN DOWN, BURN UP, Overdue).
4. Model xuất ra ảnh dashboard hoàn chỉnh (16:9, tiếng Việt, phong cách PMO).

## Output

1 ảnh dashboard gồm:
- Hàng KPI tổng (Total task, Members, Remaining Actual/Plan, Gap, Completed, Completion Rate).
- Khối task theo Assignee (bar chart).
- Burndown chart (Plan đỏ nét đứt, Actual xanh).
- Burnup chart (Total xanh lá, Completed xanh dương).
- Sprint Summary.
- Phân bố theo Role (donut).
- Bảng task Overdue (nếu có).
- Footer nhận xét tự động.

## Nguồn tham khảo

- Prompt gốc: `prompt_task_dashboard.md`
- Template dữ liệu: `AI_Source/Nguon Daily Report bang hinh anh/Monitor template.xlsx`
- Ảnh ví dụ: `AI_Source/Nguon Daily Report bang hinh anh/example.png`

## Lưu ý

- Trước khi dùng cho dự án khác **ESKITCHEN**, sửa lại phần **Khối 5 — Phân bố theo Role** trong prompt để map đúng thành viên dự án của bạn.
- Không cần backend/API — chạy hoàn toàn qua chat model có tạo ảnh.
