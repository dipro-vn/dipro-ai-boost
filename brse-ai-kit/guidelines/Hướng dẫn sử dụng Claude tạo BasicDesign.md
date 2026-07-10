# Hướng dẫn sử dụng Claude tạo Basic Design

Tài liệu này hướng dẫn cách cấu hình **Claude Desktop** để tạo tài liệu **Basic Design** từ màn hình Figma đã được đánh số bằng **Basic Design Numbering Plugin**.

---

## Điều kiện chuẩn bị

Trước khi bắt đầu, hãy đảm bảo bạn đã có:

- [x] Claude Desktop
- [x] Đã cài đặt và đăng nhập Claude Desktop
- [x] Đã đánh số màn hình bằng **Basic Design Numbering Plugin**
- [x] URL của file Figma
- [x] Bộ file Prompt gồm:
  - `Introductions.md`
  - `Validation.md`
  - `Content rule.md`
  - `Error message.md`
  - `Format rule.md`

---

## Step 1. Tạo Project Folder

Tạo một folder trên máy tính để lưu toàn bộ tài liệu Basic Design.

Ví dụ:

```text
{Dipro Project}Basic_design
```

Sau này Claude sẽ tạo toàn bộ file Basic Design trong thư mục này.

---

## Step 2. Tạo Project trên Claude Desktop

Mở **Claude Desktop**, sau đó thực hiện theo thứ tự:

1. **New Project**
2. **Add Folder**
3. Chọn folder: `{Dipro Project}Basic_design`
4. **Create Project**

Sau khi hoàn thành, Claude sẽ tạo một Project mới liên kết với folder này.

---

## Step 3. Cấu hình Introductions

Trong Project vừa tạo, tìm phần **Project Instructions**.

Copy toàn bộ nội dung của file [Introductions.md](https://drive.google.com/file/d/16bfYjlGQ1-KnYE2CSw1TyhdJQo7lYaLw/view?usp=drive_link) và dán vào phần **Instructions**.

**Mục đích:**

- Định nghĩa vai trò của Claude
- Quy trình tạo Basic Design
- Cách phân tích UI
- Quy chuẩn tài liệu

---

## Step 4. Upload bộ Skills

Trong phần **Project Knowledge / Context**, upload các file sau:

- [Validation.md](https://drive.google.com/file/d/1pMZmHQ9VPN6KfRVijygBqm2Kbdc3BUhY/view?usp=drive_link)
- [Content rule.md](https://drive.google.com/file/d/1Pwp-Xo2r78GNYZD8gDu7a73rwYSH89wT/view?usp=drive_link)
- [Error message.md](https://drive.google.com/file/d/17w6G3VmBxAv08ZEDgDdfo9c1TeTc9LmA/view?usp=drive_link)
- [Format rule.md](https://drive.google.com/file/d/1MltzQeJBRPQcKMOyNXPVaTNeRuU7vuch/view?usp=drive_link)
- [【Project name】Master_Basic_desing_xlsx_V1.0](https://docs.google.com/spreadsheets/d/1F6MMqQusChPndg_vet7V4cbZh9a_7qfi/edit?usp=sharing&ouid=112036002777829539125&rtpof=true&sd=true)

Các file này sẽ giúp Claude:

- Kiểm tra validation
- Sinh Error Message đúng chuẩn
- Viết tài liệu theo đúng format
- Tuân thủ quy tắc của dự án

---

## Step 5. Kết nối Figma Connector

Tại ô nhập nội dung chat, thực hiện theo thứ tự:

1. Nhấn **+**
2. Chọn **Connectors**
3. Chọn **Add Connector**
4. Tìm kiếm **Figma**
5. Chọn **Add Figma**

Sau khi kết nối thành công, Claude có thể đọc trực tiếp dữ liệu từ Figma.

---

## Step 6. Gửi URL màn hình Figma

Mở file Figma đã được đánh số bằng **Basic Design Numbering Plugin**.

Copy URL của màn hình cần tạo Basic Design.

Ví dụ:

```text
https://www.figma.com/design/xxxxxxxxxxxxxxxx
```

Sau đó dán URL vào ô chat của Claude.

Claude sẽ tự động:

- Đọc màn hình
- Phân tích layout
- Nhận biết các marker đã đánh số
- Hiểu cấu trúc UI
- Sinh tài liệu Basic Design

---

## Kết quả

Sau khi xử lý hoàn tất, Claude sẽ tự động tạo tài liệu **Basic Design** theo đúng format của dự án.

Tài liệu sẽ bao gồm:

1. Overview
2. Business Overview
3. Screen Overview
4. Layout
5. Item List
6. Input Items
7. Validation
8. Error Message
9. Business Rules
10. Processing Flow
11. Notes

Toàn bộ file sẽ được lưu trực tiếp trong thư mục Project đã tạo ở **Step 1**.

---

## Lưu ý

> ⚠️ Chỉ sử dụng **Claude Desktop**. Claude Web hiện không hỗ trợ Project Folder theo quy trình này.

- Luôn upload đầy đủ bộ **Skills** trước khi bắt đầu.
- Đảm bảo Figma Connector đã được kết nối.
- Mỗi màn hình Figma nên được đánh số bằng **Basic Design Numbering Plugin** trước khi tạo Basic Design để AI nhận diện chính xác từng UI Item.
