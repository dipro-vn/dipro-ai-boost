# ModalDialog

A modal dialog takes over the screen: while it is shown, only the content inside the dialog can be operated.

## When to use
- To confirm a consequential action (送信, 削除) or to demand attention before the person continues.
- Keep it short: one title, a few sentences, and at most one primary action. Use a page or a non-modal pattern for long forms.

## Variants
| Figma | Prop |
|---|---|
| Type=Deskop / Mobile | `type="desktop" \| "mobile"` |
| Show Close Button | `showCloseButton` (default `true`) |
| Show Contents | `children` present |
| Show Action Area | `actions` / `startAction` present |
| Overlay Shade | always rendered behind the dialog (`opacity-gray-600`) |
| Example with title icon | `titleIcon="warning_300-true"` |

## What the consumer provides
- `open` and `onClose` (controlled); `title`; contents as `children`.
- `actions`: `Button`s in desktop order (e.g. outlined オプション, solid-fill 実行); `startAction`: a text-style キャンセル.
- `inline` only for documentation/previews, where the shade becomes a box in the page flow.

## Accessibility notes
- `role="dialog"` + `aria-modal="true"`, named by the title (`aria-labelledby`) and described by the contents.
- On open, focus moves to the first focusable element (or one marked `data-autofocus`); Tab/Shift+Tab are trapped inside; Escape calls `onClose`; focus returns to the trigger on close; page scroll is locked.
- Always offer a visible way out — the close button or a cancel action.
