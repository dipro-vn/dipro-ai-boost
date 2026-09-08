# SPEC: User Login (Đăng nhập bằng Email + Mật khẩu)

> **Nguồn:** `.ai-boost/inputs/20260818T073609744Z-user-login/` — yêu cầu khách hàng (12/08/2026), biên bản họp kỹ thuật (13/08/2026), ràng buộc kỹ thuật, mô tả 2 màn hình.
> **Trạng thái:** Có **6 điểm chưa chốt** (xem `## Open Questions`) — các điểm này KHÔNG được tự quyết trong Design/Task.

---

## Mô tả nghiệp vụ

Hệ thống hiện đăng nhập bằng **mã nhân viên** (dạng `NV0173`, do bộ phận hành chính cấp) + mật khẩu. Tháng tới hệ thống mở cho **khách hàng doanh nghiệp bên ngoài** — nhóm này không có mã nhân viên, nên định danh đăng nhập phải chuyển sang **email**.

Ba vấn đề đang gặp với cơ chế cũ:

| # | Vấn đề | Bằng chứng | Kỳ vọng sau feature |
|---|---|---|---|
| 1 | Không có cơ chế chống dò mật khẩu | Log tháng 07/2026: 1 IP thử >4.000 lần trong một đêm vào vài mã nhân viên | Sai nhiều lần → khoá tài khoản tạm thời |
| 2 | Không kiểm soát được phiên đăng nhập | Một tài khoản bị dùng ở 2 nơi cùng lúc, không có cách ngắt | Đổi mật khẩu → thu hồi toàn bộ phiên |
| 3 | Quên mật khẩu phải gọi hành chính đặt lại tay, đọc mật khẩu qua điện thoại | PO đánh giá "vừa mất thời gian vừa không an toàn" | Tự phục vụ qua email |

**Ưu tiên cao nhất theo PO:** chống dò mật khẩu (được nhắc lại nhiều lần trong buổi trao đổi).

**Ràng buộc thời gian:** cần lên production **trước 15/09/2026** để kịp mở cho nhóm khách hàng doanh nghiệp đầu tiên.

**Quy tắc nghiệp vụ đã chốt:**

| Mã | Quy tắc | Nguồn |
|---|---|---|
| BR-01 | Định danh đăng nhập = **email** (unique toàn hệ thống) + mật khẩu | Yêu cầu KH |
| BR-02 | Sai mật khẩu **5 lần liên tiếp** → khoá tài khoản **15 phút** | Biên bản §1 |
| BR-03 | Đăng nhập đúng → bộ đếm sai về **0** | Biên bản §1 |
| BR-04 | Khoá **theo tài khoản**, KHÔNG khoá theo IP (khách doanh nghiệp dùng chung IP văn phòng) | Biên bản §1 |
| BR-05 | Thông báo khi bị khoá phải nêu rõ **còn bao lâu** mới thử lại được | Biên bản §1, mô tả màn |
| BR-06 | Access token sống **15 phút**; refresh token sống **30 ngày** | Biên bản §2 |
| BR-07 | Không tick "Ghi nhớ đăng nhập" → refresh token chỉ sống **trong phiên trình duyệt** | Biên bản §2 |
| BR-08 | Đổi/đặt lại mật khẩu thành công → **thu hồi toàn bộ refresh token** của tài khoản đó | Biên bản §2 |
| BR-09 | Link đặt lại mật khẩu sống **60 phút**, dùng **một lần** | Biên bản §3 |
| BR-10 | **Không tiết lộ** email có tồn tại trong hệ thống hay không, ở mọi thông báo | Biên bản §3, RB kỹ thuật |
| BR-11 | Sai email hay sai mật khẩu → **cùng một thông báo chung**, không phân biệt | Mô tả màn đăng nhập |
| BR-12 | Tài khoản `is_active = false` → không cho đăng nhập | RB kỹ thuật |
| BR-13 | Gửi lại email đặt lại mật khẩu phải chờ **60 giây** (chống spam) | Mô tả màn quên MK |
| BR-14 | Đặt lại mật khẩu xong **không tự động đăng nhập** — buộc đăng nhập lại bằng mật khẩu mới | Mô tả màn quên MK |
| BR-15 | Không log mật khẩu, không log token, kể cả mức debug | RB kỹ thuật |

---

## Actors & Preconditions

### Actors

