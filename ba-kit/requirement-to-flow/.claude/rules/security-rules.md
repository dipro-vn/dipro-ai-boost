# Security Rules

> **Enforcement:** Rule "không hard-code secret" được enforce cứng bằng hook **H05** (`.claude/hooks/detect-hardcoded-secret.js`) — chặn Write/Edit khi content chứa AWS key, API key (sk-/pk-/ghp_/gho_/xox), JWT literal, connection string với password, hoặc private key block. Vi phạm → tool call bị chặn ngay.

## Secret Management

- **AWS Parameter Store** là nguồn duy nhất cho secrets production — không `.env` file, không hard-code
- Không log token, password, payment data, PII người dùng
- Không commit file `.env.production`, `.env.staging`

```typescript
// ❌ SAI
const apiKey = 'sk-abc123...';
const dbUrl = 'postgresql://user:pass@host/db';

// ✅ Đúng
const apiKey = this.configService.get<string>('PAYMENT_API_KEY');
```

## API Security (NestJS)

- JWT Guard bắt buộc trên tất cả endpoint cần auth — không public route trừ login/register
- Role Guard cho endpoint admin — không kiểm tra role trong service
- `class-validator` trên tất cả DTO — không dùng raw `req.body`
- Rate limiting trên auth endpoint
- `@Exclude()` trên sensitive fields trong response DTO (password hash, internal ID, ...)

## Frontend Security (React)

- Không lưu JWT token trong `localStorage` nếu XSS là concern — dùng `httpOnly` cookie
- Sanitize input trước khi render HTML (`dangerouslySetInnerHTML` cần escape)
- Không log token hay payment data trong console
- Env vars qua `import.meta.env.VITE_*` — không hard-code URL

## Mobile Security (Flutter)

- Không hard-code API URL, secret, key — dùng `flutter_dotenv`
- Certificate pinning cho production nếu yêu cầu
- Không log payment data, token, user PII
- elepay SDK: không lưu card data locally

## Payment (điền qua /init-kit)

- Không xử lý card number trực tiếp — delegate hoàn toàn cho payment gateway SDK
- Không dùng gateway ngoài danh sách đã chọn của dự án
- (Ví dụ kit: elepay · Alipay · WeChat Pay — thay bằng gateway thật khi `/init-kit`)
