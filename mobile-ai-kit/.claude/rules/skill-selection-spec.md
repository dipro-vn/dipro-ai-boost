# Skill Selection Spec — Quy trình chọn skill trước khi thực thi

> Không chỉ riêng bước code trong [Workflow dispatcher](../CLAUDE.md#6-workflow-theo-loại-task) — áp dụng ở BẤT KỲ bước nào cần thực thi một việc gắn với framework/ngôn ngữ/domain cụ thể (code, viết test, setup CI, codegen...), được tham chiếu từ hầu hết các file trong `.claude/workflows/`.

## 1. Xác định framework và yêu cầu của task

- Có `pubspec.yaml` ở root project → Flutter/Dart, theo [language](../CLAUDE.md#language) và [Coding Convention](../CLAUDE.md#reference-1).
- Có `package.json` với dependency `react-native` → React Native, theo `rules/project-base/reactNative_common_rules.md`.
- Nếu project setup cả hai (monorepo) → xác định theo path đang code (`lib/` → Flutter, `src/`/`app/` → RN); nếu vẫn chưa rõ, hỏi tôi.
- Xác định thêm yêu cầu cụ thể của task (UI, state management, network, testing, CI/CD...) để biết cần loại skill nào (không chỉ dừng ở tên framework).

## 2. Rà soát skill đã cài

- Liệt kê skill hiện có tại `.claude/skills/` (đối chiếu `skills-lock.json` để biết nguồn, mô tả).
- Nếu đã có skill phù hợp với framework + yêu cầu vừa xác định ở mục 1 → dùng luôn, không cần tìm thêm.

## 3. Nếu chưa có skill phù hợp

1. Dùng [find-skills](../skills/find-skills/SKILL.md): `npx skills find <từ khóa framework/domain>`.
2. Trình bày kết quả cho tôi: tên skill, nguồn (owner/repo), mô tả, lý do phù hợp với task hiện tại.
3. **CHỜ tôi xác nhận đồng ý** trước khi cài (`npx skills add <package>`) — không tự ý thêm skill mới vào project.
4. Nếu tôi từ chối hoặc không tìm được skill phù hợp → tiếp tục theo [coding convention](../CLAUDE.md#reference-1) hiện có, không vì thiếu skill mà block task.

## 4. Ghi chú

- Việc thêm skill mới coi như thay đổi dependency của project → áp dụng nguyên tắc xin approve giống [Planning Spec](planning-spec.md), dù task đang code có ở mức đơn giản hay không.
