# BA Agent — Preflight Questions Detail (Bước 2b)

> **Scope:** Chi tiết 3 câu preflight (0.4 Scope / 0 Platform / 0.5 Figma URL) + 10 câu checklist chuẩn.
> **Dùng ở:** `ba-agent.md` Bước 2b — agent body chỉ giữ bảng 3-row tóm tắt + reference file này khi cần copy enforcement/template chi tiết.
> **Thứ tự hỏi BẮT BUỘC:** Câu 0.4 → Câu 0 → Câu 0.5 → 10 câu chuẩn 1-10. Không đảo.

---

## Câu 0.4 — Scope (hỏi ĐẦU TIÊN)

**Câu hỏi trình user:**

```
Feature này thuộc scope nào?
  [A] Chức năng đơn lẻ — 1 use-case cụ thể
      (VD: 'Đăng ký tài khoản', 'Reset password')
  [B] Cụm chức năng — nhiều use-case liên quan trong 1 domain
      (VD: 'Quản lý đơn hàng' gồm List/Detail/Cancel/Refund)
  [C] Toàn hệ thống — cross-domain, nhiều actor, nhiều flow
      (VD: hệ thống multi-module có 5+ flows như Auth / User Mgmt / Payment / Notification / Reporting)
```

**Lưu:** `SCOPE_TYPE`

**Quyết định logic ở Bước 5:**

| SCOPE_TYPE | Behavior ở Bước 5 Gate B1/B2 |
|---|---|
| `[A]` Single flow | Output 1/2/3 vẽ liền mạch — KHÔNG hỏi gate scope |
| `[B]` Cụm | Sau Output 1 hỏi Gate B1 "vẽ Output 2 toàn bộ N flows hay chỉ 1 flow"; sau Output 2 hỏi Gate B2 tương tự |
| `[C]` Toàn hệ thống | Same as `[B]` — bắt buộc Gate B1 + B2 |

**⚠️ Enforcement:**
- Nếu user CHƯA trả lời → **DỪNG**, không tự đoán scope
- KHÔNG được assume `[A]` chỉ vì "feature nghe có vẻ nhỏ"

---

## Câu 0 — Platform target (hỏi thứ HAI)

**Câu hỏi trình user:**

```
Feature này thiết kế cho platform nào?
(Mobile app / Web app / Website / iPad-Tablet)
```

**Lưu:** `TARGET_PLATFORM` — quyết định viewport Output 3 và Responsive Requirements

**Skip khi:**
- SPEC / user đã ghi rõ (ví dụ "app mobile cho User + web cho Admin") → tự extract từ context
- Feature multi-platform (VD: 1 phần mobile + 1 phần web) → hỏi rõ TỪNG NHÓM screens thuộc platform nào, ghi vào cột "App" trong bảng `## Screens`

**⚠️ Enforcement Câu 0:**
- Nếu user CHƯA trả lời VÀ SPEC / context CŨNG chưa có → **DỪNG trước Bước 4**
- KHÔNG tự đoán platform, KHÔNG viết `## Responsive Requirements` với breakpoint tự chọn
- Hỏi lại đến khi có answer

**Mapping platform → viewport CHUẨN CỨNG (không tự đổi):**

| Platform | Viewport (W×H) | Ghi chú |
|---|---|---|
| Mobile app | **375×812** | iPhone standard — dùng cho native iOS/Android |
| Web app (mobile-first PWA) | **375×812** | Same as mobile — web responsive mobile-first |
| Website (desktop) | **1440×1024** | Desktop standard |
| iPad / Tablet | **1024×768** | Landscape tablet |

**Áp dụng:**
- Output 3 mockup phone/screen dùng đúng viewport size theo `TARGET_PLATFORM`
- Bảng `## Responsive Requirements` liệt kê breakpoint tương ứng
- Nếu 1 feature có nhiều platform → mỗi group screens dùng viewport riêng, ghi rõ trong Screen Details

---

## Câu 0.5 — Figma URL (hỏi thứ BA)

**Câu hỏi trình user:**

```
Bạn có Figma Design file để tôi đặt output không?
(URL dạng `figma.com/design/...`)
```

**Lưu:** `FIGMA_OUTPUT_URL` — dùng xuyên suốt Output 1/2/3

**Fallback nếu chưa có tại thời điểm hỏi:** tiếp tục Bước 4 tạo SPEC.md (không cần Figma), NHƯNG **nhắc lại trước Bước 5**.

**⚠️ Enforcement Câu 0.5 (áp dụng khi bắt đầu Bước 5 — vẽ Figma):**

Phân biệt 3 câu trả lời của user + xử lý khác nhau:

| User answer | Xử lý |
|---|---|
| **"Có/Yes"** nhưng CHƯA dán URL (VD: "có mà chờ tôi lấy") | ⚠️ **DỪNG hoàn toàn, KHÔNG được auto-skip, KHÔNG tự chạy tiếp Output 1**. Hiển thị: `⏸ Đang chờ Figma URL từ bạn. Vui lòng paste URL dạng \`figma.com/design/...?node-id=...\` để BA tiếp tục Bước 5.` Chờ đến khi user paste URL mới chạy tiếp. Nếu user quên → nhắc lại mỗi turn kế. TUYỆT ĐỐI không suy diễn "chắc user không cần" rồi skip. |
| **"Không/Refuse"** rõ ràng (VD: "khỏi, không cần Figma") | Skip Output 1-3, ghi vào bảng status: "❌ Skipped — user refuse cung cấp Figma URL". Vẫn chạy Output 0 (SPEC.md) + Output 4 (HTML Prototype). |
| **URL trỏ `/board/`** (FigJam) khi user muốn vẽ high-fi mockup | Warn user, xác nhận có muốn dùng FigJam không (Output 3 cần Figma Design `/design/` để đúng chuẩn viewport). Chờ user confirm hoặc paste URL Design mới. |

- Không được tự chọn Figma file khác. Không được tự tạo file mới không hỏi.
- Nếu user để trống ≥ 2 turn liên tiếp mà không phản hồi → hỏi thẳng: **"Bạn muốn (a) tiếp tục chờ, (b) skip Figma output, hay (c) tôi tự tạo Figma file mới?"** — chờ chọn 1 trong 3 mới action.

---

## 10 câu hỏi checklist chuẩn (hỏi sau Câu 0.4/0/0.5)

1. Feature này phục vụ actor nào? (xem danh sách Actors trong `AGENTS.md`)
2. Vấn đề cụ thể đang giải quyết là gì?
3. Điều kiện tiên quyết (phải login? phải có contract? ...)?
4. Happy path chính là gì? (mô tả step by step)
5. Edge cases nào quan trọng cần xử lý?
6. Acceptance criteria — khi nào coi là done?
7. Feature liên quan đến tính năng hiện có nào không?
8. Cần hiển thị / tương tác trên app mobile không (nếu dự án có repo vai trò `mobile`)?
9. Cần real-time không? (WebSocket, push notification)
10. Liên quan tích hợp bên ngoài không? (xem danh sách integration trong `.claude/context/specification.md`)