| Actor | Mô tả | Repo liên quan |
|---|---|---|
| Nhân viên nội bộ | ~180 tài khoản đang dùng mã nhân viên `NVxxxx`. Nhân viên kho dùng máy tính bảng cả ngày → nhạy cảm với việc bị bắt đăng nhập lại | `example-web` (UI), `example-api` (xử lý) |
| Người dùng doanh nghiệp (khách hàng) | Nhóm mới, mở từ tháng 09/2026. Không có mã nhân viên | `example-web`, `example-api` |
| Hệ thống gửi email | Gửi link đặt lại mật khẩu (nhà cung cấp **chưa chọn** — xem OQ-05) | `example-api` |

> **Phạm vi: Cross-repo — 2 repo** (`example-api` + `example-web`) → **CẦN Contract Lock** trước Phase 3 (REST endpoints: login, refresh, logout, forgot-password, reset-password + error codes).
> `example-mobile` **KHÔNG** thuộc phạm vi đợt này (app mobile hiện chưa có màn đăng nhập riêng — RB kỹ thuật §Repo liên quan).

### Preconditions

- Người dùng đã có tài khoản trong hệ thống với `is_active = true`.
- Tài khoản đã có **email duy nhất** gắn với nó. *(Hiện email nằm ở bảng `employee_profiles` và **không unique** → cần xử lý dữ liệu trước khi bật tính năng; cách migrate cho 180 tài khoản cũ **chưa chốt** — xem OQ-01.)*
- Người dùng truy cập được hộp thư email của mình (bắt buộc cho luồng quên mật khẩu).
- Mật khẩu hiện tại đang hash bằng **bcrypt** — giữ nguyên thuật toán, không migrate hash.

---

## Happy Path

### HP-A — Đăng nhập thành công

1. Người dùng mở màn **Đăng nhập** (`WB_AUTH_001`).
2. Nhập **Email** (hệ thống tự chuyển chữ thường + cắt khoảng trắng hai đầu) và **Mật khẩu**.
3. (Tuỳ chọn) Tick **"Ghi nhớ đăng nhập"** — mặc định KHÔNG tick.
4. Bấm **Đăng nhập** → nút chuyển trạng thái loading và bị vô hiệu hoá.
5. Hệ thống xác thực: email tồn tại → mật khẩu đúng → tài khoản đang hoạt động → không bị khoá.
6. Hệ thống **đặt bộ đếm sai về 0** (BR-03) và cấp:
   - Access token — hạn 15 phút
   - Refresh token — hạn 30 ngày nếu có tick "Ghi nhớ đăng nhập"; nếu không tick thì chỉ tồn tại trong phiên trình duyệt (BR-07)
7. Điều hướng vào **trang chủ**; nếu trước đó người dùng bị đá ra từ một trang cụ thể → quay lại đúng trang đó.

### HP-B — Quên mật khẩu và đặt lại thành công

1. Ở màn đăng nhập, bấm link **"Quên mật khẩu?"** → mở màn **Quên mật khẩu** (`WB_AUTH_002`).
2. Nhập email → bấm **"Gửi hướng dẫn"**.
3. Hệ thống **luôn** hiển thị cùng một thông báo, bất kể email có tồn tại hay không (BR-10):
   > *"Nếu email này có trong hệ thống, chúng tôi đã gửi hướng dẫn đặt lại mật khẩu. Kiểm tra cả hộp thư rác."*
4. Nếu email tồn tại → hệ thống gửi email chứa **link đặt lại**, hạn **60 phút**, dùng **một lần** (BR-09).
5. Người dùng mở link → màn **Đặt mật khẩu mới** (`WB_AUTH_003`), nhập "Mật khẩu mới" + "Nhập lại mật khẩu mới" (có thanh hiển thị độ mạnh).
6. Bấm xác nhận → hệ thống đổi mật khẩu, **vô hiệu hoá link** (không dùng lại được) và **thu hồi toàn bộ refresh token** của tài khoản (BR-08).
7. Hiển thị thông báo ngắn thành công → đưa về màn đăng nhập, người dùng **đăng nhập lại** bằng mật khẩu mới (BR-14).

---

## Alternative Flows & Edge Cases

### Màn đăng nhập (`WB_AUTH_001`)

