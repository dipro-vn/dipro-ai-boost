# MenuList

A menu list groups menu items into one block, used as local navigation in the content area or inside a menu list box or mega menu.

## When to use
- `variant="standard"` for local / side navigation; items have rounded corners and an arrow end icon. Give child `items` to an entry to make it a collapsible section title.
- `variant="boxed"` for items shown inside a box (MenuListBox, mega menu). Add `description` / `thumbnail` for the rich "With Thumbnail" row.
- `type: 'category'` entries label a group of items (Category Titles).

## Variants
| Figma | Prop |
|---|---|
| Standard / Menu List Items, Section Titles | `variant="standard"`, entries with/without `items` |
| Boxed / Menu List Items | `variant="boxed"` |
| Boxed / With Thumbnail, Border Bottom | `variant="boxed"` + `thumbnail`/`description`, `divided` |
| Category Titles | `{ type: 'category' }` |
| Size Regular / Small | `size="regular"` (44px) / `"small"` (36px) |
| State Current / Selected | item `current` / `selected` |
| Caret Direction Down / Up | section `expanded` / `defaultExpanded` (Up = open) |
| Show Front-icon / End-icon / Tail-icon | item `icon` / `endIcon` / `external` |
| Hover, Focus | CSS `:hover`, `:focus-visible` |

## What the consumer provides
Labels, `href` or `onClick` per item, which item is current, and optional icons. Wrap a navigation list in `<nav aria-label="…">`.

## Accessibility notes
- Items are real links or buttons; current/selected items get `aria-current`.
- Section titles are buttons with `aria-expanded`/`aria-controls`; the caret flips when open.
- Category titles are plain text, not focusable. External links announce "新しいタブで開きます".
- Hover underlines the label; focus uses the system yellow + black ring (drawn inset for boxed items so a scrolling box does not clip it).
