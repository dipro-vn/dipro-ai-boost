// DADS — デジタル庁デザインシステム components. Global: window.DADS (React 18 required on window).
import type * as React from 'react';
export interface IconProps extends React.SVGProps<SVGSVGElement> {
  /** Icon name, e.g. "check_400", "arrow_right_300", "search_400", "close_400", "new_window_300". See Icon.names. */
  name: string;
  /** Pixel size (default 24). */
  size?: number;
  /** Accessible name; omit for decorative icons (aria-hidden). */
  label?: string;
}
export declare function Icon(props: IconProps): React.ReactElement;
export interface LinkProps extends React.AnchorHTMLAttributes<HTMLAnchorElement> {
  /** Opens in a new tab and shows the new_window icon. */
  external?: boolean;
}
export declare function Link(props: LinkProps): React.ReactElement;

// ---- Accordion ----
export interface AccordionProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Platform axis applied to every item: "desktop" (44px control, 18px header, default) or "mobile" (24px control, 16px header). */
  platform?: 'desktop' | 'mobile';
  /** Heading level wrapping each item's toggle button (h2–h6). Default 3. */
  headingLevel?: 2 | 3 | 4 | 5 | 6;
  /** AccordionItem elements. */
  children?: React.ReactNode;
}
export declare function Accordion(props: AccordionProps): React.ReactElement;

export interface AccordionItemProps extends Omit<React.HTMLAttributes<HTMLDivElement>, 'title'> {
  /** Header text of the section (Accordion Header); usually a question or section title. */
  title: React.ReactNode;
  /** Controlled expanded state (Expand axis). */
  open?: boolean;
  /** Initial expanded state when uncontrolled. Default false. */
  defaultOpen?: boolean;
  /** Called with the next expanded state when the header is activated. */
  onOpenChange?: (open: boolean) => void;
  /** Overrides the platform inherited from Accordion. */
  platform?: 'desktop' | 'mobile';
  /** Overrides the heading level inherited from Accordion. */
  headingLevel?: 2 | 3 | 4 | 5 | 6;
  /** Show the "return to the top of this item" link at the end of the panel. Default true. */
  returnLink?: boolean;
  /** Return link text. Default 「{title}」の先頭に戻る when title is a string. */
  returnLabel?: React.ReactNode;
  /** Base id for the heading (return-link target); generated when omitted. */
  id?: string;
  /** Panel content shown when expanded. */
  children?: React.ReactNode;
}
export declare function AccordionItem(props: AccordionItemProps): React.ReactElement;

// ---- Breadcrumb ----
export interface BreadcrumbItem {
  /** Visible page name. */
  label: React.ReactNode;
  /** Link target. Omit on the current page. */
  href?: string;
  /** Marks this item as the current page (default: the last item). */
  current?: boolean;
  /** Optional click handler for client-side routing. */
  onClick?: React.MouseEventHandler<HTMLAnchorElement>;
}
export interface BreadcrumbProps extends React.HTMLAttributes<HTMLElement> {
  /** Trail from the top level down to the current page (Units = items.length). */
  items: BreadcrumbItem[];
  /** Shows the filled home icon before the first item (Home Icon). */
  homeIcon?: boolean;
  /** Accessible name of the nav landmark. Default "パンくずナビゲーション". */
  'aria-label'?: string;
}
export declare function Breadcrumb(props: BreadcrumbProps): React.ReactElement;

// ---- Button ----
export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  /** Style axis: "solid-fill" (primary, default), "outlined" (secondary), "text" (tertiary). */
  variant?: 'solid-fill' | 'outlined' | 'text';
  /** Size axis: lg 56px, md 48px, sm 36px, xs 28px tall. Default "lg". */
  size?: 'lg' | 'md' | 'sm' | 'xs';
  /** Icon name shown before the label (Show Lead-icon). */
  leadIcon?: string;
  /** Icon name shown after the label, 16px (Show Tail-icon), e.g. "new_window_300". */
  tailIcon?: string;
  /** Renders an <a> instead of a <button>. */
  href?: string;
  children?: React.ReactNode;
}
export declare function Button(props: ButtonProps): React.ReactElement;

// ---- Card ----
export interface CardLinkItem {
  /** Link text. */
  label: React.ReactNode;
  /** Destination URL. */
  href: string;
  /** Opens in a new tab with the new_window icon. */
  external?: boolean;
}
export interface CardImage {
  /** Image URL. */
  src: string;
  /** Alternative text; "" for decorative images. */
  alt?: string;
}
export interface CardProps extends Omit<React.HTMLAttributes<HTMLElement>, 'title'> {
  /** Card title (Main Area "Title", Std-20B-150). Rendered as a heading. */
  title: React.ReactNode;
  /** Small label shown above the title (Main Area "Label"), e.g. a category or date. */
  label?: React.ReactNode;
  /** Body contents (Main Area "Contents"). */
  children?: React.ReactNode;
  /** Link = True: the whole card navigates here (hover gray-50, focus ring around the card). */
  href?: string;
  /** With href: opens in a new tab and shows the new_window icon. */
  external?: boolean;
  /** Function = True: the whole card toggles a 44px checkbox. Ignores href/onMenu. */
  selectable?: boolean;
  /** Controlled checkbox state (Function variant). */
  checked?: boolean;
  /** Initial checkbox state when uncontrolled. */
  defaultChecked?: boolean;
  /** Called when the checkbox toggles. */
  onCheckedChange?: (checked: boolean, event: React.ChangeEvent<HTMLInputElement>) => void;
  /** Disables the checkbox (Function variant). */
  disabled?: boolean;
  /** Link = False, Function = False: shows the more_vert end-icon button and calls this on press. */
  onMenu?: (event: React.MouseEvent<HTMLButtonElement>) => void;
  /** Accessible name of the end-icon button. Default "その他の操作". */
  menuLabel?: string;
  /** Image Area shown above (vertical) or left of (horizontal) the main area. */
  image?: CardImage;
  /** "vertical" (image on top, default) or "horizontal" (image on the left, as in "Horizontal layout 1"). */
  layout?: 'vertical' | 'horizontal';
  /** Sub Area link list. */
  links?: CardLinkItem[];
  /** Sub Area footer actions (right-aligned), e.g. Buttons size "md". */
  actions?: React.ReactNode;
  /** Heading level of the title (default 3). */
  headingLevel?: 2 | 3 | 4 | 5 | 6;
}
export declare function Card(props: CardProps): React.ReactElement;

// ---- Checkbox ----
export interface CheckboxProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'size' | 'type'> {
  /** Size axis: sm (24px control, 40px row), md (32px control, 48px row), lg (44px control, 60px row). Default "sm". */
  size?: 'sm' | 'md' | 'lg';
  /** Controlled checked state. Pair with onChange. */
  checked?: boolean;
  /** Uncontrolled initial checked state. */
  defaultChecked?: boolean;
  /** Shows the mixed (Indeterminate) mark; sets the native input.indeterminate. */
  indeterminate?: boolean;
  /** Error state (Default/Checked/Indeterminate Error): red outline and fill, aria-invalid. */
  error?: boolean;
  /** Disables the control (Disabled states). */
  disabled?: boolean;
  /** Ref to the underlying <input type="checkbox">. */
  inputRef?: React.Ref<HTMLInputElement>;
  /** Selection text. Other props go to the <input>; className and style go to the root <label>. */
  children?: React.ReactNode;
}
export declare function Checkbox(props: CheckboxProps): React.ReactElement;

export interface CheckboxGroupProps extends React.FieldsetHTMLAttributes<HTMLFieldSetElement> {
  /** Layout: "stacked" (one per row, Stacked set) or "inline" (wrapping row, Inline set). Default "stacked". */
  layout?: 'stacked' | 'inline';
  /** Size axis, applied to the label and to every child Checkbox without its own size. Default "sm". */
  size?: 'sm' | 'md' | 'lg';
  /** Group label rendered as the fieldset legend (Show Label). */
  label?: React.ReactNode;
  /** Legend weight. Default "bold". */
  labelWeight?: 'normal' | 'bold';
  /** Requirements marker next to the label: required / optional / readonly / disabled. */
  requirement?: 'required' | 'optional' | 'readonly' | 'disabled';
  /** Support text under the label. */
  supportText?: React.ReactNode;
  /** Error text under the options (Show Error Text); any truthy value also puts every child in the error state. */
  error?: React.ReactNode | boolean;
  /** Checkbox elements. */
  children?: React.ReactNode;
}
export declare function CheckboxGroup(props: CheckboxGroupProps): React.ReactElement;

// ---- ChipLabel ----
export interface ChipLabelProps extends React.HTMLAttributes<HTMLSpanElement> {
  /** Style axis: "text-only" (no box), "outlined" (white fill + border, default), "filled-1" (pale tint + border), "filled-2" (solid color, white text). */
  variant?: 'text-only' | 'outlined' | 'filled-1' | 'filled-2';
  /** Color axis. Gray uses solid-gray-700/800; other hues use their 700–1000 step (text/border) and 50 step (Filled 1 tint). Default "gray". */
  color?: 'gray' | 'blue' | 'light-blue' | 'cyan' | 'green' | 'lime' | 'yellow' | 'orange' | 'red' | 'magenta' | 'purple';
  /** Icon name shown before the label at 24px (Front Icon), e.g. "check_circle_true". Decorative. */
  icon?: string;
  /** Corner shape: "rounded" (radius 8, default) or "pill" (fully rounded, as in the garbage-category example). */
  shape?: 'rounded' | 'pill';
  /** The keyword — keep it to a word or two. */
  children?: React.ReactNode;
}
export declare function ChipLabel(props: ChipLabelProps): React.ReactElement;

// ---- ChipTag ----
export interface ChipTagProps extends React.HTMLAttributes<HTMLSpanElement> {
  /** Icon name shown before the label at 24px (Front Icon), e.g. "avatar_false". Decorative. */
  icon?: string;
  /** Called when the remove (×) action button is pressed. Providing it shows the Action Button. */
  onRemove?: (event: React.MouseEvent<HTMLButtonElement>) => void;
  /** Show the action button without a handler (e.g. inside a form that handles clicks itself). */
  removable?: boolean;
  /** Accessible name of the remove button. Default: "<label>を削除" (or "削除" for non-string labels). */
  removeLabel?: string;
  /** The item text, e.g. a filter value or a recipient name. */
  children?: React.ReactNode;
}
export declare function ChipTag(props: ChipTagProps): React.ReactElement;

