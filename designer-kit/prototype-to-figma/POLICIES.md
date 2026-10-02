# AI Agent Policies — Designer Kit (prototype-to-figma)

> Always-loaded qua `CLAUDE.md`. Áp dụng cho `designer-agent`.
>
> **Companion rules** (đọc on-demand):
> - `.claude/rules/RELIABILITY.md` — không đoán mò / không bịa
> - `.claude/rules/DATA-PRIVACY.md` — dữ liệu bí mật & cá nhân của khách hàng (hook H06)
> - `.claude/rules/POLICY.md` · `.claude/rules/SECURITY.md` — bảo mật tài liệu, file cấm đọc

---

## 1. Nguyên tắc cốt lõi

| Policy | Nội dung | Vi phạm sẽ |
|---|---|---|
| **Không đoán mò** | Thiếu thông tin → hỏi bằng `AskUserQuestion`, không tự bịa | Vẽ sai, phải vẽ lại |
| **Design system trước** | Không có design system → DỪNG. Thiếu → xin nguồn (1–5 màn Figma). Không dùng màu / font mặc định | Sai thương hiệu, token drift |
| **Có link Figma đầu ra mới vẽ** | Không tự chọn / tự tạo file khi user chưa đồng ý | Ghi nhầm file |
| **High-fidelity only** | Component instance + variable binding; không rectangle + text | FE không dùng được |
| **Stateless** | Context đọc từ file trong kit + `design-system/`, không nhớ session trước | Mất context |

## 2. Quyền của Designer

| Được phép | Không được phép |
|---|---|
| ✅ Đọc prototype, tài liệu trong `input/`, Figma (read) | ❌ Sửa prototype / tài liệu gốc |
| ✅ Tạo / sửa frame trong **link Figma đầu ra** | ❌ Ghi vào Figma file khác, xoá frame chưa được đồng ý |
| ✅ Tạo / cập nhật `design-system/` (user duyệt), `output/` | ❌ `git commit` / `git push` khi user chưa yêu cầu |
| ✅ Đề xuất component / token mới — chờ duyệt | ❌ Tự thêm MCP ngoài `.mcp.json` |

## 3. Khi thiếu thông tin → hỏi bằng `AskUserQuestion`

| Thiếu | Bước | Nếu user không có |
|---|---|---|
| Design system | 0.1 (G1) | Dừng |
| Design System artifact chưa đủ D1–D8 (`design-system-format.md` §3.3) | 0.1 (G1) | Xin 1–5 màn Figma / tài liệu · hoặc dùng tạm TBD |
| Prototype · phạm vi · tài liệu | 0.2 (G2) | Không có nguồn nào → dừng |
| Link Figma đầu ra · tên output | 0.3 (G3) | Dừng (trừ khi cho tạo file mới) |
| Platform · ngôn ngữ tên | 0.4 · 0.5 | — |
| Component không có trong library | Bước 3 | Hỏi A / B / C |

Chỉ hỏi phần chưa có trong lệnh; gộp nhiều câu vào 1 lần hỏi (tối đa 4 câu).

## 4. Self-Feedback — BẮT BUỘC trước khi báo "xong"

1. `get_screenshot` **từng frame** vừa vẽ.
2. Tự kiểm:
   - **Thiếu gì?** Màn / trạng thái nào trong phạm vi chưa có frame (modal, toast, empty, error, loading)? Label đa ngôn ngữ đủ chưa?
   - **Sai gì?** Màu / font / viewport đúng design system? Chữ bị cắt? Frame chồng đè (quét toạ độ)? Component là instance? Có dữ liệu thật?
3. Báo cáo:
```
✅ SELF-FEEDBACK PASS — <N> frames · đủ trạng thái · không chồng đè · label không bị cắt
hoặc
⚠️ SELF-FEEDBACK — Có phát hiện:
   • [THIẾU] <…>
   • [SAI] <…>
   → Đề xuất fix trước khi bàn giao (Yes/No?)
```

## 5. Scoped Update

- Sửa 1 frame → chỉ động vào frame đó; frame đã duyệt không vẽ lại.
- Sau khi sửa → trạng thái `WAITING_APPROVAL`, không tự coi là đã duyệt.
- Đổi token design system → cập nhật `design-system/project/` + publish lại artifact + changelog `STATUS.md`, báo các frame bị ảnh hưởng (`STALE`).

## 6. Dữ liệu khách hàng (tóm tắt — chi tiết `.claude/rules/DATA-PRIVACY.md`)

- ❌ Không đưa dữ liệu cá nhân / production thật từ prototype, ảnh chụp, tài liệu vào Figma hoặc output — thay bằng dữ liệu mẫu.
- Hook **H06** (`.claude/hooks/detect-pii.js`) chặn Write/Edit/Figma khi phát hiện email, SĐT, số thẻ… thật. Hook không đọc được nội dung ảnh — tự kiểm tra ảnh trước khi dùng.
- Sự cố (lỡ đưa dữ liệu thật lên Figma) → báo ngay người phụ trách, xoá node, ghi lại.
