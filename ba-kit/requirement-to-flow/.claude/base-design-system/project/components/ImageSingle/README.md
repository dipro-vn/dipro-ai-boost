# ImageSingle

Embeds a single image in the page (the `<img>` element), optionally with a caption.

## When to use
- Photos, figures or illustrations that support the surrounding text.
- Add a `caption` for credits (写真提供：…) or to explain what the image shows.
- Use `href` only when the image itself leads somewhere; otherwise keep it static.

## Variants
| Figma axis | Prop |
| --- | --- |
| Type = Border | `variant="border"` (default) — 1px gray-420 inner frame |
| Type = Borderless | `variant="borderless"` |
| Type = Link / Link : Hover | `href` (sets `variant="link"`) — 1px blue-900 frame, 4px on hover |
| Show Caption | `caption` |
| Img-caption Area Type = Dashed / Solid | `captionStyle="dashed"` (gray-700 dashed, default) · `"solid"` (gray-420) |

Caption: padding 8/24, Std-16N-170 gray-900 on white, 8px below the image.

## What the consumer provides
- `src` and meaningful `alt` text (or `""` when decorative). For a linked image, the alt should describe the destination.
- Optional `width`/`height` to reserve space, and `imgProps` such as `loading="lazy"`.

## Accessibility notes
- Rendered as `<figure>` with `<figcaption>`, so the caption is associated with the image.
- Frames are drawn as inset overlays so the image size does not change on hover.
- Linked images get the system focus ring.
