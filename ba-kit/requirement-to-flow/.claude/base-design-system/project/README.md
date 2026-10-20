The Digital Agency design system (デジタル庁デザインシステム, DADS) is the shared UI kit for Japanese government web services: accessible by default, plain in voice, blue-keyed, and built on Noto Sans JP. Component docs and token notes paraphrase the descriptions in the source Figma file (v2.18.0, Community).

## Content fundamentals

- Write in polite, plain Japanese (です・ます). Say what the person can do, not what the system does: 「申請する」, 「下書き保存」, 「キャンセル」.
- Keep button and menu labels to a short verb phrase; never end a label with 。.
- Mark required fields with 「※必須」 and optional ones with 「※任意」 in the `FormControlLabel`; put the error message under the field, starting with 「＊」.
- Dates read 「2026年10月11日」; use the 24-hour clock.
- No emoji, no exclamation marks, no marketing tone. Icons accompany text; they never replace it.
- External links say so: use `Link` with `external`, which adds the `new_window_300` icon and the hidden text 「新しいタブで開きます」.

## Visual foundations

### Color
- `key-900` (blue `#0017c1`) is the key color: primary buttons, links, selected and checked states. Hover goes to `key-1000`, active to `key-1200`; light key steps (`key-50`–`key-300`) are hover and selected backgrounds.
- Set body text in `solid-gray-800` on `white` (entered values in `solid-gray-900`); secondary text in `solid-gray-600`; never use a gray lighter than `solid-gray-536` for text on `white` (4.5:1 limit).
- Form-control borders are `solid-gray-600`; disabled fills are `solid-gray-300` with `solid-gray-50` text — disabled pairs fail contrast on purpose, so always show why a control is disabled.
- Status: `success-1`/`success-2`, `error-1`/`error-2`, `warning-yellow-1`/`-2`, `warning-orange-1`/`-2`. Status color always comes with an icon or words.
- Primitive scales (blue, light-blue, cyan, green, lime, yellow, orange, red, magenta, purple, 50–1200) are for chips, illustrations and charts; UI uses the Key and Semantic aliases.
- Gradients (`gradient-*`) are for large surfaces only — hero and campaign bands (`gradient-key`, or `gradient-crimson` in the Marketplace theme), quiet section washes (`gradient-key-tint`, `gradient-crimson-tint`), sale ribbons (`gradient-campaign`, white text 24px+ only) and photo scrims (`gradient-scrim`). Never on buttons, inputs, chips or status messages. See the **Gradients** card.
- Text links: `blue-1000` default, `blue-900` with a 3px underline on hover, `orange-800` active, `magenta-900` visited.

### Type
- One family: Noto Sans JP (`--font-sans`); Noto Sans Mono (`--font-mono`) for code and fixed-width numbers. Weights 400, 500 (Medium, rare) and 700 only.
- Style names encode size, weight and line height: `Std-16N-170` = 16px, Normal, line-height 1.7.
  - **Standard** (`Std-…`) — headings and body; body copy is `Std-16N-170` (or `Std-17N-170` for reading pages).
  - **Dense** (`Dns-…`, 1.2–1.3) — tables, form support text, compact lists.
  - **Oneline** (`Oln-…`, 1.0) — single-line labels in buttons, tabs, menus.
  - **Display** (`Dsp-…`) — hero headlines only.
- Letter spacing is +0.02em on most Standard and Oneline styles, 0 on Dense and Display.
- Link styles in the source are the same metrics plus an underline; use `Link` rather than separate tokens.

### Shape, depth and layout
- Radii: `radius-8` buttons, inputs and cards; `radius-6` small buttons; `radius-4` chips and x-small buttons; `radius-12`/`radius-16` panels; `radius-full` switches and pills.
- Elevation `elevation-1`…`elevation-8`, each a 0.3 key shadow plus a 0.1 ambient one. In the source, dropdowns, list boxes and the calendar use `elevation-1`, modal dialogs and the mega menu use `elevation-3`; drawers here use `elevation-8`. Prefer borders to shadows for flat content.
- Desktop (1280px): 12 columns of `layout-column-desktop`, `layout-gutter-desktop` gutters, `layout-margin-desktop` margins, content no wider than `layout-content-max`. Mobile (≤ `layout-breakpoint-mobile`): `layout-margin-mobile` margins and gutters.

### Focus and states
- Every interactive element shows the same focus ring: a 2px `yellow-300` band inside a 4px `black` outline, offset 2px (`outline: 4px solid var(--black); outline-offset: 2px; box-shadow: 0 0 0 2px var(--yellow-300)`). It holds 3:1 on every surface.
- Hover adds an underline to text labels and darkens fills one key step; active darkens further.
- Errors: the field border turns `error-1` and a Dense message starting with 「＊」 appears under the field in `error-1`.

## Themes

- **デジタル庁** (`light`, default) — the source system as published: blue key color, Noto Sans JP, 8px radii.
- **Marketplace** (`market`) — a denser commerce look on the same components, inspired by large Japanese shopping sites but using only this system's own palette (no third-party logos, names or brand colors):
  - `key-*` maps to the red ramp: `key-900` → `red-1000` crimson for buy and primary buttons, checked controls and selected tabs; hover `key-1000` (`red-1100`), active `key-1200` (`red-1200`); light key steps become red tints.
  - Text links stay blue (`blue-1000`), so links never read as buy buttons.
  - Shape and density, set in `bundle.css` under `[data-theme="market"]`: `radius-6` and `radius-8` render at 4px, larger radii roughly halve; buttons are shorter (48 / 40 / 32 / 26px), lose the hover underline and drop letter spacing; outlined buttons are neutral gray, not key-colored; the font stack prefers Hiragino Kaku Gothic ProN / Meiryo.
  - `error-1` and `key-900` are both reds here: always pair errors with the 「＊」 message or an icon.
- Switch with `data-theme="market"` on `<html>` (or any wrapper).

## Iconography

- Icons are Google Material Symbols (Apache License 2.0), copied from the file as SVG into **Assets › Icons** and bundled in `Icon`.
- Names end in the weight (`_300` light, `_400` regular) or the fill (`_false` outlined, `_true` filled): `Icon name="check_400"`, `Icon name="search_300"`.
- Icons are 24px by default (16px beside 16px text) and take `currentColor`; give an icon a `label` only when it stands alone without text.

## Using the components

Load React 18, then `components/bundle.js`; everything is on `window.DADS` (`DADS.Button`, `DADS.Checkbox`, …). Styles are in `components/bundle.css`, which also loads Noto Sans JP from Google Fonts. Each component card lists its props; Figma variant axes map to props, while hover, focus, pressed and disabled are real browser states.

## Not synced

- Font files: Noto Sans JP and Noto Sans Mono are hosted on Google Fonts and referenced by name, not stored here.
- Grid styles (12-column layouts per screen width) are summarized as layout tokens, not stored as grids.
- The "Color (Local)" picker frame and the per-page changelogs are documentation of the Figma file, not part of the system.
