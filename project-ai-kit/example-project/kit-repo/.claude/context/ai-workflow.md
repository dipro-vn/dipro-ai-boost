# AI Workflow Setup Guide

# Overview

This document describes a professional AI Agent workflow architecture using Claude AI for:
- Requirement analysis
- Figma/UI understanding
- Code generation
- Task breakdown
- Multi-agent development workflow
- Architecture generation
- QA automation
- DevOps support

---

# 1. High-Level Architecture

```txt
Client
   ↓
AI Gateway
   ↓
Claude API
   ↓
Agent System
   ├── Context Engine
   ├── Memory
   ├── Tool Calling
   ├── RAG
   └── Workflow Engine
```

---

# 2. Recommended Project Structure

```txt
project-root/
│
├── .claude/
│   ├── agents/
│   ├── commands/
│   ├── rules/
│   ├── context/
│   ├── memory/
│   ├── workflows/
│   └── settings.local.json
│
├── docs/
│   ├── requirements/
│   ├── architecture/
│   ├── api/
│   └── business/
│
├── figma/
│   ├── exported-images/
│   ├── design-tokens.json
│   ├── component-map.json
│   └── figma-links.md
│
├── frontend/
├── backend/
├── database/
└── scripts/
```

---

# 3. Context System

## Purpose

Context allows AI Agents to understand:
- business logic
- project architecture
- coding standards
- reusable patterns
- existing APIs
- database structure
- UI system

---

# 4. Context Folder Structure

```txt
.claude/context/
├── project-overview.md
├── business-rules.md
├── coding-rules.md
├── architecture.md
├── folder-structure.md
├── ui-guidelines.md
├── api-standards.md
├── db-schema.md
└── reusable-components.md
```

---

# 5. Example Project Overview

```md
# Project Overview

Project: AI Metaverse Platform

Frontend:
- ReactJS
- TypeScript
- Redux Toolkit

Backend:
- NodeJS
- MongoDB

Features:
- Meeting
- Wallet
- AI Chatbot
- Avatar System
```

---

# 6. Coding Rules

## Example

```md
# Coding Rules

- Use TypeScript only
- Functional component only
- Use RTK Query
- No inline CSS
- Use TailwindCSS
- Feature-based architecture
```

---

# 7. Requirement Structure

```txt
docs/requirements/
├── brd.md
├── srs.md
├── user-stories.md
├── acceptance-criteria.md
└── roadmap.md
```

---

# 8. Example User Story

```md
# User Story

As a user,
I want to login with Google,
So that I can access the platform quickly.

Acceptance Criteria:
- OAuth login
- Save profile
- Redirect dashboard
```

---

# 9. Figma Workflow

## Recommended Flow

```txt
Figma
↓
Export PNG Screens
↓
Export Design Tokens
↓
Generate Component Mapping
↓
AI Context Processing
```

---

# 10. Figma Folder Structure

```txt
figma/
├── exported-images/
├── design-tokens.json
├── component-map.json
└── figma-links.md
```

---

# 11. Exported Design Tokens Example

```json
{
  "colors": {
    "primary": "#4F46E5",
    "secondary": "#9333EA"
  },
  "spacing": {
    "md": "16px"
  },
  "radius": {
    "lg": "12px"
  }
}
```

---

# 12. Component Mapping Example

```json
{
  "login-page": {
    "components": [
      "email-input",
      "password-input",
      "login-button"
    ],
    "api": "/api/auth/login"
  }
}
```

---

# 13. Agent Architecture — Kit Default

```txt
.claude/agents/
├── init-agent.md             ← Kit Setup Assistant: điền AGENTS.md (chạy 1 lần)
├── ba-agent.md                ← Business Analyst: SPEC.md
├── techlead-design-agent.md   ← Tech Lead Design: DESIGN.md per repo
├── techlead-tasks-agent.md    ← Tech Lead Tasks: task-x-y.md
├── backend-agent.md           ← Backend Developer (repo vai trò `backend`)
├── frontend-agent.md          ← Frontend Developer (repo vai trò `frontend`)
├── mobile-agent.md            ← Mobile Developer (repo vai trò `mobile`)
├── designer-agent.md          ← UI Designer: Figma frames + URL vào SPEC.md
├── qc-agent.md                ← QC Manual Tester: test cases + bug report
├── qa-agent.md                ← QA Engineer: verify AC + non-regression (ngoài pipeline, gọi thủ công)
└── qc-automation-agent.md     ← QC Automation: Playwright E2E
```

Slash commands (user-facing shortcuts, không thay thế agent files):
```txt
.claude/commands/
├── init-kit.md          → triggers init-agent workflow
├── create-spec.md       → triggers ba-agent workflow
├── create-design.md     → triggers techlead-design-agent workflow
├── create-tasks.md      → triggers techlead-tasks-agent workflow
├── generate-api.md      → backend scaffold
├── create-component.md  → frontend scaffold
└── review-code.md       → code review
```

---

# 14. Frontend Agent Example

```md
# Frontend Agent

Responsibilities:
- Build React UI
- Follow Figma
- Reuse components
- Follow coding rules

Stack:
- React
- TypeScript
- TailwindCSS
```

---