// ---- CloseButton ----
export interface CloseButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  /** "icon" = Icon Close Button (44x44 glyph with a small caption, default); "text" = Text Close Button (icon + 閉じる label, 36px tall). */
  variant?: 'icon' | 'text';
  /** Language of the caption: "ja" → 閉じる (default), "en" → Close. */
  lang?: 'ja' | 'en';
  /** Overrides the caption/label text. */
  children?: React.ReactNode;
}
export declare function CloseButton(props: CloseButtonProps): React.ReactElement;

export interface ActionIconButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  /** Hit area: 24 (icon only), 40 (8px padding) or 44 (10px padding, default). The glyph is always 24px. */
  size?: 24 | 40 | 44;
  /** Icon name, e.g. "edit_false", "trash_false", "more_vert_false". Default "dummy-icon_300". */
  icon?: string;
  /** Accessible name (aria-label and tooltip). Required — the button has no visible text. */
  label: string;
}
export declare function ActionIconButton(props: ActionIconButtonProps): React.ReactElement;

// ---- Combobox ----
export interface ComboboxOption {
  /** Value stored in `value` / submitted with `name`. */
  value: string;
  /** Visible text; defaults to value. */
  label?: string;
  /** Optgroup heading; consecutive options with the same group are listed under it, indented. */
  group?: string;
  /** Shown greyed out and skipped by keyboard navigation. */
  disabled?: boolean;
}
export interface ComboboxProps extends Omit<React.HTMLAttributes<HTMLDivElement>, 'onChange' | 'defaultValue'> {
  /** "select" = Combobox Select (extends <select>: opener slot + filterable list box, default); "input" = Combobox Input (extends <input type=text>: type-ahead suggestions). */
  mode?: 'select' | 'input';
  /** Size axis: lg (56px slot / 61px rows, default), md (48 / 53), sm (44 select or 40 input / 45). */
  size?: 'lg' | 'md' | 'sm';
  /** Select mode only: allow several values; selections show as chip labels and rows get checkboxes plus the 選択解除 / 選択済みのみ表示 controls. */
  multiple?: boolean;
  /** Choices: strings or option objects (with optional `group` for optgroups). */
  options: Array<string | ComboboxOption>;
  /** Controlled value: string (single select, or the typed text in input mode) or string[] (multiple). */
  value?: string | string[];
  /** Initial value (uncontrolled). */
  defaultValue?: string | string[];
  /** Called with the new value (string, string[] for multiple, or the text in input mode). */
  onChange?: (value: any) => void;
  /** Called with the filter / typed text, e.g. to fetch options and toggle `loading`. */
  onInputChange?: (text: string) => void;
  /** Start with the list box open (uncontrolled). */
  defaultOpen?: boolean;
  /** Called when the list box opens or closes. */
  onOpenChange?: (open: boolean) => void;
  /** Slot text when nothing is selected (select mode, default "選択してください") or input placeholder. */
  placeholder?: string;
  /** Placeholder of the filter field inside the select list box. Default "絞り込み". */
  searchPlaceholder?: string;
  /** Field label (Label Units, Medium Bold); also names the list box. */
  label?: React.ReactNode;
  /** Support text under the label. */
  supportText?: React.ReactNode;
  /** Adds the ※必須 marker. */
  required?: boolean;
  /** Error message (State=Error): red border and Dense 16px message below. */
  error?: React.ReactNode;
  /** Disabled state for the slot / input and chips. */
  disabled?: boolean;
  /** Shows the 読み込み中 spinner instead of options (State/Status=Loading). */
  loading?: boolean;
  /** Text under the spinner. Default "読み込み中". */
  loadingText?: string;
  /** Text when the filter matches nothing (State=No Results). Default "項目がありません". */
  noResultsText?: string;
  /** Number of chips shown before the "…" overflow chip (multiple). Default 3. */
  maxChips?: number;
  /** Form field name (hidden inputs in select mode, the text input in input mode). */
  name?: string;
}
export declare function Combobox(props: ComboboxProps): React.ReactElement;

// ---- DatePicker ----
export interface DatePickerValue {
  /** Year digits as typed, e.g. "2025". */
  year?: string;
  /** Month digits as typed, e.g. "01". */
  month?: string;
  /** Day digits as typed, e.g. "20". */
  day?: string;
}
export interface DatePickerDate {
  /** Full year, e.g. 2025. */
  year: number;
  /** Month 1–12. */
  month: number;
  /** Day of month 1–31. */
  day: number;
}
export interface DatePickerProps extends Omit<React.FieldsetHTMLAttributes<HTMLFieldSetElement>, 'onChange' | 'defaultValue'> {
  /** Type axis: "consolidated" (one framed field with 年/月/日 units, default) or "separated" (one box per part with the unit notched into the top border). */
  type?: 'consolidated' | 'separated';
  /** Size axis: lg 56px (default), md 48px, sm 40px tall (separated boxes add a 12px label notch above). */
  size?: 'lg' | 'md' | 'sm';
  /** Label text rendered as the fieldset legend. Omit to hide it — then pass aria-label. */
  label?: React.ReactNode;
  /** Support text under the label (e.g. "例：2025年01月20日"), linked to every part with aria-describedby. */
  supportText?: React.ReactNode;
  /** Error state: red border(s) and aria-invalid. Implied when errorText is set. */
  error?: boolean;
  /** Error text under the field. Spec default copy: "＊正しい日付を入力してください。". */
  errorText?: React.ReactNode;
  /** Shows the "※必須" marker and sets aria-required on each part. */
  required?: boolean;
  /** Shows the "※任意" marker (ignored when required). */
  optional?: boolean;
  /** Override for the required marker text. Default "※必須". */
  requiredText?: string;
  /** Override for the optional marker text. Default "※任意". */
  optionalText?: string;
  /** Controlled value (strings as typed). */
  value?: DatePickerValue;
  /** Initial value when uncontrolled. */
  defaultValue?: DatePickerValue;
  /** Called with the whole next value whenever a part is typed or a date is picked/cleared in the calendar. */
  onChange?: (value: DatePickerValue) => void;
  /** Show Year: set false for month/day only. Default true. */
  showYear?: boolean;
  /** Show Day: set false for year/month only. Default true. */
  showDay?: boolean;
  /** Show Calendar Button: adds the button that opens the Calendar Panel in a popover. Default false. */
  showCalendarButton?: boolean;
  /** Disables every part and the calendar button (grey fill). */
  disabled?: boolean;
  /** Readonly state: dashed border, values focusable but not editable; calendar button disabled. */
  readOnly?: boolean;
  /** Base form name; parts are submitted as `${name}-year`, `${name}-month`, `${name}-day`. */
  name?: string;
  /** Year unit text. Default "年". */
  yearText?: string;
  /** Month unit text. Default "月". */
  monthText?: string;
  /** Day unit text. Default "日". */
  dayText?: string;
  /** First year offered by the calendar's year opener. Default today − 100. */
  minYear?: number;
  /** Last year offered by the calendar's year opener. Default today + 10. */
  maxYear?: number;
}
export declare function DatePicker(props: DatePickerProps): React.ReactElement;

export interface DatePickerCalendarProps extends Omit<React.HTMLAttributes<HTMLDivElement>, 'onSelect'> {
  /** Selected date (Date Cell State=Selected). */
  value?: DatePickerDate | null;
  /** Month shown first when there is no value: { year, month }. Defaults to today's month. */
  defaultMonth?: { year: number; month: number };
  /** Called when a date cell is activated (click, Enter or Space). */
  onSelect?: (date: DatePickerDate) => void;
  /** Called by the "削除" action. */
  onClear?: () => void;
  /** Called by the "今日" action; when omitted the action calls onSelect with today. */
  onToday?: (date: DatePickerDate) => void;
  /** First year in the year opener. Default today − 100. */
  minYear?: number;
  /** Last year in the year opener. Default today + 10. */
  maxYear?: number;
  /** Overrides "today" (for tests and previews). */
  today?: Date;
  /** Moves focus into the date grid on mount (used by DatePicker's popover). */
  autoFocus?: boolean;
  /** Clear action label. Default "削除". */
  clearLabel?: string;
  /** Today action label. Default "今日". */
  todayLabel?: string;
}
export declare function DatePickerCalendar(props: DatePickerCalendarProps): React.ReactElement;

// ---- Disclosure ----
export interface DisclosureProps extends Omit<React.DetailsHTMLAttributes<HTMLDetailsElement>, 'open'> {
  /** Text of the toggle (summary) row. */
  summary: React.ReactNode;
  /** Controlled expanded state (Expand axis). */
  open?: boolean;
  /** Initial expanded state when uncontrolled. Default false. */
  defaultOpen?: boolean;
  /** Called with the next expanded state when the summary is activated. */
  onOpenChange?: (open: boolean) => void;
  /** Show the Return link (「…」の先頭に戻る) at the end of the content. Default false. */
  returnLink?: boolean;
  /** Return link text. Default 「{summary}」の先頭に戻る when summary is a string. */
  returnLabel?: React.ReactNode;
  /** Id of the summary (return-link target); generated when omitted. */
  id?: string;
  /** Supplementary content revealed when expanded. */
  children?: React.ReactNode;
}
export declare function Disclosure(props: DisclosureProps): React.ReactElement;

// ---- Divider ----
export interface DividerProps extends React.HTMLAttributes<HTMLHRElement> {
  /** Line style: "solid" (default) or "dash" (dash and gap are each 2 × weight). */
  variant?: 'solid' | 'dash';
  /** Line color: "gray-420" (default, decorative), "gray-536" (meets 3:1 contrast), "black" (strongest). */
  color?: 'gray-420' | 'gray-536' | 'black';
  /** Line thickness in px, 1–4. Default 1. */
  weight?: 1 | 2 | 3 | 4;
  /** Vertical margin above and below the line in px (default 16). */
  spacing?: number;
}
export declare function Divider(props: DividerProps): React.ReactElement;

