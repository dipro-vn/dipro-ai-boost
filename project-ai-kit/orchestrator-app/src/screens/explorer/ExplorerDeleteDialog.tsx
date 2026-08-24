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
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { commands, isAppCommandError, type ExplorerDeletePreview } from "@/lib/tauri-client";
import type { ExplorerFolderTarget } from "@/screens/explorer/explorer-types";

interface ExplorerDeleteDialogProps {
  target: ExplorerFolderTarget | null;
  onClose: () => void;
  onDeleted: (target: ExplorerFolderTarget) => void;
}

function extractErrorMessage(error: unknown): string {
  if (isAppCommandError(error)) return error.message;
  if (error instanceof Error) return error.message;
  return String(error);
}

export function ExplorerDeleteDialog({ target, onClose, onDeleted }: ExplorerDeleteDialogProps) {
  const [preview, setPreview] = useState<ExplorerDeletePreview | null>(null);
  const [typed, setTyped] = useState("");
  const [deleting, setDeleting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    setPreview(null);
    setTyped("");
    setErrorMessage(null);
    if (!target) return;

    let cancelled = false;
    commands
      .previewDeleteExplorerEntry(target.path)
      .then((result) => {
        if (!cancelled) setPreview(result);
      })
      .catch((error) => {
        if (!cancelled) setErrorMessage(extractErrorMessage(error));
      });

    return () => {
      cancelled = true;
    };
  }, [target]);

  async function handleDelete() {
    if (!target || !preview || !canDelete || deleting) return;
    setDeleting(true);
    setErrorMessage(null);
    try {
      await commands.deleteExplorerEntry(target.path, typed.trim());
      onDeleted(target);
      onClose();
    } catch (error) {
      setErrorMessage(extractErrorMessage(error));
    } finally {
      setDeleting(false);
    }
  }

  const blocked =
    !preview ||
    preview.runningSlots.length > 0 ||
    preview.lockedFiles.length > 0 ||
    preview.protectedPaths.length > 0 ||
    preview.symlinkPaths.length > 0;
  const canDelete = !!target && !!preview && !blocked && typed.trim() === preview.name;

  return (
    <Dialog open={target !== null} onOpenChange={(open) => !open && !deleting && onClose()}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>Xoá folder “{target?.name}”?</DialogTitle>
          <DialogDescription className="break-all">
            Thao tác này không hoàn tác được và không đi qua Thùng rác.
          </DialogDescription>
        </DialogHeader>

        {preview === null && !errorMessage ? (
          <div className="flex flex-col gap-3">
            <div className="skeleton h-5 w-40" />
            <div className="skeleton h-20 w-full" />
            <div className="skeleton h-9 w-full" />
          </div>
        ) : preview ? (
          <div className="flex flex-col gap-3">
            {(preview.runningSlots.length > 0 ||
              preview.lockedFiles.length > 0 ||
              preview.protectedPaths.length > 0 ||
              preview.symlinkPaths.length > 0) && (
              <Alert variant="destructive">
                <AlertTitle>Không thể xoá an toàn</AlertTitle>
                <AlertDescription>
                  {preview.runningSlots.length > 0 && (
                    <p>Đang có agent chạy: {preview.runningSlots.join(", ")}.</p>
                  )}
                  {preview.lockedFiles.length > 0 && <p>Có file đang bị Contract Lock bảo vệ.</p>}
                  {preview.protectedPaths.length > 0 && <p>Có path hệ thống hoặc restricted bên trong.</p>}
                  {preview.symlinkPaths.length > 0 && <p>Có symlink bên trong, thao tác bị chặn để tránh xoá nhầm ngoài root.</p>}
                </AlertDescription>
              </Alert>
            )}

            <div className="rounded-lg border border-destructive/40 p-3 text-sm">
              <p className="font-medium">Sẽ bị xoá vĩnh viễn:</p>
              <p className="text-muted-foreground">
                {preview.fileCount} file và {preview.folderCount} folder bên trong.
              </p>
              <p className="mt-1 break-all font-mono text-xs text-muted-foreground">{preview.path}</p>
            </div>

            <div className="flex flex-col gap-1">
              <Label htmlFor="explorer-delete-confirm">
                Gõ lại <code>{preview.name}</code> để xác nhận
              </Label>
              <Input
                id="explorer-delete-confirm"
                autoFocus
                autoComplete="off"
                value={typed}
                disabled={blocked || deleting}
                onChange={(event) => setTyped(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === "Enter" && canDelete) void handleDelete();
                }}
              />
            </div>
          </div>
        ) : null}

        {errorMessage && (
          <Alert variant="destructive">
            <AlertTitle>Không xoá được folder</AlertTitle>
            <AlertDescription className="break-all">{errorMessage}</AlertDescription>
          </Alert>
        )}

        <DialogFooter>
          <Button variant="ghost" onClick={onClose} disabled={deleting}>
            Huỷ
          </Button>
          <Button variant="destructive" onClick={() => void handleDelete()} disabled={!canDelete || deleting}>
            {deleting ? "Đang xoá..." : "Xoá vĩnh viễn"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
