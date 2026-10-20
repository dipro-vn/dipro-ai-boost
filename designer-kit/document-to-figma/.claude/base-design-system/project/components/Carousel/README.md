# Carousel

Shows several slides one at a time with controls to move between them; use it sparingly, as the guidelines caution against relying on carousels for important information.

## When to use
- A small set (2–5) of promotional banners or highlights on a top page.
- Never for information people must not miss; every slide is also reachable through すべてのスライド.
- No autoplay is provided.

## Variants
| Figma component / state | Prop |
| --- | --- |
| Carousel / Normal | `variant="normal"` (default) — main panel (696:392) + Next Area preview with a 次のスライド button, step numbers below |
| Carousel / Narrow | `variant="narrow"` — main panel + previous / next arrows with "n / N" |
| Carousel / Single | `variant="single"` — one banner, no controls |
| State = Expanded (Show All Slides) | `expanded`/`defaultExpanded`, `onExpandedChange` — every slide listed, numbered in the normal variant |
| Main Area Default / Hover / Focus | slides with `href` are links; hover draws the key-900 double frame |

## What the consumer provides
- `slides` with `src`, `alt` (the banner's text) and optional `href`.
- An accessible `label` for the carousel region; optional `index`/`defaultIndex` + `onIndexChange`.
- Banner images at a 696:392 ratio (1024:392 for single).

## Accessibility notes
- A `section` with `aria-roledescription="カルーセル"`; each slide is a group labelled "n / N".
- Slide changes are announced politely; the current step number has `aria-current`.
- すべてのスライド is a disclosure button with `aria-expanded`.
- The narrow arrows follow the 24px XS spec, which is smaller than the recommended touch target; leave space around them.