// ---- Drawer ----
export interface DrawerProps extends Omit<React.DialogHTMLAttributes<HTMLDialogElement>, 'open' | 'title' | 'onClose'> {
  /** Controlled open state. The drawer is always modal (showModal). */
  open?: boolean;
  /** Initial open state when uncontrolled. */
  defaultOpen?: boolean;
  /** Called with false when the user closes the drawer (close button, Escape, backdrop click). */
  onOpenChange?: (open: boolean) => void;
  /** Called when the user asks to close the drawer. */
  onClose?: (event: React.SyntheticEvent) => void;
  /** Expansion pattern: "right" (default, 390px from the right), "left" (390px from the left), "full" (whole screen). */
  side?: 'right' | 'left' | 'full';
  /** Optional heading in the header bar; it names the dialog. Without it, aria-label (default "メニュー") is used. */
  title?: React.ReactNode;
  /** Label of the text close button. Default "閉じる". */
  closeLabel?: string;
  /** Drawer content, e.g. a MobileMenu. Add data-autofocus to the element that should receive focus first. */
  children?: React.ReactNode;
}
export declare function Drawer(props: DrawerProps): React.ReactElement;

// ---- EmergencyBanner ----
export interface EmergencyBannerAction {
  /** Button label, e.g. "避難所の一覧を見る". */
  label: React.ReactNode;
  /** Destination URL (renders an <a>). */
  href?: string;
  /** Click handler (renders a <button> when no href). */
  onClick?: (event: React.MouseEvent) => void;
}
export interface EmergencyBannerProps extends Omit<React.HTMLAttributes<HTMLElement>, 'title'> {
  /** Platform axis: "desktop" (24px title, 20px body, 32px padding) or "mobile" (20px title, 16px body). Default "desktop". */
  platform?: 'desktop' | 'mobile';
  /** Title. By convention it starts with 【緊急】. */
  title: React.ReactNode;
  /** Heading level used for the title. Default 2. */
  headingLevel?: 1 | 2 | 3 | 4 | 5 | 6;
  /** Optional update date/time (Show Date), e.g. "2025年1月1日 06:00更新". */
  date?: React.ReactNode;
  /** Optional call to action (Link=True). Rendered as a red solid button inside a red outline frame. */
  action?: EmergencyBannerAction;
  /** Description. */
  children?: React.ReactNode;
}
export declare function EmergencyBanner(props: EmergencyBannerProps): React.ReactElement;

// ---- FileUpload ----
export interface FileUploadFile {
  /** File name shown in the selection list. */
  name: string;
  /** Size in bytes, shown next to the name and used by the summary. */
  size?: number;
}
export interface FileUploadProps extends Omit<React.HTMLAttributes<HTMLDivElement>, 'onChange'> {
  /** Type axis: "drop-area" (button inside a drag-and-drop area, default) or "button" (Button Only). */
  type?: 'drop-area' | 'button';
  /** Allow several files; the selection list becomes numbered (Type=Multiple) and new picks are appended. */
  multiple?: boolean;
  /** Controlled list of selected files (File objects or {name,size}). */
  files?: Array<File | FileUploadFile>;
  /** Initial list of selected files (uncontrolled). */
  defaultFiles?: Array<File | FileUploadFile>;
  /** Called with the full new list after a pick, drop or 解除. */
  onChange?: (files: Array<File | FileUploadFile>) => void;
  /** Passed to the native input, e.g. ".jpg,.png,.pdf". */
  accept?: string;
  /** Form field name of the native file input. */
  name?: string;
  /** Field label (Label Units, Medium Bold). */
  label?: React.ReactNode;
  /** Support text under the label; newlines are kept. */
  supportText?: React.ReactNode;
  /** Marks the field required (adds ※必須). */
  required?: boolean;
  /** Field-level error message (State=Error): red border on the area / button and the message under the button. */
  error?: React.ReactNode;
  /** Per-file check; return one or more messages to show that item in the error style (Error Mixed). */
  validate?: (file: File | FileUploadFile) => string | string[] | null | undefined;
  /** Show the Select Summary line (count, MB and bytes) once files are selected. */
  showSummary?: boolean;
  /** Button label. Default "ファイルを選択". */
  buttonLabel?: string;
  /** Text next to the button in the drop area. Default "または、このエリア内にドラッグ＆ドロップ". */
  dropText?: string;
  /** Label of the checkbox that widens the drop target to the whole window (Full Drop Area). */
  wideLabel?: string;
  /** Disables picking and dropping. */
  disabled?: boolean;
}
export declare function FileUpload(props: FileUploadProps): React.ReactElement;

// ---- FormControlLabel ----
export interface FormControlLabelProps extends React.HTMLAttributes<HTMLElement> {
  /** Size axis: sm (Std-16 label, 4px gap), md (Std-17 label, 8px gap), lg (Std-18 label, 8px gap). Default "md". */
  size?: 'sm' | 'md' | 'lg';
  /** Weight axis: label text weight. Default "bold". */
  weight?: 'normal' | 'bold';
  /** Element used: "label" (default, row is a <label htmlFor>), "legend" (to caption a <fieldset>), or "div" (plain text). */
  as?: 'label' | 'legend' | 'div';
  /** id of the control the label names (as="label" only). */
  htmlFor?: string;
  /** Requirements marker: "required" (※必須, red), "optional" (※任意), "readonly" (編集不可 badge), "disabled" (無効 badge). Omit to hide. */
  requirement?: 'required' | 'optional' | 'readonly' | 'disabled';
  /** Overrides the default marker text. */
  requirementText?: string;
  /** Support text shown under the label (Show Support Text). Reference it from the control via aria-describedby={supportId}. */
  supportText?: React.ReactNode;
  /** id given to the support text element. Defaults to a generated id. */
  supportId?: string;
  /** The label text. */
  children?: React.ReactNode;
}
export declare function FormControlLabel(props: FormControlLabelProps): React.ReactElement;

// ---- HamburgerMenuButton ----
export interface HamburgerMenuButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  /** Component set: "text" = Desktop & Mobile Button (24px icon + label, 36px tall, default); "icon" = 44px Icon Button with a caption under the glyph. */
  variant?: 'text' | 'icon';
  /** Type axis: "menu" (hamburger glyph, opens the menu, default) or "close" (× glyph, closes it). */
  type?: 'menu' | 'close';
  /** Lang axis: default label language — "ja" (メニュー / 閉じる, default) or "en" (Menu / Close; MENU / CLOSE on the icon button). */
  lang?: 'ja' | 'en';
  /** Overrides the default label. Keep it short; it is also the accessible name. */
  children?: React.ReactNode;
}
export declare function HamburgerMenuButton(props: HamburgerMenuButtonProps): React.ReactElement;

// ---- HeaderContainer ----
export interface HeaderContainerProps extends Omit<React.HTMLAttributes<HTMLElement>, 'title'> {
  /** Layout: "slim" (default) = logo, menu and utility in one row; "full" = logo + utility on top, menu on its own full-width row. */
  layout?: 'slim' | 'full';
  /** Site / service name shown in the logo area (text title slot, Bold 16/1.5). Ignored when `logo` is given. */
  title?: React.ReactNode;
  /** Makes the title a link, usually to the top page. */
  titleHref?: string;
  /** Custom logo content (e.g. an <a><img alt="…"></a>) replacing the text title. */
  logo?: React.ReactNode;
  /** Header container items area (2): utility links, language selector, search, HamburgerMenuButton… */
  utility?: React.ReactNode;
  /** Horizontal menu area (3), typically a HorizontalMenu. */
  nav?: React.ReactNode;
  /** Extra content rendered after the inner row (e.g. a MegaMenu overlay layer). */
  children?: React.ReactNode;
}
export declare function HeaderContainer(props: HeaderContainerProps): React.ReactElement;

// ---- Heading ----
export interface HeadingProps extends React.HTMLAttributes<HTMLHeadingElement> {
  /** Semantic level → h1…h6. Default 2. */
  level?: 1 | 2 | 3 | 4 | 5 | 6;
  /** Visual size (Figma Size axis) in px. Defaults by level: h1 36, h2 32, h3 28, h4 24, h5 20, h6 18. 64/57 use the Display styles. */
  size?: 64 | 57 | 45 | 36 | 32 | 28 | 24 | 20 | 18 | 16;
  /** Shoulder (Style=Shoulder): short lead text shown above the heading, grouped with it in an <hgroup>. Sized one step down (28…16). */
  shoulder?: React.ReactNode;
  /** Front icon name (Style=Front-icon), e.g. "document_false"; sized to the heading (80px at 64 … 20px at 16). Decorative. */
  icon?: string;
  /** Show the key-color chip bar before the text (Style=Chip). */
  chip?: boolean;
  /** Add a key-color ruler under the heading, weight in px (Building Blocks / Rulers); spaced 4× its weight above and below. */
  ruler?: 2 | 4 | 6 | 8;
  /** Heading text. */
  children?: React.ReactNode;
}
export declare function Heading(props: HeadingProps): React.ReactElement;

// ---- HorizontalMenu ----
export interface HorizontalMenuItem {
  /** Visible label (Dns-16B-130). */
  label: React.ReactNode;
  /** Destination for a plain link item. Ignored when the item is expandable. */
  href?: string;
  /** Marks the item for the current page/section: Selected style (4px key-900 underline) and aria-current="page" on links. */
  current?: boolean;
  /** Optional 24px front icon name (Show Front-icon). */
  icon?: string;
  /** Content shown under the bar while the item is open, e.g. a MegaMenu. Makes the item a disclosure button with a caret. */
  panel?: React.ReactNode;
  /** Makes the item a disclosure button (caret down/up) without a built-in panel; handle the content yourself via onExpandedChange. */
  expandable?: boolean;
  /** Click handler for the link or button. */
  onClick?: (event: React.MouseEvent) => void;
  /** React key; defaults to the index. */
  key?: React.Key;
}
export interface HorizontalMenuProps extends Omit<React.HTMLAttributes<HTMLElement>, 'onChange'> {
  /** Menu items, left to right. */
  items: HorizontalMenuItem[];
  /** Controlled index of the open (expanded) item, or null for none. Caret=Up on that item. */
  expandedIndex?: number | null;
  /** Initially open item when uncontrolled. */
  defaultExpandedIndex?: number | null;
  /** Called with the new open index (or null) when an item is toggled, Escape is pressed or the user clicks outside. */
  onExpandedChange?: (index: number | null) => void;
  /** Accessible name of the <nav> landmark. Default "メインメニュー". */
  'aria-label'?: string;
}
export declare function HorizontalMenu(props: HorizontalMenuProps): React.ReactElement;

