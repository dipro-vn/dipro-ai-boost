# SPEC: In-App VoIP Call

## Mô tả nghiệp vụ

Dipro Admin (quản lý admin site) cần gọi điện trực tiếp cho Company Admin trong app để trao đổi về đơn hàng mà không cần rời khỏi ứng dụng. Cuộc gọi là **1 chiều**: Dipro Admin khởi tạo — Company Admin nhận. Lịch sử cuộc gọi được lưu 3 tháng.

---

## Actors & Preconditions

| Actor | Role | Preconditions |
|---|---|---|
| Dipro Admin | Khởi tạo cuộc gọi | Đã đăng nhập, có quyền admin, có ít nhất 1 Company được assign |
| Company Admin | Nhận cuộc gọi | Đã đăng nhập, app đang chạy hoặc push notification enabled |

**Preconditions chung:**
- Cả 2 phía đã có tài khoản trong hệ thống
- Kết nối internet ổn định (Wi-Fi hoặc 4G+)
- Microphone permission đã được cấp trên thiết bị

---

## Flow Tổng Quan

```
Dipro Admin → Mở App → Company List → Tap Company → Company Detail
                                                           ↓ Tap "Gọi"
                                                     Outgoing Call Screen
                                                           ↓ [Ringing]
                                     Company Admin ← Incoming Call (push / overlay)
                                                           ↓ [Accept]
                                                     In-Call Screen (cả 2 bên)
                                                           ↓ [Hang up — either side]
                                                     Call Ended Summary → Call History

[Timeout / Reject]:
Outgoing Call Screen → [No answer 30s / Rejected] → Toast → Company Detail

[Mất mạng trong cuộc gọi]:
In-Call Screen → [Network lost] → Toast "Kết nối bị gián đoạn" → Call Ended Summary
```

---

## Happy Path

1. Dipro Admin mở app, vào **Company List**
2. Tìm / chọn company muốn gọi
3. Vào **Company Detail**, tap nút **"Gọi ngay"**
4. App hiển thị **Outgoing Call Screen** — ringing, hiện tên/avatar company
5. Company Admin nhận **push notification** (app background) hoặc **in-app overlay** (app foreground)
6. Company Admin tap **"Chấp nhận"**
7. Cả 2 bên vào **In-Call Screen** — mute / speaker / hang up
8. 1 trong 2 bên tap **"Kết thúc"** → cuộc gọi đóng
9. **Call Ended Summary** hiển thị (tên, thời lượng, timestamp, trạng thái)
10. Cuộc gọi lưu vào **Call History**

---

## Alternative Flows & Edge Cases

| Case | Trigger | Xử lý |
|---|---|---|
| Không trả lời | Sau 30 giây ringing | Tự động ngắt, toast "Không có phản hồi", log "Missed" |
| Từ chối | Company Admin tap "Từ chối" | Ngắt ngay, toast "Cuộc gọi bị từ chối", log "Declined" |
| Mất mạng trong cuộc gọi | Network drop | Toast "Kết nối bị gián đoạn", kết thúc call, log "Disconnected" |
| Company Admin đang bận | Đang trong cuộc gọi khác | Toast "Đang bận" cho Dipro Admin, không gọi được |
| Microphone bị từ chối | Permission denied | Modal yêu cầu cấp quyền + link vào Settings |
| App bị kill trong khi gọi | Force close | Cuộc gọi kết thúc, log "Disconnected" |

---

## Acceptance Criteria

- [ ] Dipro Admin khởi tạo cuộc gọi VoIP đến bất kỳ Company Admin nào trong danh sách
- [ ] Company Admin nhận push notification khi app background, in-app overlay khi foreground
- [ ] Cuộc gọi kết nối thành công trong ≤ 3 giây sau khi Company Admin chấp nhận
- [ ] Dipro Admin có thể mute microphone và bật loa ngoài trong cuộc gọi
- [ ] Cuộc gọi tự động kết thúc sau 30 giây không có người nhận
- [ ] Tất cả cuộc gọi (Completed / Missed / Declined / Disconnected) được lưu vào Call History
- [ ] Call History hiển thị tối thiểu 3 tháng dữ liệu
- [ ] Chất lượng âm thanh đảm bảo nghe rõ trên kết nối 4G

---

## Out of Scope (v1)

- Company Admin gọi ngược lại Dipro Admin
- Conference call (> 2 người)
- Video call
- Ghi âm cuộc gọi
- Multitasking VoIP (gọi trong khi dùng app khác)
- Lịch sử cuộc gọi quá 3 tháng
- Web version của tính năng gọi

---

## Screens

> Tổng: **8 màn hình** (5 Dipro Admin · 3 Company Admin)

