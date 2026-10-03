#!/usr/bin/env python3
"""Danh sach BAT BUOC cua design-system-format.md (§3.3 token vai tro, §4 README, §5 component, §8 STATUS).

Dung chung: extract-design-tokens.py (--emit-status) va verify-design-system.py.
Sua chuan (.claude/sys-agent/design-system/design-system-format.md) -> sua o day.
"""
import re

# §3.3 — token vai tro bat buoc theo D#
ROLES = [
    ("D1", ["primary", "primary-hover", "primary-active", "primary-subtle", "primary-text", "on-primary"]),
    ("D2", ["white", "page-bg", "surface", "surface-subtle", "surface-disabled", "text-high", "text-middle",
            "text-low", "divider-low", "divider-middle", "divider-high", "overlay-scrim"]),
    ("D3", ["success-100", "success-700", "info-100", "info-700", "warning-100", "warning-800",
            "negative-100", "negative-500", "negative-600", "focus-ring"]),
    ("D5", ["radius-none", "radius-xs", "radius-sm", "radius-md", "radius-lg", "radius-xl", "radius-full",
            "shadow-flat", "shadow-raise", "shadow-stick", "shadow-float", "shadow-popout", "shadow-focus"]),
    ("D7", ["viewport-web", "header-height", "control-md", "table-header-height", "table-row-height",
            "modal-width"]),
]
# 1 trong nhom la du
ROLE_ALT = [("D7", ["sidebar-width", "tabbar-height"])]
# buoc thang tuy chon (§3.3) — co thi tot, khong bat buoc
OPTIONAL = ["success-50", "success-500", "info-50", "info-500", "warning-50", "warning-400", "negative-50",
            "sidebar-collapsed", "nav-item-height", "control-sm", "control-lg", "content-max"]
SPACE_RE = re.compile(r"^space-\d+(\.\d+)?$")
TYPE_GROUPS = ["Heading", "Text"]
MIN_STYLES = 4

# §5 — component toi thieu (D6); SideNav / TabBar: 1 trong 2
COMPONENTS = ["Button", "TextField", "Select", "Checkbox", "Radio", "Switch", "Badge", "Tabs", "Table",
              "Pagination", "Modal", "Toast", "InlineMessage", "PageHeader", "Breadcrumb", "AppHeader",
              "AppShell", "Icon"]
COMP_ALT = ["SideNav", "TabBar"]

# trang thai khong do duoc khi crawl read-only (hover / nhan / focus / disabled / sau thao tac)
UNOBSERVABLE = {"primary-hover", "primary-active", "surface-disabled", "divider-high", "focus-ring",
                "shadow-focus", "shadow-float", "Toast"}

SOURCES = {"figma", "screens", "docs", "code", "website"}

# §8 STATUS.md
STATUS_HEADINGS = ["Platform", "Thứ tự ưu tiên nguồn", "Thiếu (TBD)", "Mâu thuẫn cần xác nhận", "Changelog"]
STATUS_LINES = ["Trạng thái", "Artifact", "Nguồn"]
NOTE_RO = "khong quan sat duoc tren website (read-only) — can designer xac nhan"
NOTE_NOT_SEEN = "khong thay tren cac man da quet"


def all_required():
    """-> [(D#, ten)] moi token bat buoc (nhom ALT ghi 'a / b')."""
    out = [(d, n) for d, names in ROLES for n in names]
    out += [(d, " / ".join(names)) for d, names in ROLE_ALT]
    return out