// ---- ImageSingle ----
export interface ImageSingleProps extends React.HTMLAttributes<HTMLElement> {
  /** Image URL. */
  src: string;
  /** Alternative text; describe the content, or "" when the image is decorative. */
  alt: string;
  /** Caption below the image (Show Caption). Rendered as <figcaption>. */
  caption?: React.ReactNode;
  /** Img-caption Area type: "dashed" (gray-700 dashed frame, default) or "solid" (gray-420 frame). */
  captionStyle?: 'dashed' | 'solid';
  /** Type axis: "border" (gray-420 frame), "borderless" or "link" (blue-900 frame, 4px on hover). Defaults to "link" when href is set, otherwise "border". */
  variant?: 'border' | 'borderless' | 'link';
  /** Wraps the image in a link. */
  href?: string;
  /** With href: opens in a new tab. */
  external?: boolean;
  /** Intrinsic width attribute of the image (reserves layout space). */
  width?: number;
  /** Intrinsic height attribute of the image. */
  height?: number;
  /** Extra attributes for the <img> (loading, srcSet, sizes…). */
  imgProps?: React.ImgHTMLAttributes<HTMLImageElement>;
}
export declare function ImageSingle(props: ImageSingleProps): React.ReactElement;

// ---- InputText ----
export interface InputTextProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'size'> {
  /** Size axis: lg 56px (default), md 48px, sm 40px tall (sm uses radius-4 and a 4px label gap). */
  size?: 'lg' | 'md' | 'sm';
  /** Label text (Label Units). Omit to hide the label (Show Label=false) — then pass aria-label. */
  label?: React.ReactNode;
  /** Support text shown under the label and linked with aria-describedby. */
  supportText?: React.ReactNode;
  /** Error state: red border and aria-invalid. Implied when errorText is set. */
  error?: boolean;
  /** Error text shown under the field (e.g. "＊氏名を入力してください。"). */
  errorText?: React.ReactNode;
  /** Shows the "※必須" marker and sets aria-required. */
  required?: boolean;
  /** Shows the "※任意" marker (ignored when required). */
  optional?: boolean;
  /** Override for the required marker text. Default "※必須". */
  requiredText?: string;
  /** Override for the optional marker text. Default "※任意". */
  optionalText?: string;
  /** Readonly state: dashed border, value still focusable and selectable. */
  readOnly?: boolean;
  /** Fixed width for the field only (e.g. 69 for a 3-digit postal code part); the label keeps its natural width. */
  inputWidth?: number | string;
  /** Extra class for the <input> itself. className/style go to the root wrapper; all other props go to the <input>. */
  inputClassName?: string;
}
export declare function InputText(props: InputTextProps): React.ReactElement;

// ---- LanguageSelector ----
export interface LanguageSelectorLanguage {
  /** Identifier passed to onChange. */
  value: string;
  /** Language name written in that language (e.g. "English", "한국어"). */
  label: string;
  /** BCP 47 tag set as lang / hreflang on the option. */
  lang?: string;
  /** URL of the page in that language; when omitted the option only calls onChange. */
  href?: string;
}
export interface LanguageSelectorProps extends Omit<React.HTMLAttributes<HTMLDivElement>, 'onChange'> {
  /** Languages in the menu. Default 日本語 / English / 简体中文 / 繁体中文 / 한국어. */
  languages?: LanguageSelectorLanguage[];
  /** Selected language value, controlled. */
  value?: string;
  /** Initially selected language when uncontrolled. Default the first language. */
  defaultValue?: string;
  /** Called when a language is chosen. */
  onChange?: (value: string, language: LanguageSelectorLanguage) => void;
  /** Menu open state, controlled (caret turns up when open). */
  open?: boolean;
  /** Initial open state when uncontrolled. */
  defaultOpen?: boolean;
  /** Called when the menu opens or closes. */
  onOpenChange?: (open: boolean) => void;
  /** Accessible name of the icon opener. Default "Language（言語選択）". */
  label?: string;
  /** Menu alignment under the opener: "end" (right edge, default) or "start". */
  align?: 'start' | 'end';
}
export declare function LanguageSelector(props: LanguageSelectorProps): React.ReactElement;

// ---- List ----
export type ListNumbering = 'decimal' | 'upper-alpha' | 'lower-alpha' | 'upper-roman' | 'lower-roman' | 'dai-fullwidth' | 'dai-kanji'
  | 'fullwidth' | 'kanji' | 'paren-fullwidth' | 'paren-kanji' | 'katakana' | 'paren-katakana' | 'iroha' | 'paren-iroha' | 'circled';
export interface ListProps extends React.HTMLAttributes<HTMLUListElement | HTMLOListElement> {
  /** true → numbered list (<ol>, List with Numbers); false → bulleted list (<ul>, List with List Marks). Default false. */
  ordered?: boolean;
  /** Bullet shape. Default by nesting depth: disc → circle → square. */
  marker?: 'disc' | 'circle' | 'square' | 'square-outlined';
  /** Bullet size in px. Default 6. */
  markerSize?: 4 | 6 | 8 | 10;
  /** Number marker type: "decimal" 1. · "upper-alpha" A. · "lower-alpha" a. · "upper-roman" I. · "lower-roman" i. · "dai-fullwidth" 第１ · "dai-kanji" 第一 · "fullwidth" １ · "kanji" 一 · "paren-fullwidth" （１） · "paren-kanji" （一） · "katakana" ア · "paren-katakana" （ア） · "iroha" イ · "paren-iroha" （イ） · "circled" ①. Default "decimal". */
  numbering?: ListNumbering;
  /** Vertical padding above and below each item in px (Spacing axis). Default 8; nested lists inherit. */
  spacing?: 4 | 8 | 12;
  /** Extra left indent for a flat list in px (Indent axis). Nested lists get 32px per level automatically. */
  indent?: 0 | 32 | 64;
  /** First number of a numbered list. Default 1. */
  start?: number;
  /** ListItem elements. */
  children?: React.ReactNode;
}
export interface ListItemProps extends React.LiHTMLAttributes<HTMLLIElement> {
  /** Makes the item text a link (Link=True): blue-1000, underlined. */
  href?: string;
  /** Opens in a new tab and shows the 16px new-window tail icon (Show Tail-icon). */
  external?: boolean;
  /** Overrides this item's number (and continues counting from it). */
  value?: number;
  /** Item text; a nested <List> placed here is rendered below it, indented 32px. */
  children?: React.ReactNode;
}
export declare function List(props: ListProps): React.ReactElement;
export declare function ListItem(props: ListItemProps): React.ReactElement;

// ---- MegaMenu ----
export interface MegaMenuLinkItem {
  /** Link text (Dns-16N-130). */
  label: React.ReactNode;
  /** Destination URL. */
  href: string;
  /** Optional 24px front icon name. */
  icon?: string;
  /** Opens in a new tab and shows the new_window tail icon. */
  external?: boolean;
  /** Click handler. */
  onClick?: (event: React.MouseEvent) => void;
}
export interface MegaMenuBanner {
  /** Caption shown under the image (also the link text). */
  label: React.ReactNode;
  /** Destination URL. */
  href: string;
  /** Image URL (rendered as a decorative <img alt="">) or any node, e.g. an inline SVG illustration. */
  image?: string | React.ReactNode;
  /** Click handler. */
  onClick?: (event: React.MouseEvent) => void;
}
export interface MegaMenuColumn {
  /** Mega Menu / Item Type axis: "menu" (link list), "large-banner" (one 220px image banner), "banner" (two 84px banners), "banner-menu" (one banner + links). Inferred from banners/items when omitted. */
  type?: 'menu' | 'large-banner' | 'banner' | 'banner-menu';
  /** Links for "menu" and "banner-menu" columns. */
  items?: MegaMenuLinkItem[];
  /** Banners for the banner types. */
  banners?: MegaMenuBanner[];
  /** Optional accessible name for the column's link list. */
  label?: string;
}
export interface MegaMenuProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Title of the panel (Std-28B-150), usually the label of the opening menu item. */
  title?: React.ReactNode;
  /** Sub title under the title (Std-16N-170). Line breaks in a string are kept. */
  description?: React.ReactNode;
  /** Link to the 2nd-layer (category top) page shown under the title. */
  titleLink?: { href: string; label: React.ReactNode };
  /** Content columns, left to right (typically up to three). */
  columns?: MegaMenuColumn[];
  /** Shows the 閉じる text close button and is called on it or on Escape inside the panel. */
  onClose?: (event: React.SyntheticEvent) => void;
  /** Close button label. Default "閉じる". */
  closeLabel?: string;
  /** Heading level of the title. Default 2. */
  headingLevel?: 2 | 3 | 4;
  /** Extra content appended after the columns. */
  children?: React.ReactNode;
}
export declare function MegaMenu(props: MegaMenuProps): React.ReactElement;
export interface MegaMenuOverlayProps extends React.HTMLAttributes<HTMLDivElement> {}
/** Overlay Shade (opacity-gray-600, fixed full-screen) placed behind an open mega menu; give it onClick to close. */
export declare function MegaMenuOverlay(props: MegaMenuOverlayProps): React.ReactElement;

