# POLICY — Bảo vệ tài sản & IP

> **Scope:** Rule tổ chức, áp dụng cho **con người + AI agent**. Đây là policy chung của công ty — không chỉ về code, nên vẫn áp dụng cho BA kit dù kit này không có repo dự án.
> **Mức độ:** `MUST` = bắt buộc · `MUST NOT` = tuyệt đối cấm · `SHOULD` = nên · `MAY` = được phép có điều kiện. Vi phạm được coi là sự cố bảo mật, phải report ngay (§9).
> **Companion:** `POLICIES.md` §3.5 + §3.6 (AI behavior) · `SECURITY.md` (file cấm đọc) · `DATA-PRIVACY.md` (dữ liệu KH) · `RELIABILITY.md` (no hallucination).

**Liên quan nhất tới BA kit:** §2 (dùng AI) · §5 (dữ liệu client) · §8 (bàn giao) · §9 (báo sự cố). §1 §3 §4 §6 §7 vẫn áp dụng nhưng ít chạm tới trong workflow BA thường ngày.

---

## 1. NO_CODE_EXFILTRATION — Không đưa tài sản nội bộ ra ngoài

**MUST NOT:**

- Đưa source code / tài liệu / requirement của tổ chức hay client lên **public repo** (GitHub public, Gist, Pastebin, CodeSandbox, StackBlitz, Replit…)
- Đưa lên **git cá nhân**, cloud cá nhân (Google Drive/Dropbox riêng), USB, email cá nhân
- Chia sẻ cho **bên thứ ba** (freelancer, forum, chat công khai) khi chưa có phê duyệt

**MUST:** chỉ làm việc trong **môi trường & tài khoản được tổ chức cấp phép**; khi rời project → xoá local copy, revoke access.

---

## 2. AI_TOOL_USAGE — Quy tắc dùng AI

**MUST NOT:**

- Dán **secret** (API key, token, password, private key, connection string) vào bất kỳ AI tool nào
- Dán **dữ liệu thật của client** (PII, payment, đơn hàng thật) vào AI tool bên ngoài — xem `POLICIES.md` §3.6
- Dán **toàn bộ tài liệu độc quyền của client** lên AI web chưa được duyệt
- Dùng output của AI mà không review nguồn gốc & license (§4)

**MAY (có điều kiện):**

- Dùng AI cho nội dung **generic** (cấu trúc tài liệu, wording, boilerplate không chứa domain data của KH)
- Dùng AI đã được tổ chức **duyệt & cấu hình** (enterprise / no-training / on-prem)
- **Che / thay thế** tên người, email, endpoint, dữ liệu thật bằng placeholder **trước khi** hỏi AI

**Áp dụng cụ thể cho kit này:**

- MCP servers khai trong `.claude/settings.json` = whitelist đã được phê duyệt — không tự thêm MCP mới khi chưa xin ý kiến
- ⚠️ **Figma MCP đẩy dữ liệu ra cloud bên ngoài** — mọi thứ vẽ lên frame coi như đã ra khỏi công ty (`POLICIES.md` §3.6)
- Không tạo public Gist / Sandbox từ nội dung trong workspace

---

## 3. SECRETS_MANAGEMENT — Quản lý bí mật

**MUST NOT:** hard-code secret trong file output; commit `.env` / keystore / service account JSON; log secret; gửi secret qua chat/email không mã hoá.

**MUST:** secret nằm trong **secret manager được cấp phép** (AWS Parameter Store hoặc tương đương), không trong git. Nếu lỡ commit → **rotate ngay** + report (§9) + xoá khỏi history.

Danh sách file cụ thể không được đọc → `SECURITY.md`.

---

## 4. THIRD_PARTY_CODE_&_LICENSE — Bản quyền

**Với BA kit, điểm chạm là HTML Prototype và Figma frame:**

**MUST NOT:**

- Chèn ảnh / icon / font **có bản quyền** vào prototype hoặc Figma frame mà chưa kiểm tra license
- Copy code từ internet / AI vào prototype mà không kiểm tra license
- Đưa nội dung có license không tương thích vào deliverable cho client

**MUST:** ưu tiên asset free-for-commercial (MIT / Apache-2.0 / CC0); ghi nguồn khi license yêu cầu attribution.

---

## 5. CLIENT_DATA_&_PRIVACY — Dữ liệu client & quyền riêng tư

