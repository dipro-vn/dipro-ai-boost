# system-to-doc — BA Kit Feature

> Nhận một **hệ thống đã có sẵn** (website đang chạy · source code · database · file khách hàng cung cấp) → agent tự khảo sát → sinh **tài liệu phiên bản đầu tiên** cho dự án LABO / Maintain.
>
> Chiều ngược của `requirement-to-flow`: ở kia là *requirement → hệ thống*, ở đây là *hệ thống → tài liệu*.

---

## Dùng khi nào

- Nhận bàn giao một dự án đang chạy mà **không có tài liệu** (hoặc tài liệu đã lỗi thời)
- Cần baseline để về sau **phân tích ảnh hưởng** mỗi khi khách yêu cầu sửa đổi
- Cần **báo khách danh sách lỗi đang tồn tại** trước khi mình nhận trách nhiệm maintain

---

## Quy trình từ A → Z

### Bước 1 — Chuẩn bị thư mục dự án + nguồn đầu vào

```
my-project/
├── sources/
│   ├── 仕様書.pdf                ← file khách hàng cung cấp (nếu có)
│   ├── schema.sql                ← dump database (nếu có)
│   └── auth.json                 ← trạng thái đăng nhập Playwright (nếu có)
└── source-code/                  ← repo hệ thống (nếu có)
```

Chuẩn bị sẵn để trả lời agent:

| Hạng mục | Cần chuẩn bị |
|---|---|
| **Website** | URL (có thể nhiều site). Có staging thì ưu tiên staging |
| **Tài khoản** | Mỗi role một tài khoản quan sát. Thiếu role nào → phần đó agent ghi "chưa xác minh được" |
| **Source code** | Đường dẫn repo |
| **Database** | Dump/schema, hoặc connection read-only. **Không có cũng chạy được** — chương database sẽ được ghi rõ là không có |
| **Vùng cấm chạm** | URL / chức năng tuyệt đối không được thao tác |

### Bước 2 — Copy thư mục vào dự án

```bash
1- Mở folder system-to-doc bạn tải từ GitHub về
2- Copy toàn bộ thư mục
3- Paste vào trong folder dự án bạn tạo
```

Sau khi copy:

```
my-project/
├── sources/                 ← nguồn của bạn
├── source-code/
├── CLAUDE.md                ← bootstrap
├── POLICIES.md              ← AI behavior rules
├── AGENTS.md                ← mô tả agent (không cần sửa)
├── templates/               ← template tài liệu
└── .claude/
    ├── agents/system-analyst.md
    ├── sys-agent/           ← support docs
    ├── skills/system-analyst/
    └── commands/
        ├── analyze-system.md
        ├── basic-design.md
        └── bug-list.md
```

Cài dependency 1 lần:

```bash
pip install openpyxl python-docx matplotlib
npm i -D playwright && npx playwright install chromium
```

### Bước 3 — Chạy agent

```bash
cd my-project
claude
```

**Cách A — Natural language:**
```
Hãy phân tích hệ thống ở https://stg.example.jp và làm tài liệu High Level
```

**Cách B — Slash command:**
```
/analyze-system https://stg.example.jp
```

**Agent sẽ:**

1. **Hỏi bạn 8 câu trước khi chạm vào hệ thống** — phạm vi · website · **quyền thao tác** · tài khoản · database · source code · mức chi tiết · ngôn ngữ
2. **In bảng tổng hợp câu trả lời** và chờ bạn xác nhận (sai chỗ nào sửa ngay tại đây)
3. Khảo sát hệ thống ở **chế độ chỉ đọc** (mặc định)
4. Sinh **Output 1** + tự chấm chất lượng bằng script
5. Hỏi bạn có làm **Output 2** không

> ⚠️ **Quan trọng — câu hỏi về quyền thao tác:** mặc định agent chạy read-only, mọi request ghi bị chặn ở tầng mạng. Chỉ nới quyền khi bạn đang trỏ vào staging có dữ liệu test.

### Bước 4 — Nhận kết quả

Mỗi lần chạy đều được lưu snapshot vào `versions/v<N>_<DDMMYYYY>/` để so sánh với lần trước.

Cần sửa gì → ghi vào mục **Feedback** trong `versions/v<N>_.../run-log.md` rồi trigger lại agent.

---

## Các Output

### Output 1 — High Level System Analysis ✅ luôn có

File Word `01_HighLevel_<system>_v<N>.docx`, 4 chương:

| Chương | Nội dung |
|---|---|
| **1. Product Overview** | Sản phẩm làm về cái gì · ai dùng · cấu thành hệ thống |
| **2. Functional Overview** | Bảng toàn bộ chức năng: module · actor · mô tả · nguồn bằng chứng · trạng thái xác minh |
| **3. Database Detail** | Danh sách bảng · chi tiết cột · quan hệ. *Chỉ có khi bạn cung cấp được database* |
| **4. Overall System Flow** | Sơ đồ tổng quan (ảnh PNG chèn trong tài liệu) + diễn giải |
| *Phụ lục A* | **Danh sách điểm chưa chắc chắn** + việc cần làm để xác nhận |
| *Phụ lục B* | Điều kiện khảo sát (quét những gì, bằng tài khoản nào, ngày nào) |

### Output 2 — chỉ chạy khi bạn đồng ý ⬜

Sau khi Output 1 xong, agent hỏi bạn **một lần**:

| Lựa chọn | Kết quả |
|---|---|
| **Basic Design** | Ghi spec chi tiết từng màn hình vào **master Excel của công ty** (đúng template đang dùng, mỗi màn 1 sheet) |
| **Bug List** | File `02_BugList_<system>_v<N>.xlsx` — danh sách lỗi đang tồn tại, để báo khách hàng phòng ngừa trách nhiệm |
| **Cả hai** | |
| **Dừng ở Output 1** | |

---

## Ba điều kit này cam kết

| Cam kết | Cách thực thi |
|---|---|
| **Không bịa** | Mọi dòng trong tài liệu đều gắn với một bằng chứng cụ thể (ảnh chụp màn hình, dòng code, câu query). Không có bằng chứng thì ghi rõ "chưa xác minh được", không viết đại cho đẹp |
| **Không phá hệ thống** | Mặc định chỉ đọc. Muốn agent bấm nút ghi dữ liệu thì bạn phải đồng ý rõ ràng; gặp nút xoá/thanh toán agent vẫn dừng lại hỏi |
| **Tự chấm, không tự khen** | Sau khi sinh tài liệu, agent chạy bộ script kiểm tra và in số thật (`N checks · X PASS · 0 FAIL`). Còn lỗi thì sửa rồi chạy lại, không được báo xong |

---

## Chạy lại lần sau

Chạy `/analyze-system` lần nữa trên cùng dự án — agent đọc lại kết quả lần trước và hỏi bạn:

- **Delta** — chỉ khảo sát phần chưa phủ + kiểm lại phần cũ *(mặc định)*
- **Chạy lại toàn bộ** — khi hệ thống đã thay đổi nhiều
- **Không khảo sát** — chỉ đọc lại tài liệu cũ để trả lời câu hỏi của bạn