| Screen Code | Screen | Actor | App | Screen Type | Transition To |
|---|---|---|---|---|---|
| DA_VOIP_001 | Company List | Dipro Admin | DA* | List | → DA_VOIP_002 (tap company) |
| DA_VOIP_002 | Company Detail | Dipro Admin | DA* | Detail | → DA_VOIP_003 (tap "Gọi") |
| DA_VOIP_003 | Outgoing Call | Dipro Admin | DA* | Modal | [Accept] → DA_VOIP_004 / [No answer/Reject] → DA_VOIP_002 + toast |
| DA_VOIP_004 | In-Call (Caller) | Dipro Admin | DA* | Modal | → DA_VOIP_005 (hang up) |
| DA_VOIP_005 | Call Ended Summary | Dipro Admin | DA* | Modal | → DA_VOIP_002 / → DA_VOIP_006 |
| DA_VOIP_006 | Call History | Dipro Admin | DA* | List | — |
| CA_VOIP_001 | Incoming Call | Company Admin | CA* | Modal | [Accept] → CA_VOIP_002 / [Decline] → dismiss |
| CA_VOIP_002 | In-Call (Receiver) | Company Admin | CA* | Modal | → dismiss (hang up) |

> *Epic code chưa được xác định — cần điền qua `/init-kit` khi dự án được khởi tạo.

---

## Screen Details

### DA_VOIP_001 — Company List

**Happy Case:**
- Layout: Full-screen list, search bar ở top, FAB lịch sử gọi bottom-right
- Components:

  | Vị trí | Component | Nội dung | Action |
  |---|---|---|---|
  | Top | Search bar | "Tìm công ty..." | Filter list real-time |
  | Body | List item | Avatar + Tên company + Online status dot (xanh/xám) | Tap → DA_VOIP_002 |
  | Body | Sub-text | Lần gọi gần nhất (timestamp, nếu có) | — |
  | Bottom-right | FAB | Icon lịch sử | Tap → DA_VOIP_006 |

- Interactions: Pull-to-refresh / Infinite scroll
- Animation đề xuất: Skeleton loader khi load danh sách

**Non-Happy Case:**

| Trigger | Hiển thị | Message |
|---|---|---|
| Danh sách rỗng | Empty state illustration | "Chưa có công ty nào được assign" |
| Lỗi load | Error banner + Retry button | "Không thể tải danh sách. Thử lại." |
| Mất mạng | Banner sticky | "Không có kết nối mạng" |

---

### DA_VOIP_002 — Company Detail

**Happy Case:**
- Layout: Header lớn (avatar + tên + status) → Info section → Recent calls → Sticky CTA bottom
- Components:

  | Vị trí | Component | Nội dung | Action |
  |---|---|---|---|
  | Header | Avatar large | Logo / ảnh đại diện company | — |
  | Header | Status badge | Online / Offline / Busy | — |
  | Body | Info rows | Tên, địa chỉ, số đơn hàng active | — |
  | Body | Recent calls | 3 cuộc gọi gần nhất (thu gọn) | Tap "Xem tất cả" → DA_VOIP_006 |
  | Bottom sticky | Button primary | "Gọi ngay" | Tap → DA_VOIP_003 |

- Interactions: Button "Gọi ngay" disabled + tooltip khi Offline/Busy
- Animation đề xuất: Shared element transition từ list avatar

**Non-Happy Case:**

| Trigger | Hiển thị | Message |
|---|---|---|
| Company offline | Button disabled + tooltip | "Company Admin hiện không online" |
| Company đang bận | Button disabled + tooltip | "Company Admin đang trong cuộc gọi khác" |

---

### DA_VOIP_003 — Outgoing Call Screen

**Happy Case:**
- Layout: Full-screen overlay (dark background), caller info center, actions bottom
- Components:

  | Vị trí | Component | Nội dung | Action |
  |---|---|---|---|
  | Center-top | Avatar large | Logo company (với ringing pulse animation) | — |
  | Center | Text primary | Tên company | — |
  | Center | Text secondary | "Đang gọi..." (animated dots) | — |
  | Bottom | Icon button | Loa ngoài (toggle) | Bật/tắt speaker |
  | Bottom | Icon button | Mute (toggle) | Bật/tắt mute |
  | Bottom | Button red | "Kết thúc" | Cancel call → DA_VOIP_002 |

- Animation đề xuất: Fade-in full screen, ringing pulse trên avatar

**Non-Happy Case:**

| Trigger | Hiển thị | Message |
|---|---|---|
| Timeout 30s | Auto dismiss + toast | "Không có phản hồi" |
| Bị từ chối | Auto dismiss + toast | "Cuộc gọi bị từ chối" |
| Mất mạng | Auto dismiss + toast | "Kết nối bị gián đoạn" |
| Microphone permission denied | Modal | "Cần quyền microphone để gọi điện" + nút "Mở Cài đặt" |

