# system-to-doc — BA Kit

> Nhận một **hệ thống đã có sẵn** (website đang chạy · source code · database · Figma) → AI tự khảo sát → dựng **bộ tài liệu baseline có version**. Về sau mỗi khi khách gửi **yêu cầu thay đổi (CR)**, AI đối chiếu baseline để trả lời CR ảnh hưởng tới đâu.
>
> Hướng dẫn có hình: [`docs/Hướng dẫn sử dụng System to Doc.docx`](docs/)

---

## Hai luồng

| | Luồng 1 — Baseline | Luồng 2 — Change Request |
|---|---|---|
| Khi nào | Lần đầu nhận dự án · hệ thống đã đổi nhiều | Khách gửi yêu cầu thay đổi |
| Lệnh | `/analyze-system` | `/change-request <file / link / nội dung>` |
| Đọc | Website · Source · DB · Figma | Baseline mới nhất + nội dung CR |
| Ra | `outputs/ver<N>_<DDMMYY>_<tên>/` — 7 output | `outputs/ver<N>_<DDMMYY>_CR-<id>-<tên>/` — impact 6 trục |

---

## Chuẩn bị (1 lần)

```bash
# 1. Copy toàn bộ folder system-to-doc vào folder dự án
# 2. Cài dependency
pip install openpyxl python-docx matplotlib
npm i -D playwright && npx playwright install chromium
# 3. (Vẽ Figma) kết nối Figma MCP
claude mcp add --transport http figma https://mcp.figma.com/mcp
```

```
my-project/
├── CLAUDE.md · POLICIES.md · AGENTS.md · templates/ · .claude/    ← kit (không sửa)
├── inputs/
│   ├── db/schema.sql      ← (tuỳ chọn) dump CHỈ CẤU TRÚC, không dữ liệu
│   └── cr/                ← nơi bỏ file yêu cầu thay đổi (Luồng 2)
└── outputs/               ← AI tự tạo, mỗi lần chạy 1 folder version
```

---

## Luồng 1 — chạy lần đầu

```bash
cd my-project && claude
/analyze-system
```

AI sẽ hỏi (chọn đáp án hoặc gõ vào ô *Other*):

| Nhóm | AI hỏi | Chuẩn bị sẵn |
|---|---|---|
| **Website** | Bao nhiêu site · URL · staging/production · tài khoản role nào · **ai cấp, có được phép dùng để quét không** · chỉ ĐỌC hay được CREATE/UPDATE · vùng cấm | URL, tài khoản **test** |
| **Source code** | Bao nhiêu repo · đường dẫn · FE/BE · repo FE thuộc website nào | Đường dẫn repo trên máy |
| **Database** *(tuỳ chọn)* | Có file schema / quyền đọc DB / chỉ có migration / không có | `mysqldump --no-data` hoặc `pg_dump --schema-only` |
| **Figma** *(tuỳ chọn)* | Link design hiện tại · **link file để vẽ flow** | Link `figma.com/design/...` |
| Khác | Có làm bug list không · ngôn ngữ · nguồn có dữ liệu thật không | |

> ⚠️ **Mật khẩu không gõ vào chat.** Khi cần đăng nhập, AI mở trình duyệt — bạn tự đăng nhập, AI chỉ lưu phiên vào `.auth/` (không commit, không nằm trong output).
> ⚠️ Mặc định AI **chỉ đọc** — mọi thao tác ghi bị chặn ở tầng mạng.
> Thiếu thứ gì (không có DB, không có Figma…) → AI ghi lại và **chạy tiếp** phần còn lại.

AI in **bảng tổng hợp** → bạn trả lời `OK` → AI khảo sát và sinh output. Phát hiện dữ liệu nhạy cảm (`.env`, key, dump có dữ liệu thật…) → AI **cảnh báo và dừng** chờ bạn xử lý.

### Output Luồng 1