// ---- MenuList ----
export interface MenuListItem {
  /** "category" renders a non-interactive Category Title; omit for a menu item / section title. */
  type?: 'item' | 'category';
  /** Visible text (List Item / Menu / Section Title / Category). */
  label: React.ReactNode;
  /** Renders the item as a link. Without it the item is a <button>. */
  href?: string;
  /** Click handler (buttons and links). */
  onClick?: (event: React.MouseEvent) => void;
  /** Front icon name, 24px (Show Front-icon). */
  icon?: string;
  /** End icon name, 16px (Show End-icon). Standard items default to "arrow_right_300"; pass null to hide. */
  endIcon?: string | null;
  /** Shows the new_window tail icon and opens the link in a new tab (Show Tail-icon). */
  external?: boolean;
  /** Standard: the page you are on (State=Current). Sets aria-current. */
  current?: boolean;
  /** Boxed: the chosen item (State=Selected). Sets aria-current. */
  selected?: boolean;
  /** Disables a button item. */
  disabled?: boolean;
  /** Boxed only: secondary line under the label (With Thumbnail / Show Description). */
  description?: React.ReactNode;
  /** Boxed only: 48×48 thumbnail node (With Thumbnail / Show Thumbnail). */
  thumbnail?: React.ReactNode;
  /** Standard only: child items — turns the row into a collapsible Section Title with a caret. */
  items?: MenuListItem[];
  /** Section title: controlled expanded state (Caret Direction Up = expanded). */
  expanded?: boolean;
  /** Section title: initial expanded state when uncontrolled. */
  defaultExpanded?: boolean;
  /** Section title: called with the next expanded state. */
  onToggle?: (expanded: boolean, event: React.MouseEvent) => void;
  /** React key; defaults to the index. */
  key?: React.Key;
  /** Extra class on the item element. */
  className?: string;
}
export interface MenuListProps extends Omit<React.HTMLAttributes<HTMLUListElement>, 'children'> {
  /** "standard" (rounded items for local navigation, default) or "boxed" (square items inside a box / menu list box). */
  variant?: 'standard' | 'boxed';
  /** Size axis: "regular" 44px rows (default) or "small" 36px rows. */
  size?: 'regular' | 'small';
  /** Boxed thumbnail rows: draw a bottom divider (Border Bottom=True). */
  divided?: boolean;
  /** The items, section titles and category titles, in order. */
  items: MenuListItem[];
}
export declare function MenuList(props: MenuListProps): React.ReactElement;

// ---- MenuListBox ----
export interface MenuListBoxProps extends Omit<React.HTMLAttributes<HTMLDivElement>, 'children'> {
  /** Opener text — names what the box lists (e.g. "並び替え"). */
  label: React.ReactNode;
  /** Opener style axis: "text" (default), "outlined" or "filled". */
  variant?: 'text' | 'outlined' | 'filled';
  /** Opener size axis: "default" 44px or "small" 36px. */
  size?: 'default' | 'small';
  /** Opener text weight axis: "bold" (default) or "normal". */
  weight?: 'bold' | 'normal';
  /** Front icon name shown before the label, 20px (Show Front Icon). */
  icon?: string;
  /** Controlled open state (Arrow=Up when open). */
  open?: boolean;
  /** Initial open state when uncontrolled. */
  defaultOpen?: boolean;
  /** Called with the next open state (toggle, Escape, outside click). */
  onOpenChange?: (open: boolean) => void;
  /** Max height of the box; content beyond it scrolls (Menu List with Scrollbar). */
  maxHeight?: number | string;
  /** Render the box in the document flow instead of as an overlay. */
  inline?: boolean;
  /** Set false to keep the box open on outside clicks. Default true. */
  closeOnOutsideClick?: boolean;
  /** Box content — normally a MenuList with variant="boxed". */
  children?: React.ReactNode;
}
export declare function MenuListBox(props: MenuListBoxProps): React.ReactElement;

// ---- MobileMenu ----
export interface MobileMenuProps extends React.HTMLAttributes<HTMLElement> {
  /** Accessible name of the <nav> landmark. Default "メニュー". */
  'aria-label'?: string;
  /** MobileMenuItem, MobileMenuSection and MobileMenuDivider elements. */
  children?: React.ReactNode;
}
export declare function MobileMenu(props: MobileMenuProps): React.ReactElement;

export interface MobileMenuItemProps extends Omit<React.LiHTMLAttributes<HTMLLIElement>, 'onClick'> {
  /** Item text (Dns-16N-120). Children are used when omitted. */
  label?: React.ReactNode;
  /** Destination URL (link items). */
  href?: string;
  /** Optional 24px front icon name (Show Front-icon). */
  icon?: string;
  /** Opens in a new tab and shows the 16px new_window tail icon (Show Tail-icon). */
  external?: boolean;
  /** State=Selected: key-100 fill and aria-current="page". */
  current?: boolean;
  /** Indent=True: 32px left inset. Items nested via `items` are indented automatically. */
  indent?: boolean;
  /** Caret Direction=Right end icon, for a link that drills into a deeper menu level. */
  drilldown?: boolean;
  /** Nested MobileMenuItem elements; turns the row into an accordion button (Caret Direction=Down when closed, Up when open). */
  items?: React.ReactNode;
  /** Controlled open state of the nested items. */
  open?: boolean;
  /** Initial open state when uncontrolled. */
  defaultOpen?: boolean;
  /** Called with the next open state when the accordion row is toggled. */
  onOpenChange?: (open: boolean, event: React.MouseEvent) => void;
  /** Click handler for the row link/button. */
  onClick?: (event: React.MouseEvent) => void;
  children?: React.ReactNode;
}
export declare function MobileMenuItem(props: MobileMenuItemProps): React.ReactElement;

export interface MobileMenuSectionProps extends Omit<React.LiHTMLAttributes<HTMLLIElement>, 'title'> {
  /** Section title text (Dns-16B-120). */
  title: React.ReactNode;
  /** Optional 24px front icon (Style=Default, Show Front-icon). Ignored when `chip` is set. */
  icon?: string;
  /** Style=Section Bar: 4×20 color chip before the title — "gray" (solid-gray-600) or "key" (Custom Color, key-1000). */
  chip?: 'gray' | 'key';
  /** Indent=True: 32px left inset. */
  indent?: boolean;
  /** Makes the title a link with a Caret Direction=Right end icon. */
  href?: string;
  /** Makes the title an accordion button (caret down/up) that shows/hides the section items. */
  collapsible?: boolean;
  /** Controlled open state (collapsible sections). */
  open?: boolean;
  /** Initial open state when uncontrolled (collapsible sections). */
  defaultOpen?: boolean;
  /** Called with the next open state when a collapsible title is toggled. */
  onOpenChange?: (open: boolean, event: React.MouseEvent) => void;
  /** Heading level wrapping the title. Default 2. */
  headingLevel?: 2 | 3 | 4 | 5 | 6;
  /** MobileMenuItem elements of the section. */
  children?: React.ReactNode;
}
export declare function MobileMenuSection(props: MobileMenuSectionProps): React.ReactElement;

export interface MobileMenuDividerProps extends React.LiHTMLAttributes<HTMLLIElement> {}
/** 1px solid-gray-420 rule (33px tall block) between groups of items. */
export declare function MobileMenuDivider(props: MobileMenuDividerProps): React.ReactElement;

export interface MobileMenuBackButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  /** Label, e.g. the parent level name. Default "戻る". */
  children?: React.ReactNode;
}
/** Back Button: left arrow + underlined label, returns to the previous menu level. */
export declare function MobileMenuBackButton(props: MobileMenuBackButtonProps): React.ReactElement;

// ---- ModalDialog ----
export interface ModalDialogProps extends Omit<React.HTMLAttributes<HTMLDivElement>, 'title'> {
  /** Whether the dialog is shown (controlled). Nothing renders when false. */
  open: boolean;
  /** Called on Escape, the close button, or (with closeOnOverlayClick) a click on the shade. */
  onClose?: (event: React.SyntheticEvent) => void;
  /** Type axis: "desktop" (480px, 24px padding, default) or "mobile" (280px, stacked full-width buttons). */
  type?: 'desktop' | 'mobile';
  /** Dialog title (Headings, Size=28 on desktop). Used as the accessible name. */
  title: React.ReactNode;
  /** Optional icon name shown before the title, e.g. "warning_300-true". */
  titleIcon?: string;
  /** Heading level for the title. Default 2. */
  headingLevel?: 1 | 2 | 3 | 4 | 5 | 6;
  /** Show Close Button: renders the Text Close Button in the title area. Default true. */
  showCloseButton?: boolean;
  /** Overrides the close button label (default 閉じる). */
  closeLabel?: React.ReactNode;
  /** Contents (Show Contents). Std-16N-170 text; block children are spaced 24px apart. */
  children?: React.ReactNode;
  /** Button Stack (Show Action Area), in desktop order left→right, e.g. [outlined, solid-fill]. Mobile stacks them reversed, primary on top. */
  actions?: React.ReactNode;
  /** A low-emphasis action placed at the far left on desktop and last on mobile, e.g. a text キャンセル button. */
  startAction?: React.ReactNode;
  /** Close when the overlay shade is clicked. Default false. */
  closeOnOverlayClick?: boolean;
  /** Render in the document flow (shade as a box, no focus move/scroll lock) instead of fixed over the viewport — for docs and previews. */
  inline?: boolean;
}
export declare function ModalDialog(props: ModalDialogProps): React.ReactElement | null;

// ---- NoticeBlock ----
export interface NoticeBlockProps extends Omit<React.HTMLAttributes<HTMLDivElement>, 'title'> {
  /** Style axis: border-rounded (white, rounded), border-solid (white, square with a 4px colour bar), fill-rounded (tinted, rounded), fill-solid (tinted, square with bar). Default "border-rounded". */
  variant?: 'border-rounded' | 'border-solid' | 'fill-rounded' | 'fill-solid';
  /** Type axis: "notice1" (neutral gray) or "notice2" (light blue). Default "notice1". */
  type?: 'notice1' | 'notice2';
  /** Optional title (Show Title), Std-16B-170. */
  title?: React.ReactNode;
  /** Renders the title as h1–h6; without it the title is a bold paragraph. */
  headingLevel?: 1 | 2 | 3 | 4 | 5 | 6;
  /** Optional outlined chip label before the title (Show Chip Label), e.g. "補足". */
  chipLabel?: React.ReactNode;
  /** Optional disclosures (Show Disclosures) — one or more NoticeBlockDisclosure elements. */
  disclosures?: React.ReactNode;
  /** Main contents (Show Contents). */
  children?: React.ReactNode;
}
export declare function NoticeBlock(props: NoticeBlockProps): React.ReactElement;

