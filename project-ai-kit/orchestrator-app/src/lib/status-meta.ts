import {
  Ban,
  Circle,
  CircleAlert,
  CircleCheck,
  CircleHelp,
  CirclePause,
  CircleX,
  Loader2,
  MinusCircle,
  type LucideIcon,
} from "lucide-react";
import type { NodeStatus } from "@/lib/tauri-client";

/**
 * Single source of truth for how every one of the 8 `NodeStatus` values
 * renders — used by every screen that shows a node (Board, detail panel,
 * future Gate screens). Each status has its own icon in addition to color,
 * so it stays distinguishable in both themes and for anyone who can't rely
 * on color alone (AC-E1-33 / AC-E3-09).
 *
 * MVP1 can only ever produce `idle`, `done`, and `done-incomplete` from
 * file-system inference — the other 5 are modeled (and shown here, e.g. in
 * a legend) but never appear on a real Board yet, since there is no agent
 * runner until MVP2.
 */
export interface StatusMeta {
  label: string;
  icon: LucideIcon;
  /** Tailwind color token — same class works in both themes since these
   * are semantic tokens (see shadcn's `--destructive` etc.), not raw hex. */
  colorClass: string;
  spin?: boolean;
  reachableInMvp1: boolean;
}

export const STATUS_META: Record<NodeStatus, StatusMeta> = {
  idle: {
    label: "Chưa bắt đầu",
    icon: Circle,
    colorClass: "text-muted-foreground",
    reachableInMvp1: true,
  },
  running: {
    label: "Đang chạy",
    icon: Loader2,
    colorClass: "text-info",
    spin: true,
    reachableInMvp1: false,
  },
  "waiting-input": {
    label: "Chờ trả lời",
    icon: CircleHelp,
    colorClass: "text-warning",
    reachableInMvp1: false,
  },
  done: {
    label: "Hoàn thành",
    icon: CircleCheck,
    colorClass: "text-success",
    reachableInMvp1: true,
  },
  "done-incomplete": {
    label: "Hoàn thành (chưa đầy đủ)",
    icon: CircleAlert,
    colorClass: "text-warning",
    reachableInMvp1: true,
  },
  // Khác `done-incomplete` ở chỗ stage kế tiếp VẪN mở: output còn thiếu
  // nằm ở công cụ ngoài (Figma MCP, mkdocs) mà app không kiểm chứng được,
  // nên đây là cảnh báo chứ không phải chặn. Detail của node nói rõ thiếu gì.
  "done-partial": {
    label: "Hoàn thành (thiếu output)",
    icon: CircleAlert,
    colorClass: "text-warning",
    reachableInMvp1: true,
  },
  failed: {
    label: "Lỗi",
    icon: CircleX,
    colorClass: "text-destructive",
    reachableInMvp1: false,
  },
  blocked: {
    label: "Bị chặn",
    icon: Ban,
    colorClass: "text-warning",
    reachableInMvp1: false,
  },
  skipped: {
    label: "Đã bỏ qua",
    icon: MinusCircle,
    colorClass: "text-muted-foreground/60",
    reachableInMvp1: false,
  },
  // AC-E6-04 — must stay visually distinct from `failed`: the action here
  // is Resume/Re-run, not Retry.
  interrupted: {
    label: "Bị gián đoạn",
    icon: CirclePause,
    colorClass: "text-warning",
    reachableInMvp1: false,
  },
};

export function statusMeta(status: NodeStatus): StatusMeta {
  return STATUS_META[status];
}
