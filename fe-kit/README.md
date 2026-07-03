# Adapter: Claude (Claude Code / Cowork / claude.ai)

## 1. Installation

macOS/WSL

```python
curl -fsSL https://claude.ai/install.sh | bash
```

Windows PowerShell

```python
irm https://claude.ai/install.ps1 | iex
```

## 2. Prompt tạo CLAUDE.md cho codebase

<role>
Bạn là Tech Lead đang onboard một kỹ sư mới vào [CurrentProject] (công cụ lập kế hoạch mục tiêu theo trọng số của chúng tôi).
</role>

<context>
[User tự điền: mô tả [CurrentProject] làm gì, core logic, cách tính toán...]
</context>

<task>
Tạo file CLAUDE.md ở thư mục gốc.
Đồng thời, áp dụng progressive disclosure bằng cách tạo các file tài liệu riêng trong thư mục `.claude/docs/` cho từng mảng kỹ thuật chi tiết (ví dụ: `.claude/docs/architecture.md`, `.claude/docs/state_management.md`, `.claude/docs/date_logic.md`).
</task>

<requirements>
- CLAUDE.md tối đa 150 dòng. Chỉ tập trung vào thông tin áp dụng chung cho toàn dự án.
- Dùng Progressive Disclosure: Giữ CLAUDE.md thuần túy là file index và điều hướng ở mức tổng quan. Tách toàn bộ chi tiết kỹ thuật sâu, data model, cấu trúc component và logic phức tạp ra các file riêng có tên phù hợp trong `.claude/docs/`.
- Viết cho một agent/developer chưa từng thấy codebase này.
- Mọi mục phải actionable (hành động được), không trang trí.
</requirements>

Bao gồm chính xác các mục sau trong CLAUDE.md, theo đúng thứ tự này:

1. Project Overview: [CurrentProject] làm gì, trong 2-3 câu.
2. Tech Stack: liệt kê kèm version khi cần.
3. Dev Commands: cách cài đặt, chạy dev server, và build.
4. Core Logic Summary: tóm tắt ngắn gọn về cách tính trọng số.
5. Key Constraints: những thứ Claude tuyệt đối không được thay đổi hoặc tự suy diễn.
6. Additional Documentation: link trực tiếp tới các file domain cụ thể đã tạo trong thư mục `.claude/docs/`.

<tone>
Mang tính kỹ thuật. Trực diện. Không rườm rà. Không ngôn ngữ marketing.
</tone>

## 3. Đối ứng task với 1 command

Trong thư mục dự án đã có `CLAUDE.md`, gọi command tương ứng với task:

| Task        | Command            | Trigger khi                                  |
| ----------- | ------------------ | -------------------------------------------- |
| Feature mới | `/new-feature`     | Có story/issue cần build từ đầu              |
| Bug fix     | `/bug-fix`         | Có lỗi cần sửa                               |
| Code review | `/code-review`     | Có PR/changeset cần review trước merge       |
| Refactoring | `/refactoring`     | Cải cấu trúc code, không đổi hành vi         |
| Sinh test   | `/test-generation` | Cần bổ sung/tạo test cho feature hoặc module |

**Ví dụ:**

```
/new-feature Thêm trang profile: avatar upload, cập nhật họ tên/email, lưu qua Server Action.
```

```
/bug-fix Nút submit form checkout bị disabled sau lần submit đầu, không recover khi lỗi network.
```

```
/code-review
```

Claude sẽ tự điều phối toàn bộ pipeline: phân tích yêu cầu → thiết kế → implement → test → review. Hỏi lại nếu còn thông tin chưa đủ, đề xuất plan và chờ xác nhận trước khi viết code.

**Cấu trúc kit:**

```
.claude/
├── agents/          # 5 agent: analyst, architect, developer, tester, reviewer
├── commands/        # 5 workflow: new-feature, bug-fix, code-review, refactoring, test-generation
├── skills/          # ~90 skill theo prefix: react-*, nextjs-*, typescript-*, form-*, react-query-*, mui-*, tailwind-*, security-*, performance-*, testing-jest-*, ...
└── settings.local.json  # Git & security guardrails
```

## 4. Cài đặt FIGMA MCP: https://github.com/vkhanhqui/figma-mcp-go