export interface NoticeBlockDisclosureProps extends Omit<React.DetailsHTMLAttributes<HTMLDetailsElement>, 'onToggle'> {
  /** Summary text next to the toggle control. */
  summary: React.ReactNode;
  /** Optional outlined chip label in the summary row. */
  chipLabel?: React.ReactNode;
  /** Controlled expanded state (Expand axis). */
  open?: boolean;
  /** Initial expanded state when uncontrolled. Default false. */
  defaultOpen?: boolean;
  /** Called with the next expanded state when the summary is activated. */
  onToggle?: (open: boolean) => void;
  /** Content revealed when expanded (indented 32px). */
  children?: React.ReactNode;
}
export declare function NoticeBlockDisclosure(props: NoticeBlockDisclosureProps): React.ReactElement;

// ---- NotificationBanner ----
export interface NotificationBannerAction {
  /** Button label, e.g. "詳細を確認する". */
  label: React.ReactNode;
  /** Click handler (renders a <button>). */
  onClick?: (event: React.MouseEvent) => void;
  /** Destination URL (renders a button-styled <a>). */
  href?: string;
}
export interface NotificationBannerProps extends Omit<React.HTMLAttributes<HTMLElement>, 'title'> {
  /** Usage axis: success, error, warning, info1 (blue) or info2 (gray). Sets the icon, border and button colour. Default "info1". */
  usage?: 'success' | 'error' | 'warning' | 'info1' | 'info2';
  /** Style axis: "standard" (rounded, 3px border) or "color-chip" (square, 2px border plus a coloured bar on the left). Default "standard". */
  variant?: 'standard' | 'color-chip';
  /** Platform set: "desktop" (36px icon, 20px title) or "mobile" (24px icon, 17px title). Default "desktop". */
  platform?: 'desktop' | 'mobile';
  /** Mobile only — Button axis: stack the actions ("vertical", Ver) or put them side by side ("horizontal", Horiz). Default "vertical". */
  buttonLayout?: 'vertical' | 'horizontal';
  /** Banner title (required). */
  title: React.ReactNode;
  /** Heading level used for the title. Default 2. */
  headingLevel?: 1 | 2 | 3 | 4 | 5 | 6;
  /** Optional date line shown above the description (Show Date), e.g. "2025年4月1日 10:00". */
  date?: React.ReactNode;
  /** Called when the close button is pressed. Supplying it shows the close button (Show Close). */
  onClose?: (event: React.MouseEvent<HTMLButtonElement>) => void;
  /** Shows the close button and hides the banner itself when pressed (uncontrolled). */
  dismissible?: boolean;
  /** Close button label. Default "閉じる". */
  closeLabel?: string;
  /** Close set Type: "default" (icon + label, 36px tall) or "compact" (44×44, small label under the icon). Default "default". */
  closeType?: 'default' | 'compact';
  /** Primary action (Show Primary Button), solid fill in the usage colour. */
  primaryAction?: NotificationBannerAction;
  /** Secondary action (Show Secondary Button), outlined in the usage colour. */
  secondaryAction?: NotificationBannerAction;
  /** Description body. */
  children?: React.ReactNode;
}
export declare function NotificationBanner(props: NotificationBannerProps): React.ReactElement;

// ---- PageNavigation ----
export interface PageNavigationProps extends Omit<React.HTMLAttributes<HTMLElement>, 'onChange'> {
  /** Type axis: "text" (underlined text buttons, 48px, default), "arrow" (round arrow buttons), "outlined" (bordered buttons, 56px). */
  type?: 'text' | 'arrow' | 'outlined';
  /** Size of the round buttons when type="arrow": l 44px (default), m 32px, s 24px, xs 20px circles. */
  arrowSize?: 'l' | 'm' | 's' | 'xs';
  /** Total number of pages. Default 1. */
  total?: number;
  /** Current page (1-based), controlled. */
  page?: number;
  /** Initial page when uncontrolled. Default 1. */
  defaultPage?: number;
  /** Called with the requested page number when previous / next is used. */
  onChange?: (page: number) => void;
  /** Label of the previous control. Default "前のページ" (e.g. "前の3件"). */
  previousLabel?: string;
  /** Label of the next control. Default "次のページ" (e.g. "次の3件"). */
  nextLabel?: string;
  /** Renders the previous control as a link. */
  previousHref?: string;
  /** Renders the next control as a link. */
  nextHref?: string;
  /** Replaces the "page / total" counter text. */
  label?: React.ReactNode;
  /** Accessible name of the nav landmark. Default "ページナビゲーション". */
  'aria-label'?: string;
}
export declare function PageNavigation(props: PageNavigationProps): React.ReactElement;

// ---- ProgressIndicator ----
export interface ProgressIndicatorProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Style axis: "spinner" (rotating), "linear" (sliding bar) or "static" (non-animated hourglass). Default "spinner". */
  variant?: 'spinner' | 'linear' | 'static';
  /** Composition axis: "stacked" (48px indicator / 240px bar above the label) or "inlined" (24px indicator / 80px bar beside the label). Default "stacked". */
  composition?: 'stacked' | 'inlined';
  /** Visible label (Show Label), e.g. "読み込み中". When omitted, a visually hidden "読み込み中" (or aria-label) is announced instead. */
  label?: React.ReactNode;
  /** Underlay axis: places the indicator on a white rounded panel with a gray border (for use over content or overlays). */
  underlay?: boolean;
  /** Linear only: 0–100 makes the bar determinate (role="progressbar"). Omit for an indeterminate animation. */
  value?: number;
}
export declare function ProgressIndicator(props: ProgressIndicatorProps): React.ReactElement;

// ---- Radio ----
export interface RadioProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'size' | 'type'> {
  /** Size axis: sm (24px control, 40px row), md (32px control, 48px row), lg (44px control, 60px row). Default "sm". */
  size?: 'sm' | 'md' | 'lg';
  /** Value submitted with the form and matched against RadioGroup value. */
  value?: string;
  /** Controlled checked state (normally managed by RadioGroup). */
  checked?: boolean;
  /** Error state: red ring and dot, aria-invalid. */
  error?: boolean;
  /** Disables the option. */
  disabled?: boolean;
  /** Ref to the underlying <input type="radio">. */
  inputRef?: React.Ref<HTMLInputElement>;
  /** Selection text. Other props go to the <input>; className and style go to the root <label>. */
  children?: React.ReactNode;
}
export declare function Radio(props: RadioProps): React.ReactElement;

export interface RadioGroupProps extends Omit<React.FieldsetHTMLAttributes<HTMLFieldSetElement>, 'onChange'> {
  /** Layout: "stacked" (one per row) or "inline" (wrapping row). Default "stacked". */
  layout?: 'stacked' | 'inline';
  /** Size axis, applied to the label and to every child Radio without its own size. Default "sm". */
  size?: 'sm' | 'md' | 'lg';
  /** Shared input name. Defaults to a generated one. */
  name?: string;
  /** Controlled selected value. */
  value?: string;
  /** Uncontrolled initial value. */
  defaultValue?: string;
  /** Called with the newly selected value. */
  onChange?: (value: string, event: React.ChangeEvent<HTMLInputElement>) => void;
  /** Group label rendered as the fieldset legend (Show Label). */
  label?: React.ReactNode;
  /** Legend weight. Default "bold". */
  labelWeight?: 'normal' | 'bold';
  /** Requirements marker next to the label. */
  requirement?: 'required' | 'optional' | 'readonly' | 'disabled';
  /** Support text under the label. */
  supportText?: React.ReactNode;
  /** Error text under the options (Show Error Text); any truthy value also puts every child in the error state. */
  error?: React.ReactNode | boolean;
  /** Radio elements (each with a value). */
  children?: React.ReactNode;
}
export declare function RadioGroup(props: RadioGroupProps): React.ReactElement;

// ---- ResourceList ----
export interface ResourceListProps extends React.HTMLAttributes<HTMLUListElement> {
  /** "list" (rows divided by a bottom border, default) or "frame" (each row a rounded card, 16px apart). */
  variant?: 'list' | 'frame';
  /** "inline" (default): only the title link / form control / action button are interactive.
   *  "whole": the entire contents area is one target (link, button, or label of the form control). */
  interaction?: 'inline' | 'whole';
  /** Form control shown at the start of every row: "none" (default), "checkbox" or "radio". */
  control?: 'none' | 'checkbox' | 'radio';
  /** Shared input name for the row controls (required for a radio group). */
  name?: string;
  /** ResourceListItem elements. */
  children?: React.ReactNode;
}
export declare function ResourceList(props: ResourceListProps): React.ReactElement;

