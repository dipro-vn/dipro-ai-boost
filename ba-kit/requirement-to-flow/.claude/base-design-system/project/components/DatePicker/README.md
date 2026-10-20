# DatePicker

A date entry control made of typed year/month/day fields plus an optional calendar panel for picking a date visually.

## When to use
- Dates people know by heart (生年月日): `type="separated"` without the calendar button — typing is fastest.
- Dates near today (予約日, 交付日): `type="consolidated"` with `showCalendarButton` so the Calendar Panel can be used.
- Use `showYear={false}` or `showDay={false}` for month/day or year/month only values.
- `DatePickerCalendar` can be used on its own (e.g. inline in a page or another popover).

## Variants
| Figma | Prop |
| --- | --- |
| Input Date · Type = Consolidated / Separated | `type="consolidated"` (default) / `"separated"` |
| Size = Large / Medium / Small | `size="lg"` / `"md"` / `"sm"` (56 / 48 / 40px fields) |
| State = Error | `error` or `errorText` (Std-16N-170 error text below) |
| State = Readonly | `readOnly` (dashed borders) |
| State = Disabled | `disabled` |
| hover / focus | CSS (black border on hover; the focused part gets the system focus ring) |
| Show Calendar Button / Show Year / Show Day | `showCalendarButton` / `showYear` / `showDay` |
| Calendar Button State = Open | automatic while the popover is open (arrow turns up, `aria-expanded`) |
| Date Cell State = Selected / Null | the selected date in `value`; days outside the month render empty |

## What the consumer provides
- `label`, `supportText` showing the expected format (例：2025年01月20日 / 西暦、半角), `required`/`optional`.
- `value`/`onChange` (strings as typed) or `defaultValue`; validation and `errorText` are yours.
- Year range for the calendar via `minYear`/`maxYear`.

## Accessibility notes
- The unit is a `<fieldset>` with the label as `<legend>`; each part is a numeric text input labelled 年/月/日.
- The calendar button has `aria-haspopup="dialog"`/`aria-expanded`; the panel opens with focus on the selected (or today's) date.
- Grid keys: arrows move by day/week, Home/End to week start/end, PageUp/PageDown by month (Shift for year); Enter selects; Escape closes and returns focus to the button. Each date button has a full label such as "2025年10月23日 木曜日".
