// ─── UI Detection Patterns ───────────────────────────────────────────────────

/** Phân biệt header cột bảng với cell value để chỉ đánh số header, không đánh số dữ liệu body */
export const TABLE_HEADER_PATH_RE =
  /table-header|thead|header-cell|column-header|table\/head|table-header-row|col-header/i;

/** Nhận diện cell/row body để loại khỏi danh sách auto-number */
export const TABLE_BODY_PATH_RE =
  /table-cell|table\/cell|table-row|table\/body|tbody|data-row|row-cell|table\/row(?!.*header)|cell-content/i;

/** Tìm text là giá trị đã nhập trong input, không phải label cần mô tả trong BD */
export const INPUT_VALUE_PATH_RE =
  /textfield|text-field|input-field|textarea|combobox|select-menu|search-input|<textfield>|\/input|input\/|placeholder|value-text|entered-text/i;

/** Giữ label form trong BD và loại trừ chúng khỏi nhóm input value */
export const INPUT_LABEL_PATH_RE =
  /field-label|form-label|label-text|\/label|> label|floating-label/i;

/** Nhận diện layer icon/action qua tên (EN/JA) khi path không đủ rõ */
export const ICON_NAME_RE =
  /checkbox|check-box|check_box|delete|trash|remove|close|icon|edit|pencil|pen|write|add|plus|minus|search|menu|more|overflow|chevron|arrow|radio|toggle|switch|btn|button|link|star|clock|time|history|duplicate|dup|copy|update|version|play|favorite|fav|共有|削除|編集|リンク|履歴|更新|複製/i;

/** Xác định cột/vùng toolbar action trong bảng để ưu tiên đánh số icon thao tác */
export const ACTION_PATH_RE =
  /action|アクション|操作|table-header|table-cell|table\/column|toolbar|icon-bar|pagination/i;

// ─── Sample / Value Filter Patterns ─────────────────────────────────────────

/** Loại mã ghế A1–E10 khỏi numbering — chỉ chọn seat map một lần */
export const SEAT_CODE_RE = /^[A-E]\d{1,2}$/i;

// ─── Business Label Patterns ─────────────────────────────────────────────────

/** Khớp text nút chuẩn (キャンセル, Save, 決済…) để đánh số button/link */
export const BUTTON_LABEL_RE =
  /^(キャンセル|保存|cancel|save|作成|共有|share|ok|submit|エクスポート|export|削除|delete|追加|add|登録|register|閉じる|close|確定|apply|適用|更新|update|戻る|back|決済|[＋\+−\-])$/i;

/** Nhận diện link-text checkout (カートに追加, 決済を確定) là item BD bắt buộc */
export const BD_LINK_TEXT_RE =
  /戻る|カートに追加|一覧に戻る|参加者を追加|＋.*追加|決済を確定/i;

/** Label sidebar tóm tắt đơn hàng — vùng phải màn checkout cần coverage đầy đủ */
export const BD_OUTPUT_LABEL_RE =
  /ご注文内容|小計|合計金額|合計|プロモーションコード|プロモーション|注文内容/i;

/** Tiêu đề section BD (01 —, ログイン…) để boost section_title trong auto-select */
export const BD_SECTION_TITLE_RE =
  /^(0[1-9]|[1-9]\d?)\s*[—\-–－.·]\s*|^(ログイン|決済|お申し込み|支払い|ご注文|参加者|座席|プロモーション|グループ|申込)/;

/** Màn hình enterprise / simulation / VAS FLOW — tiêu đề và nhãn vùng chính */
export const BD_SIMULATION_TITLE_RE =
  /VAS\s*FLOW|シミュレーション|シミュレータ|登録|FAST|\/\s*OZ/i;

/** Nút/link thao tác màn simulation & danh sách */
export const BD_SIMULATION_ACTION_RE =
  /保存して計算|PDF出力|計算|出力|一覧に戻る|新規|検索|クリア|リセット|実行|確認/i;

/** Label form checkout — participant, card, CVV… cần có trong BD document */
export const BD_FORM_LABEL_RE =
  /^(参加者名|参加者|メール|メールアドレス|座席選択|カード番号|有効期限|カード名義|CVV|セキュリティ|購入枚数|申込タイプ|お名前|氏名)/;

/** Tiêu đề card/section màn BĐS & simulation (アクセス情報, 計算諸条件…) */
export const BD_CARD_SECTION_TITLE_RE =
  /アクセス情報|計算諸条件|投資内容|収入計画|資金調達|諸条件$|情報$/;