# 15. Command System

```txt
.claude/commands/
├── create-page.md
├── create-api.md
├── generate-task.md
├── refactor.md
└── create-component.md
```

---

# 16. Command Example

```md
# Create Component

Input:
- component name

Output:
- TSX
- SCSS
- Test file
- Storybook
```

---

# 17. Memory System

## Purpose

Memory allows AI to remember:
- business decisions
- architecture decisions
- sprint history
- reusable patterns

---

# 18. Memory Structure

```txt
.claude/memory/
├── decisions/
├── sprint-history/
├── architecture-history/
└── reusable-patterns/
```

---

# 19. Tool Calling Architecture

```txt
Claude
   ↓
MCP Server
   ├── File Tool
   ├── Git Tool
   ├── Database Tool
   ├── Browser Tool
   └── Figma Tool
```

---

# 20. Recommended MCP Tools

| Tool | Purpose |
|---|---|
| Filesystem | Read/write project |
| Git | Commit/review changes |
| Database | Query schemas |
| Browser | Open websites |
| Figma API | Read UI design |
| Swagger | API understanding |

---

# 21. RAG Architecture

## Purpose

Allow AI to search large codebases semantically.

```txt
Codebase
↓
Embedding
↓
Vector Database
↓
Semantic Search
↓
Claude AI
```

---

# 22. Recommended RAG Stack

| Component | Tool |
|---|---|
| Embedding | OpenAI / Voyage |
| Vector DB | Pinecone / Chroma |
| Framework | LlamaIndex |
| Workflow | LangGraph |

---

# 23. Workflow Engine — BMAD Pipeline (Kit Default)

```txt
Requirement
↓
ba-agent  →  SPEC.md
↓
[song song]
  techlead-design-agent  →  DESIGN.md per repo
  qc-agent               →  test-cases/tc_*.md
  designer-agent         →  Figma frames + URL vào SPEC.md ## Screens
↓
techlead-tasks-agent  →  tasks/task-x-y.md
  Phase 1,2: template BE tasks
  Phase 3:   template FE/Mobile tasks — có ## API Contract sẵn
↓
CONTRACT LOCK (BE + FE + Mobile + PM confirm REST endpoints / WebSocket / Push)
↓
Phase 1-2: backend-agent
  task-1-x  DB migration
  task-2-x  API endpoint  →  output: ## API Contract (method/path/request/response)
↓
[copy API Contract vào task-3-x.md trước khi FE bắt đầu]
↓
Phase 3 [song song]:
  frontend-agent:
    Step 1  tạo service file  (gọi đúng endpoint trong API Contract)
    Step 2  tạo TanStack Query hooks
    Step 3  wire UI + integration check localhost
  mobile-agent:
    Step 1  tạo repository/service
    Step 2  tạo Riverpod provider
    Step 3  wire screen + integration check localhost
↓
Phase 4: qc-automation-agent  →  Playwright E2E + execution-report.md
↓
Deploy STG → PROD
```

**Key rule:** FE/Mobile KHÔNG bắt đầu code trước khi có `## API Contract` từ BE.
Integration check (localhost BE + FE = data thật trên màn hình) là DoD bắt buộc của mỗi FE task.

Chi tiết đầy đủ (bảng repo/actor thật của dự án) → `AGENTS.md` section `<bmad_workflow>`.

---

# 24. Example Workflow Files

```txt
.claude/workflows/
├── new-feature.md
├── bug-fix.md
├── release-flow.md
└── code-review.md
```

---

# 25. Recommended Technologies

| Purpose | Technology |
|---|---|
| AI Model | Claude |
| Agent Framework | CrewAI |
| Workflow | LangGraph |
| RAG | LlamaIndex |
| Vector DB | Pinecone |
| MCP | Anthropic MCP |
| Frontend | React |
| Backend | NodeJS |

---

# 26. Advanced Production Context

```txt
context/
├── current-sprint/
├── architecture-decisions/
├── business-decisions/
├── reusable-components/
├── api-catalog/
├── event-flow/
├── user-flow/
└── domain-knowledge/
```

---

# 27. Important Principles

## Priority Order

| Priority | Component |
|---|---|
| 1 | Context |
| 2 | Rules |
| 3 | Memory |
| 4 | Tool Access |
| 5 | Workflow |
| 6 | Multi-Agent |

---

# 28. Common Mistakes

## Bad

```txt
Generate an app
```

Result:
- random architecture
- inconsistent code
- hallucination

---

## Good

```txt
Requirement
+
Figma
+
Rules
+
Architecture
+
Context
+
Memory
+
Tool Access
```

Result:
- production-quality output
- consistent architecture
- reusable patterns
- scalable workflow

---

# 29. Final Production Architecture

```txt
Requirement
+
Codebase
+
Figma
+
Rules
+
Architecture
+
Memory
+
RAG
↓
Claude AI Agent System
↓
Generate:
- Tasks
- UI
- APIs
- Tests
- Docs
- Refactors
```

---

# 30. Goal

The goal is to transform Claude from:
- simple chatbot

into:
- AI Software Engineer
- AI PM
- AI Architect
- Autonomous Coding Agent
- Enterprise AI Development System
</content>
