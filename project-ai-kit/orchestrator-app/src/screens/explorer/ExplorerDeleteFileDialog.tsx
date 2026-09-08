import { useEffect, useState } from "react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { commands, isAppCommandError } from "@/lib/tauri-client";
import type { ExplorerFolderTarget } from "@/screens/explorer/explorer-types";

interface ExplorerDeleteFileDialogProps {
  target: ExplorerFolderTarget | null;
  onClose: () => void;
  onDeleted: (target: ExplorerFolderTarget) => void;
}

function extractErrorMessage(error: unknown): string {
  if (isAppCommandError(error)) return error.message;
  if (error instanceof Error) return error.message;
  return String(error);
}

/**
 * Xác nhận xoá đúng một file.
 *
 * Cố tình nhẹ hơn `ExplorerDeleteDialog`: xoá folder có thể cuốn theo cả cây
 * con không nhìn thấy trên màn hình nên nó bắt gõ lại tên, còn ở đây thứ bị
 * xoá hiện ngay trước mắt.
 */
export function ExplorerDeleteFileDialog({
  target,
  onClose,
  onDeleted,
}: ExplorerDeleteFileDialogProps) {
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    setErrorMessage(null);
    setDeleting(false);
  }, [target]);

  async function handleDelete() {
    if (!target || deleting) return;
    setDeleting(true);
    setErrorMessage(null);
    try {
      await commands.deleteExplorerFile(target.path);
      onDeleted(target);
      onClose();
    } catch (error) {
      setErrorMessage(extractErrorMessage(error));
    } finally {
      setDeleting(false);
    }
  }

  return (
    <Dialog open={target !== null} onOpenChange={(open) => !open && !deleting && onClose()}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Xoá file?</DialogTitle>
          <DialogDescription className="break-all">
            <code>{target?.path}</code>
          </DialogDescription>
        </DialogHeader>

        <p className="text-sm text-muted-foreground">
          File bị xoá khỏi đĩa, không vào Thùng rác — không hoàn tác được từ trong app.
        </p>

        {errorMessage && (
          <Alert variant="destructive">
            <AlertTitle>Không xoá được file</AlertTitle>
            <AlertDescription className="break-all">{errorMessage}</AlertDescription>
          </Alert>
        )}

        <DialogFooter>
          <Button variant="ghost" onClick={onClose} disabled={deleting}>
            Huỷ
          </Button>
          <Button variant="destructive" onClick={() => void handleDelete()} disabled={deleting}>
            {deleting ? "Đang xoá..." : "Xoá file"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
