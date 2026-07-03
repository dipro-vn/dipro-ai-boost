---
name: code-review-architecture-review
description: 
---

# Architecture Review

**Category:** code-review · **Status:** 🟢 Active

## When to use
Khi review kiến trúc: tách layer, coupling, reuse, đặt code đúng chỗ.

## Steps
1. Tách layer: UI không gọi DB/HTTP trực tiếp; logic ở service/hook, không lẫn vào component.
2. Coupling: module phụ thuộc qua interface/prop, không import xuyên tầng tùy tiện.
3. Đặt đúng chỗ: util chung vào shared, logic domain vào module domain, không nhét vào view.
4. Reuse vs trùng lặp: tách phần lặp thành hook/util; nhưng tránh abstraction non.
5. Hướng phụ thuộc: tầng trong không phụ thuộc tầng ngoài; tránh import vòng.

## Template
```
component (UI)  ->  hook (state)  ->  service (logic)  ->  api/db
- component: render + sự kiện
- hook: ghép state, gọi service
- service: business logic thuần, dễ test
```

## Example
**Good:** logic ở service/hook, component mỏng, phụ thuộc một chiều, không import vòng.
**Avoid:** fetch + business logic nhồi trong component, import vòng, abstraction quá sớm.

## Checklist
- [ ] Layer tách rõ (UI/state/logic/data)
- [ ] Coupling thấp, phụ thuộc qua interface
- [ ] Code đặt đúng tầng/đúng module
- [ ] Reuse hợp lý, không import vòng
