---
name: project-planning
description: Risk identification, dependency mapping, critical path analysis cho dự án theo phase-gate Waterfall. Dùng khi pm-agent cần điền Dependencies & Risks trong PLAN.md, xác định Contract Lock timing, hoặc phân tích critical path cross-repo.
metadata:
  tags: project-management, risk-management, agile-planning, critical-path
---

# Project Planning

> Áp dụng cho: `pm-agent` khi tạo PLAN.md — phần Dependencies, Risks, Timeline, Contract Lock

---

## Khi nào dùng skill này

- Điền section **Dependencies & Risks** trong PLAN.md
- Xác định **Critical Path** để estimate deadline chính xác
- Quyết định **Contract Lock** timing trước Phase 3
- Identify **phase-gate blockers** (G1–G6)
- Phân tích dependency cross-repo khi feature chạm BE + FE + Mobile

---

## 1. Risk Identification Checklist

Với mỗi feature, scan qua các category sau và đánh dấu risk nào apply:

### Technical Risks

| Risk | Dấu hiệu | Mitigation |
|---|---|---|
| **DB migration không rollback được** | Migration thay đổi column type, drop column, rename table | Thêm task verify `down()` hoạt động trước khi merge |
| **N+1 query performance** | Task có list endpoint với relation lồng nhau | Yêu cầu `EXPLAIN ANALYZE` trong Definition of Done |
| **Redis cache stampede** | Feature mới + cache TTL ngắn + traffic cao | Dùng stale-while-revalidate hoặc lock pattern |
| **Socket.IO memory leak** | Task Mobile có Socket listener mới | Verify cleanup `socket.off()` trong dispose |
| **TypeORM orderBy injection** | Task có sortable list endpoint | Bắt buộc whitelist map (đã có bug prod) |
| **Contract mismatch FE/BE** | Feature cross-repo, FE và BE develop song song | Contract Lock bắt buộc trước Phase 3 |

### Integration Risks

| Risk | Dấu hiệu | Mitigation |
|---|---|---|
| **elepay SDK version conflict** | Payment flow mới, pubspec update | Test trên cả iOS và Android trước STG |
| **Firebase push token expired** | Notification feature mới hoặc thay đổi payload | Test device token refresh flow |
| **Yamato/Sagawa API timeout** | Delivery integration task | Add retry logic + timeout config |
| **JWT token rotation** | Auth change ảnh hưởng nhiều repo | Coordinate deploy order: BE trước, FE/Mobile sau |

### Business Risks

| Risk | Dấu hiệu | Mitigation |
|---|---|---|
| **Spec ambiguity** | SPEC có từ "tương tự", "v.v.", threshold chưa định nghĩa | BA confirm trước khi Tech Lead viết DESIGN |
| **Scope creep** | User story có "và các tính năng liên quan" | Ghi Out of Scope rõ trong SPEC |
| **Phase-gate dependency** | Feature cần G3 approve trước khi deploy STG | Confirm gate với PM/Stakeholder trước khi estimate |
| **Multi-tenant data isolation** | Feature mới đọc/ghi data company khác | Security review bắt buộc |

---

## 2. Dependency Mapping — Cross-repo

### Bước 1: Xác định repo bị ảnh hưởng

```
Đọc SPEC → Actors → map actor → repo (theo bảng Ecosystem trong AGENTS.md), ví dụ:
  Actor A (mobile end-user)  → repo mobile
  Actor B (org admin)        → repo frontend #1 + repo backend
  Actor C (system admin)     → repo frontend #2 + repo backend
  Actor D (supplier)         → repo frontend #3 + repo backend
  Actor E (driver)           → repo frontend #4 + repo backend
```

### Bước 2: Identify contract points

Với mỗi cặp repo, ghi rõ:

```markdown
## Contract Points
| Interface | BE task | FE/Mobile task | Lock timing |
|---|---|---|---|
| REST endpoint `POST /orders` | task-2-2 | task-3-1 | Trước Phase 3 |
| WebSocket event `order:status` | task-2-3 | task-3-2 (Mobile) | Trước Phase 3 |
| Push notification payload | task-2-4 | task-3-3 (Mobile) | Trước Phase 3 |
```

### Bước 3: Dependency graph đơn giản

```
task-1-1 (migration)
    │
    ▼
task-2-1 (service) ──── task-2-2 (controller)
                               │
                    ┌──────────┴──────────┐
                    ▼                     ▼
            task-3-1 (FE React)   task-3-2 (Flutter)   ← song song sau Contract Lock
                    │                     │
                    └──────────┬──────────┘
                               ▼
                        task-4-1 (integration test)
```

