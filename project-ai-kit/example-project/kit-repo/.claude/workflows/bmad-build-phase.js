export const meta = {
  name: 'bmad-build-phase',
  description: 'BMAD Build+Verify+Test phase — Dev (Backend trước, Frontend/Mobile song song sau) → QA verify → QC (checklist + automation song song). Chạy sau khi bmad-plan-phase đã được user duyệt.',
  phases: [
    { title: 'Dev', detail: 'Backend trước (API Contract), Frontend/Mobile song song sau đó' },
    { title: 'QA', detail: 'Verify AC + coverage + non-regression' },
    { title: 'QC', detail: 'Execution checklist + E2E automation — song song' },
  ],
}

if (!args?.feature) {
  throw new Error('Thiếu args.feature — cần tên feature (kebab-case) để chạy pipeline')
}

phase('Dev')
const be = await agent(
  `Đọc .claude/agents/backend-agent.md rồi đóng vai Backend Developer, implement các task Phase 1→2 (DB migration + API) ` +
  `cho feature "${args.feature}" — task files nằm trong <DOCS_ROOT>/features/${args.feature}/<backend-repo>/tasks/ ` +
  `(xem <DOCS_ROOT> thật và tên repo vai trò backend trong AGENTS.md section Ecosystem). ` +
  `Output PHẢI kèm bảng API Contract đầy đủ (method, path, request, response).`,
  { agentType: 'backend-agent', label: 'backend-agent' }
)
log('Backend xong.')

const [fe, mobile] = await parallel([
  () =>
    agent(
      `Đọc .claude/agents/frontend-agent.md rồi đóng vai Frontend Developer, implement task Phase 3 cho feature "${args.feature}" ` +
      `— áp dụng cho tất cả repo vai trò frontend liên quan tới feature này (xem AGENTS.md Ecosystem). ` +
      `Trước khi code, paste bảng API Contract sau vào section "## API Contract" của task file Phase 3 tương ứng ` +
      `(giữ đúng bước 5b trong AGENTS.md — FE không tự đoán endpoint), rồi mới implement theo Step1→Step2→Step3:\n${JSON.stringify(be)}`,
      { agentType: 'frontend-agent', label: 'frontend-agent', phase: 'Dev' }
    ),
  () =>
    agent(
      `Đọc .claude/agents/mobile-agent.md rồi đóng vai Mobile Developer, implement task Phase 3 cho feature "${args.feature}" ` +
      `(bỏ qua và trả về "no mobile scope" nếu dự án không có repo vai trò mobile, hoặc feature này không chạm repo đó). ` +
      `Trước khi code, paste bảng API Contract sau vào section "## API Contract" của task file Phase 3 tương ứng, rồi mới implement:\n${JSON.stringify(be)}`,
      { agentType: 'mobile-agent', label: 'mobile-agent', phase: 'Dev' }
    ),
])

phase('QA')
const qa = await agent(
  `Đọc .claude/agents/qa-agent.md rồi đóng vai QA, verify toàn bộ task vừa implement cho feature "${args.feature}" — ` +
  `unit test, coverage, Acceptance Criteria, non-regression`,
  { agentType: 'qa-agent', label: 'qa-agent' }
)
log(qa?.status === 'FAIL' ? 'QA FAIL — cần dev fix và re-run trước khi release' : 'QA xong')

phase('QC')
const [checklist, automation] = await parallel([
  () =>
    agent(
      `Đọc .claude/agents/qc-agent.md rồi đóng vai QC, sinh test execution checklist trước release cho feature "${args.feature}"`,
      { agentType: 'qc-agent', label: 'qc-agent', phase: 'QC' }
    ),
  () =>
    agent(
      `Đọc .claude/agents/qc-automation-agent.md rồi đóng vai QC Automation, test feature "${args.feature}" bằng Playwright E2E (headed mode). ` +
      `Nếu chưa có repo E2E testing (xem section "E2E Testing" trong AGENTS.md) hoặc website DEV chưa chạy → dừng lại, báo rõ điều kiện còn thiếu thay vì đoán.`,
      { agentType: 'qc-automation-agent', label: 'qc-automation-agent', phase: 'QC' }
    ),
])

return { feature: args.feature, be, fe, mobile, qa, checklist, automation }
