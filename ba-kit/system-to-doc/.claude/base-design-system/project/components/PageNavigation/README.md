# PageNavigation

Page navigation lets a person step backward and forward through content that has been split across several pages or sections.

## When to use
- Below search results or long lists split into pages ("1 / 24").
- Inside a section to page through a small set of cards ("前の3件" / "次の3件").
- Not for jumping to arbitrary pages or for multi-step forms (use `StepNavigation`).

## Variants
- Figma `Type=Text | Arrow | Outlined` → `type="text" | "arrow" | "outlined"`.
  - text: underlined `key-900` bold labels with 24px arrows, 48px tall; hover fills `key-50`.
  - outlined: 1px `key-800` border, 56px tall; hover fills `key-200` and underlines.
  - arrow: round icon-only buttons with a `key-1000` 1px ring; hover thickens the ring.
- Building block `Page Navigation Arrows Size=L/M/S/XS` → `arrowSize="l" | "m" | "s" | "xs"`.
- `State=Hover` → CSS `:hover`; focus uses the system focus ring.

## What the consumer provides
- `total` and `page` (controlled, with `onChange`) or `defaultPage`.
- Optional `previousLabel` / `nextLabel`, `label` for a custom counter, and `previousHref` / `nextHref` for link-based paging.

## Accessibility notes
- Wrapped in `nav` (default label "ページナビゲーション"); the counter is `aria-live="polite"` so changes are announced.
- Arrow-only buttons get their accessible name from `previousLabel` / `nextLabel`.
- At the first / last page the control is `aria-disabled` and greyed (`solid-gray-300`); this disabled look is not drawn in the source file.
