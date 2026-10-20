# UtilityLink

Utility links give quick access to features and links a service should always keep within reach, such as help, contact or sitemap.

## When to use
- In a header or footer strip for persistent, secondary destinations (よくある質問, お問い合わせ, アクセス).
- Not for primary navigation or in-text links (use `Link`).

## Variants
- `Link Items` → `UtilityLinkItem`: `Show Front Icon` → `icon` (16px glyph name); `Show End Icon` → `external` (16px `new_window_300`, opens a new tab).
- `Link Units Units=2…5` → `UtilityLink` with that many `items` (or `UtilityLinkItem` children), 16px apart, wrapping when space runs out.
- `State=Hover` → CSS: the 1px underline thickens to 3px.

## What the consumer provides
- Short labels, `href`s, optional lead icons and `external` for off-site targets.

## Accessibility notes
- `UtilityLink` is a `ul`; place it inside a labelled `nav` when it is a navigation region.
- Lead icons are decorative; the new-window icon is announced as "新しいタブで開きます".
- Text is `solid-gray-800`, Dns-16N-130, always underlined; keyboard focus shows the system focus ring.
