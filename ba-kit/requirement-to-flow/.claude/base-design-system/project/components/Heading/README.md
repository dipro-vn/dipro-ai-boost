# Heading

A heading placed at the top of a page or before a paragraph that names its topic.

## When to use
- Page titles (`level={1}`) and section titles (`level` 2–6) in proper document order.
- Choose `size` for visual weight independently of `level`; don't skip levels just to get a size.

## Variants
| Figma | Prop | Values |
|---|---|---|
| Size | `size` | 64, 57 (Display), 45, 36, 32, 28, 24, 20, 18, 16 (Standard bold) |
| Style=Shoulder | `shoulder` | lead text above, one step smaller (28…16) |
| Style=Front-icon | `icon` | icon name; 80px at size 64 down to 20px at 16 |
| Style=Chip | `chip` | key-900 bar before the text, width/inset scaled per size |
| Building Blocks / Rulers | `ruler` | 2, 4, 6, 8 px key-900 rule below (spaced 8/16/24/32px) |
| — | `level` | 1–6 → `h1`–`h6` (default 2; default size by level 36/32/28/24/20/18) |

Text is solid-gray-800, bold, with the line-height and letter-spacing of each type style. Style props can be combined.

## What the consumer provides
- The heading text and the correct semantic `level`.
- Surrounding margins (the Figma example uses 24px below and 56–96px above, by size).

## Accessibility notes
- Shoulder text is rendered as `<p>` inside `<hgroup>` with the heading, so it is not part of the heading's accessible name.
- Icons, chip bars and rulers are decorative (`aria-hidden`).
