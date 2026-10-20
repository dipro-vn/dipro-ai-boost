# StepNavigation

Step navigation lays out a procedure as a sequence of logical steps so people can see the whole path to completion and where they are in it; it can also act as navigation between steps.

## When to use
- Multi-page applications and forms (e.g. カード交付申請) — horizontal above the form to show progress.
- A vertical list on an overview page explaining the steps before a person starts.
- Not for paging through results (use `PageNavigation`) or showing site hierarchy (use `Breadcrumb`).

## Variants
- Component sets `Step Navigation / Horizontal` and `/ Vertical` → `orientation="horizontal" | "vertical"`.
- `Size=Normal | Small` → `size="normal" | "small"` (52px / 38px markers; Std-18B-160 / Dns-16B-130 titles).
- `Position=First | Middle | Last` → derived from the order of `steps` (connector lines are drawn only between steps).
- `Description` → `description` (boolean, default true) plus each step's `description` text.
- `Link=True` → give a step `href` or `onClick`; the title becomes an underlined link (3px underline on hover).
- Number building block `State=Completed | Reached | Default | Skipped | Editing | Error` → `steps[i].status`; `Current=True` → `current` index (outer ring).

## What the consumer provides
- `steps`: `[{ title, description?, status?, href? }]`.
- `current`: the 0-based index of the step being shown.

## Accessibility notes
- Renders `nav` > `ol`; the current step has `aria-current="step"`.
- The number and badges are decorative; each title carries visually hidden text "ステップN（状態）" so status is not conveyed by shape or color alone.
- Link titles show the system focus ring.
