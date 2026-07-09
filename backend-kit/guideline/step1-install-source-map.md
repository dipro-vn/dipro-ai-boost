# Step 1: Install A Source-Map Tool

The goal of this step is to create a local source map so AI agents can understand the backend codebase before making changes.

Choose one tool:

- **CodeGraph**: simple and fast, good for most NestJS backend projects.
- **Understand-Anything**: richer knowledge output, useful for legacy projects or repositories with limited documentation.

Source-map setup is optional for `backend-kit`. If a project has no source-map tool installed, agents must fall back to normal file and text search.

## Option A: CodeGraph

Project: https://github.com/colbymchenry/codegraph

### 1. Install The CLI

```bash
curl -fsSL https://raw.githubusercontent.com/colbymchenry/codegraph/main/install.sh | sh
codegraph install
```

### 2. Initialize The Backend Project

Run this at the root of the target backend repository:

```bash
cd /path/to/your-backend-project
codegraph init
```

### 3. Use It During Work

```bash
codegraph explore "OrdersModule controller service repository flow"
```

### 4. Sync After Code Changes

```bash
codegraph sync
```

If `codegraph sync` is unavailable in the installed version, run `codegraph init` again from the project root.

## Option B: Understand-Anything

Project: https://github.com/Egonex-AI/Understand-Anything

### 1. Install The Plugin

Run these commands inside Claude Code:

```text
/plugin marketplace add Egonex-AI/Understand-Anything
/plugin install understand-anything
```

### 2. Analyze The Backend Project

```text
/understand
```

### 3. Ask Questions About The Codebase

```text
/understand-chat Trace the request flow for GET /api/orders.
/understand-explain src/orders/orders.service.ts
```

### 4. Sync After Code Changes

```text
/understand
```

`/understand` is incremental by default. Use `--language en` if you want generated knowledge output in English:

```text
/understand --language en
```

## Expected Agent Behavior

When a source-map tool is available:

1. Use it before broad manual search.
2. Use it to identify the relevant modules, providers, DTOs, entities, migrations, and tests.
3. Verify important findings by reading the actual source files before editing.
4. Sync the source map after code changes when the tool supports syncing.

When no source-map tool is available:

1. Use normal file and text search.
2. Report that source-map setup is not present.
3. Continue the task without blocking.

## Generated Output

Source-map outputs such as `.codegraph/` and `.understand-anything/` are project-local generated state. Do not commit them unless the project explicitly chooses to track them.
