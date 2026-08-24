import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { DiffView } from "@/screens/board/DiffView";

interface DiffModalProps {
  /** Đường dẫn file đang so sánh; `null` đóng modal. */
  path: string | null;
  oldValue: string;
  newValue: string;
  onClose: () => void;
}

/**
 * Diff toàn màn hình cho file vi phạm contract. `DiffView` render
 * `splitView`, mà `ActionPanel` chỉ chiếm 1/3 bề ngang Board — hai cột ở đó
 * hẹp tới mức không đọc được. Không dùng `ArtifactModal` vì đây là 2 nội
 * dung, không đi qua `ArtifactContentView`; khung dialog chép từ
 * `VersionCompareDialog` — nơi diff đã có sẵn vùng cuộn riêng.
 */
export function DiffModal({ path, oldValue, newValue, onClose }: DiffModalProps) {
  return (
    <Dialog open={path !== null} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="flex h-[85vh] max-w-4xl flex-col overflow-hidden sm:max-w-4xl">
        <DialogHeader>
          <DialogTitle>So sánh với nội dung đã khoá</DialogTitle>
          <DialogDescription className="truncate font-mono text-xs">{path}</DialogDescription>
        </DialogHeader>
        <div className="min-h-0 flex-1 overflow-auto rounded-lg border border-border">
          <DiffView path={path ?? undefined} oldValue={oldValue} newValue={newValue} />
        </div>
      </DialogContent>
    </Dialog>
  );
}
