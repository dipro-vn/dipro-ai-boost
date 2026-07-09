# Understand-Anything

Use Understand-Anything when the target backend repository has a `.understand-anything/` directory at the project root.

Understand-Anything is useful for larger, legacy, or poorly documented backend repositories where a persistent knowledge graph helps agents reason about modules, domains, and request flows.

## When To Use

Use it before broad manual search when you need to:

- Ask a high-level question about the backend codebase.
- Trace domain behavior across many modules.
- Explain an unfamiliar service, controller, repository, or migration.
- Inspect what changed since the last analysis.

## Commands

Analyze or refresh the project:

```text
/understand
```

Ask a question:

```text
/understand-chat Trace the order creation flow.
```

Explain one file or symbol:

```text
/understand-explain src/orders/orders.service.ts
```

View project overview:

```text
/understand-dashboard
```

Inspect changes:

```text
/understand-diff
```

Generate English output:

```text
/understand --language en
```

## Rules

- If `.understand-anything/` does not exist, skip this tool and use normal file search.
- Do not install or run the initial analysis unless the user asks for setup.
- Verify important findings by reading the source file before editing.
- Do not commit generated Understand-Anything output unless the project explicitly tracks it.
