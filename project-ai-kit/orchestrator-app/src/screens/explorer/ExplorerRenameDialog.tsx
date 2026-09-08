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
import { isAppCommandError } from "@/lib/tauri-client";
import type { ExplorerEntryTarget } from "@/screens/explorer/explorer-types";

interface ExplorerRenameDialogProps {
  target: ExplorerEntryTarget | null;
  onClose: () => void;
  onRename: (target: ExplorerEntryTarget, newName: string) => Promise<void>;
}

function extractErrorMessage(error: unknown): string {
  if (isAppCommandError(error)) return error.message;
  if (error instanceof Error) return error.message;
  return String(error);
}

export function ExplorerRenameDialog({ target, onClose, onRename }: ExplorerRenameDialogProps) {
  const [name, setName] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [renaming, setRenaming] = useState(false);

  useEffect(() => {
    // Điền sẵn tên cũ: đổi tên hầu như luôn là sửa vài ký tự, không phải gõ lại.
    setName(target?.name ?? "");
    setErrorMessage(null);
    setRenaming(false);
  }, [target]);

  const label = target?.isDir ? "folder" : "file";
  const trimmed = name.trim();
  const unchanged = trimmed === target?.name;

  async function handleRename() {
    if (!target || !trimmed || unchanged || renaming) return;
    setRenaming(true);
    setErrorMessage(null);
    try {
      await onRename(target, trimmed);
      onClose();
    } catch (error) {
      setErrorMessage(extractErrorMessage(error));
    } finally {
      setRenaming(false);
    }
  }

  return (
    <Dialog open={target !== null} onOpenChange={(open) => !open && !renaming && onClose()}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Đổi tên {label}</DialogTitle>
          <DialogDescription className="break-all">
            <code>{target?.path}</code>
          </DialogDescription>
        </DialogHeader>

        <div className="flex flex-col gap-2">
          <Label htmlFor="explorer-rename-name">Tên mới</Label>
          <Input
            id="explorer-rename-name"
            autoFocus
            autoComplete="off"
            value={name}
            disabled={renaming}
            onChange={(event) => setName(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") {
                event.preventDefault();
                void handleRename();
              }
            }}
          />
          <p className="text-xs text-muted-foreground">
            Chỉ nhập tên, không nhập đường dẫn — {label} ở nguyên chỗ cũ.
          </p>
        </div>

        {errorMessage && (
          <Alert variant="destructive">
            <AlertTitle>Không đổi được tên</AlertTitle>
            <AlertDescription className="break-all">{errorMessage}</AlertDescription>
          </Alert>
        )}

        <DialogFooter>
          <Button variant="ghost" onClick={onClose} disabled={renaming}>
            Huỷ
          </Button>
          <Button onClick={() => void handleRename()} disabled={!trimmed || unchanged || renaming}>
            {renaming ? "Đang đổi..." : "Đổi tên"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
