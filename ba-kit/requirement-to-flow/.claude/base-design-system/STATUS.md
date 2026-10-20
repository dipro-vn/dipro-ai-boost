# Design System — Base (DADS) cho ba-kit

- Trạng thái: DRAFT — base dùng chung, chưa có người duyệt cho dự án cụ thể
- Artifact: https://claude.ai/artifact/WCjMDsToWAsjADJBWjHQwe (nguồn copy, version 1791704971-2855; artifact public, tạo ngoài tổ chức)
- Nguồn: デジタル庁デザインシステム デザインデータ v2.18.0 (Figma Community) — `project/tokens.json` `meta`

## Platform
| Platform | Theme (`data-theme`) | Viewport | Khung màn | Screen prefix |
|---|---|---|---|---|
| Web desktop | `light` (mặc định) · `market` | `viewport-web` 1280px | lưới 12 cột, `layout-margin-desktop` 80px, `content-max` 1120px | theo dự án |
| Web mobile | `light` · `market` | ≤ `layout-breakpoint-mobile` 767px | `layout-margin-mobile` 16px | theo dự án |

## Thứ tự ưu tiên nguồn
1. Giá trị quan sát được của hệ thống / Design System của dự án (khi có)
2. Base này (`project/`)
3. Nguyên tắc `prompt_design_system.md`

## Thiếu (TBD)
| D# | Token / component | Ghi chú |
|---|---|---|
| D7 | `sidebar-width` / `tabbar-height` | DADS không có sidebar / tab bar — màn admin cần sidebar thì hỏi designer |
| D7 | `viewport-mobile` | DADS chỉ cho breakpoint 767px, không có khung SP cố định — khai `viewport_width` khi vẽ |
| D6 | `Toast` | Không có trong DADS — dùng `NotificationBanner` (thông báo trang) hoặc hỏi designer |
| D6 | `AppShell` | Không có — ghép `HeaderContainer` + nội dung theo lưới |
| D6 | `SideNav` / `TabBar` | Không có — `MenuList` / `MobileMenu` gần nhất, cần designer xác nhận |
| — | File SVG trong `assets/Icons/` | Chưa tải (nằm ở asset store của artifact); icon đã có sẵn trong `Icon` của `bundle.js` |

## Mâu thuẫn cần xác nhận
| # | Nội dung | Quyết định tạm |
|---|---|---|
| 1 | Chuẩn công ty cần chữ 12px (`text-12`), DADS nhỏ nhất 14px | `text-12` = `Dns-14N-130` (14px) |
| 2 | Chuẩn công ty có 600 (semibold), DADS chỉ 400 / 500 / 700 | `*-semibold` dùng 700 |
| 3 | `info-*`: DADS không có token info riêng | dùng thang `blue` |
| 4 | Điều khoản sử dụng DADS cho sản phẩm khách hàng | Chưa kiểm — PM xác nhận trước khi giao màn dựng bằng base cho khách. Icon: Google Material Symbols (Apache-2.0) theo `project/README.md` |

## Changelog
| Ngày | Thay đổi |
|---|---|
| 2026-10-20 | Copy `project/` từ artifact DADS; thêm lớp chuẩn công ty (`tools/add-company-layer.py`): token vai trò D1–D7, spacing / size, type `Heading` / `Text`, 8 component alias |
