# Git Workflow

## Quy tắc cơ bản

- **Không auto-commit**: Không chạy `git commit` hay `git push` khi chưa được user yêu cầu rõ ràng
- **Không force push**: Không `git push --force` lên `main`/`develop` trong bất kỳ trường hợp nào
- **Không skip hooks**: Không `--no-verify`, không bypass pre-commit hook

## Branch Naming Convention

```
feat/<STORY-ID>_<short-description>     # ví dụ: feat/01-DEV-001_company-account
fix/<STORY-ID>_<short-description>      # ví dụ: fix/01-DEV-042_order-pagination
chore/<description>                     # ví dụ: chore/update-dependencies
```

`<STORY-ID>` = Backlog issue ID (ví dụ: `01-DEV-001`)

## Commit Message Format

```
<type>(<scope>): <subject> (#<STORY-ID>)

[body — optional, nếu cần giải thích WHY]
```

**Types:** `feat` · `fix` · `chore` · `refactor` · `test` · `docs`

**Scope:** tên module hoặc component — ví dụ `order`, `auth`, `OrderCard`

**Ví dụ:**
```
feat(order): add bulk cancel endpoint for admin (#01-DEV-001)
fix(auth): handle expired JWT refresh token edge case (#01-DEV-042)
chore(deps): upgrade TypeORM to 0.3.20
```

## Pull Request

**Creator checklist:**
- [ ] Branch name đúng convention `feat/<STORY-ID>_description`
- [ ] Commit message đúng format, có `(#STORY-ID)`
- [ ] PR title: `[STORY-ID] mô tả`
- [ ] PR description có Backlog story/task link
- [ ] Không có `console.log` / `debugPrint` / debug code
- [ ] Không expose secret / API key trong code
- [ ] UI đúng với design (Figma / mockup) nếu có thay đổi UI
- [ ] Pass CI trước khi request review

**Reviewer checklist:**
- [ ] Screenshot / screen recording đính kèm nếu có thay đổi UI
- [ ] Resolve hết comment trước khi merge
- [ ] Cần ít nhất 1 reviewer approve

## Merge Freeze

Không merge non-critical PR trong thời gian freeze release (hỏi PM về lịch freeze trước khi tạo PR lớn).

---

## Enforcement — Hooks

Các rule sau được enforce cứng bằng hook (không chỉ soft rule trong prompt):

| Hook | Rule enforce | Cơ chế |
|---|---|---|
| **H02** | Không `git push --force` lên `main` / `develop` / `master` / `release/*` | `.claude/hooks/guard-bash.js` — chặn tại PreToolUse Bash |
| **H03** | Không `--no-verify`, `--no-gpg-sign`, `-c commit.gpgsign=false` | `.claude/hooks/guard-bash.js` — chặn tại PreToolUse Bash |
| **H04** | Không `rm -rf` trên `/`, `~`, `$HOME`, wildcard | `.claude/hooks/guard-bash.js` — chặn tại PreToolUse Bash |

→ Khi vi phạm, tool call bị `exit 2` và trả lỗi ngay cho AI. Muốn xem chi tiết: đọc `.claude/hooks/guard-bash.js`.