| ID | Tình huống | Hành vi mong đợi |
|---|---|---|
| AF-01 | Email sai định dạng | Báo lỗi ngay **dưới ô email**, kích hoạt khi rời khỏi ô (blur). Không gọi API |
| AF-02 | Bỏ trống email hoặc mật khẩu | Báo lỗi bắt buộc tại ô tương ứng, không gọi API |
| AF-03 | Sai email **hoặc** sai mật khẩu | **Cùng một thông báo chung** ở đầu form, không nói rõ sai cái nào (BR-11). Bộ đếm sai của tài khoản +1 nếu email tồn tại |
| AF-04 | Sai lần thứ 5 liên tiếp | Tài khoản bị khoá 15 phút. Thông báo nêu rõ thời gian còn lại (BR-05) |
| AF-05 | Đăng nhập trong lúc tài khoản đang bị khoá — **kể cả nhập đúng mật khẩu** | Từ chối, hiển thị thông báo khoá kèm **số phút còn lại**. Không cấp token |
| AF-06 | Hết 15 phút khoá, nhập đúng | Đăng nhập thành công, bộ đếm về 0 |
| AF-07 | Hết 15 phút khoá, tiếp tục nhập sai | ⚠️ **CHƯA CHỐT** — xem OQ-02 |
| AF-08 | Tài khoản `is_active = false` | *"Tài khoản đã bị vô hiệu hoá, liên hệ quản trị viên"* |
| AF-09 | Mất mạng / server lỗi (5xx) | Banner đỏ ở đầu form, **giữ nguyên email đã gõ**, cho thử lại |
| AF-10 | Bấm Enter / click nhiều lần liên tiếp | Chỉ **một** request được gửi; nút bị vô hiệu hoá trong lúc đang gửi |
| AF-11 | Access token hết hạn (15 phút) khi đang dùng | Hệ thống tự làm mới bằng refresh token, người dùng không bị gián đoạn |
| AF-12 | Refresh token hết hạn / đã bị thu hồi | Đá về màn đăng nhập, ghi nhớ trang đang xem để quay lại sau khi đăng nhập |
| AF-13 | Không tick "Ghi nhớ đăng nhập" rồi đóng trình duyệt | Mở lại phải đăng nhập lại (BR-07) |

### Màn quên mật khẩu (`WB_AUTH_002`)

| ID | Tình huống | Hành vi mong đợi |
|---|---|---|
| AF-14 | Email không tồn tại trong hệ thống | Hiển thị **đúng thông báo như trường hợp tồn tại**; KHÔNG gửi email (BR-10) |
| AF-15 | Email sai định dạng | Báo lỗi dưới ô email, không gọi API |
| AF-16 | Bấm "Gửi hướng dẫn" lần 2 trong vòng 60 giây | Chặn, hiển thị thời gian phải chờ (BR-13) |
| AF-17 | Yêu cầu link mới khi link cũ chưa hết hạn | ⚠️ **CHƯA CHỐT** — xem OQ-06 |

### Màn đặt mật khẩu mới (`WB_AUTH_003`)

| ID | Tình huống | Hành vi mong đợi |
|---|---|---|
| AF-18 | Link quá 60 phút | *"Link đã hết hạn"* + nút gửi lại |
| AF-19 | Link đã dùng rồi | **Cùng thông báo như hết hạn** — không phân biệt hai trường hợp |
| AF-20 | Hai ô mật khẩu không khớp | Báo lỗi **dưới ô thứ hai** |
| AF-21 | Mật khẩu mới không đạt quy tắc | Báo lỗi **dưới ô thứ nhất**. ⚠️ Quy tắc cụ thể **CHƯA CHỐT** — xem OQ-04 |
| AF-22 | Đặt lại thành công trong lúc tài khoản đang bị khoá 15 phút | ⚠️ **CHƯA CHỐT** — xem OQ-03 |
| AF-23 | Đặt lại thành công khi có phiên khác đang mở trên thiết bị khác | Phiên đó bị thu hồi, lần thao tác kế tiếp bị đá về màn đăng nhập (BR-08) |

---

## Acceptance Criteria

### Đăng nhập

