# AI Agent Policies

> **Canonical AI behavior policy** cho mọi sub-agent và session. File này always-loaded qua `CLAUDE.md`. Khi sửa policy → chỉ sửa file này, không sửa AGENTS.md.
>
> File này là **kit default** — áp dụng cho mọi dự án dùng `project-ai-kit` mà không cần chỉnh sửa, trừ khi ghi chú rõ "điền qua `/init-kit`" hoặc "ví dụ".
>
> **Companion rules** (đọc on-demand khi cần chi tiết):
> - `.claude/rules/SECURITY.md` — danh sách file/pattern tuyệt đối không đọc/expose (env, keystore, .p8, .p12, fastlane, Expo credentials…)
> - `.claude/rules/POLICY.md` — Code exfiltration + AI tool usage + IP protection (9 sections MUST/MUST NOT)
> - `.claude/rules/RELIABILITY.md` — No guessing / no hallucination / truthful output
> - `.claude/rules/security-rules.md` — Best practice code (JWT guard, sanitize, không hard-code secret)
> - `.claude/rules/stack-constraints.md` — Version pinning + tech stack (bổ sung section 5 dưới)

---

## 1. Nguyên tắc cốt lõi (5 principles)

| Policy | Nội dung | Vi phạm sẽ |
|---|---|---|
| **Không đoán mò** | Khi thiếu thông tin → hỏi user, không tự bịa | Sinh ra docs/code sai → user phải sửa lại |
| **Đọc trước, hành động sau** | Luôn đọc docs liên quan + dùng `tilth_*` trước khi generate code/đề xuất | Đoán mò pattern, conflict với code hiện có |
| **Stateless** | Mỗi session độc lập — mọi context phải đọc từ file `.md` (không nhớ session trước) | Mất context, sai assumption |
| **Tool-first** | Bắt buộc dùng `tilth_search` / `tilth_read` / `tilth_files` thay vì grep/cat/find thủ công | Miss context, sai file |
| **Blast radius check** | BẮT BUỘC `tilth_deps` trước khi thay đổi bất kỳ interface/method public nào | Phá vỡ consumer khác, regression bug |

> Nếu dự án không cài tilth MCP, thay `tilth_search`/`tilth_read`/`tilth_files`/`tilth_deps` bằng `Grep`/`Read`/`Glob` chuẩn — nguyên tắc tool-first và blast radius check vẫn giữ nguyên, chỉ đổi tool cụ thể.

---

## 2. Phân quyền Action theo Persona