---

### DA_VOIP_004 — In-Call Screen (Caller)

**Happy Case:**
- Layout: Full-screen overlay, call timer top, avatar center, action buttons bottom
- Components:

  | Vị trí | Component | Nội dung | Action |
  |---|---|---|---|
  | Top | Call timer | "00:00" đếm lên | — |
  | Center | Avatar large | Logo company + tên | — |
  | Bottom | Icon button | Mute (highlight khi active) | Toggle mute |
  | Bottom | Icon button | Loa ngoài (highlight khi active) | Toggle speaker |
  | Bottom | Button red | "Kết thúc" | End call → DA_VOIP_005 |

- Animation đề xuất: Waveform animation khi đang nói

**Non-Happy Case:**

| Trigger | Hiển thị | Message |
|---|---|---|
| Mất mạng đột ngột | Toast + auto end | "Kết nối bị gián đoạn" → DA_VOIP_005 |
| Company Admin hang up | Auto dismiss | Toast "Cuộc gọi đã kết thúc" → DA_VOIP_005 |

---

### DA_VOIP_005 — Call Ended Summary

**Happy Case:**
- Layout: Bottom sheet (không full screen), tự dismiss sau 5s hoặc user tap
- Components:

  | Vị trí | Component | Nội dung | Action |
  |---|---|---|---|
  | Top | Status icon | ✅ xanh (completed) / ❌ đỏ (missed/error) | — |
  | Body | Text | Tên company | — |
  | Body | Text | Thời lượng: "2 phút 34 giây" | — |
  | Body | Text | Thời gian: "14:32 — 07/09/2026" | — |
  | Body | Status badge | Completed / Missed / Declined / Disconnected | — |
  | Bottom | Button primary | "Gọi lại" | → DA_VOIP_003 |
  | Bottom | Button outline | "Đóng" | → DA_VOIP_002 |

- Animation đề xuất: Slide-up bottom sheet

**Non-Happy Case:**

| Trigger | Hiển thị | Message |
|---|---|---|
| Missed | Icon đỏ + badge | Status: "Không có phản hồi" |
| Declined | Icon đỏ + badge | Status: "Cuộc gọi bị từ chối" |
| Disconnected | Icon đỏ + badge | Status: "Kết nối bị gián đoạn" |

---

### DA_VOIP_006 — Call History List

**Happy Case:**
- Layout: Full-screen list, filter tabs top
- Components:

  | Vị trí | Component | Nội dung | Action |
  |---|---|---|---|
  | Top | Filter tabs | Tất cả / Missed / Completed | Filter list |
  | Body | List item | Avatar + Tên + Status icon (màu) + Thời lượng + Timestamp | Tap → Call detail modal |
  | Body | Date separator | "Hôm nay" / "Hôm qua" / "DD/MM/YYYY" | — |

- Interactions: Swipe-right trên item → shortcut "Gọi lại"
- Animation đề xuất: Skeleton loader

**Non-Happy Case:**

| Trigger | Hiển thị | Message |
|---|---|---|
| Không có lịch sử | Empty state | "Chưa có cuộc gọi nào" |
| Filter Missed rỗng | Empty state | "Không có cuộc gọi nhỡ nào" |
| Lỗi load | Error + Retry | "Không thể tải lịch sử. Thử lại." |

---

### CA_VOIP_001 — Incoming Call Screen (Company Admin)

**Happy Case:**
- Layout: Full-screen overlay (kể cả khi app background — native-style incoming call UI)
- Components:

  | Vị trí | Component | Nội dung | Action |
  |---|---|---|---|
  | Center | Avatar large | "Dipro Admin" logo + tên (với ringing pulse) | — |
  | Center | Text | "Đang gọi đến..." | — |
  | Bottom | Button green | "Chấp nhận" | → CA_VOIP_002 |
  | Bottom | Button red | "Từ chối" | Dismiss + notify caller |

- Interactions: Ringing sound + vibration (follow device settings)
- Animation đề xuất: Ringing pulse, fade-in overlay

**Non-Happy Case:**

| Trigger | Hiển thị | Message |
|---|---|---|
| App bị kill (background) | Push notification | "Dipro Admin đang gọi" + Accept/Decline action trực tiếp trên notification |
| Caller cancel trước khi accept | Auto dismiss overlay | — |
| Microphone permission denied | Modal | "Cần quyền microphone để nghe cuộc gọi" + "Mở Cài đặt" |

---

### CA_VOIP_002 — In-Call Screen (Receiver)