- **AC-01** — Người dùng có email hợp lệ + mật khẩu đúng + `is_active = true` + không bị khoá → đăng nhập thành công và vào trang chủ.
- **AC-02** — Email nhập có chữ hoa hoặc khoảng trắng thừa hai đầu (`  User@Example.com  `) → vẫn đăng nhập được như `user@example.com`.
- **AC-03** — Nhập sai email hoặc sai mật khẩu → thông báo hiển thị **giống hệt nhau** ở cả hai trường hợp; không có bất kỳ dấu hiệu nào (nội dung, mã lỗi, thời gian phản hồi khác biệt rõ rệt) cho biết email có tồn tại.
- **AC-04** — Sai mật khẩu lần 1→4: vẫn cho thử tiếp. Sai lần thứ **5** liên tiếp: tài khoản bị khoá và mọi lần thử tiếp theo trong 15 phút đều bị từ chối.
- **AC-05** — Trong lúc bị khoá, nhập **đúng** mật khẩu vẫn bị từ chối và không cấp token.
- **AC-06** — Thông báo khoá hiển thị **số phút còn lại** và giá trị này giảm dần theo thời gian thực tế.
- **AC-07** — Sai 4 lần rồi nhập đúng lần 5 → đăng nhập thành công; sau đó sai tiếp 4 lần **không** bị khoá (bộ đếm đã reset về 0).
- **AC-08** — Tài khoản A bị khoá thì tài khoản B (dù cùng IP) vẫn đăng nhập bình thường.
- **AC-09** — Tài khoản `is_active = false` → hiển thị *"Tài khoản đã bị vô hiệu hoá, liên hệ quản trị viên"*, không cấp token, và **không** làm tăng bộ đếm khoá.
- **AC-10** — Bấm nút Đăng nhập / Enter 5 lần liên tiếp thật nhanh → chỉ có **1** request được gửi đi (kiểm chứng qua network log), bộ đếm sai chỉ tăng tối đa 1.
- **AC-11** — Server trả 5xx hoặc mất mạng → banner đỏ đầu form và **email đã gõ vẫn còn** trong ô.

### Phiên đăng nhập

- **AC-12** — Access token hết hạn sau đúng 15 phút; refresh token còn hạn → phiên tự làm mới, người dùng không thấy gián đoạn.
- **AC-13** — Tick "Ghi nhớ đăng nhập" → đóng và mở lại trình duyệt trong vòng 30 ngày vẫn còn đăng nhập.
- **AC-14** — KHÔNG tick "Ghi nhớ đăng nhập" → đóng trình duyệt rồi mở lại phải đăng nhập lại.
- **AC-15** — Đăng nhập trên 2 trình duyệt, đặt lại mật khẩu ở trình duyệt 1 → trình duyệt 2 bị đá về màn đăng nhập ở thao tác kế tiếp.
- **AC-16** — Bị đá ra khi đang ở một trang cụ thể → sau khi đăng nhập lại, quay về **đúng trang đó**, không phải trang chủ.

### Quên / đặt lại mật khẩu

- **AC-17** — Nhập email tồn tại và email không tồn tại → thông báo trên màn hình **giống hệt nhau**.
- **AC-18** — Email tồn tại → nhận được email chứa link đặt lại trong hộp thư.
- **AC-19** — Bấm "Gửi hướng dẫn" lần 2 trong vòng 60 giây → bị chặn và hiển thị thời gian chờ.
- **AC-20** — Link mở trong vòng 60 phút và chưa dùng → vào được màn đặt mật khẩu mới.
- **AC-21** — Link mở sau 60 phút → hiển thị *"Link đã hết hạn"* + nút gửi lại.
- **AC-22** — Link đã dùng thành công 1 lần → mở lại hiển thị **đúng thông báo như hết hạn**, không phân biệt.
- **AC-23** — Hai ô mật khẩu không khớp → lỗi hiển thị dưới ô thứ hai, không gọi API.
- **AC-24** — Đặt lại thành công → hiển thị thông báo ngắn, chuyển về màn đăng nhập, **không** tự động đăng nhập.
- **AC-25** — Đăng nhập bằng **mật khẩu cũ** sau khi đã đặt lại → thất bại; bằng mật khẩu mới → thành công.

### Bảo mật & vận hành

