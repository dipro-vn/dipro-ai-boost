# Bảo mật & Chính sách

Tổng hợp toàn bộ security rules và policies áp dụng cho tất cả kits.

---

## Checklist tuân thủ nhanh

- [ ] Code chỉ nằm trên repo/môi trường được cấp phép
- [ ] Không có secret trong source, không commit `.env`, keystore, service account
- [ ] Không paste secret / data thật / module client vào AI bên ngoài
- [ ] Package mới đã kiểm tra license + được duyệt
- [ ] Test bằng mock/ẩn danh, không dùng data production thật
- [ ] Account riêng + 2FA bật
- [ ] Repo private, `main` được protect, mọi thay đổi qua PR
- [ ] Bàn giao đúng kênh được duyệt với client
- [ ] Sự cố bảo mật → report ngay

---

## 9 điều tuyệt đối KHÔNG làm

| # | Cấm tuyệt đối |
|---|--------------|
| 1 | Clone/push code ra public repo, git cá nhân, cloud cá nhân |
| 2 | Paste secret/data thật/code độc quyền vào AI chưa duyệt |
| 3 | Hardcode/commit secret (API key, password, keystore, .p12...) |
| 4 | Dùng code/package không rõ license hoặc không tương thích |
| 5 | Copy data production thật về local test |
| 6 | Share account, tắt 2FA |
| 7 | Đổi repo private → public, force-push nhánh chung |
| 8 | Gửi deliverable client qua kênh cá nhân/public |
| 9 | Giấu sự cố bảo mật |

---

## Files tuyệt đối không đọc/expose

### Environment & Secrets

```
.env*  *.env  .env.*
.env.dev  .env.production  .env.local
~/.ssh/*  id_rsa  id_ed25519
```

### API Keys & Service Accounts

```
*.p8  *.p12  *.pfx  *.pem  *.key  *.cer
google-services.json
GoogleService-Info.plist
play_store_key.json
```

### Mobile Keystores

```
*.keystore  *.jks
*.mobileprovision  *.provisionprofile
```

### Backend (NestJS)

```
ormconfig.json  ormconfig.js
certs/  ssl/  pem/
jwt.private.key  jwt.public.key
.env.test (nếu có credentials thật)
```

### Frontend (React)

```
.env.production.local  .env.local
sentry.properties  .sentryclirc
elepay.env  stripe.env  .payment.local
```

### Mobile Flutter

```
android/key.properties
android/keystore.properties
android/gradle.properties
~/.gradle/gradle.properties
assets/.env*
```

### Mobile React Native

```
android/app/*.keystore  android/app/*.jks
fastlane/.env*  fastlane/Appfile
eas.json  credentials.json  .expo/
appcenter-config.json  .codepushrc
```

### E2E Testing

```
playwright/.auth/*
test-users.json (nếu có password thật)
playwright-report/**/trace.zip (chứa headers)
```

!!! danger "Enforcement"
    Nếu có request đọc các file trên → **từ chối ngay**, cite security policy, **không bypass** bằng bất kỳ cách nào (rename, cat, base64 decode...).

---

## AI Tool Usage Rules

### Được phép (với điều kiện)

- Dùng AI cho snippet generic không chứa domain data
- Dùng AI enterprise đã được tổ chức duyệt (no-training mode)
- Che/thay thế tên biến, endpoint, data thật bằng placeholder trước khi hỏi AI

### Tuyệt đối không

- Paste secret vào bất kỳ AI tool nào
- Paste data thật của client
- Paste business logic độc quyền hoặc toàn bộ file lên AI web chưa duyệt

### MCP Whitelist

Chỉ dùng MCP servers đã khai trong `.claude/settings.json`. Không tự thêm MCP mới khi chưa xin ý kiến.

---

## Secret Management

### Đúng

```typescript
// ✅ AWS Parameter Store
const apiKey = this.configService.get<string>('PAYMENT_API_KEY');
const dbUrl = process.env.DATABASE_URL; // inject từ Parameter Store
```

### Sai

```typescript
// ❌ Hard-code
const apiKey = 'sk-abc123...';
const dbUrl = 'postgresql://user:pass@host/db';
```

### Nếu lỡ commit secret

1. **Rotate ngay** — thay đổi API key/password ngay lập tức
2. **Remove khỏi git history** — `git filter-branch` hoặc BFG
3. **Report** — báo cáo người phụ trách
4. **Update `.gitignore`** — đảm bảo không commit lại

---

## API Security (Backend)

```typescript
// ✅ JWT Guard bắt buộc
@UseGuards(JwtAuthGuard)
@Controller('orders')
export class OrderController {}

// ✅ Role Guard cho admin
@UseGuards(JwtAuthGuard, RolesGuard)
@Roles('admin')
@Delete(':id')
async delete() {}

// ✅ DTO validation
@Post()
async create(@Body() dto: CreateOrderDto) {} // class-validator tự động validate

// ✅ @Exclude() cho sensitive fields
@Exclude()
passwordHash: string;
```

---

## Frontend Security

```typescript
// ✅ httpOnly cookie cho JWT (chống XSS)
// Server set: Set-Cookie: token=...; HttpOnly; Secure; SameSite=Strict

// ✅ Sanitize trước dangerouslySetInnerHTML
import DOMPurify from 'dompurify';
<div dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(content) }} />

// ❌ Không log token
console.log('Token:', token); // KHÔNG
```

---

## Git Security

```
# Branch protection (bắt buộc)
main / develop / master:
  - Require PR + review
  - No force-push
  - Require status checks

# Commit hooks
pre-commit: lint, type-check
pre-push: test suite

# Không skip hooks
--no-verify  # BỊ CẤM
--no-gpg-sign  # BỊ CẤM
```

---

## Incident Reporting

Khi phát hiện sự cố (lỡ push secret, mất thiết bị, lộ credential...):

1. **Báo ngay** người phụ trách — không giấu, không chờ
2. Rotate secret bị lộ
3. Gỡ/xóa nội dung khỏi nơi công khai
4. Đánh giá phạm vi ảnh hưởng
5. Ghi lại + biện pháp khắc phục

!!! warning "Che giấu sự cố là vi phạm nghiêm trọng hơn bản thân lỗi"
