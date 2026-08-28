export const meta = {
  name: 'bmad-build-phase',
  description: 'BMAD Build+Verify+Test phase — Backend (loop với QA tới khi sạch bug) → Frontend/Mobile song song (loop với QA tới khi sạch bug) → QC (checklist + automation song song). Chạy sau khi bmad-plan-phase đã được user duyệt.',
  phases: [
    { title: 'Backend', detail: 'Backend implement → QA verify → loop fix tới khi PASS (tối đa 3 lần)' },
    { title: 'Frontend/Mobile', detail: 'Song song, dùng API Contract + design-analysis.md → QA verify → loop fix tới khi PASS (tối đa 3 lần)' },
    { title: 'QC', detail: 'Execution checklist + E2E automation — song song' },
  ],
}

if (!args?.feature) {
  throw new Error('Thiếu args.feature — cần tên feature (kebab-case) để chạy pipeline')
}

const MAX_ITERATIONS = 3
const STOP_INSTRUCTION =
  'Sau khi in Output, DỪNG LẠI — không hỏi thêm câu hỏi xác nhận bước tiếp theo (vd "bạn có muốn tôi tiếp tục không?").'

const QA_SCHEMA = {
  type: 'object',
  properties: {
    status: { type: 'string', enum: ['PASS', 'FAIL'] },
    issues: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          summary: { type: 'string' },
          file: { type: 'string' },
          severity: { type: 'string' },
        },
        required: ['summary'],
      },
    },
  },
  required: ['status', 'issues'],
}

// ---------- Backend: implement → QA verify → loop fix tới khi PASS ----------
phase('Backend')

let be = await agent(
  `Đọc .claude/agents/backend-agent.md rồi đóng vai Backend Developer, implement các task Phase 1→2 (DB migration + API) ` +
  `cho feature "${args.feature}" — task files nằm trong <DOCS_ROOT>/features/${args.feature}/<backend-repo>/tasks/ ` +
  `(xem <DOCS_ROOT> thật và tên repo vai trò backend trong AGENTS.md section Ecosystem). ` +
  `Output PHẢI kèm bảng API Contract đầy đủ (method, path, request, response). ${STOP_INSTRUCTION}`,
  { agentType: 'backend-agent', label: 'backend-agent' }
)
log('Backend implement xong.')

let beQa = await agent(
  `Đọc .claude/agents/qa-agent.md rồi đóng vai QA, verify CHỈ các task Backend (Phase 1→2) vừa implement cho feature "${args.feature}" ` +
  `— unit test, coverage, Acceptance Criteria liên quan BE, non-regression. CHƯA xét Frontend/Mobile vì chưa implement. ` +
  `Trả về status PASS nếu không còn issue nào cần fix, FAIL kèm issues cụ thể (file + mô tả) nếu còn bug.`,
  { agentType: 'qa-agent', label: 'qa-agent:backend', schema: QA_SCHEMA }
)

let beIteration = 0
while ((!beQa || beQa.status === 'FAIL') && beIteration < MAX_ITERATIONS) {
  beIteration++
  log(`Backend QA FAIL (lần ${beIteration}/${MAX_ITERATIONS}) — quay lại backend-agent fix.`)
  be = await agent(
    `Đọc .claude/agents/backend-agent.md rồi đóng vai Backend Developer, sửa các bug sau do QA phát hiện cho feature "${args.feature}":\n` +
    `${JSON.stringify(beQa?.issues ?? [])}\n` +
    `Sau khi sửa xong, in lại Output đầy đủ (kèm bảng API Contract cập nhật nếu có thay đổi). ${STOP_INSTRUCTION}`,
    { agentType: 'backend-agent', label: `backend-agent:fix-${beIteration}` }
  )
  beQa = await agent(
    `Đọc .claude/agents/qa-agent.md rồi đóng vai QA, verify lại CHỈ các task Backend (Phase 1→2) cho feature "${args.feature}" ` +
    `sau khi dev vừa fix issues sau:\n${JSON.stringify(beQa?.issues ?? [])}`,
    { agentType: 'qa-agent', label: `qa-agent:backend-${beIteration}`, schema: QA_SCHEMA }
  )
}

if (!beQa || beQa.status !== 'PASS') {
  log(`Backend QA vẫn chưa PASS sau ${MAX_ITERATIONS} lần fix — dừng workflow, cần user quyết định hướng xử lý.`)
  return {
    feature: args.feature,
    needsUserInput: true,
    stage: 'backend',
    iterations: { backend: beIteration },
    be,
    qa: beQa,
  }
}
log('Backend QA PASS — chuyển sang Frontend/Mobile.')

// ---------- Frontend/Mobile: implement → QA verify → loop fix tới khi PASS ----------
phase('Frontend/Mobile')

const designAnalysisPath = `<DOCS_ROOT>/features/${args.feature}/design-analysis.md`

