# Divider

A visual separator between sections, components or groups of content — the `<hr>` of the system — used to improve readability.

## When to use
- Between groups in menus, lists and page sections where whitespace alone is not enough.
- Prefer spacing or headings first; add a divider when the boundary must be explicit.

## Variants
| Figma | Prop | Values |
|---|---|---|
| Component set Solid / Dash | `variant` | `solid` (default), `dash` (dash = gap = 2 × weight) |
| Color | `color` | `gray-420` (default), `gray-536`, `black` |
| Weight | `weight` | `1`–`4` px |

The Figma component reserves 16px above and below the line; `spacing` changes it (use `0` for full-bleed dividers inside menus).

## What the consumer provides
- Placement and, if needed, horizontal inset via `style`/`className`.

## Accessibility notes
- Renders `<hr>` (role separator). If the line is purely decorative inside a widget, pass `aria-hidden`.
- `gray-420` is decorative contrast; use `gray-536` or `black` when the line itself conveys structure.
