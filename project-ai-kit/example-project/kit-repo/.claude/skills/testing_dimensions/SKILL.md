---
name: Testing Dimensions
description: Checklist testing theo platform — dùng kết hợp với rbt_manual_testing. AI xác định platform rồi áp thêm các dimension tương ứng vào bộ TCs đang sinh.
---

# Testing Dimensions

## Cách dùng

Skill này **không dùng độc lập** — dùng kết hợp với `rbt_manual_testing`.

Trước khi sinh TCs, AI phải hỏi:

```
1. Feature này chạy trên platform nào? (Web / Mobile / Desktop / Nhiều platform?)
2. App có hỗ trợ multi-language không?
3. Có tính năng đặc thù nào không? (push notification, offline mode, v.v.)
```

Sau đó áp các section tương ứng bên dưới như **lớp bổ sung** lên bộ TCs từ base skill.

---

## Web Platform

### Browser Behavior

| Scenario | Cần verify |
|----------|-----------|
| Refresh (F5) | State trang được preserve hay reset theo đúng business rule? |
| Hard refresh (Ctrl+Shift+R) | Cache xóa, data load lại đúng? |
| Multi-tab | Mở cùng trang ở 2 tab: action ở tab 1 có reflect sang tab 2 không? |
| Back/Forward button | State restore đúng? Không bị lỗi hoặc mất data? |
| Bookmark/copy URL | Truy cập trực tiếp qua URL: đúng trang, đúng state? |
| F5 trên Create/Edit page | Refresh có confirm discard unsaved changes? Không mất data âm thầm |
| F5 trên Management/List page | Data reload từ server, không dùng stale cache |
| F5 trên Confirmation popup | Popup đóng hay resubmit? Không tạo duplicate request |
| Browser Back sau submit | Không resubmit form — không tạo duplicate record |

### Session & Cookie

| Scenario | Cần verify |
|----------|-----------|
| Cookie hết hạn | Redirect về login, không blank screen |
| Session timeout | Thông báo rõ ràng, không mất data đang nhập |
| Multi-tab khác user | Đăng nhập account khác ở tab khác: không conflict session |

### Responsive & Layout

| Scenario | Cần verify |
|----------|-----------|
| Zoom 125%, 150% | Layout không vỡ, text không bị cắt |
| Resize cửa sổ trình duyệt | Breakpoints hoạt động đúng |
| Độ phân giải tối thiểu hỗ trợ | Không bị scroll ngang ngoài ý muốn |

### Cross-Browser

Test trên: **Chrome, Safari, Firefox, Edge**

- Layout nhất quán không?
- Chức năng hoạt động đúng trên tất cả browser?
- Console không có lỗi JS nghiêm trọng?

---

## Mobile Platform

### Cài đặt ứng dụng

| Scenario | Cần verify |
|----------|-----------|
| Fresh install | App hoạt động đúng, không cần data migration |
| Uninstall | Data local bị xóa hoàn toàn (không để lại PII) |
| Reinstall / Update | Data migration đúng; setting cũ còn hay reset theo spec |

### App Lifecycle

| Scenario | Cần verify |
|----------|-----------|
| Background → Foreground | State app được preserve đúng? Session còn hay hết? |
| Force-close → Reopen | Data chưa submit có mất không? Session xử lý thế nào? |
| Kill app (swipe away) | Data đang nhập dở có recover khi reopen? Không corrupt local state |
| Nghe điện thoại trong khi dùng app | Quay lại app sau cuộc gọi: state ok? |
| Cảnh báo pin yếu | Popup hệ thống không làm crash hay mất state app |

### Quyền truy cập (Permissions)

| Permission | Cần verify |
|-----------|-----------|
| Camera | Allow vs Deny: tính năng liên quan hoạt động / graceful fallback |
| Gallery / Photos | Allow vs Deny |
| Location | Allow / Allow while using / Deny: từng case xử lý đúng? |
| Notifications | Allow vs Deny |
| Thu hồi quyền trong Settings | App xử lý graceful, không crash |

### Xoay màn hình

| Scenario | Cần verify |
|----------|-----------|
| Portrait → Landscape | Layout adapts, state không mất |
| Landscape → Portrait | Tương tự |
| Khóa xoay màn hình | Tính năng vẫn dùng được bình thường |