- **AC-26** — Không có mật khẩu, access token, hay refresh token nào xuất hiện trong log ở mọi mức (bao gồm debug).
- **AC-27** — Mật khẩu lưu ở dạng hash **bcrypt**; 180 tài khoản hiện có **không phải** đặt lại mật khẩu do đổi thuật toán.
- **AC-28** — Bộ đếm sai mật khẩu hoạt động đúng khi API chạy **nhiều instance song song**: sai 3 lần qua instance 1 + 2 lần qua instance 2 → tài khoản bị khoá.
- **AC-29** — Không có cột nào của bảng `users` bị đổi tên hoặc xoá (`employee_code`, `password_hash`, `is_active` giữ nguyên).
- **AC-30** — Email dùng để đăng nhập là **duy nhất**: không thể tồn tại 2 tài khoản active có cùng email.

---

## Out of Scope

| # | Hạng mục | Lý do |
|---|---|---|
| 1 | **OTP / SMS cho đăng nhập thường** | PO từ chối rõ ràng: tốn chi phí tin nhắn, nhân viên kho thường để điện thoại ngoài tủ đồ |
| 2 | **2FA / xác thực hai lớp** | "Nếu sau này cần thì bàn riêng, không phải đợt này" |
| 3 | **Bắt buộc đổi mật khẩu định kỳ 3 tháng** | PO yêu cầu bỏ — "chỉ tổ khiến mọi người ghi mật khẩu ra giấy dán lên màn hình" |
| 4 | **Giới hạn/khoá theo địa chỉ IP** | Bị bác tại buổi họp kỹ thuật: khách doanh nghiệp dùng chung IP văn phòng sẽ bị khoá nhầm cả công ty |
| 5 | **Đăng nhập trên `example-mobile`** | App mobile hiện chưa có màn đăng nhập riêng — không thuộc đợt này |
| 6 | **Trang quản lý / ngắt phiên đăng nhập theo thiết bị** | ⚠️ Chưa quyết — mặc định KHÔNG làm đợt này, xử lý qua BR-08 (đổi mật khẩu = thu hồi hết phiên). Xem OQ-03 |
| 7 | **Đăng nhập bằng mạng xã hội / SSO** | Không xuất hiện trong bất kỳ tài liệu input nào |
| 8 | **Đăng ký tài khoản tự phục vụ** | Không có trong yêu cầu — tài khoản vẫn do bộ phận hành chính cấp |
| 9 | **Màn đổi mật khẩu khi đang đăng nhập** | Input chỉ mô tả luồng quên mật khẩu. BR-08 nhắc "đổi mật khẩu" nhưng không có mô tả màn — nếu cần, tách feature riêng |

---

## Open Questions

> **Chưa được quyết — KHÔNG tự chọn phương án ở bước Design/Task.** Mục 1–4 do PM (anh Dũng) đang chờ PO (chị Hương) trả lời trước thứ Sáu; mục 5–6 là câu hỏi phát sinh khi viết SPEC.

| ID | Câu hỏi | Các phương án đang đặt lên bàn | Ảnh hưởng nếu chưa chốt | Người quyết |
|---|---|---|---|---|
| **OQ-01** | **Migrate 180 tài khoản đang dùng mã nhân viên thế nào?** | (a) Hành chính nhập email cho từng người; (b) Cho đăng nhập bằng **cả** mã cũ lẫn email trong 3 tháng chuyển tiếp *(Tech Lead nghiêng về, QC lo làm phức tạp cơ chế khoá)*; (c) Bắt tất cả đặt lại qua "Quên mật khẩu" | **Chặn Phase 1** (migration DB) và đổi cả AC-30, AC-04. Phương án (b) làm phát sinh thêm nhánh flow đăng nhập | PO |
| **OQ-02** | **Hết 15 phút khoá mà vẫn sai tiếp thì sao?** | (a) Khoá tiếp 15 phút; (b) Tăng dần 15 → 30 → 60 phút; (c) Khoá hẳn, chờ admin mở | Chặn AF-07. Phương án (c) phát sinh thêm màn admin (chưa có trong scope) | PO |
| **OQ-03** | **Có cần trang xem/ngắt phiên đăng nhập theo thiết bị không?** | (a) Có trang quản lý thiết bị; (b) Chỉ dựa vào "đổi mật khẩu = thu hồi hết phiên" *(rẻ hơn nhiều)* | Ảnh hưởng scope & timeline 15/09. SPEC này đang giả định (b) và ghi ở Out of Scope #6 | PO |
| **OQ-04** | **Quy tắc mật khẩu mới là gì?** | Hệ thống cũ: tối thiểu 6 ký tự, không yêu cầu gì thêm. Giữ nguyên hay siết lại (độ dài, loại ký tự)? | Chặn AF-21, AC-23 và phần thanh độ mạnh mật khẩu ở `WB_AUTH_003` | PO / Tech Lead |
| **OQ-05** | **Nhà cung cấp gửi email cho luồng quên mật khẩu?** | Chưa chọn (vướng chung với một feature khác) | Chặn HP-B bước 4, AC-18. Không có nhà cung cấp = không test được luồng quên mật khẩu end-to-end | Tech Lead / PM |
| **OQ-06** | **Yêu cầu link đặt lại mới khi link cũ chưa hết hạn thì link cũ có bị vô hiệu không?** | (a) Vô hiệu link cũ, chỉ link mới nhất dùng được; (b) Cả hai link cùng có hiệu lực | Chặn AF-17. Ảnh hưởng cả test case bảo mật | Tech Lead |