/** Label form BĐS / đầu tư — 物件価格, 駅名, 利回り… */
export const BD_REAL_ESTATE_LABEL_RE =
  /物件価格|満室想定|賃料収入|維持費|自己資金|金利|借入|不動産|現況|駅名|徒歩|乗降人数|^アクセス\d|メモ$|仲介|表面利回り|自己資金比率|CF\s*\/|CCR|収入計画|資金調達|投資内容/i;

/** Option radio/tab thanh toán — phân loại payment UI items */
export const BD_RADIO_OPTION_RE =
  /今すぐ|後で|クレジットカード|銀行振込|一般席|前方席|gift|register|proxy|複数|代表者|ギフト/i;

// ─── Section Metadata ────────────────────────────────────────────────────────

/** Tên section JP/VN cho Excel export khi nhóm numbered items theo vùng màn hình */
export const SECTION_META = {
  header: { sectionNo: 0, sectionNameJP: "ヘッダーエリア", sectionNameVN: "Vùng header" },
  search: { sectionNo: 1, sectionNameJP: "条件付き検索エリア", sectionNameVN: "Vùng search" },
  operation: { sectionNo: 2, sectionNameJP: "操作エリア", sectionNameVN: "Vùng thao tác" },
  table: { sectionNo: 3, sectionNameJP: "データ一覧エリア", sectionNameVN: "Vùng danh sách dữ liệu" },
  other: { sectionNo: 4, sectionNameJP: "その他", sectionNameVN: "Khác" },
};

// ─── Spec Fallback Descriptions ──────────────────────────────────────────────

