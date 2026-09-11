# Stack Constraints — Không được vi phạm

## Tech Stack Cố định

| Layer | Bắt buộc dùng | Tuyệt đối không dùng |
|---|---|---|
| Database | PostgreSQL + TypeORM | MySQL, MongoDB, SQLite, Prisma |
| API Style | REST | GraphQL, gRPC, tRPC |
| Payment | _(điền qua /init-kit — ví dụ kit: elepay · Alipay · WeChat Pay)_ | Stripe, PayPal, VNPay |
| Mobile State | `hooks_riverpod` | Provider, BLoC, GetX, MobX |
| Mobile HTTP | Retrofit + Dio | `http` package, `chopper` |
| Mobile Routing | `auto_route` | `go_router`, `Navigator.push` trực tiếp |
| Web Server State | TanStack Query v5 | Redux Toolkit cho server data |
| Web Client State | Redux Toolkit v2 | Context API cho auth/global state |
| Web Forms | react-hook-form + yup | Formik, AntD Form.Item rules |
| Secrets | AWS Parameter Store | `.env` production, hard-code |

## Version Cố định (không tự nâng cấp)

| Package | Version | Ghi chú |
|---|---|---|
| TypeORM | 0.3.x | Có known bug với `orderBy` — xem postgresql.md |
| Ant Design | v6 | Breaking changes từ v5 — check migration guide |
| TanStack Query | v5 | Object syntax, không positional |
| react-router-dom | v7 | `useNavigate` thay `useHistory` |
| TailwindCSS | v4 | Config via PostCSS, không `tailwind.config.js` cũ |
| hooks_riverpod | 3.0.1 | |

## Mobile Version Convention

```
DEV:  0.0.<build_number>
STG:  0.1.<build_number>
PROD: 1.0.<build_number>
```

Không đảo ngược, không bỏ qua STG để lên thẳng PROD.