**Happy Case:**
- Layout: Tương tự DA_VOIP_004
- Components:

  | Vị trí | Component | Nội dung | Action |
  |---|---|---|---|
  | Top | Call timer | "00:00" đếm lên | — |
  | Center | Avatar large | "Dipro Admin" | — |
  | Bottom | Icon button | Mute (toggle) | Toggle mute |
  | Bottom | Icon button | Loa ngoài (toggle) | Toggle speaker |
  | Bottom | Button red | "Kết thúc" | End call → dismiss |

- Animation đề xuất: Waveform animation khi nói

**Non-Happy Case:**

| Trigger | Hiển thị | Message |
|---|---|---|
| Mất mạng | Toast + auto end | "Kết nối bị gián đoạn" |
| Caller hang up | Auto dismiss | Toast "Cuộc gọi đã kết thúc" |

---

## Responsive Requirements

| Breakpoint | Screen size | Ghi chú |
|---|---|---|
| Mobile iOS | 390×844 (iPhone 14) | Layout chuẩn — feature này mobile-only |
| Mobile Android | 360×800 (Android mid-range) | Đảm bảo tương thích notch / gesture navigation bar |

**Quy tắc chung:**
- Navigation: Bottom tab bar (follow app convention hiện tại)
- Font scale: Follow system font size (accessibility support)
- Call overlay: Full-screen, không bị navigation bar / notch che
- Push notification: Test trên thiết bị thật (không chỉ simulator) — iOS APNs + Android FCM

---

## UX Review Notes

**UX:** Happy path chỉ 3 tap (List → Detail → Gọi) — đủ ngắn, không friction. Status badge Online/Offline/Busy trên Company Detail giúp Dipro Admin biết có nên gọi hay không trước khi tap, tránh missed call vô ích. Nút "Gọi lại" trong Call Ended Summary giúp retry ngay mà không cần quay lại danh sách.
⚠️ Đề xuất thêm badge đỏ (unread missed calls) trên icon Call History trong bottom tab nếu app hỗ trợ — giúp Dipro Admin biết có cuộc gọi nhỡ cần follow up.

**Information Design:** Call History dùng filter tab + status icon màu sắc (xanh/đỏ) + date separator → dễ quét nhanh để tìm cuộc gọi nhỡ. Call Ended Summary đủ thông tin (tên, thời lượng, timestamp, trạng thái) trong 1 bottom sheet gọn — không cần vào detail màn hình riêng.
⚠️ Label status cần nhất quán giữa Call Ended Summary và Call History: dùng cùng 1 bộ từ (Completed / Missed / Declined / Disconnected).

**Performance:** ⚠️ VoIP SDK (Agora / Daily.co / Twilio) phải được init khi app launch, KHÔNG init khi user tap "Gọi" — tránh delay 1–2 giây trước khi Outgoing Call Screen hiển thị. Push notification cho CA_VOIP_001 phụ thuộc APNs/FCM latency — cần test trên thiết bị thật ở nhiều điều kiện mạng.

---

## Figma Link

| Screen Code | Screen | Figma Link |
|---|---|---|
| DA_VOIP_001 | Company List | [Xem Figma](https://www.figma.com/design/VKAAOyoSPvgoB3H2qdeeV3/ES-Kitchen-phase-2?node-id=30492-48288&m=dev) |
| DA_VOIP_002 | Company Detail | [Xem Figma](https://www.figma.com/design/VKAAOyoSPvgoB3H2qdeeV3/ES-Kitchen-phase-2?node-id=30492-48341&m=dev) |
| DA_VOIP_003 | Outgoing Call | [Xem Figma](https://www.figma.com/design/VKAAOyoSPvgoB3H2qdeeV3/ES-Kitchen-phase-2?node-id=30493-48286&m=dev) |
| DA_VOIP_004 | In-Call (Caller) | [Xem Figma](https://www.figma.com/design/VKAAOyoSPvgoB3H2qdeeV3/ES-Kitchen-phase-2?node-id=30493-48307&m=dev) |
| DA_VOIP_005 | Call Ended Summary | [Xem Figma](https://www.figma.com/design/VKAAOyoSPvgoB3H2qdeeV3/ES-Kitchen-phase-2?node-id=30494-48286&m=dev) |
| DA_VOIP_006 | Call History | [Xem Figma](https://www.figma.com/design/VKAAOyoSPvgoB3H2qdeeV3/ES-Kitchen-phase-2?node-id=30494-48308&m=dev) |
| CA_VOIP_001 | Incoming Call | [Xem Figma](https://www.figma.com/design/VKAAOyoSPvgoB3H2qdeeV3/ES-Kitchen-phase-2?node-id=30495-48286&m=dev) |
| CA_VOIP_002 | In-Call (Receiver) | [Xem Figma](https://www.figma.com/design/VKAAOyoSPvgoB3H2qdeeV3/ES-Kitchen-phase-2?node-id=30495-48304&m=dev) |