let [fe, mobile] = await parallel([
  () =>
    agent(
      `Đọc .claude/agents/frontend-agent.md rồi đóng vai Frontend Developer, implement task Phase 3 cho feature "${args.feature}" ` +
      `— áp dụng cho tất cả repo vai trò frontend liên quan tới feature này (xem AGENTS.md Ecosystem). ` +
      `Trước khi code: (1) paste bảng API Contract sau vào section "## API Contract" của task file Phase 3 tương ứng ` +
      `(giữ đúng bước 5b trong AGENTS.md — FE không tự đoán endpoint):\n${JSON.stringify(be)}\n` +
      `(2) đọc "${designAnalysisPath}" (output của design-analyst-agent — screens đã phân tích + bảng asset export) nếu file tồn tại, ` +
      `dùng làm nguồn design chính. Rồi mới implement theo Step1→Step2→Step3. ${STOP_INSTRUCTION}`,
      { agentType: 'frontend-agent', label: 'frontend-agent', phase: 'Frontend/Mobile' }
    ),
  () =>
    agent(
      `Đọc .claude/agents/mobile-agent.md rồi đóng vai Mobile Developer, implement task Phase 3 cho feature "${args.feature}" ` +
      `(bỏ qua và trả về "no mobile scope" nếu dự án không có repo vai trò mobile, hoặc feature này không chạm repo đó). ` +
      `Trước khi code: (1) paste bảng API Contract sau vào section "## API Contract" của task file Phase 3 tương ứng:\n${JSON.stringify(be)}\n` +
      `(2) đọc "${designAnalysisPath}" (output của design-analyst-agent) nếu file tồn tại, dùng làm nguồn design chính. Rồi mới implement. ${STOP_INSTRUCTION}`,
      { agentType: 'mobile-agent', label: 'mobile-agent', phase: 'Frontend/Mobile' }
    ),
])
log('Frontend/Mobile implement xong.')

let finalQa = await agent(
  `Đọc .claude/agents/qa-agent.md rồi đóng vai QA, verify TOÀN BỘ feature "${args.feature}" ` +
  `(Backend đã PASS từ trước + Frontend/Mobile vừa implement) — unit test, coverage, Acceptance Criteria, non-regression.`,
  { agentType: 'qa-agent', label: 'qa-agent:final', schema: QA_SCHEMA }
)

let feIteration = 0
while ((!finalQa || finalQa.status === 'FAIL') && feIteration < MAX_ITERATIONS) {
  feIteration++
  log(`Final QA FAIL (lần ${feIteration}/${MAX_ITERATIONS}) — quay lại Frontend/Mobile fix.`)
  const fixIssues = JSON.stringify(finalQa?.issues ?? [])
  ;[fe, mobile] = await parallel([
    () =>
      agent(
        `Đọc .claude/agents/frontend-agent.md rồi đóng vai Frontend Developer, sửa các bug sau do QA phát hiện cho feature "${args.feature}" ` +
        `(chỉ sửa issue thuộc phạm vi frontend — bỏ qua issue không liên quan):\n${fixIssues}\n${STOP_INSTRUCTION}`,
        { agentType: 'frontend-agent', label: `frontend-agent:fix-${feIteration}`, phase: 'Frontend/Mobile' }
      ),
    () =>
      agent(
        `Đọc .claude/agents/mobile-agent.md rồi đóng vai Mobile Developer, sửa các bug sau do QA phát hiện cho feature "${args.feature}" ` +
        `(chỉ sửa issue thuộc phạm vi mobile — bỏ qua issue không liên quan, hoặc trả về "no mobile scope" nếu dự án không có repo mobile):\n${fixIssues}\n${STOP_INSTRUCTION}`,
        { agentType: 'mobile-agent', label: `mobile-agent:fix-${feIteration}`, phase: 'Frontend/Mobile' }
      ),
  ])
  finalQa = await agent(
    `Đọc .claude/agents/qa-agent.md rồi đóng vai QA, verify lại TOÀN BỘ feature "${args.feature}" sau khi dev vừa fix issues sau:\n${fixIssues}`,
    { agentType: 'qa-agent', label: `qa-agent:final-${feIteration}`, schema: QA_SCHEMA }
  )
}

if (!finalQa || finalQa.status !== 'PASS') {
  log(`Final QA vẫn chưa PASS sau ${MAX_ITERATIONS} lần fix — dừng workflow, cần user quyết định hướng xử lý.`)
  return {
    feature: args.feature,
    needsUserInput: true,
    stage: 'frontend-mobile',
    iterations: { backend: beIteration, feMobile: feIteration },
    be,
    fe,
    mobile,
    qa: finalQa,
  }
}
log('Final QA PASS — chuyển sang QC.')

// ---------- QC ----------
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

return {
  feature: args.feature,
  be,
  fe,
  mobile,
  qa: finalQa,
  checklist,
  automation,
  iterations: { backend: beIteration, feMobile: feIteration },
}