### Network

| Scenario | Cần verify |
|----------|-----------|
| Offline hoàn toàn | Error state rõ ràng, không crash, không vòng lặp retry vô hạn |
| Chuyển WiFi → 4G | Session giữ hay mất? Action đang chạy dở xử lý thế nào? |
| Mạng chậm (3G) | Loading indicator hiển thị? Timeout có giới hạn? |
| Airplane mode | App switch sang Airplane mode: graceful degradation, không crash |
| Khôi phục mạng | Auto-retry hay cần user refresh? |

### Gestures & Input

| Scenario | Cần verify |
|----------|-----------|
| Swipe | Swipe action đúng hướng, không trigger nhầm gesture khác |
| Pinch-zoom | Zoom in/out trên màn hình cho phép; không zoom màn hình không hỗ trợ |
| Long-press | Context menu hoặc action đúng theo spec |
| Multi-touch | Hai ngón tay cùng lúc không gây unexpected behavior |

### Push Notification

| Scenario | Cần verify |
|----------|-----------|
| App đang mở (foreground) | Hiển thị in-app notification hay toast? |
| App đang chạy nền (background) | Notification xuất hiện ở system tray? |
| App đã bị tắt (killed) | Vẫn nhận được notification? |
| Tap vào notification | Deep-link đúng màn hình liên quan? |
| Nhiều notification | Badge count đúng số? |
| Cùng account trên nhiều thiết bị | Notification gửi đến tất cả hay chỉ device đang active? |
| Notification bị trễ | Nội dung vẫn đúng sau khi tới muộn? |
| Notification trùng lặp | Không hiện 2 lần cho cùng 1 event? |

---

## Desktop Platform

### Keyboard Navigation

| Phím | Cần verify |
|------|-----------|
| Tab | Focus đi qua đúng thứ tự tất cả element tương tác |
| Shift+Tab | Reverse order đúng |
| Enter / Space | Kích hoạt button, checkbox đang focus |
| Escape | Đóng modal, dropdown, dialog |
| Arrow keys | Di chuyển trong dropdown, list, datepicker |

### Keyboard Shortcuts

- Liệt kê và test tất cả shortcut đã khai báo (Ctrl+S, Ctrl+Z, v.v.)
- Shortcut có conflict với OS shortcut không?
- Shortcut có hoạt động khi focus đang trong text field?
- Shortcut nhiều phím (Ctrl+Shift+...) có trigger đúng?

### Mouse / Pointer

| Scenario | Cần verify |
|----------|-----------|
| Hover | Tooltip, button state, cursor changes hiển thị đúng? |
| Right-click | Context menu hiện đúng options cho element đó? |
| Double-click vs Single-click | Behavior phân biệt rõ, không trigger nhầm? |

### Window & OS

| Scenario | Cần verify |
|----------|-----------|
| Resize cửa sổ | Layout adapts, có min-size hợp lý |
| Maximize / Restore | Layout đúng ở cả 2 state |
| Nhiều màn hình | Window drag sang màn hình 2 không bị lỗi render |
| OS Dark mode | UI đọc được, không bị chữ trắng trên nền trắng |
| Copy/Paste từ clipboard hệ thống | Paste vào field app hoạt động đúng |

---

## Batch Platform

*(Áp dụng cho tính năng batch processing: scheduled jobs, import/export hàng loạt, data migration)*

### Execution

| Scenario | Cần verify |
|----------|-----------|
| Scheduled trigger | Batch chạy đúng giờ theo lịch config |
| Manual trigger | Trigger thủ công hoạt động đúng, không conflict với scheduled run |
| Concurrent execution | 2 batch cùng loại không chạy song song (lock mechanism hoạt động) |

### Validation & Error Handling

| Scenario | Cần verify |
|----------|-----------|
| Record lỗi — dừng toàn bộ | Nếu spec "all-or-nothing": 1 lỗi → rollback toàn bộ, không partial update |
| Record lỗi — tiếp tục | Nếu spec "best-effort": skip record lỗi, xử lý records còn lại |
| Output log | Log ghi đủ: timestamp, số record xử lý, số record lỗi, chi tiết lỗi từng record |
| Notification khi hoàn thành | Email / alert gửi đúng recipient với kết quả tóm tắt (nếu có) |

### Data Integrity