/** Mô tả JP/VN mặc định khi AI không generate spec — giữ output Excel nhất quán */
export const SPEC_FALLBACK = {
  save_button: {
    itemNameJP: "保存ボタン",
    itemNameVN: "Nút lưu",
    type: "Button",
    descriptionJP:
      "クリック時、現在の画面設定および一覧の入力内容を保存する。入力値に不備がある場合は保存せず、対象項目にエラーメッセージを表示する。",
    descriptionVN:
      "Khi click, hệ thống lưu thiết lập màn hình hiện tại và nội dung đã nhập trong danh sách. Nếu dữ liệu không hợp lệ, không lưu và hiển thị thông báo lỗi tại item tương ứng.",
    comment: "API endpoint、validation chi tiếtは要確認",
  },
  cancel_button: {
    itemNameJP: "キャンセルボタン",
    itemNameVN: "Nút hủy",
    type: "Button",
    descriptionJP:
      "クリック時、編集内容を破棄し、前画面へ戻る、または保存前の状態に戻す。具体的な遷移先は要確認。",
    descriptionVN:
      "Khi click, hủy nội dung chỉnh sửa và quay về màn hình trước hoặc trạng thái trước khi lưu. Đích chuyển màn hình cần xác nhận.",
    comment: "遷移先/破棄確認ダイアログの有無は要確認",
  },
  toggle: {
    itemNameJP_ip: "IPアドレス制限 有効/無効切替",
    itemNameVN_ip: "Bật/tắt giới hạn địa chỉ IP",
    itemNameJPSuffix: " 有効/無効切替",
    itemNameVNPrefix: "Bật/tắt ",
    type: "Toggle",
    defaultValue: "OFF",
    descriptionJP:
      "ONの場合、登録されたIPアドレスからのみアプリケーションへのアクセスを許可する。OFFの場合、IPアドレスによるアクセス制限を行わない。切替後、「保存」ボタン押下時に設定を保存する。",
    descriptionVN:
      "Khi ON, hệ thống chỉ cho phép truy cập ứng dụng từ các địa chỉ IP đã đăng ký. Khi OFF, hệ thống không áp dụng giới hạn truy cập theo địa chỉ IP. Sau khi thay đổi, thiết lập được lưu khi nhấn nút 「保存」.",
    comment:
      "ON/OFF変更時に即時保存するか、保存ボタン押下時に保存するかは要確認。ただし画面上に保存ボタンがあるため、保存ボタン押下時に反映する想定。",
  },
  delete_icon: {
    itemNameJP: "削除アイコン",
    itemNameVN: "Icon xóa",
    type: "Icon Button",
    descriptionJP:
      "クリック時、対象行を削除対象とする。保存ボタン押下時に削除内容を反映する。削除前に確認ダイアログを表示するかは要確認。",
    descriptionVN:
      "Khi click, đánh dấu dòng tương ứng để xóa. Nội dung xóa được phản ánh khi nhấn nút lưu. Việc hiển thị dialog xác nhận trước khi xóa cần xác nhận.",
    comment: "即時削除か保存時反映か、確認ダイアログ有無は要確認",
  },
  add_icon: {
    itemNameJP: "行追加アイコン",
    itemNameVN: "Icon thêm dòng",
    type: "Icon Button",
    descriptionJP:
      "クリック時、登録用の入力行を1行追加する。追加行には名称、IPアドレス等を入力できる。",
    descriptionVN:
      "Khi click, thêm 1 dòng nhập liệu mới. Dòng thêm có thể nhập tên, địa chỉ IP, v.v.",
    comment: "最大登録件数は要確認",
  },
  ip_address_input: {
    itemNameJP: "IPアドレス",
    itemNameVN: "Địa chỉ IP",
    type: "Input",
    required: "条件付き",
    maxlength: "15",
    descriptionJP:
      "IPv4アドレスを入力する。CIDR表記による範囲指定を許可する場合がある。IPv6は対象外。保存時に形式チェックを行う。",
    descriptionVN:
      "Nhập địa chỉ IPv4. Có thể cho phép ký hiệu CIDR để chỉ định dải. Không hỗ trợ IPv6. Kiểm tra định dạng khi lưu.",
    comment: "CIDR許可有無、重複IP許可有無、空欄許可有無は要確認",
  },
  name_input: {
    itemNameJP: "名称",
    itemNameVN: "Tên",
    type: "Input",
    descriptionJP:
      "登録する設定の名称を入力する。利用者が識別しやすい名称を設定する。",
    descriptionVN:
      "Nhập tên cho thiết lập đăng ký. Người dùng đặt tên dễ nhận biết.",
    comment: "最大文字数、使用可能文字は要確認",
  },
  table_no: {
    itemNameJP: "No",
    itemNameVN: "Số thứ tự",
    type: "Table Header",
    descriptionJP: "登録行の連番を表示する。行追加・削除に応じて表示順に採番する。",
    descriptionVN:
      "Hiển thị số thứ tự các dòng đăng ký. Đánh số lại theo thứ tự hiển thị khi thêm/xóa dòng.",
  },
  breadcrumb: {
    type: "Breadcrumb",
    descriptionJP:
      "現在表示している画面の階層を表示する。上位階層をクリックできる場合は対象画面へ遷移する。",
    descriptionVN:
      "Hiển thị cấp bậc màn hình hiện tại. Nếu có thể click cấp trên thì chuyển tới màn hình tương ứng.",
    comment: "クリック可否は要確認",
  },
  title: {
    type: "Title",
    descriptionJP: "現在表示している画面名を表示する。",
    descriptionVN: "Hiển thị tên màn hình hiện tại.",
  },
  table_column_header: {
    type: "Table Header",
    descriptionJPPrefix: "一覧の「",
    descriptionJPSuffix: "」列名を表示する。",
    descriptionVNPrefix: "Hiển thị tên cột 「",
    descriptionVNSuffix: "」 trong danh sách.",
  },
  table_row_header: {
    type: "Table Header",
    descriptionJPPrefix: "表における",
    descriptionJPSuffix: "項目の行見出しです。",
    descriptionVNPrefix: "Header dòng cho item ",
    descriptionVNSuffix: " trong bảng.",
  },
  input: {
    type: "Input",
    descriptionJPSuffix: "を入力する項目。入力値は保存時に検証される。詳細仕様未定の場合はcomment参照。",
    descriptionVNPrefix: "Trường nhập ",
    descriptionVNSuffix: ". Giá trị được kiểm tra khi lưu. Chi tiết xem comment nếu chưa rõ.",
    comment: "詳細仕様未定",
  },
  select: {
    type: "Dropdown",
    descriptionJPSuffix: "を選択する項目。選択肢以外は選択不可。",
    descriptionVNPrefix: "Dropdown chọn ",
    descriptionVNSuffix: ". Không chọn được giá trị ngoài danh sách.",
    comment: "選択肢一覧は要確認",
  },
  checkbox: {
    type: "Checkbox",
    required: "任意",
    descriptionJPSuffix: "の選択状態を指定する。チェック状態を処理条件に反映する。",
    descriptionVNPrefix: "Checkbox chỉ định trạng thái ",
    descriptionVNSuffix: ". Trạng thái được dùng làm điều kiện xử lý.",
  },
  radio: {
    type: "Radio",
    descriptionJPSuffix: "を選択するラジオボタン。",
    descriptionVNPrefix: "Radio button chọn ",
    descriptionVNSuffix: ".",
  },
  button: {
    type: "Button",
    descriptionJPPrefix: "クリック時、",
    descriptionJPSuffix: "処理を実行する。入力条件に基づいて処理を行う。",
    descriptionVNPrefix: "Khi click, thực hiện xử lý ",
    descriptionVNSuffix: " theo điều kiện đã nhập.",
    comment: "詳細仕様未定",
  },
  icon_generic: {
    type: "Icon Button",
    descriptionJP: "クリック時、画面上の操作を実行する。詳細は要確認。",
    descriptionVN: "Khi click, thực hiện thao tác trên màn hình. Chi tiết cần xác nhận.",
    comment: "詳細仕様未定",
  },
  default: {
    descriptionJPSuffix: "を表示・操作する画面項目。",
    descriptionVNPrefix: "Item màn hình hiển thị/thao tác ",
    descriptionVNSuffix: ".",
    comment: "詳細仕様未定",
  },
};

