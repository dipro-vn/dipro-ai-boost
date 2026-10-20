# MenuListBox

A menu list box is an opener — a text label plus an arrow showing open/closed — that reveals a box containing a menu list.

## When to use
- Compact pickers for navigation or view options (sort order, category jump) where a full menu list would take too much space.
- For a form value, use a select box instead; this is not a form control.

## Variants
| Figma (Openers) | Prop |
|---|---|
| Style Text / Outlined / Filled | `variant="text"` (default) / `"outlined"` / `"filled"` |
| Size Default (44px) / Small (36px) | `size="default"` / `"small"` |
| Text Weight Bold / Normal | `weight="bold"` / `"normal"` |
| Arrow Down / Up | closed / open (`open`, `defaultOpen`, `onOpenChange`) |
| Show Front Icon | `icon` |
| State Hover / Focus | CSS `:hover`, `:focus-visible` |
| Menu List with Scrollbar & Categories | `maxHeight` + a `MenuList variant="boxed"` with category entries as children |

## What the consumer provides
The opener `label`, optional `icon`, and the box content (usually `<MenuList variant="boxed" items={…}/>`, optionally with category titles or thumbnail rows). Close it yourself (`open`) after a selection if needed.

## Accessibility notes
- The opener is a `<button>` with `aria-expanded` and `aria-controls` pointing at the box.
- Escape closes the box and returns focus to the opener; a click outside closes it.
- Hover underlines the label; focus uses the system yellow + black ring.
