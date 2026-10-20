# ChipTag

A pill-shaped item that displays a piece of user-chosen information (a filter, a recipient, an attribute) and lets the person remove it.

## When to use
- Showing applied search conditions with a way to clear each one.
- Listing selected recipients, attributes or keywords that can be deleted individually.
- For read-only status keywords use `ChipLabel` instead.

## Variants
| Figma prop | Prop | Notes |
|---|---|---|
| Action Button | `onRemove` / `removable` | Shows the 24px cancel (×) button. |
| Front Icon / Icon | `icon` | 24px icon before the label (e.g. `avatar_false`). |
| State=Hover/Active | CSS | Label turns key-1000 and the × switches to its filled glyph. |
| State=Focus | CSS | System focus ring around the × button. |

Key-50 fill, 1px key-900 border, full radius, 32px tall, label Oln-16N-100 in key-900.

## What the consumer provides
- The label as children.
- `onRemove` to delete the item from its own state (the component is stateless).
- Optional `removeLabel` when the label is not plain text.

## Accessibility notes
- The remove control is a real `<button>` named "<label>を削除"; its hit area is stretched over the whole chip.
- After removal, move focus to a sensible place (the next chip or the field) — the component cannot do that for you.
