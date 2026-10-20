# Switch

Switches toggle a setting that takes effect immediately and whose result is visible right away.

## When to use
- `Switch` (OnOff Switch) for an on/off setting applied without a save button (収集日の通知).
- `SwitchMode` (Mode Switch) to flip between two display modes, e.g. リスト表示 / カレンダー表示 or ℃ / °F.
- If the change needs confirming with a submit button, or its effect is not visible on screen, use `Checkbox` or `Radio` instead.

## Variants
- OnOff Switch `Selected` Left/Right → `checked`/`defaultChecked` (off / on with check mark); `State` Disabled → `disabled`; Hover, Active and Focus are CSS (4px solid-gray-420 ring, 6px solid-gray-600 ring, system focus ring).
- Mode Switch `Selected`/`Checked` Left/Right → `value`/`defaultValue` `"left" | "right"`; Mode Switch with Label → `leftLabel` + `rightLabel` (16px gap, Oln-16N-100); without labels, give `aria-label`.

## What the consumer provides
- `Switch`: a visible label as children or an `aria-label`; `onChange` like a checkbox.
- `SwitchMode`: the two mode names and `onChange(value)`.

## Accessibility notes
- `Switch` is a native checkbox with `role="switch"`, so Space toggles it and it submits with forms.
- `SwitchMode` is a `<button role="switch">`; `aria-checked="true"` means the right-hand mode, and the right label names it. Clicking either label selects that mode.
