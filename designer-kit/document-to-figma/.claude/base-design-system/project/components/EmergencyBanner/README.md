# EmergencyBanner

A top-priority banner that grabs the user's attention during an emergency (disasters, evacuation orders, critical outages).

## When to use
- Only for genuine emergencies that override everything else on the page; place it at the very top, above the header content.
- Keep one per page. For ordinary announcements use `NotificationBanner`.

## Variants
| Figma axis | Prop |
| --- | --- |
| Platform = Desktop / Mobile | `platform="desktop" \| "mobile"` |
| Link = True / False | `action` present / absent |
| State = Hover | CSS `:hover` on the action (outline and fill go to `error-2`) |
| Show Date | `date` |

Frame: 6px `warning-orange-1` border on white. The action is a red solid button (`error-1`) wrapped in a red outline frame (4px desktop / 2px mobile); half width on desktop, full width on mobile.

## What the consumer provides
- `title` beginning with 【緊急】, an optional update time, the description as children, and an optional `action` (`{ label, href | onClick }`).

## Accessibility notes
- Rendered as a `<section>` labelled by its heading (`headingLevel`, default 2).
- If the banner is injected after load, pass `role="alert"` so assistive tech announces it.
- The action is a real link or button with the system focus ring; the visual frame is not a separate focus stop.
