# FileUpload

A labelled file picker built on `<input type="file">` that lets people choose one or several files with a button or by drag and drop, then review and remove them before submitting.

## When to use
- Attaching evidence documents in an application form (証明書類の登録), one FileUpload per required document.
- Use `type="drop-area"` on desktop-first forms where dragging from a file manager is common; use `type="button"` where space is tight or drag and drop is unlikely (mobile).
- Use `multiple` only when the procedure really accepts several files.

## Variants
| Figma | Prop |
| --- | --- |
| File Upload Type = With DropArea / Button Only | `type="drop-area" \| "button"` |
| Button in Drop Area / Button Only State = Default, Dragover | automatic while files are dragged over the area |
| State = Error | `error` |
| SelectSummary (bool) | `showSummary` |
| File Selection Type = None / Single / Multiple | no files / `multiple` false / `multiple` true |
| Single : Error, Multiple : Error Mixed | `validate` returning messages for a file |
| Full Drop Area | the "ブラウザウィンドウ全体に広げる" checkbox in the drop area |

## What the consumer provides
- `label`, `supportText` (accepted formats, which document) and `accept`.
- `validate` for per-file problems (format, size) and `error` for field-level problems; the component does not upload anything — read the list from `onChange` and send it on submit.

## Accessibility notes
- The native file input is visually hidden; the visible outlined button opens it and is labelled by the field label plus its own text, and described by support text, error and the current selection.
- Each 解除 button has an `aria-label` naming the file. The selection is a real `<ul>` / `<ol>`.
- Drag and drop is an enhancement only; everything works with the button and keyboard. The window-wide drop target is opt-in through a real checkbox.