| Scenario | Cần verify |
|----------|-----------|
| DB update đúng | Records được cập nhật chính xác sau batch success |
| Rollback khi fail | Batch fail giữa chừng → data về trạng thái trước khi chạy |
| Idempotency | Chạy lại batch cùng input → không tạo duplicate records |

### Output

| Scenario | Cần verify |
|----------|-----------|
| File output location | File lưu đúng thư mục / storage bucket theo config |
| File format | Format (CSV, Excel, PDF...) và encoding đúng spec |
| File naming | Tên file đúng convention (VD: `batch_result_YYYYMMDD_HHMMSS.csv`) |

---

## Cross-Platform

*(Áp dụng cho mọi platform khi relevant)*

### UI & Message Handling

| Loại | Cần verify |
|------|-----------|
| Toast / Snackbar | Xuất hiện sau action, tự dismiss sau X giây, không duplicate |
| Inline validation | Hiện đúng vị trí field lỗi, biến mất khi sửa đúng |
| Modal / Dialog | Chặn interaction bên dưới, đóng được, focus trap bên trong |
| Loading state | Spinner / skeleton hiện trong khi chờ async |
| Empty state | Message rõ ràng khi không có data, không blank |
| Error state | Message rõ + action recovery (Retry, Go back) |
| Status indicator (badge, chip, tag) | Đúng màu / label theo từng state |

### Security

| Scenario | Cần verify |
|----------|-----------|
| Token hết hạn | Redirect về login, không blank screen, không crash |
| Truy cập URL trực tiếp khi chưa có quyền | 403 hoặc redirect, không lộ data |
| Role-based UI | Feature bị ẩn/disable đúng với role không có quyền |
| Action nhạy cảm | Yêu cầu xác nhận lại mật khẩu / 2FA nếu có? |
| SQL Injection | Nhập `' OR '1'='1`, `'; DROP TABLE--`, `1; SELECT *` vào textbox/search → blocked, không execute, không expose DB error |
| XSS | Nhập `<script>alert(1)</script>`, `<img src=x onerror=alert(1)>` vào input → escaped khi display, không execute trong browser |
| CSRF | Request không có valid CSRF token → rejected với 403; không thể trigger action từ external site |

### API Layer

| Scenario | Cần verify |
|----------|-----------|
| Success (2xx) | UI phản ánh đúng data trả về |
| Client error (4xx) | Thông báo thân thiện, không hiện raw error |
| Server error (5xx) | Không crash, hiện error state + recovery action |
| Timeout | Request treo quá lâu → timeout message sau X giây |
| Retry | Request fail có retry tự động hay cần user trigger? |
| Rapid action | Submit nhiều lần liên tiếp nhanh → không duplicate request |

### Database Integrity

| Scenario | Cần verify |
|----------|-----------|
| Submit trùng lặp | Blocked hoặc merged, không tạo duplicate record |
| Soft delete | Record xóa không hiện trong UI, nhưng còn trong DB nếu cần recover |
| Partial failure | Multi-step operation fail giữa chừng → không để data ở trạng thái không nhất quán |
| Refresh sau submit | Data đã persist vào DB, không chỉ update in-memory |

### Multi-Language

| Scenario | Cần verify |
|----------|-----------|
| Switch language | Toàn bộ UI text cập nhật, không sót hardcode |
| Thiếu translation key | Fallback hiển thị gì? (key thô hay ngôn ngữ mặc định?) |
| Ký tự đặc biệt | CJK, dấu tiếng Việt, RTL (Arabic) hiển thị đúng? |
| Format locale | Ngày/giờ, số, tiền tệ đúng theo ngôn ngữ? |
| Text overflow | Bản dịch dài hơn (Đức, Nhật) có làm vỡ layout? |

### Non-functional

*(Kiểm tra mức độ cơ bản — test chuyên sâu cần tool riêng)*

| Scenario | Threshold gợi ý |
|----------|----------------|
| Thời gian load trang chính | < 3 giây trên mạng bình thường |
| Action thông thường (submit, search) | < 2 giây |
| List/table với 1000+ records | Pagination/scroll/search vẫn mượt |
| Session dài (30+ phút) | Không bị chậm dần hoặc crash |
| Crash giữa chừng | Reopen app: data state nhất quán, không corrupt |
