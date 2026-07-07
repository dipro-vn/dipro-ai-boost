# POLICY — Code Security & IP Protection Rules

> **Scope:** Áp dụng cho **mọi thành viên, mọi repo** trong dự án (backend / web / mobile / E2E / SRS / deliverable client).
> **Mục tiêu:** Bảo vệ source code, dữ liệu client, và IP của tổ chức — chống rò rỉ ra ngoài dưới mọi hình thức.
> **Mức độ:** Đây là rule **bắt buộc** (MUST). Vi phạm được coi là sự cố bảo mật, phải report ngay.
> **Từ khóa:** `MUST` = bắt buộc · `MUST NOT` = tuyệt đối cấm · `SHOULD` = nên · `MAY` = được phép có điều kiện.
> **Companion:** `POLICIES.md` (AI behavior), `SECURITY.md` (restricted files), `RELIABILITY.md` (no hallucination).

---

## 1. NO_CODE_EXFILTRATION — Không đưa code ra ngoài

**MUST NOT:**

- Clone, copy, crawl, scrape, hoặc mirror source code / repo của tổ chức hay client ra **bất kỳ nơi nào bên ngoài** hệ thống được cấp phép
- Push / upload code (một phần hoặc toàn bộ) lên **public repo** (GitHub public, GitLab public, Gist, Pastebin, CodeSandbox, StackBlitz, Replit…)
- Đưa code lên **git cá nhân**, cloud cá nhân (Google Drive/Dropbox riêng), USB, email cá nhân
- Paste code / config / schema vào **AI tool bên ngoài** (ChatGPT web, Claude web cá nhân, Copilot chưa được duyệt, v.v.) khi code đó là proprietary hoặc chứa business logic của client
- Chia sẻ code cho **bên thứ ba** (freelancer, bạn bè, forum, chat công khai) khi chưa có phê duyệt
- Fork repo tổ chức về **account cá nhân**

**MUST:**

- Chỉ làm việc với code trên **repo / môi trường được tổ chức cấp phép**
- Mọi bản sao code phải nằm trong **thiết bị & tài khoản được quản lý**
- Khi rời project / nghỉ việc → xóa toàn bộ local copy, revoke access

---

## 2. AI_TOOL_USAGE — Quy tắc dùng AI với code

**MUST NOT:**

- Dán **secret** (API key, token, password, private key, connection string) vào bất kỳ AI tool nào
- Dán **dữ liệu thật của client** (PII, dữ liệu payment, đơn hàng thật) vào AI tool bên ngoài
- Dán **business logic độc quyền** hoặc **toàn bộ file/module** của client lên AI web chưa duyệt
- Dùng output của AI mà **không review license & nguồn gốc** (xem mục 4)

**MAY (được phép có điều kiện):**

- Dùng AI cho **snippet generic** (thuật toán chung, boilerplate, regex, util không chứa domain data)
- Dùng AI đã được tổ chức **duyệt & cấu hình** (enterprise / no-training mode / on-prem)
- **Che / thay thế** tên biến, endpoint, dữ liệu thật bằng placeholder trước khi hỏi AI

**SHOULD:**

- Ưu tiên AI tool có chế độ **không dùng data để train** (Zero Data Retention / no-training)
- Ghi nhớ: **AI là công cụ hỗ trợ, không phải kênh lưu trữ code**

**Áp dụng cụ thể cho Claude Code trong kit này:**

- MCP servers khai trong `.claude/settings.json` = danh sách whitelist đã được tổ chức phê duyệt — không tự thêm MCP mới khi chưa xin ý kiến
- Không gửi source code ra qua MCP call đến service ngoài danh sách whitelist
- Không tạo public GitHub Gist / Sandbox từ code trong workspace

---

## 3. SECRETS_MANAGEMENT — Quản lý bí mật

**MUST NOT:**

- Hardcode secret trong source (API key, password, token, keystore password, signing key)
- Commit `.env`, `google-services.json` / `GoogleService-Info.plist`, keystore, `.p12`, `.pem`, service account JSON
- Log secret ra console / crash report / analytics
- Gửi secret qua chat / email không mã hóa

**MUST:**

- Secret nằm trong **AWS Parameter Store** (theo `stack-constraints.md`) hoặc secret manager tương đương được cấp phép — không trong git
- `.gitignore` phải chặn: `.env*`, keystore, `*.p12`, `*.pem`, `*.jks`, service account files
- Nếu lỡ commit secret → **rotate ngay** + report + xóa khỏi git history

Xem thêm: `SECURITY.md` (danh sách file cụ thể) + `security-rules.md` (best practice code).

---

## 4. THIRD_PARTY_CODE_&_LICENSE — Code ngoài & bản quyền

**MUST NOT:**

- Copy code từ internet / repo khác / AI mà **không kiểm tra license**
- Đưa code có license **không tương thích** (GPL/AGPL vào sản phẩm thương mại closed-source) mà chưa được duyệt
- Copy code có bản quyền của bên khác vào deliverable client

