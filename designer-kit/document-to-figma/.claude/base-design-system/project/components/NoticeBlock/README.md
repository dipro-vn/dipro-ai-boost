# NoticeBlock

An emphasised block of supplementary information, typically placed next to form fields to give concrete examples or list documents the user will need.

## When to use
- Highly useful help for a procedure form: sample variations, required documents, where to find a number.
- Not for input rules or constraints (allowed characters, length) — those belong in the input's own support text.
- Not for system messages; use `NotificationBanner` instead.

## Variants
| Figma axis | Prop |
| --- | --- |
| Style = Border-Rounded / Border-Solid / Fill-Rounded / Fill-Solid | `variant="border-rounded" \| "border-solid" \| "fill-rounded" \| "fill-solid"` |
| Type = Notice1 / Notice2 | `type="notice1"` (gray) \| `"notice2"` (light blue) |
| Show Title | `title` (+ optional `headingLevel`) |
| Show Chip Label | `chipLabel` (outlined, light blue) |
| Show Contents | `children` |
| Show Disclosures / Expand | `disclosures` holding `NoticeBlockDisclosure` (`open` / `defaultOpen` / `onToggle`, optional `chipLabel`) |

"Solid" styles are square-cornered with a 4px colour bar on the left; "Rounded" styles use `radius-12`.

## What the consumer provides
- The contents as children (paragraphs, lists or a table), an optional title and chip label, and any disclosures.

## Accessibility notes
- The block is a plain container; pass `headingLevel` when the title should appear in the document outline.
- Disclosures use native `<details>/<summary>`, so they are keyboard operable and expose expanded state; the toggle glyph is decorative.
