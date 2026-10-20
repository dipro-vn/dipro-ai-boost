# NotificationBanner

A banner the site or service pushes to the user to announce high-priority information — about the whole service, a page or a single element — optionally asking them to act (e.g. maintenance notices, required follow-ups).

## When to use
- Service-wide or page-level announcements that must be seen regardless of what the user is doing.
- Results of an operation that need a follow-up action (complete, failed, attention needed).
- For crisis information use `EmergencyBanner`; for inline supplementary help use `NoticeBlock`.

## Variants
| Figma axis | Prop |
| --- | --- |
| Usage = Success / Error / Warning / Info 1 / Info 2 | `usage="success" \| "error" \| "warning" \| "info1" \| "info2"` |
| Style = Standard / Color Chip | `variant="standard" \| "color-chip"` |
| Set = Desktop / Mobile | `platform="desktop" \| "mobile"` |
| Button = Ver / Horiz (Mobile) | `buttonLayout="vertical" \| "horizontal"` |
| Show Date / Date | `date` |
| Show Close, Close Type | `onClose` or `dismissible`, `closeType="default" \| "compact"` |
| Show Primary / Secondary Button | `primaryAction`, `secondaryAction` (`{ label, onClick \| href }`) |

Desktop standard success/error banners use a tinted background (`green-50` / `red-50`, the nearest tokens to the source tints); all others are white.

## What the consumer provides
- `title` (short, states the outcome) and the description as children.
- Optional date, close handler and up to two actions. Buttons use `Button` (md) recoloured to the usage colour.

## Accessibility notes
- Rendered as a `<section>` labelled by its heading (`headingLevel`, default 2).
- The usage icon carries a text label (成功 / エラー / 警告 / お知らせ) so meaning never depends on colour alone.
- For banners inserted after page load, add `role="status"` (or `role="alert"` for errors) via props.
- The close button is a real `<button>`; the compact type keeps "閉じる" as its accessible name.
