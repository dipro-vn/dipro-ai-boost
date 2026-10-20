# Gradients

A showcase of the system's gradient tokens (`gradient-*`), the large-surface fills for banners, hero bands and image overlays.

## When to use
- `gradient-key` for hero and campaign bands in the デジタル庁 theme; `gradient-crimson` for the same role in the Marketplace theme.
- `gradient-key-tint` / `gradient-crimson-tint` as quiet section backgrounds; set body text in `solid-gray-800` on them.
- `gradient-campaign` for short, large sale ribbons only (white text at 24px+ or bold 19px+).
- `gradient-scrim` over photos so a white caption at the bottom stays legible; `gradient-placeholder` only for empty image slots.

## Don't
- Don't put gradients on buttons, inputs, chips or status messages — those use flat `key-*` and semantic colors.
- Don't layer two gradients or invent new stops; add a token instead.

## What the consumer provides
Apply the token as a background: `background: var(--gradient-key);`. Gradients are not per-theme, so pick the key or crimson variant to match the active theme.
