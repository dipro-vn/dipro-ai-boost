# Card

A container that groups content about a single topic; the system restricts what goes inside so cards stay easy to scan.

## When to use
- Lists of news, services or procedures where each item has a label, a title and a short description.
- `href` when the whole card leads to one page; `selectable` when people pick several items (e.g. documents to request).
- Prefer a plain list when items have no supporting content.

## Variants
| Figma building block / axis | Prop |
| --- | --- |
| Main Area · Link = True | `href` (+ `external`) — the whole card is the link; hover gray-50 |
| Main Area · Function = True | `selectable`, `checked`/`defaultChecked`, `onCheckedChange` — 44px checkbox, whole card toggles |
| Main Area · Link = False, Function = False | default; `onMenu` shows the more_vert end-icon button |
| Label / Contents | `label`, `children` |
| Image Area | `image={{ src, alt }}` |
| Sub Area · Link Lists / Footer Actions | `links=[{ label, href }]`, `actions` (right-aligned, 8px gap) |
| Horizontal layout | `layout="horizontal"` (image on the left, up to 260px) |

Frame: 1px gray-420, radius 16; main area padding 16/24 with 16px gaps; label Std-16N-170 gray-800, title Std-20B-150 gray-900.

## What the consumer provides
- A short `title` (rendered as `h3` by default; change with `headingLevel`), an optional `label` and a one- or two-sentence body.
- Image alt text, or `alt: ""` when the image only decorates.
- Buttons for `actions` (`Button size="md"`).
- Not reproduced: the Image Area's overlaid label and small form-control button.

## Accessibility notes
- Link cards keep a single real link on the title, stretched over the card, and draw the system focus ring around the whole card.
- Selectable cards use a native checkbox labelled by the title; clicking anywhere on the card toggles it.
- Sub-area links and buttons stay separately focusable above the stretched hit area.