export interface ResourceListAction {
  /** Accessible name of the function button, e.g. "その他の操作". */
  label: string;
  /** Icon name; default "more_vert_false". */
  icon?: string;
  /** Click handler. */
  onClick?: (event: React.MouseEvent<HTMLButtonElement>) => void;
  /** Disable only the action button. */
  disabled?: boolean;
}
export interface ResourceListItemProps extends Omit<React.LiHTMLAttributes<HTMLLIElement>, 'title' | 'onChange' | 'onClick'> {
  /** List title — the main, 20px bold line. */
  title: React.ReactNode;
  /** Small line above the title (Show Label). */
  label?: React.ReactNode;
  /** Trailing one-line text, e.g. a date or status (Show Sublabel). */
  sublabel?: React.ReactNode;
  /** Line under the title (Show Support Text). */
  supportText?: React.ReactNode;
  /** Front icon name, 24px (Show Front Icon). */
  icon?: string;
  /** Destination: the title becomes a link (inline) or the whole row does (whole). State=Link. */
  href?: string;
  /** Click handler for the title link / whole row. */
  onClick?: (event: React.MouseEvent) => void;
  /** Function / action button at the row end (Show Function Button). */
  action?: ResourceListAction;
  /** Controlled checked state of the row control; checked rows render as Selected. */
  checked?: boolean;
  /** Initial checked state when uncontrolled. */
  defaultChecked?: boolean;
  /** Change handler of the row control. */
  onChange?: (event: React.ChangeEvent<HTMLInputElement>) => void;
  /** Input value of the row control. */
  value?: string;
  /** Input name; overrides the list's name. */
  name?: string;
  /** Disables the control and action; with interaction="whole" the whole row is greyed out. */
  disabled?: boolean;
  /** Id of the row input (generated when omitted). */
  id?: string;
  /** Extra content appended inside the row. */
  children?: React.ReactNode;
}
export declare function ResourceListItem(props: ResourceListItemProps): React.ReactElement;

// ---- SearchBox ----
export interface SearchBoxOption {
  /** Value reported to onScopeChange / onSearch. */
  value: string;
  /** Visible text; defaults to value. */
  label?: string;
}
export interface SearchBoxProps extends Omit<React.HTMLAttributes<HTMLDivElement>, 'onChange'> {
  /** Size axis: lg 57px (default), md 48px, sm 40px tall. The solid button follows the same size. */
  size?: 'lg' | 'md' | 'sm';
  /** Scope axis: options for the search-scope selector at the left. Omit or pass [] to hide it. */
  scopes?: Array<string | SearchBoxOption>;
  /** Controlled scope value. */
  scope?: string;
  /** Initial scope value (uncontrolled). Defaults to the first option. */
  defaultScope?: string;
  /** Called with the new scope value. */
  onScopeChange?: (scope: string) => void;
  /** Caption above the scope value (lg / md only) and its accessible name. Default "検索対象". */
  scopeLabel?: string;
  /** Controlled query text. */
  value?: string;
  /** Initial query text (uncontrolled). */
  defaultValue?: string;
  /** Called with the new query text on every keystroke. */
  onChange?: (value: string) => void;
  /** Called on submit (Enter, button, or a shortcut chip) with the query and the scope. */
  onSearch?: (query: string, scope?: string) => void;
  /** Placeholder for the query field. */
  placeholder?: string;
  /** Accessible name of the query field. Default "サイト内検索". */
  label?: string;
  /** Search button: "solid" (Solid Fill button, default), "text" (icon + 検索 text), "icon" (44px icon-only, compact), "none". */
  buttonVariant?: 'solid' | 'text' | 'icon' | 'none';
  /** Button label (visible, or the accessible name for "icon"). Default "検索". */
  buttonLabel?: string;
  /** Fixed keywords shown as outlined small buttons below the box (Search Shortcuts). */
  shortcuts?: string[];
  /** Caption before the shortcuts. Default "よくある検索：". */
  shortcutsLabel?: string;
  /** Content of the advanced-search disclosure panel (Search Filters). Omit to hide the panel. */
  filters?: React.ReactNode;
  /** Disclosure label of the filters panel. Default "詳細検索". */
  filtersLabel?: string;
  /** Start with the filters panel opened. */
  defaultFiltersOpen?: boolean;
  /** Form field name of the query input. */
  name?: string;
  /** Disables the field, scope and button. */
  disabled?: boolean;
}
export declare function SearchBox(props: SearchBoxProps): React.ReactElement;

// ---- SelectBox ----
export interface SelectBoxOption {
  /** Submitted value. */
  value: string;
  /** Visible text; defaults to value. */
  label?: string;
  /** Disables this option. */
  disabled?: boolean;
}
export interface SelectBoxOptionGroup {
  /** Group heading (<optgroup label>). */
  label: string;
  /** Options inside the group. */
  options: Array<SelectBoxOption | string>;
}
export interface SelectBoxProps extends Omit<React.SelectHTMLAttributes<HTMLSelectElement>, 'size'> {
  /** Size axis: lg 56px (default), md 48px, sm 40px tall (sm uses radius-4 and a 4px label gap). */
  size?: 'lg' | 'md' | 'sm';
  /** Label text (Label Units). Omit to hide the label (Show Label=false) — then pass aria-label. */
  label?: React.ReactNode;
  /** Support text under the label, linked with aria-describedby. */
  supportText?: React.ReactNode;
  /** Error state: red border and aria-invalid. Implied when errorText is set. */
  error?: boolean;
  /** Error text shown under the field. */
  errorText?: React.ReactNode;
  /** Shows the "※必須" marker, sets aria-required and makes the placeholder option unselectable. */
  required?: boolean;
  /** Shows the "※任意" marker (ignored when required). */
  optional?: boolean;
  /** Override for the required marker text. Default "※必須". */
  requiredText?: string;
  /** Override for the optional marker text. Default "※任意". */
  optionalText?: string;
  /** Options as strings, {value,label} objects or {label, options} groups. <option> children are also accepted. */
  options?: Array<string | SelectBoxOption | SelectBoxOptionGroup>;
  /** First empty option text. Default "選択してください"; pass null to omit it. */
  placeholder?: string | null;
  /** Fixed width of the field only (e.g. 100 for a year select); the label keeps its natural width. */
  selectWidth?: number | string;
  /** Extra class for the <select>. className/style go to the root wrapper; all other props go to the <select>. */
  selectClassName?: string;
  children?: React.ReactNode;
}
export declare function SelectBox(props: SelectBoxProps): React.ReactElement;

// ---- StepNavigation ----
export interface StepNavigationStep {
  /** Step title (e.g. "基本情報入力"). */
  title: React.ReactNode;
  /** Supporting text under the title (Description). */
  description?: React.ReactNode;
  /** Number marker state: "completed" (check badge), "reached" (filled), "default" / "upcoming" (outlined), "skipped" (dashed), "editing" (編集中), "error" (エラー). Default "default". */
  status?: 'completed' | 'reached' | 'default' | 'upcoming' | 'skipped' | 'editing' | 'error';
  /** Marks this step as current when the `current` prop is not used. */
  current?: boolean;
  /** Makes the title a link to this step (Link=True). */
  href?: string;
  /** Click handler for the title link (also turns the title into a link). */
  onClick?: React.MouseEventHandler<HTMLAnchorElement>;
  /** Overrides the displayed step number (default index + 1). */
  number?: React.ReactNode;
}
export interface StepNavigationProps extends React.HTMLAttributes<HTMLElement> {
  /** The ordered steps; first / middle / last positions are derived from the order. */
  steps: StepNavigationStep[];
  /** Layout: "horizontal" (markers in a row, text below, default) or "vertical" (markers in a column, text beside). */
  orientation?: 'horizontal' | 'vertical';
  /** Size axis: "normal" (52px marker, 18px titles, default) or "small" (38px marker, 16px titles). */
  size?: 'normal' | 'small';
  /** Index (0-based) of the current step; draws the outer ring and sets aria-current="step". */
  current?: number;
  /** Show step descriptions (Description). Default true. */
  description?: boolean;
  /** Accessible name of the nav landmark. Default "ステップナビゲーション". */
  'aria-label'?: string;
}
export declare function StepNavigation(props: StepNavigationProps): React.ReactElement;

// ---- Switch ----
export interface SwitchProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'type'> {
  /** Controlled on state (Selected=Right). Pair with onChange. */
  checked?: boolean;
  /** Uncontrolled initial on state. */
  defaultChecked?: boolean;
  /** Disables the switch (State=Disabled). */
  disabled?: boolean;
  /** Ref to the underlying <input type="checkbox" role="switch">. */
  inputRef?: React.Ref<HTMLInputElement>;
  /** Visible label after the switch. Without it, pass aria-label. Other props go to the <input>; className/style to the root. */
  children?: React.ReactNode;
}
export declare function Switch(props: SwitchProps): React.ReactElement;

export interface SwitchModeProps extends Omit<React.ButtonHTMLAttributes<HTMLButtonElement>, 'value' | 'defaultValue' | 'onChange'> {
  /** Controlled side (Checked=Left / Right). */
  value?: 'left' | 'right';
  /** Uncontrolled initial side. Default "left". */
  defaultValue?: 'left' | 'right';
  /** Called with the new side. */
  onChange?: (value: 'left' | 'right', event: React.MouseEvent) => void;
  /** Mode label before the switch (Mode Switch with Label). Clicking it selects "left". */
  leftLabel?: React.ReactNode;
  /** Mode label after the switch. Clicking it selects "right"; it also names the switch. */
  rightLabel?: React.ReactNode;
  /** Disables the switch (State=Disabled). */
  disabled?: boolean;
}
export declare function SwitchMode(props: SwitchModeProps): React.ReactElement;

