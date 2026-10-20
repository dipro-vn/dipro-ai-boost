# Button

Buttons let a person choose and run an action with a single click or tap.

## When to use
- `solid-fill` for the one primary action of a view (送信, 申請する). Keep one per area.
- `outlined` for secondary actions next to a primary one.
- `text` for low-emphasis actions (キャンセル, 戻る); it is always underlined so it still reads as interactive.
- Use a link (`Link`) rather than a button when the action only navigates; pass `href` only for button-styled navigation.

## Sizes
`lg` 56px (default), `md` 48px, `sm` 36px, `xs` 28px. Labels are Oneline Oln-16B-100 in every size; radius steps down from `radius-8` (lg, md) to `radius-6` (sm) and `radius-4` (xs).

## What the consumer provides
- The label as children — a short verb phrase.
- Optional `leadIcon` (sized to the button) and `tailIcon` (16px, e.g. `new_window_300` for external targets).
- `disabled` only when the reason is visible nearby; disabled fills are `solid-gray-300` and fail contrast by design.

## States
Hover darkens to `key-1000` and underlines the label; active goes to `key-1200`; keyboard focus draws the system focus ring (2px `yellow-300` band inside a 4px `black` outline).
