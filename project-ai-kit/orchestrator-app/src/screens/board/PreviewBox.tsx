import type { ReactNode } from "react";
import { Maximize2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface PreviewBoxProps {
  /** Đường dẫn file, hiển thị ở hàng tiêu đề. */
  label: string;
  /** Tooltip cho label (vd checksum). */
  labelTitle?: string;
  /** Tailwind max-height của khung cuộn — vd `max-h-80`. */
  maxHeightClass: string;
  onExpand: () => void;
  expandLabel?: string;
  /** Chặn nút phóng to khi nội dung đầy đủ chưa sẵn sàng. */
  expandDisabled?: boolean;
  children: ReactNode;
}

/**
 * Khung preview có nút phóng to. Hai gate panel (`TriggerGatePanel`,
 * `ContractLockPanel`) nhồi nội dung file vào khung cuộn thấp nằm trong
 * vùng cuộn của `ActionPanel` — đọc để duyệt gate gần như không được, nên
 * mỗi khung cần một lối mở ra modal toàn màn hình.
 */
export function PreviewBox({
  label,
  labelTitle,
  maxHeightClass,
  onExpand,
  expandLabel = "Xem toàn bộ nội dung",
  expandDisabled,
  children,
}: PreviewBoxProps) {
  return (
    <div className="flex flex-col gap-1">
      <div className="flex items-center justify-between gap-2">
        <p className="truncate font-mono text-xs text-muted-foreground" title={labelTitle ?? label}>
          {label}
        </p>
        <Button
          variant="ghost"
          size="icon-sm"
          onClick={onExpand}
          disabled={expandDisabled}
          aria-label={expandLabel}
          title={expandLabel}
        >
          <Maximize2 />
        </Button>
      </div>
      <div className={cn(maxHeightClass, "overflow-y-auto rounded-lg border border-border p-3")}>
        {children}
      </div>
    </div>
  );
}
