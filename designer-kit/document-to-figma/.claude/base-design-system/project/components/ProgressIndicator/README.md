# ProgressIndicator

Tells the user that work they triggered is still in progress, such as waiting for a data request to respond.

## When to use
- `spinner` while waiting for something of unknown duration (loading a page section, submitting).
- `linear` for a bar-shaped wait inside a layout; pass `value` (0–100) when the progress is actually known.
- `static` where motion is undesirable or impossible (printing, reduced motion contexts) but a waiting state must still be shown.
- Use `underlay` when the indicator sits over other content or a dimmed overlay.

## Variants
| Figma axis | Prop |
| --- | --- |
| Style = Spinner / Linear / Static | `variant="spinner" \| "linear" \| "static"` |
| Composition = Stacked / Inlined | `composition="stacked" \| "inlined"` (48px vs 24px; 240px vs 80px bar) |
| Underlay = True / False | `underlay` |
| Show Label | `label` |

Colours follow the key colour: track `key-100`, ink `key-1200`. Spinner and linear animate with CSS keyframes; both stop under `prefers-reduced-motion: reduce`.

## What the consumer provides
- A short label (読み込み中, 送信しています…). Without one, a hidden "読み込み中" is still announced.
- Optional `value` for a determinate linear bar.

## Accessibility notes
- Indeterminate indicators render `role="status"` with `aria-live="polite"`, so the label is announced when it appears.
- A determinate linear bar renders `role="progressbar"` with `aria-valuenow`.
- The graphics are `aria-hidden`; meaning comes from the label.
