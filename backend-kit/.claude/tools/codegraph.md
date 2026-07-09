# CodeGraph

Use CodeGraph when the target backend repository has a `.codegraph/` directory at the project root.

CodeGraph helps agents answer source questions with symbol-level context and call paths before editing code. It is especially useful for tracing NestJS request flow across controllers, services, repositories, guards, interceptors, and tests.

## When To Use

Use CodeGraph before broad manual search when you need to:

- Locate a module, provider, DTO, entity, migration, or test.
- Trace a request flow from controller to service to data access.
- Understand which files are affected by an interface or contract change.
- Find existing project conventions before generating new code.

## Commands

Explore a feature or symbol:

```bash
codegraph explore "OrdersModule controller service query flow"
```

Sync after code changes:

```bash
codegraph sync
```

If sync is unavailable in the installed version, re-run:

```bash
codegraph init
```

## Rules

- If `.codegraph/` does not exist, skip CodeGraph and use normal file search.
- Do not install or initialize CodeGraph unless the user asks for setup.
- Verify important CodeGraph findings by reading the source file before editing.
- Do not commit generated CodeGraph output unless the project explicitly tracks it.
