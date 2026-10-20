# Breadcrumb

Breadcrumb navigation shows where the current page sits in the site hierarchy once a person has moved into lower levels.

## When to use
- On pages two or more levels below the top, above the page heading.
- Not as the only navigation, and not for step-by-step flows (use `StepNavigation`).

## Variants
- Figma `Units=2…5` → the length of `items`; any length works and the list wraps on narrow screens.
- Building block `Home Icon` → `homeIcon` (filled home glyph before the first item).
- Building block `State=Default/Hover/Active` → CSS: `blue-1000` underlined, hover `blue-900` with a 3px underline, active `orange-800`.

## What the consumer provides
- `items`: `[{ label, href }]` from the top level to the current page. The last item (or the one with `current: true`) renders as plain `solid-gray-800` text.
- Optional `aria-label` if the default "パンくずナビゲーション" does not fit.

## Accessibility notes
- Renders `nav` > `ol`; the current page carries `aria-current="page"`.
- The 12px `arrow_right` separators are decorative (`aria-hidden`).
- Links show the system focus ring on keyboard focus.