// ─── AI Prompts ───────────────────────────────────────────────────────────────

/** System prompt cho AI chọn element theo mô tả user (manual numbering, tiếng Việt) */
export const AI_SELECT_SYSTEM_VI =
  "Ban la tro ly danh so UI tren Figma. Tu doc mo ta nguoi dung (moi format, nhieu dong, tieng Viet/Nhat/Anh). " +
  "Chon DUNG nodeId tu danh sach: text=, label=, name=, path=, box=@, center=. " +
  "Tu suy ra so thu tu (number) va element can danh theo y nghia cau. " +
  "Khong giai thich, chi tra JSON hop le.";

/** System prompt cho AI chọn element — ràng buộc format number string JA */
export const AI_SELECT_SYSTEM_JA =
  "Figma UI番号付け。numberは文字列\"11.1.1\"形式（11.1.1を11.1にしない）。JSONのみ。";

/** System prompt auto-select BD: rule chọn ~30–50 item, bảng, action, sidebar */
export const AUTO_SELECT_SYSTEM =
  "You are a UI Basic Design numbering assistant.\n\n" +
  "Select only UI elements that should be described in a Basic Design document.\n\n" +
  "Target: ONE number per logical BD item (~35-70 items for a full screen; complex enterprise/simulation screens may need 50-70). " +
  "Do NOT number every text node — group related UI into a single item.\n\n" +
  "Select: screen title, section title, tab, breadcrumb item, form label, input, select, " +
  "checkbox, radio, button, action icon, table column header, table row header, menu item, " +
  "pagination control, search condition label, output field label.\n\n" +
  "Do NOT select: breadcrumb separators (/ > ／ ＞ |), pure values (numbers, dates, money, " +
  "-, 0, 0.00), sample user data (names, emails, 認証済), description paragraphs, seat codes " +
  "(A1-E10 individually — pick seat map once), table body cell values, sample data, " +
  "decorative text, duplicate child text when parent should be selected, logo decoration, " +
  "generic layer names (Button, Icon, Frame).\n\n" +
  "Table rules:\n" +
  "1. Horizontal table: column headers only, not body cells.\n" +
  "2. Vertical-header table: left column row headers; top column headers if meaningful; " +
  "not values on the right.\n" +
  "3. If unsure header vs data, ignore.\n\n" +
  "Breadcrumb: select meaningful items; ignore separators and dates unless clearly a screen item.\n\n" +
  "Button/input: prefer container/parent; do not select parent and child duplicate.\n\n" +
  "Action rules (MUST select):\n" +
  "- Footer/header buttons: Cancel/キャンセル, Save/保存, 戻る, 適用, 決済を確定する, カートに追加 link.\n" +
  "- Sidebar order summary (right column): ご注文内容, 小計, 合計金額, プロモーションコード, all sidebar buttons.\n" +
  "- Section content: radio/tab options (今すぐ支払う, クレジットカード), quantity +/- , ＋参加者を追加.\n" +
  "- Form labels: 参加者名, メール, カード番号, 有効期限, CVV, カード名義.\n" +
  "- Header icons (cart, menu), edit pencil icons.\n" +
  "- Table action icons: delete row (trash), add row (+), edit in アクション/action column.\n" +
  "- Items with roleHint=button, roleHint=icon, action=must_select, or toolbarPos= must be selected.\n" +
  "- For identical row action icons or seat cells (A1-E10), select ONE representative per type.\n\n" +
  "Output JSON only, no markdown. Keep each item compact (nodeId, number, label, itemType, confidence only):\n" +
  '{"items":[{"number":1,"nodeId":"...","label":"...","itemType":"...","confidence":0.95}]}';