> Chi tiết đầy đủ cho BA → `POLICIES.md` §3.6 + `.claude/rules/DATA-PRIVACY.md`.

**MUST NOT:**

- Copy **dữ liệu production thật** (user, đơn hàng, giao dịch, PII) về local để dựng mockup
- Chia sẻ database dump / export thật ra ngoài môi trường được duyệt
- Chụp màn hình chứa PII rồi gửi qua kênh không được duyệt (Slack public, chat cá nhân)
- Đăng nhập hệ thống của khách bằng **tài khoản thật** — yêu cầu tài khoản test

**MUST:** dùng **dữ liệu mẫu** (`DATA-PRIVACY.md` §4) cho mọi output; truy cập theo **least privilege**; tuân thủ yêu cầu bảo mật của thị trường target (Nhật/EU/US) — hỏi PM nếu chưa rõ.

---

## 6. ACCESS_CONTROL — Quản lý truy cập

**MUST:** dùng **account riêng**, bật **2FA/MFA**, access do tổ chức cấp, revoke ngay khi rời project.

**MUST NOT:** share credential, dùng lại credential cũ, để lộ token khi screen share / demo.

---

## 7. REPOSITORY_PROTECTION

**MUST:** repo tổ chức để **private** mặc định; nhánh chung được protect (require PR, no force-push); mọi thay đổi qua **PR**.

**MUST NOT:** đổi repo private → public khi chưa được duyệt; xoá lịch sử / force-push nhánh chung; skip hooks (`--no-verify`, `--no-gpg-sign`).

---

## 8. DELIVERABLE_HANDOFF — Bàn giao cho client

**MUST:**

- Chỉ bàn giao qua **kênh đã thoả thuận** với client (repo client, file server được duyệt)
- **Sanitize trước khi share**: SPEC.md / prototype / Figma frame không còn dữ liệu thật, không còn thông tin nội bộ (giá, man-month, ghi chú nội bộ)
- Chạy checklist bàn giao → `DATA-PRIVACY.md` §5, và quét: `node .claude/hooks/detect-pii.js --scan <output-folder>`
- Deliverable chỉ gửi đúng người có thẩm quyền phía client

**MUST NOT:** gửi qua email cá nhân, chat công khai, hoặc link public không giới hạn.

---

## 9. INCIDENT_REPORTING — Báo cáo sự cố

**MUST — nếu xảy ra (hoặc nghi ngờ):** lỡ đẩy dữ liệu thật lên Figma/Backlog/Slack/Drive, lỡ paste data thật vào AI, lỡ commit secret, mất thiết bị, lộ credential…

→ **Báo ngay** cho người phụ trách (không giấu, không chờ), sau đó:

1. Rotate secret bị lộ
2. Xoá/gỡ nội dung khỏi nơi đã đẩy lên — **bao gồm node trên Figma và snapshot trong `versions/`**
3. Đánh giá phạm vi ảnh hưởng
4. Ghi lại sự cố + biện pháp khắc phục

> ⚠️ **Ai làm 4 bước trên:** đây là quy trình của **con người phụ trách**, không phải việc AI tự thực hiện.
> AI dính incident thì **dừng + báo user + hỏi cách khắc phục** — **KHÔNG tự** rotate secret, **KHÔNG tự** xoá node Figma hay snapshot `versions/` (khó hoàn tác). Xem `POLICIES.md` §5 mức 4.

> Báo sớm **giảm thiệt hại**. Che giấu sự cố là vi phạm nghiêm trọng hơn bản thân lỗi.

---

## Bảng tóm tắt MUST NOT

| # | Tuyệt đối KHÔNG |
|---|---|
| 1 | Đưa code/tài liệu ra public repo, git cá nhân, cloud cá nhân |
| 2 | Paste secret / dữ liệu thật / tài liệu độc quyền vào AI chưa duyệt |
| 3 | Hard-code / commit secret |
| 4 | Dùng asset hoặc code không rõ license trong prototype/Figma |
| 5 | Copy dữ liệu production thật về local |
| 6 | Share account / tắt 2FA |
| 7 | Đổi repo private → public, force-push nhánh chung |
| 8 | Bàn giao qua kênh cá nhân/public, hoặc chưa sanitize |
| 9 | Giấu sự cố bảo mật |
