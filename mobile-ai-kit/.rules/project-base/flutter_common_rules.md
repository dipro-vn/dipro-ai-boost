# Flutter Common Rules — Mobile AI Kit

## 1. Một project = (1 kiến trúc) × (1 state management)
- Mỗi project chọn **đúng 1 kiến trúc** (Clean Architecture / MVVM / ...) và **đúng 1 state management** (Riverpod / BLoC / ...).

## 2. Dependency Rule
- Tầng business/domain **không import** `package:flutter/*` (không `BuildContext`, `Widget`, `material`).
- Data phụ thuộc Domain **qua interface**, không ngược lại.
- UI **không** gọi thẳng API / DB / SharedPreferences → luôn đi qua repository/service.
- Kiểm chứng nhanh: file logic nghiệp vụ mà có `import 'package:flutter/...'` → sai.

## 3. State bất biến (Immutable state)
- State / Entity / DTO phải **immutable**, có `copyWith`, so sánh bằng value.
- Dùng `freezed` (ưu tiên) hoặc `equatable`; không tự viết `==`/`hashCode` tay nếu tránh được.
- Không mutate field trực tiếp — luôn tạo state mới.

## 4. State holder phải framework-agnostic
- `Bloc`/`Cubit`/`Notifier`/`ViewModel` **không** giữ `BuildContext`, không gọi `Navigator`, không show `SnackBar` trực tiếp.
- Điều hướng & side-effect UI xử lý ở tầng widget (qua `ref.listen` / `BlocListener` / listener).

## 5. Logic test được không cần UI
- Mọi logic nghiệp vụ phải **unit test được** mà không cần `WidgetTester`.
- Nếu phải dựng widget mới test được logic → logic đang đặt sai chỗ.

## 6. Tổ chức code
- **Feature-first**: tổ chức theo feature trước, layer sau. Không gom hết `models/` `widgets/` toàn app vào 1 chỗ.
- Code dùng chung > 1 feature → đẩy vào `core/`.
- **1 file = 1 trách nhiệm chính.**

## 7. Naming (file & folder)
- File / folder: `snake_case` (vd: `user_profile_page.dart`).
- Suffix theo vai trò: `_page` / `_widget` / `_repository` / `_remote_data_source` / `_model` / `_usecase` / `_state` / và `_bloc` `_cubit` `_notifier` `_view_model` tùy state management.

## 8. Class & symbol
- Class / enum / typedef: `PascalCase`.
- Biến / hàm / param: `camelCase`. Private: prefix `_`.
- Constant: `lowerCamelCase` (theo Effective Dart, **không** `SCREAMING_CAPS`).
- Boolean: prefix `is/has/can/should` (`isLoading`, `hasError`).

## 9. Rule code Dart/Flutter (pattern-agnostic, BẮT BUỘC)
- Bật null-safety; hạn chế tối đa `!` (bang) → ưu tiên `?.`, `??`, pattern matching.
- **Không** `print()` trong production → dùng logger.
- Không để `Future` chạy mà không `await` / `unawaited()`.
- Không dùng `BuildContext` sau `await` khi chưa check `context.mounted`.
- Không `catch (e)` rồi nuốt lỗi im lặng.

## 10. Widget & performance
- Ưu tiên `const` constructor mọi nơi có thể.
- **Tách widget con thay vì tách method trả về `Widget`** (const + thu hẹp scope rebuild).
- Widget nhỏ, một trách nhiệm; `build()` không chứa logic nghiệp vụ / gọi API.
- `setState` chỉ cho UI state cục bộ tạm thời; state nghiệp vụ → dùng state management của project.
- List dài → `ListView.builder`, không `Column` + `map`.

## 11. Async & data
- DTO (tầng data) có `fromJson/toJson`; Entity (domain) thuần, không.
- Có **mapper** rõ ràng DTO ↔ Entity; không xài DTO thẳng lên UI.
- Mọi I/O async + có xử lý lỗi & loading state.

## 12. Đa ngôn ngữ (i18n) — nếu project có config multi-language
- Không hard-code chuỗi hiển thị → dùng `l10n` / `intl`.
- Mọi label, message, format ngày/tiền tệ đều qua localization.

## 13. Linting baseline (chung mọi project)
Đặt vào `analysis_options.yaml` ở root mỗi repo:
```yaml
include: package:flutter_lints/flutter.yaml

analyzer:
  language:
    strict-casts: true
    strict-inference: true
    strict-raw-types: true
  exclude:
    - "**/*.g.dart"
    - "**/*.freezed.dart"
    - "**/*.gr.dart"
    - "**/*.mocks.dart"

linter:
  rules:
    - always_use_package_imports
    - avoid_print
    - avoid_dynamic_calls
    - prefer_const_constructors
    - prefer_const_constructors_in_immutables
    - prefer_final_locals
    - require_trailing_commas
    - unawaited_futures
    - use_build_context_synchronously
    - cancel_subscriptions
    - close_sinks
```
- CI fail nếu còn lint warning. `dart format` trước khi commit.

## 14. Test (BẮT BUỘC tối thiểu)
- **Unit test**: cho logic nghiệp vụ (usecase / repository / state holder). Mock dependency (`mocktail`/`mockito`), không gọi network thật.
- **Widget test**: cho widget có logic hiển thị quan trọng.
- File test mirror cấu trúc `lib/` trong `test/`, đặt tên `<file>_test.dart`.

## 15. Checklist review (dán vào PR template)
```
[ ] Tầng domain/business KHÔNG import package:flutter
[ ] UI không gọi thẳng API/DB — đi qua repository/service
[ ] State immutable (freezed/equatable), không mutate trực tiếp
[ ] State holder không giữ BuildContext / không điều hướng trực tiếp
[ ] Logic nghiệp vụ KHÔNG nằm trong build()
[ ] Không hard-code chuỗi hiển thị (đã qua l10n) — nếu có i18n
[ ] Có unit test cho logic nghiệp vụ mới
[ ] dart format + flutter analyze sạch (0 warning)
[ ] Đặt tên file/class đúng quy ước (mục 7, 8)
[ ] Code dùng chung > 1 feature đã đẩy vào core/
```

## 16. Hướng dẫn cho AI assistant (khi sinh/sửa code)
1. Nhận diện project đang dùng **kiến trúc nào × state management nào** (xem cấu trúc thư mục, `pubspec.yaml`) rồi sinh code đúng pattern đó — **không tự ý đổi pattern**.
2. Luôn tuân thủ toàn bộ rule mục 2–12 (phần không đổi giữa các pattern).
3. Đặt code đúng tầng, đúng feature, đúng quy ước tên.
4. Kèm/đề xuất unit test cho logic nghiệp vụ mới.
5. Khi sửa code vi phạm rule, nêu rõ vi phạm điều nào (theo số mục).