**MUST:**

- Kiểm tra license của **mọi package mới** trước khi thêm (MIT / BSD / Apache-2.0 an toàn cho thương mại)
- Ghi nguồn khi dùng snippet có license yêu cầu attribution
- Package mới đưa vào project phải được **duyệt** (không tự ý thêm dependency lạ) — Dev đề xuất Tech Lead trước khi `npm install` / `pub add` / `pod install`

---

## 5. CLIENT_DATA_&_PRIVACY — Dữ liệu client & quyền riêng tư

**MUST NOT:**

- Copy **dữ liệu production thật** (user, đơn hàng, giao dịch, PII) về máy local để test
- Chia sẻ database dump / export thật ra ngoài môi trường được duyệt
- Chụp màn hình chứa PII và gửi qua kênh không được duyệt (Slack public channel, Facebook chat...)

**MUST:**

- Test bằng **mock / seed / dữ liệu ẩn danh** — có helper trong repo hoặc hỏi Tech Lead
- Tuân thủ yêu cầu bảo mật dữ liệu của thị trường target (Nhật/EU/US) — hỏi PM nếu chưa rõ compliance requirement
- Truy cập dữ liệu client theo nguyên tắc **least privilege** (chỉ đủ để làm việc)

---

## 6. ACCESS_CONTROL — Quản lý truy cập

**MUST:**

- Dùng **account riêng của mỗi người**, không share credential
- Bật **2FA / MFA** cho git, cloud, AI enterprise, MCP tokens
- Access do tổ chức cấp — **không tự cấp / không mượn** account
- Revoke access ngay khi thành viên rời project

**MUST NOT:**

- Dùng chung account, dùng lại credential cũ, để lộ token trong screen share

---

## 7. REPOSITORY_&_BRANCH_PROTECTION

**MUST:**

- Repo tổ chức để **private** mặc định
- `main` / `master` / `develop` được **protect** (require PR + review, no force-push)
- Mọi thay đổi qua **PR**, có review — không push thẳng
- `.gitignore` chuẩn cho từng stack (NestJS / React / Flutter / RN) chặn build artifact, secret, node_modules, Pods, .dart_tool, target/

**MUST NOT:**

- Đổi repo private → public khi chưa được duyệt
- Xóa lịch sử / force-push lên nhánh chung
- Skip hooks (`--no-verify`, `--no-gpg-sign`) — xem `git-workflow.md`

---

## 8. DELIVERABLE_HANDOFF — Bàn giao cho client

**MUST:**

- Chỉ bàn giao qua **kênh được thỏa thuận** với client (repo client, file server được duyệt)
- Xóa secret / config nội bộ khỏi bản bàn giao (SPEC.md / DESIGN.md / PLAN.md sanitize trước khi share ra ngoài)
- Deliverable (SRS, source, doc) chỉ gửi đúng người có thẩm quyền phía client

**MUST NOT:**

- Gửi source/doc client qua email cá nhân, chat công khai, link public không giới hạn

---

## 9. INCIDENT_REPORTING — Báo cáo sự cố

**MUST — Nếu xảy ra (hoặc nghi ngờ):**

- Lỡ push code/secret lên public, lỡ paste data thật vào AI, mất thiết bị, lộ credential…

→ **Báo ngay** cho người phụ trách (không giấu, không chờ), sau đó:

1. Rotate secret bị lộ
2. Xóa/gỡ nội dung khỏi nơi công khai
3. Đánh giá phạm vi ảnh hưởng
4. Ghi lại sự cố + biện pháp khắc phục

> Báo sớm **giảm thiệt hại**. Che giấu sự cố là vi phạm nghiêm trọng hơn bản thân lỗi.

---

## Checklist tuân thủ nhanh

- [ ] Code chỉ nằm trên repo/môi trường được cấp phép
- [ ] Không có secret trong source / không commit `.env`, keystore, service account
- [ ] Không paste secret / data thật / module client vào AI bên ngoài
- [ ] Package mới đã kiểm tra license + được duyệt
- [ ] Test bằng mock/ẩn danh, không dùng data production thật
- [ ] Account riêng + 2FA bật
- [ ] Repo private, `main` được protect, mọi thay đổi qua PR
- [ ] Bàn giao đúng kênh được duyệt với client
- [ ] Sự cố bảo mật → report ngay

---

## Bảng tóm tắt MUST NOT (đọc nhanh)

| # | Tuyệt đối KHÔNG |
|---|---|
| 1 | Clone / crawl / push code ra public repo, git cá nhân, cloud cá nhân |
| 2 | Paste secret / data thật / code độc quyền vào AI chưa duyệt |
| 3 | Hardcode / commit secret |
| 4 | Dùng code/package không rõ license hoặc license không tương thích |
| 5 | Copy data production thật về local |
| 6 | Share account / tắt 2FA |
| 7 | Đổi repo private → public, force-push nhánh chung |
| 8 | Gửi deliverable client qua kênh cá nhân/public |
| 9 | Giấu sự cố bảo mật |
