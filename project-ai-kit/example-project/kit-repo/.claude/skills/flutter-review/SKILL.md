---
name: flutter-review
description: Code review và best practices cho mobile app Flutter/Dart. Stack: Riverpod 3, Retrofit+Dio, auto_route, freezed, socket_io_client, payment SDK. Trigger khi review Flutter code, hỏi "code này đúng không", hoặc implement tính năng mobile.
metadata:
  tags: flutter, dart, mobile, riverpod, code-review
---

# Flutter Review — Mobile

> Áp dụng cho repo có vai trò `mobile` trong bảng Ecosystem (`AGENTS.md`)

## Stack Reference

| Thành phần | Package | Pitfall phổ biến |
|---|---|---|
| State | `hooks_riverpod 3.0.1` | Không dùng Provider/BLoC/GetX |
| Routing | `auto_route 11.1.0` | Không dùng `Navigator.push` trực tiếp |
| HTTP | `dio 5.9.2` + `retrofit 4.9.2` | Không dùng `http` package |
| Model | `freezed 3.x` + `json_annotation 4.9.0` | Phải chạy build_runner sau khi sửa |
| Real-time | `socket_io_client 3.1.4` | Phải cleanup `off()` trong dispose |
| Payment | payment SDK (vd elepay — thay bằng payment SDK thật của dự án nếu khác) | — |
| Reactive | `rxdart 0.28.0` | — |
| Config | `flutter_dotenv 6.0.0` | Không hard-code URL/key |
| Sizing | `flutter_screenutil 5.9.3` | Dùng `.w`, `.h`, `.sp` |
| Storage | `shared_preferences 2.5.4` | — |

**Mobile Version Convention:**
- DEV: `0.0.<build>` · STG: `0.1.<build>` · PROD: `1.0.<build>`

## Checklist Review

### 1. State Management — Riverpod

- [ ] Dùng `hooks_riverpod` — không dùng `provider`, `flutter_bloc`, `get`?
- [ ] `StateNotifierProvider` cho async state với `AsyncValue`?
- [ ] `ConsumerWidget` hoặc `HookConsumerWidget` — không dùng `StatefulWidget` với Riverpod?
- [ ] `ref.watch` trong build, `ref.read` trong callback — không lẫn lộn?
- [ ] Provider dispose đúng cách (scoped / autoDispose nếu cần)?

### 2. HTTP / API — Retrofit + Dio

- [ ] Dùng Retrofit `@RestApi()` abstract class — không gọi Dio trực tiếp trong service?
- [ ] Dio interceptor cho auth token (không xử lý token thủ công từng call)?
- [ ] Timeout config đặt trong DioProvider?
- [ ] Error handling: parse response error thành business exception?
- [ ] Không dùng `http` package?

### 3. Models — freezed

- [ ] `@freezed` annotation trên class?
- [ ] `factory` constructor với `fromJson`?
- [ ] Đã chạy `flutter pub run build_runner build --delete-conflicting-outputs` sau khi sửa?
- [ ] Không sửa thủ công file `.g.dart` hoặc `.freezed.dart`?

### 4. Routing — auto_route

- [ ] Route định nghĩa trong `AppRouter` — không dùng `Navigator.push`?
- [ ] Deep link xử lý trong `AppRouter`?
- [ ] `context.router.push(RouteClass(...))` — không dùng string route?

### 5. Real-time — Socket.IO

- [ ] Socket listener cleanup `socket.off('event')` trong `dispose`?
- [ ] `socket.disconnect()` khi không cần?
- [ ] Không tạo nhiều socket instance — singleton qua Provider?

### 6. UI / Responsive

- [ ] `flutter_screenutil` cho sizing: `.w`, `.h`, `.sp`?
- [ ] Không hard-code pixel sizes?
- [ ] `const` constructor khi widget không thay đổi?
- [ ] `cached_network_image` cho remote images?

### 7. Security & Config

- [ ] Không hard-code URL, API key, secret?
- [ ] Lấy config từ `flutter_dotenv`?
- [ ] Không log payment data, token, user PII?
- [ ] Certificate pinning cho production (nếu yêu cầu)?

### 8. Performance

- [ ] Không heavy work trong `build()` method?
- [ ] `ListView.builder` cho large list (không `ListView` với nhiều children)?
- [ ] Image cache đúng với `flutter_cache_manager`?
- [ ] `async/await` đúng — không blocking UI thread?

### 9. Version Convention

- [ ] `pubspec.yaml` version đúng format theo env (DEV/STG/PROD)?
- [ ] `versionCode` Android tăng đúng theo build number CI/CD?

## Output Format khi review

```
📱 FLUTTER REVIEW — [file/widget/service]

🔴 Critical:
  - [vấn đề nghiêm trọng]

🟡 Warning:
  - [vấn đề nên fix]

🟢 OK:
  - [điểm tốt]

💡 Suggestions:
  - [cải thiện optional]
```

## Chi tiết đầy đủ

> Skill này là nguồn guidelines đầy đủ cho Flutter/Dart — không có file guidelines riêng bên ngoài.