// ---- Table ----
export interface TableColumn<Row = any> {
  /** Unique key; also the default property read from each row. */
  key: string;
  /** Header label (Header Cell "Label"). */
  label: React.ReactNode;
  /** Makes the header a sort button with the sort icon (Sort State Default / Ascending / Descending). */
  sortable?: boolean;
  /** Value used for sorting when uncontrolled; defaults to row[key]. */
  sortValue?: (row: Row) => string | number | null | undefined;
  /** Custom cell content; defaults to row[key]. */
  render?: (row: Row, index: number) => React.ReactNode;
  /** Returns a URL to render the cell as "Cell with Link". */
  href?: (row: Row) => string | null | undefined;
  /** Link Area axis: "data" (only the text is the link, default) or "cell" (the whole cell is the link). */
  linkArea?: 'data' | 'cell';
  /** Renders this column's body cells as row headers (th scope="row", gray header fill). */
  rowHeader?: boolean;
  /** Front-icon name in the header cell. */
  icon?: string;
  /** Front-icon name (or per-row function) in body cells. */
  cellIcon?: string | ((row: Row) => string | null | undefined);
  /** Horizontal alignment; "end" for numbers. */
  align?: 'start' | 'center' | 'end';
  /** Fixed CSS width, e.g. "200px" or "25%". */
  width?: string | number;
}
export interface TableSort {
  /** Column key being sorted. */
  key: string;
  /** Sort direction. */
  direction: 'ascending' | 'descending';
}
export interface TableProps extends Omit<React.TableHTMLAttributes<HTMLTableElement>, 'rows'> {
  /** Column definitions, left to right. */
  columns: TableColumn[];
  /** Row data objects. */
  rows: any[];
  /** Size axis: "default" (cells 67px, Std-16N-170) or "dense" (45px, Dns-16N-130). */
  size?: 'default' | 'dense';
  /** Border axis: "grid" (Bottom & Right, default), "horizontal" (Bottom only) or "none". */
  border?: 'grid' | 'horizontal' | 'none';
  /** Stripe state: every second row gets the gray-50 fill. */
  striped?: boolean;
  /** Hover state: highlights the hovered row with key-50. */
  hoverable?: boolean;
  /** Selected state: keys of rows painted key-100 (aria-selected). */
  selectedKeys?: Array<string | number>;
  /** Row key property name or function (default "id"). */
  rowKey?: string | ((row: any, index: number) => string | number);
  /** Controlled sort state. */
  sort?: TableSort | null;
  /** Initial sort state when uncontrolled. */
  defaultSort?: TableSort | null;
  /** Called with the next sort state when a sortable header is pressed. */
  onSortChange?: (sort: TableSort) => void;
  /** When true, rows are rendered in the given order (sort them yourself, e.g. server-side). */
  manualSort?: boolean;
  /** Visible table caption. */
  caption?: React.ReactNode;
}
export declare function Table(props: TableProps): React.ReactElement;

// ---- TableControl ----
export interface TableControlProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Controls laid out in a row with space-between and a 24px gap (wraps on narrow screens). */
  children?: React.ReactNode;
}
export declare function TableControl(props: TableControlProps): React.ReactElement;

export interface TableControlGroupProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Buttons / dividers grouped with a 16px gap (e.g. 印刷, CSVダウンロード | 新規追加). */
  children?: React.ReactNode;
}
export declare function TableControlGroup(props: TableControlGroupProps): React.ReactElement;

export interface TableControlDividerProps extends React.HTMLAttributes<HTMLSpanElement> {}
/** Vertical Divider: 30px tall, 1px solid-gray-536 rule between button groups. */
export declare function TableControlDivider(props: TableControlDividerProps): React.ReactElement;

export interface TableControlSearchProps extends Omit<React.HTMLAttributes<HTMLDivElement>, 'onChange' | 'defaultValue'> {
  /** Controlled keyword. */
  value?: string;
  /** Initial keyword when uncontrolled. */
  defaultValue?: string;
  /** Called on every keystroke. */
  onChange?: (value: string, event: React.ChangeEvent<HTMLInputElement>) => void;
  /** Called with the keyword when the 検索 button is pressed or Enter is hit. */
  onSearch?: (value: string) => void;
  /** Shows the text-style リセット button; called after the field is cleared. */
  onReset?: () => void;
  /** Accessible name of the field (visually hidden). Default "検索キーワード". */
  label?: string;
  /** Placeholder text. */
  placeholder?: string;
  /** Result count shown after the box, e.g. "120 件" (announced as status). */
  count?: React.ReactNode;
  /** Submit button label. Default "検索". */
  buttonLabel?: string;
  /** Reset button label. Default "リセット". */
  resetLabel?: string;
  /** id of the input. */
  id?: string;
  /** name of the input. */
  name?: string;
}
export declare function TableControlSearch(props: TableControlSearchProps): React.ReactElement;

export interface TableControlItemsPerPageProps extends Omit<React.HTMLAttributes<HTMLDivElement>, 'onChange' | 'defaultValue'> {
  /** Page-size choices. Default [10, 50, 100, 200, 500]. */
  options?: number[];
  /** Controlled current page size. */
  value?: number;
  /** Initial page size when uncontrolled (default first option). */
  defaultValue?: number;
  /** Called with the chosen page size. */
  onChange?: (value: number) => void;
  /** Unit appended to each number. Default "件". */
  unit?: string;
  /** Group label. Default "表示件数". */
  label?: string;
}
export declare function TableControlItemsPerPage(props: TableControlItemsPerPageProps): React.ReactElement;

// ---- TableOfContents ----
export interface TableOfContentsItem {
  /** Link text (the target heading's text). Ignored for heading entries. */
  label?: React.ReactNode;
  /** In-page anchor of the target heading, e.g. "#overview". */
  href?: string;
  /** Marks the entry for the section currently in view (aria-current="location"). */
  current?: boolean;
  /** One nested level of entries, indented 32px. */
  children?: TableOfContentsItem[];
  /** When set, this entry is a non-link group heading (Headings Size=16) that starts a new group. */
  heading?: React.ReactNode;
}
export interface TableOfContentsProps extends React.HTMLAttributes<HTMLElement> {
  /** Type axis: "borderless" (default), "border-dotted", "border-solid". */
  type?: 'borderless' | 'border-dotted' | 'border-solid';
  /** Title shown above the list and used as the nav's accessible name. Default "このページの目次". */
  title?: React.ReactNode;
  /** Entries in page order; `{ heading }` entries split the list into groups. */
  items: TableOfContentsItem[];
}
export declare function TableOfContents(props: TableOfContentsProps): React.ReactElement;

// ---- Tabs ----
export interface TabsItem {
  /** Tab label text (Tab Label Body). */
  label: React.ReactNode;
  /** Content of the associated tab panel. */
  content?: React.ReactNode;
  /** Stable key used for value/defaultValue/onChange; defaults to the index as a string. */
  value?: string;
  /** Skips the tab in keyboard navigation and blocks selection. */
  disabled?: boolean;
}
export interface TabsProps extends Omit<React.HTMLAttributes<HTMLDivElement>, 'onChange'> {
  /** Tabs to render, in order. */
  items: TabsItem[];
  /** Type axis: label position relative to the panel — "top" (default), "bottom", "left", "right". */
  position?: 'top' | 'bottom' | 'left' | 'right';
  /** Type = Top Reflow / Bottom Reflow: labels wrap onto several rows (horizontal positions only). */
  reflow?: boolean;
  /** Controlled selected tab value. */
  value?: string;
  /** Initially selected tab value when uncontrolled. Default: first tab. */
  defaultValue?: string;
  /** Called with the newly selected value. */
  onChange?: (value: string) => void;
  /** Accessible name of the tab list (aria-label). */
  label?: string;
  /** Base id for tab/panel ids; generated when omitted. */
  id?: string;
}
export declare function Tabs(props: TabsProps): React.ReactElement;

// ---- TextArea ----
export interface TextAreaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  /** Text Area Units size: controls the label style (lg Std-18B, md Std-17B, sm Std-16B) and label gap (8 / 8 / 4). Default "lg". */
  size?: 'lg' | 'md' | 'sm';
  /** Label text (Label Units). Omit to hide the label (Show Label=false) — then pass aria-label. */
  label?: React.ReactNode;
  /** Support text under the label (e.g. "100文字以内"), linked with aria-describedby. */
  supportText?: React.ReactNode;
  /** Error state: red border and aria-invalid. Implied by errorText or by exceeding maxCount. */
  error?: boolean;
  /** Error text shown under the letter counter. */
  errorText?: React.ReactNode;
  /** Shows the "※必須" marker and sets aria-required. */
  required?: boolean;
  /** Shows the "※任意" marker (ignored when required). */
  optional?: boolean;
  /** Override for the required marker text. Default "※必須". */
  requiredText?: string;
  /** Override for the optional marker text. Default "※任意". */
  optionalText?: string;
  /** Character limit shown by the Letter Counter ("0/100"); over the limit the counter and border turn red. Native maxlength is not applied. */
  maxCount?: number;
  /** Show Count: set false to hide the counter even when maxCount is set. Default true. */
  showCount?: boolean;
  /** Controlled value. */
  value?: string;
  /** Initial value when uncontrolled. */
  defaultValue?: string;
  /** Field height (default 120px); the user can still resize vertically. */
  height?: number | string;
  /** Readonly state: dashed border. */
  readOnly?: boolean;
  /** Extra class for the <textarea>. className/style go to the root wrapper; all other props go to the <textarea>. */
  textareaClassName?: string;
}
export declare function TextArea(props: TextAreaProps): React.ReactElement;

// ---- UtilityLink ----
export interface UtilityLinkItemProps extends React.AnchorHTMLAttributes<HTMLAnchorElement> {
  /** Lead icon name, 16px (Show Front Icon), e.g. "help_false", "location_false". */
  icon?: string;
  /** Opens in a new tab and shows the 16px new_window tail icon (Show End Icon). */
  external?: boolean;
  /** Link text. */
  children?: React.ReactNode;
}
export declare function UtilityLinkItem(props: UtilityLinkItemProps): React.ReactElement;
export interface UtilityLinkEntry {
  /** Link text. */
  label: React.ReactNode;
  /** Link target. */
  href: string;
  /** Lead icon name. */
  icon?: string;
  /** Opens in a new tab with the tail icon. */
  external?: boolean;
  /** Optional click handler. */
  onClick?: React.MouseEventHandler<HTMLAnchorElement>;
}
export interface UtilityLinkProps extends React.HTMLAttributes<HTMLUListElement> {
  /** Links in the unit (Units = items.length, typically 2–5). Alternatively pass UtilityLinkItem children. */
  items?: UtilityLinkEntry[];
  /** UtilityLinkItem elements, used when `items` is not given. */
  children?: React.ReactNode;
}
export declare function UtilityLink(props: UtilityLinkProps): React.ReactElement;
// /* company-layer:begin */ — ten chuan cong ty, alias component DADS
export declare const TextField: typeof InputText;
export declare const Select: typeof SelectBox;
export declare const Badge: typeof ChipLabel;
export declare const Pagination: typeof PageNavigation;
export declare const Modal: typeof ModalDialog;
export declare const InlineMessage: typeof NoticeBlock;
export declare const PageHeader: typeof Heading;
export declare const AppHeader: typeof HeaderContainer;
// /* company-layer:end */
