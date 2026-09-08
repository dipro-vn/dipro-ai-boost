# Cài đặt Dipro AI Boost trên macOS

Gửi file này kèm theo `.dmg` cho người nhận. Không cần biết lập trình để làm theo.

---

## Trước khi bắt đầu — kiểm tra 2 thứ

### 1. Máy phải là Mac chip Apple Silicon

Bấm  → **About This Mac**. Dòng **Chip** phải ghi **Apple M1 / M2 / M3 / M4**.

Nếu ghi **Intel** thì bản này **không chạy được** — báo lại người gửi để họ build bản khác.

### 2. Máy phải có Claude Code

Mở **Terminal** (bấm ⌘ + dấu cách, gõ `Terminal`, Enter), dán dòng này rồi Enter:

```bash
claude --version
```

- Hiện ra số phiên bản → xong, qua bước tiếp theo.
- Báo `command not found` → cài Claude Code trước tại **https://claude.com/product/claude-code**, đăng nhập, rồi quay lại.

> Dipro AI Boost **không tự gọi AI** — nó chạy Claude Code trên máy bạn. Không có Claude Code thì app mở được nhưng không chạy được agent nào.
>
> Bạn **không** cần cài Node.js, pnpm hay Rust. Những thứ đó chỉ dành cho người build app.

---

## Bước 1 — Chép app vào máy

1. Bấm đúp file `Dipro AI Boost_0.1.0_aarch64.dmg`.
2. Cửa sổ hiện ra có biểu tượng app và thư mục **Applications**.
3. **Kéo** biểu tượng **Dipro AI Boost** thả vào **Applications**.
4. Đóng cửa sổ, bấm nút ⏏︎ bên cạnh "Dipro AI Boost" ở thanh bên Finder để tháo đĩa ảo.

---

## Bước 2 — Cho phép macOS mở app

Lần đầu mở, macOS sẽ **chặn** và hiện thông báo đại loại *"Apple could not verify…"* hoặc *"…cannot be opened"*.

**Đây là bình thường.** App không có virus và cũng không hỏng — xem [giải thích](#vì-sao-macos-chặn) bên dưới.

Làm theo đúng thứ tự:

1. Mở **Launchpad** → bấm **Dipro AI Boost** một lần. macOS hiện thông báo chặn → bấm **Done** / **OK**.
2. Mở  → **System Settings** → **Privacy & Security**.
3. **Kéo xuống gần cuối trang.** Sẽ thấy một dòng kiểu:
   > *"Dipro AI Boost" was blocked to protect your Mac.*
4. Bấm nút **Open Anyway** bên cạnh dòng đó.
5. Nhập mật khẩu máy (hoặc Touch ID) nếu được hỏi.
6. Hiện hộp thoại xác nhận → bấm **Open Anyway** lần nữa.

App mở lên. **Chỉ phải làm một lần** — những lần sau bấm mở như mọi app khác.

> ⚠️ Trên macOS 15 (Sequoia) trở lên, cách cũ "giữ Control rồi bấm → Open" **không còn tác dụng**. Phải đi đường Privacy & Security ở trên.

### Cách nhanh hơn (nếu bạn quen Terminal)

Thay cho toàn bộ Bước 2, mở Terminal và dán:

```bash
xattr -dr com.apple.quarantine "/Applications/Dipro AI Boost.app"
```

Rồi mở app bình thường. Lệnh này gỡ cờ đánh dấu "file tải từ internet", không sửa gì trong app.

---

## Vì sao macOS chặn?

macOS chỉ mở thẳng những app đã được ký bằng tài khoản **Apple Developer** trả phí. Dipro AI Boost là app nội bộ của công ty, chưa mua tài khoản đó, nên macOS không xác minh được người phát hành và chặn lại theo mặc định.

Cảnh báo này nói về **nguồn gốc chưa xác minh**, không phải phát hiện phần mềm độc hại. Bước 2 là cách Apple cho phép bạn tự chấp nhận rủi ro đó cho một app cụ thể.

---

## Sau khi cài xong

App cần một **thư mục project** để làm việc. Lần đầu mở, chọn **Tạo project mới** rồi làm theo hướng dẫn trên màn hình, hoặc hỏi người gửi file này để lấy thư mục project có sẵn.

## Gặp lỗi?

| Hiện tượng | Xử lý |
|---|---|
| *"…is damaged and can't be opened"* | File `.dmg` tải về bị lỗi dở dang — tải lại từ đầu |
| Không thấy dòng **Open Anyway** trong Privacy & Security | Phải thử mở app **một lần** trước đã, dòng đó mới xuất hiện |
| App mở nhưng báo không tìm thấy `claude` | Chưa cài Claude Code, hoặc cài ở chỗ lạ — vào **Settings → Claude CLI path** trong app để chỉ đường dẫn |
| Máy Intel | Bản này không chạy được, cần bản universal — báo người gửi |
