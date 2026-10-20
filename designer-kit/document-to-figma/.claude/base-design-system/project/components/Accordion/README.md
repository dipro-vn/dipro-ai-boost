# Accordion

An accordion collapses a run of same-kind sections (e.g. an FAQ) so readers can scan the headers and open only what they need.

## When to use
- Several consecutive, parallel sections such as Q&A entries or procedure steps.
- To collapse just part of a section, use `Disclosure` instead.

## Variants
| Figma axis | Prop |
|---|---|
| Platform = Desktop / Mobile | `platform="desktop" \| "mobile"` on `Accordion` (or per item) |
| Expand = False / True | `open` / `defaultOpen` + `onOpenChange` on `AccordionItem` |
| State = Default / Hover / Focus | CSS `:hover` (gray-50 row, thicker control ring) and `:focus-visible` (yellow fill + focus ring) |
| Accordion Controls Down / Up | follows the expanded state automatically |

Desktop: 44px control area (32px ring, 20px arrow), header Std-18N-160, panel padding 24/32/24/52. Mobile: 24px control (20px ring, 16px arrow), header Std-16N-170, panel padding 16/8/16/32.

## What the consumer provides
- `AccordionItem` children inside `Accordion`, each with a `title` and panel content.
- Optional `returnLabel`, or `returnLink={false}` to hide the 「…」の先頭に戻る link.
- `headingLevel` matching the page outline (default `h3`).

## Accessibility notes
- Each header is a `<button aria-expanded aria-controls>` inside a heading; the panel is a `role="region"` labelled by the button and uses `hidden` when collapsed.
- The return link points at the item heading so keyboard and screen-reader users can jump back after a long panel.