/** System prompt sinh Basic Design spec JP/VN từ numbered UI elements */
export const SPEC_SYSTEM_PROMPT =
  "You are a senior Japanese BrSE creating Basic Design item definitions from Figma UI elements.\n" +
  "Return JSON only. No markdown. No explanation outside JSON. No extra fields beyond schema.\n\n" +
  "Do NOT describe only what the item is. For each item describe:\n" +
  "- purpose (what it is used for)\n" +
  "- user action (how the user interacts)\n" +
  "- default state if inferable\n" +
  "- system behavior on click/change/input\n" +
  "- validation if inferable\n" +
  "- enable/disable conditions if inferable\n" +
  "- unclear points in comment using 要確認 or 詳細仕様未定\n\n" +
  "Rules:\n" +
  "- Generate specs ONLY for the given numbered items.\n" +
  "- Do not invent API names, DB tables, or exact business rules unless provided in input.\n" +
  "- If required/maxlength/default/status unknown, use \"-\".\n" +
  "- status should be \"New\" unless clearly otherwise.\n" +
  "- Use detectedRole hints (save_button, cancel_button, toggle, delete_icon, add_icon, ip_address_input, name_input, table_no, breadcrumb, etc.) to write accurate behavior.\n" +
  "- Toggle ON/OFF: type=Toggle; describe ON/OFF behavior and that save likely happens on 保存 button if present on screen.\n" +
  "- Save button (保存): describe saving current settings with validation.\n" +
  "- Cancel button (キャンセル): describe discarding edits and navigation back.\n" +
  "- Delete icon: describe row deletion, likely applied on save, confirm dialog 要確認.\n" +
  "- Add/plus icon: describe adding a new input row.\n" +
  "- IP address input: IPv4, CIDR may apply, format check on save.\n" +
  "- Name input (名称): describe naming purpose.\n" +
  "- Table header: describe column display.\n" +
  "- Breadcrumb: describe hierarchy display and navigation.\n" +
  "- Title: describe screen title display.\n\n" +
  "When the user message includes a \"Business context\" section, treat it as authoritative for screen purpose, user flows, business rules, and validation. Align every item description with that context. Do not contradict it.\n\n" +
  "Schema: {\"items\":[{\"no\":\"1\",\"itemNameJP\":\"...\",\"itemNameVN\":\"...\",\"type\":\"Button\",\"status\":\"New\",\"required\":\"-\",\"maxlength\":\"-\",\"default\":\"-\",\"descriptionJP\":\"...\",\"descriptionVN\":\"...\",\"comment\":\"\"}]}";

// ─── Tuning Constants ─────────────────────────────────────────────────────────

/** Giới hạn candidates gửi AI khi manual select — tránh vượt context window */
export const CANDIDATE_LIMIT = 300;

/** Giới hạn elements trong pass auto-number structural */
export const AUTO_NUMBER_LIMIT = 500;

/** Tolerance pixel theo trục Y để gom elements cùng hàng khi sort reading order */
export const READING_ORDER_ROW_PX = 16;

/** Token limit API cho bước auto-select AI */
export const AUTO_SELECT_MAX_TOKENS = 8192;

/** Số candidate selectable tối đa gửi vào prompt auto-select */
export const AUTO_SELECTABLE_LIMIT = 140;

/** Số node context-only tối đa (tham chiếu layout, không được chọn) */
export const AUTO_CONTEXT_LIMIT = 60;

/** Số item tối đa sau finalize auto-select — giữ BD document gọn */
export const AUTO_FINAL_MAX = 48;

/** Token limit API cho bước generate Basic Design spec */
export const SPEC_GENERATION_MAX_TOKENS = 8192;

/** Số item mỗi batch khi gọi AI sinh spec — tránh timeout với màn hình lớn */
export const SPEC_AI_BATCH_SIZE = 20;

/** Khoảng cách bbox tối đa để lấy nearby text làm ngữ cảnh spec */
export const NEARBY_TEXT_MAX_DIST = 120;

/** Số nearby text tối đa gắn vào mỗi numbered item */
export const NEARBY_TEXT_LIMIT = 8;

/** Giới hạn kích thước PNG export frame (4 MB) */
export const FRAME_EXPORT_MAX_BYTES = 4 * 1024 * 1024;
