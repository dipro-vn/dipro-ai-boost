# PROMPT TẠO DASHBOARD 

Luôn tạo **01 ảnh dashboard infographic hiện đại** theo phong cách quản lý dự án chuyên nghiệp.

## Quy tắc chung

- Ngôn ngữ: **Tiếng Việt**
- Tỷ lệ ảnh: **16:9**
- Phong cách: **Executive Dashboard / PMO Report**
- Màu sắc:
  - Xanh dương: KPI chính
  - Xanh lá: Hoàn thành
  - Cam: Kế hoạch
  - Đỏ: Cảnh báo
  - Tím: Thống kê nhân sự
- Font hiện đại, dễ đọc.
- Có icon cho từng KPI.
- Các khối có bo góc, đổ bóng nhẹ.
- Hiển thị logo text: 
- Header hiển thị:
  - Tên sprint
  - Ngày báo cáo
  - Thời gian sprint

---

## Bố cục dashboard

### Hàng KPI trên cùng

Hiển thị:

- Tổng task
- Tổng nhân sự
- Còn lại (Actual)
- Kế hoạch còn lại (Plan)
- Gap vs Plan
- Đã hoàn thành
- Tỷ lệ hoàn thành

### Công thức

```text
Total Members = số assignee có trong bảng

Current Remaining = giá trị ACTUAL mới nhất

Planned Remaining = giá trị PLAN cùng ngày

Gap = Actual - Plan

Completed = Current Scope - Current Remaining

Completion Rate = Completed / Current Scope × 100%
```

---

### Khối 1 — Task theo Assignee

Biểu đồ cột dọc nhiều màu.

Yêu cầu:

- Sắp xếp giảm dần theo TOTAL
- Hiển thị số task trên đầu cột
- Hiển thị Top 3 nổi bật

---

### Khối 2 — Burn Down

Vẽ biểu đồ đường:

- PLAN: màu đỏ nét đứt
- ACTUAL: màu xanh

Quy tắc:

- Chỉ vẽ ACTUAL đến ngày hiện tại có dữ liệu
- Không nối ACTUAL cho các ngày tương lai
- Luôn vẽ toàn bộ PLAN

---

### Khối 3 — Burn Up

Vẽ biểu đồ đường:

- TOTAL: màu xanh lá
- COMPLETED: màu xanh dương

Quy tắc:

- Chỉ vẽ COMPLETED đến ngày hiện tại có dữ liệu
- Không vẽ dữ liệu tương lai
- Luôn vẽ TOTAL đầy đủ

Nếu không cung cấp COMPLETED:

```text
COMPLETED = TOTAL - ACTUAL
```

---

### Khối 4 — Sprint Summary

Hiển thị:

- Sprint Scope ban đầu
- Current Scope
- Current Remaining
- Completed
- Completion Rate
- Gap vs Plan

---

### Khối 5 — Phân bố theo Role

Tự động map theo dữ liệu 

```text
BrsE:
- Dao Thu Hong

PM:
- TRAN DUC LONG

Designer:


BE:


FE:


MOBILE:


QC:

INFRA:

```

Hiển thị:

- Donut chart
- Số task theo role
- Tỷ lệ %

---

### Khối 6 — Task Overdue

Nếu có dữ liệu task trễ:

Gộp theo:

```text
Assignee → Số lượng task trễ
```

Hiển thị bảng:

| Assignee | Overdue |
|-----------|---------:|

Sắp xếp giảm dần.

KPI:

- Total Overdue Tasks
- Affected Members
- Highest Risk Owner

Nếu không có dữ liệu:

```text
Không hiển thị khối này.
```

---

### Footer

Hiển thị:

- Tổng số thành viên tham gia sprint
- Ngày kết thúc sprint
- Nhận xét tự động

Ví dụ:

```text
Tiến độ đang chậm hơn kế hoạch 4 task.

Cần tập trung xử lý các task còn lại để đảm bảo mục tiêu sprint.
```

Hoặc:

```text
Sprint đang đi đúng kế hoạch.

Tiếp tục duy trì tiến độ hiện tại.
```

---

## Dữ liệu đầu vào

Tôi sẽ dán dữ liệu theo format:

```text
Thống kê task

Assignee	TOTAL
...

BURN DOWN
ACTUAL
PLAN

BURN UP
TOTAL
COMPLETED

Danh sách task overdue
...
```

Bạn phải:

- Tự động phân tích dữ liệu
- Tính toán KPI
- Tự động nhóm role
- Tự động nhóm overdue
- Tự động tạo dashboard dạng ảnh màu sắc
- Không hỏi lại
- Không trả về bảng markdown
- Chỉ xuất ra hình ảnh dashboard hoàn chỉnh

---

## Quy tắc đặc biệt

- Nếu ngày chưa xảy ra thì không vẽ ACTUAL và COMPLETED.
- Nếu TOTAL thay đổi giữa sprint thì Burn Up phải phản ánh thay đổi scope.
- Cho phép COMPLETED âm ở ngày đầu tiên nếu backlog tăng thêm.
- Luôn ưu tiên khả năng đọc khi số lượng nhân sự nhiều.
- Tên người dài phải tự động xuống dòng hoặc rút gọn hợp lý.
- Dashboard phải giống phong cách PMO/Executive Report.
