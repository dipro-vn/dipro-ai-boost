export const meta = {
  name: 'bmad-plan-phase',
  description: 'BMAD Planning phase — BA → Design (Tech Lead/QC/Designer song song) → Tech Lead Tasks. Dừng lại chờ user duyệt trước khi chạy bmad-build-phase. Không bao gồm PM.',
  phases: [
    { title: 'BA', detail: 'Phân tích yêu cầu, tạo SPEC.md' },
    { title: 'Design', detail: 'Tech Lead + QC manual TC + Designer Figma — chạy song song' },
    { title: 'Tasks', detail: 'Phân rã Design-Technical.md thành task files' },
  ],
}

if (!args?.feature) {
  throw new Error('Thiếu args.feature — cần tên feature (kebab-case) để chạy pipeline')
}

phase('BA')
const spec = await agent(
  `Đọc .claude/agents/ba-agent.md rồi đóng vai BA, tạo SPEC.md cho feature "${args.feature}". ` +
  `Mô tả thêm: ${args.description || '(không có — nếu thiếu thông tin bắt buộc để hoàn thành SPEC thì hỏi lại, không tự giả định)'}`,
  { agentType: 'ba-agent', label: 'ba-agent' }
)
log('BA xong: SPEC.md đã tạo')

phase('Design')
const [design, testcases, ui] = await parallel([
  () => agent(
    `Đọc .claude/agents/techlead-design-agent.md rồi đóng vai Tech Lead, tạo Design-Technical.md per repo từ SPEC.md của feature "${args.feature}"`,
    { agentType: 'techlead-design-agent', label: 'techlead-design-agent', phase: 'Design' }
  ),
  () => agent(
    `Đọc .claude/agents/qc-agent.md rồi đóng vai QC, sinh manual test cases (RBT) từ SPEC.md của feature "${args.feature}"`,
    { agentType: 'qc-agent', label: 'qc-agent', phase: 'Design' }
  ),
  () => agent(
    `Đọc .claude/agents/designer-agent.md rồi đóng vai Designer, tạo Figma screens + điền Figma URL vào SPEC.md ## Screens cho feature "${args.feature}"`,
    { agentType: 'designer-agent', label: 'designer-agent', phase: 'Design' }
  ),
])
log('Design phase xong: Design-Technical.md (per repo) + test cases + Figma screens')

phase('Tasks')
const tasks = await agent(
  `Đọc .claude/agents/techlead-tasks-agent.md rồi đóng vai Tech Lead Tasks, phân rã Design-Technical.md thành task files cho feature "${args.feature}"`,
  { agentType: 'techlead-tasks-agent', label: 'techlead-tasks-agent' }
)
log('Tasks xong: task files đã tạo')

return {
  feature: args.feature,
  spec,
  design,
  testcases,
  ui,
  tasks,
  gate:
    `⏸ GATE — Planning phase xong (SPEC + DESIGN + test cases + Figma + tasks) cho feature "${args.feature}". ` +
    `Review toàn bộ output trước. Khi đã duyệt, chạy: /create-feature ${args.feature} build`,
}