**Điểm kỹ thuật cần Tech Lead quyết (không phải nghiệp vụ, ghi lại để không thất lạc):**

- Lưu bộ đếm sai mật khẩu ở đâu — Redis (nhanh, tự hết hạn, nhưng dự án chưa có Redis) hay cột trong PostgreSQL (không thêm hạ tầng, nhưng ghi nhiều). Tech Lead nghiêng về PostgreSQL đợt này; cần xác nhận hiệu năng với PM. **Ràng buộc cứng: đếm trong bộ nhớ của một process là KHÔNG đủ** (nhiều instance API chạy song song) → xem AC-28.
- Email hiện nằm ở `employee_profiles` và **không unique** → cần migration đưa email thành định danh unique cho đăng nhập, đồng thời không đổi tên/xoá cột đang có của bảng `users`.

---

## Screens

| Screen Code | Screen | Actor | App | Screen Type | Mô tả ngắn | Figma Link |
|---|---|---|---|---|---|---|
| `WB_AUTH_001` | Đăng nhập | Nhân viên nội bộ · Người dùng doanh nghiệp | example-web | Form | Logo trên, form giữa, không ảnh nền/banner. Ô Email (tự lowercase + trim), ô Mật khẩu (có nút hiện/ẩn), checkbox "Ghi nhớ đăng nhập" (mặc định không tick). Nút Đăng nhập chiếm hết chiều ngang form, có trạng thái loading + disabled. Dưới cùng có link "Quên mật khẩu?". Hiển thị lỗi inline dưới ô email và banner lỗi chung ở đầu form | _(chưa có)_ |
| `WB_AUTH_002` | Quên mật khẩu — nhập email | Nhân viên nội bộ · Người dùng doanh nghiệp | example-web | Form | Một ô Email + nút "Gửi hướng dẫn" + link quay lại đăng nhập. Sau khi gửi luôn hiện cùng một thông báo bất kể email tồn tại hay không. Nút gửi lại có đếm ngược 60 giây | _(chưa có)_ |
| `WB_AUTH_003` | Đặt mật khẩu mới | Nhân viên nội bộ · Người dùng doanh nghiệp | example-web | Form | Mở từ link trong email. Hai ô "Mật khẩu mới" + "Nhập lại mật khẩu mới", kèm thanh độ mạnh mật khẩu. Xử lý trạng thái link hết hạn / đã dùng (cùng một thông báo + nút gửi lại). Thành công → thông báo ngắn rồi về màn đăng nhập | _(chưa có)_ |

**Ghi chú bảng Screens:**

- **Chưa có thiết kế Figma** — cả 2 mô tả màn hình đều là "chụp lại từ bản vẽ trên bảng buổi họp". Designer cần tạo frame và điền cột `Figma Link`.
- **Module prefix `WB`** được suy ra cho `example-web` vì bảng Ecosystem trong `AGENTS.md` **chưa khai Epic code** cho các repo. Nếu dự án đã có quy ước Epic code khác, cần đổi lại prefix cho khớp — báo BA để cập nhật.
- Yêu cầu phi chức năng cho UI: PO nhấn mạnh **"đơn giản thôi, nhân viên kho mở bằng máy tính bảng đời cũ, đừng nặng"** → tránh ảnh nền nặng, animation phức tạp.
- Ràng buộc thiết kế: `WB_AUTH_003` phụ thuộc **OQ-04** (quy tắc mật khẩu) để vẽ đúng thanh độ mạnh và text hướng dẫn.
- Không có màn hình nào thuộc `example-mobile` trong đợt này.