---

## 3. Critical Path Analysis

Critical path = chuỗi tasks **dài nhất** từ start → done mà không thể song song.

### Cách tính

```
1. List tất cả tasks với estimate (giờ)
2. Xác định dependency chain
3. Critical path = chain có tổng giờ lớn nhất

Ví dụ:
  Chain A: task-1-1(2h) → task-2-1(4h) → task-2-2(3h) → task-3-1(5h) → task-4-1(2h) = 16h
  Chain B: task-1-1(2h) → task-2-1(4h) → task-2-2(3h) → task-3-2(5h) → task-4-1(2h) = 16h
  → Critical path = 16h = minimum timeline nếu 1 dev làm tuần tự
  → Với 2 dev (FE + Mobile song song Phase 3): 16h - 5h (mobile song song) = 11h
```

### Buffer Rules (ví dụ)

| Loại task | Buffer thêm |
|---|---|
| Task có DB migration | +20% (verify rollback, staging apply) |
| Task có payment flow | +30% (elepay sandbox test, iOS/Android) |
| Task cross 3+ repo | +25% (coordination overhead) |
| Task có integration bên ngoài (Yamato/HubSpot) | +40% (external API unpredictable) |
| Feature mới chưa có pattern trong codebase | +30% (tilth_search, learning curve) |

---

## 4. Phase-Gate Checklist (G1–G6)

Trước khi estimate deadline, xác định feature cần pass gate nào:

| Gate | Tiêu chí | Blocker nếu fail |
|---|---|---|
| **G1** — Requirements | SPEC.md approved, AC rõ ràng | Không được bắt đầu Design |
| **G2** — Design | Design-Technical.md approved, Contract Lock signed | Không được bắt đầu Phase 3 |
| **G3** — Code Complete | Tất cả tasks "Request Review", CI pass | Không được deploy STG |
| **G4** — STG Testing | QC sign-off, no Critical/Major bug open | Không được deploy PROD |
| **G5** — Release | PM + Stakeholder approve | Không release |
| **G6** — Post-release | Monitor 48h, no P1 bug | Retrospective + close sprint |

**Điền vào PLAN.md:**
```markdown
## Phase-Gate Alignment
- Gate cần pass: G-X | Deadline: <date>
- G2 Contract Lock: <date> — confirm trước khi Phase 3 start
- Rollback plan nếu G4 fail: <mô tả>
```

---

## 5. Timeline Estimation Formula

```
Minimum timeline = Critical Path (giờ) ÷ số dev available × buffer
Working hours/day = 6h (trừ meeting, review)

Ví dụ:
  Critical path = 20h
  Dev available = 2 (1 BE + 1 FE)
  BE path = 10h, FE path = 10h (song song)
  Timeline = max(10h, 10h) = 10h thực thi
  Buffer migration = +20% → 12h
  Số ngày = 12h ÷ 6h/ngày = 2 ngày
```

**Luôn ghi rõ assumptions:**
```markdown
## Assumptions
- BE dev: 1 người × 6h/ngày thực tế
- FE dev: 1 người × 6h/ngày thực tế
- Review + fix: +1 ngày buffer
- STG deploy + QC: +1 ngày
```

---

## 6. Contract Lock Checklist

Điền trước khi Phase 3 bắt đầu, cần confirm từ BE + FE + Mobile + PM:

```markdown
## Contract Lock — <Feature> — <Date>

### REST API
- [ ] `POST /api/v1/<resource>` — request/response DTO finalized
- [ ] `GET /api/v1/<resource>/:id` — response schema finalized
- [ ] Error codes: 400/401/403/404/409 documented

### WebSocket (nếu có)
- [ ] Event name: `<entity>:<action>` format
- [ ] Payload schema finalized
- [ ] Room/namespace xác định

### Push Notification (nếu có)
- [ ] `title` / `body` template finalized
- [ ] `data` payload schema finalized

Signed off by: BE __ / FE __ / Mobile __ / PM __
```

---

## Anti-Patterns

- ❌ Estimate "2 tuần" không có task breakdown — không track được progress
- ❌ Bỏ qua Contract Lock — nguyên nhân #1 làm lại FE/Mobile khi BE thay đổi API
- ❌ Không tính buffer cho migration task — rollback trên STG thường mất thêm 1–2h
- ❌ FE và BE estimate độc lập, cộng lại làm timeline — phải identify song song được không
- ❌ Ghi risk là "có thể bị delay" mà không có mitigation action cụ thể
- ❌ Không ghi deployment order khi có JWT/auth change cross-repo