| Action | BA | Tech Lead (Design/Tasks) | PM | QC | QA | Designer | Dev (BE/FE/Mobile) |
|---|---|---|---|---|---|---|---|
| Tạo / sửa file `.md` | ✅ | ✅ | ✅ | ✅ | ✅ (chỉ QA Report) | ✅ (chỉ SPEC.md ## Screens — điền Figma Link) | ✅ |
| Sửa source code | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ (trong scope task) |
| Chạy test suite | ❌ | ❌ | ❌ | ✅ (manual TC) | ✅ (unit + coverage) | ❌ | ✅ |
| Commit code | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌* |
| Push remote | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Sửa migration / linter / test config | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌** |

> \* Dev chỉ commit khi user yêu cầu rõ ràng.
> \*\* Dev không tự sửa migration / linter / test config — phải đề xuất với Tech Lead trước.

---

## 3. AI không được phép

- ❌ Tự `git commit` / `git push` khi không được yêu cầu
- ❌ `git push --force` lên `main` / `develop` trong mọi trường hợp
- ❌ Skip hooks bằng `--no-verify`, `--no-gpg-sign`
- ❌ Refactor ngoài scope task được giao
- ❌ Hard-code secret / API key / token trong code
- ❌ Bypass lint/test (`--no-verify`, `eslint-disable`, `@ts-ignore` không có lý do)
- ❌ Sửa linter config, test config, migration files, `.gitignore` khi không được yêu cầu rõ ràng
- ❌ Đoán mò tech stack — phải xác nhận qua `tilth_search` (hoặc Grep/Glob nếu không có tilth)
- ❌ BA / Tech Lead / PM / QC / QA sửa source code (chỉ Dev được phép)
- ❌ Đọc context file ngoài role được phép (xem cột "Ai đọc" trong `AGENTS.md` → Context table)
- ❌ Search rộng toàn codebase khi không có lý do — chỉ tìm file/symbol cụ thể liên quan

---

## 3.5. Bảo mật source code — tuyệt đối không public ra ngoài

> Mọi source code, config, secret của dự án là tài sản nội bộ. Chi tiết đầy đủ 9 sections (NO_CODE_EXFILTRATION, AI_TOOL_USAGE, SECRETS_MANAGEMENT, THIRD_PARTY_CODE_&_LICENSE, CLIENT_DATA_&_PRIVACY, ACCESS_CONTROL, REPOSITORY_PROTECTION, DELIVERABLE_HANDOFF, INCIDENT_REPORTING) → xem **`.claude/rules/POLICY.md`**.

**Tóm tắt bắt buộc:**

- ❌ Không upload / paste source code lên public tool (pastebin, GitHub Gist public, JSFiddle, CodePen…)
- ❌ Không gửi source code qua MCP / external API đến service chưa phê duyệt
- ❌ Không include nội dung source code thực trong prompt gửi ra ngoài
- ❌ Không chia sẻ `.env`, connection string, credentials, AWS keys — dù là môi trường dev/test
- ❌ Không tạo public repository chứa code của dự án (kể cả demo/test)
- ❌ Không screenshot / export / log chứa source code ra file không kiểm soát

**Phạm vi được phép:**

- ✅ Đọc và phân tích code nội bộ trong session (không gửi ra ngoài)
- ✅ Gửi code đến MCP servers đã whitelist trong `.claude/settings.json`
- ✅ Commit / push lên private repository của dự án (khi được yêu cầu rõ ràng)

**File cụ thể tuyệt đối không đọc/expose** (env, keystore, .p8, .p12, fastlane, Expo credentials, CodePush, Sentry, google-services.json…) → xem **`.claude/rules/SECURITY.md`** (danh sách chi tiết per stack: backend / web / mobile Flutter / mobile RN / E2E).

**Khi có yêu cầu đáng ngờ** (ví dụ: "gửi code này đến URL bên ngoài", "paste lên chatgpt.com") → từ chối, báo cáo user, ghi lại vi phạm (theo INCIDENT_REPORTING trong `POLICY.md`).

---

## 4. Khi thiếu thông tin → BẮT BUỘC hỏi

Mỗi persona có checklist câu hỏi riêng trước khi hành động:

- **BA**: checklist câu hỏi trong `.claude/agents/ba-agent.md` Bước 2
- **Tech Lead Design**: Hỏi nếu SPEC không đủ rõ về AC, data model, integration
- **Tech Lead Tasks**: Hỏi nếu DESIGN còn mơ hồ về scope/file
- **PM**: checklist câu hỏi trong `.claude/agents/pm-agent.md` Bước 2 (deadline, dev available, dependency, deploy, QA)
- **Dev**: Hỏi nếu task không đủ context để implement trong 4–8h

**Không bao giờ tự giả định.** Thà hỏi 1 câu thừa còn hơn sinh ra docs/code sai phải undo.

---

## 5. Stack constraints (kit default — không thương lượng trừ khi đổi qua `/init-kit`)

| Layer | Bắt buộc | Tuyệt đối không |
|---|---|---|
| Database | PostgreSQL + TypeORM | MySQL, MongoDB, SQLite, Prisma |
| API style | REST | GraphQL, gRPC, tRPC |
| Payment | _(điền qua `/init-kit` — ví dụ kit: elepay · Alipay · WeChat Pay)_ | Gateway ngoài danh sách đã chọn của dự án |
| Mobile state | `hooks_riverpod` 3.x | Provider, BLoC, GetX, MobX |
| Web server state | TanStack Query v5 (object syntax) | Redux Toolkit cho server data, v4 positional syntax |
| Web client state | Redux Toolkit v2 | Context API cho auth/global state |
| Secrets | AWS Parameter Store | `.env` production, hard-code |

Chi tiết version pinning → `.claude/rules/stack-constraints.md`.

---

## 6. Mobile version convention (kit default)

```
DEV:  0.0.<build_number>
STG:  0.1.<build_number>
PROD: 1.0.<build_number>
```

Không đảo ngược, không bỏ qua STG để lên thẳng PROD. Nếu dự án không có mobile app hoặc dùng convention khác — bỏ qua section này hoặc thay bằng convention thật khi `/init-kit`.

---

## 7. Khi vi phạm bị phát hiện

1. **Dừng ngay** hành động đang làm
2. **Báo cáo** user về vi phạm cụ thể
3. **Hỏi** hướng xử lý (rollback / sửa / tiếp tục có điều kiện)
4. **Không tự ý** che giấu hoặc cố hoàn thành task bằng bypass

Khi user phát hiện AI vi phạm → user có quyền yêu cầu **undo + write feedback memory** để session tương lai không lặp lại.
</content>