| # | Output | File trong `outputs/ver<N>_.../` |
|---|---|---|
| **O1** | **Danh sách màn hình theo website** — tổng số màn, item từng màn, xử lý, lỗi hiển thị, liên kết giữa các màn (template Basic Design công ty) | `01_Screens/BasicDesign_WEB-01_ver<N>.xlsx` (1 file / website) |
| **O2** | **API Documentation** — mọi API theo group (+ batch): làm gì, method, request, response; sheet tổng hợp có link tới từng API · **sơ đồ map code** FE ↔ BE ↔ DB | `02_API/API_Doc_….xlsx` · `02_API/CodeMap_….png` |
| **O3** | **Database Documentation** — tổng quan bảng, quan hệ, từng bảng: field · kiểu · format · giới hạn · maxlength · mục đích · ERD | `03_DB/DB_Doc_….xlsx` · `03_DB/ERD_….png` |
| **O4** | **Design System** hệ thống cũ (từ website / Figma + source) — đúng format artifact **Design System** của claude.ai: brand book, màu theo theme, thang chữ, spacing/radius/shadow, component có preview, logo/icon, cover. Đồng ý thì publish thành link private | `04_DesignSystem/project/` · `04_DesignSystem/link.md` |
| **O5** | **Figma flow** — Output 1 Flow tổng quan + Output 2 Screen flow | link trong `05_Figma/figma-links.md` |
| **O6** | **Tài liệu tổng hợp** — đã chạy gì, có gì, ở đâu | `06_Overview/Overview_….docx` |
| **O7** | **Bug list hiện trạng** mức Medium–High *(nếu chọn)* | `07_BugList/BugList_….xlsx` |
| — | **Mục lục version** — mọi output, số lượng, kết quả kiểm tra | `README.md` |

Mọi dòng trong tài liệu gắn với bằng chứng (ảnh chụp, dòng code, schema). Không có bằng chứng → ghi `UNKNOWN` / "cần xác minh", **không viết đại cho đẹp**. Danh sách điểm chưa chắc nằm ở Phụ lục A của O6.

---

## Luồng 2 — khi có 1 yêu cầu thay đổi

**Bước 1 — đưa yêu cầu vào** (1 trong 3 cách):

| Cách | Làm gì |
|---|---|
| File *(khuyến nghị)* | Bỏ file (`.docx` `.pdf` `.xlsx` `.md` ảnh chụp) vào `inputs/cr/` → `/change-request inputs/cr/<tên-file>` |
| Dán trực tiếp | `/change-request` rồi dán nội dung yêu cầu |
| Link | `/change-request <link Backlog / Drive / Figma>` — không đọc được link thì AI nhờ bạn tải file về `inputs/cr/` |

**Bước 2 — AI làm:** tìm baseline mới nhất → hỏi xác nhận + hỏi chỗ chưa rõ → phân tích **6 trục**:

| Trục | Trả lời |
|---|---|
| Hệ thống | CR tác động tới site / module / repo / batch nào |
| Database | Thêm gì? Xung đột với cái cũ không? |
| Nghiệp vụ | Sửa gì? Ảnh hưởng nghiệp vụ hiện tại không? |
| Màn hình | Thêm / sửa / xoá màn nào? Ảnh hưởng màn hiện tại không? |
| Bên thứ 3 | Thêm liên kết nào? Ảnh hưởng liên kết hiện tại không? |
| Mockup | Màn mới có nhất quán với Design System cũ không? |

**Output Luồng 2** (`outputs/ver<N>_<DDMMYY>_CR-<id>-<tên>/`): `CR-<id>_Impact.xlsx` (chi tiết 6 trục + câu hỏi) · `CR-<id>_Summary.md` (≤ 1 trang, gửi KH được) · Figma **view CR mới** (chỉ phần thay đổi + phần bị ảnh hưởng, không vẽ đè bản cũ).

CR đã được làm xong trong hệ thống → chạy `/analyze-system` chọn **Delta** để có baseline mới.

---

## Version

```
outputs/
├── ver1_011026_baseline/              Luồng 1
├── ver2_151026_CR-001-them-coupon/    Luồng 2 — trỏ về ver1
└── ver3_201026_baseline-delta/        Luồng 1 Delta sau khi CR-001 đã code xong
```
Không bao giờ sửa version cũ. Muốn góp ý → ghi vào mục **Feedback** trong `run-log.md` của version rồi chạy lại.

---

## Kit cam kết

| Cam kết | Cách thực thi |
|---|---|
| **Không bịa** | Mọi khẳng định gắn bằng chứng; thiếu thì ghi `UNKNOWN` + câu hỏi |
| **Không phá hệ thống** | Mặc định chỉ đọc; gặp nút xoá/thanh toán vẫn dừng hỏi; không bao giờ kết nối DB của khách |
| **Không làm lộ dữ liệu** | Quét nhạy cảm trước khi đọc, hook chặn PII trước khi ghi/đẩy lên Figma, mật khẩu không bao giờ vào file |
| **Tự chấm, không tự khen** | Mỗi output qua script kiểm tra, in số thật `N checks · X PASS · 0 FAIL` |
