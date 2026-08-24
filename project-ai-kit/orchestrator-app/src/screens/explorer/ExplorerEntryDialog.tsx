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
import type { ExplorerCreateKind, ExplorerFolderTarget } from "@/screens/explorer/explorer-types";

interface ExplorerEntryDialogProps {
  kind: ExplorerCreateKind | null;
  target: ExplorerFolderTarget | null;
  onClose: () => void;
  onCreate: (kind: ExplorerCreateKind, target: ExplorerFolderTarget, name: string) => Promise<void>;
}

function extractErrorMessage(error: unknown): string {
  if (isAppCommandError(error)) return error.message;
  if (error instanceof Error) return error.message;
  return String(error);
}

export function ExplorerEntryDialog({ kind, target, onClose, onCreate }: ExplorerEntryDialogProps) {
  const [name, setName] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    setName("");
    setErrorMessage(null);
    setCreating(false);
  }, [kind, target]);

  async function handleCreate() {
    if (!kind || !target || !name.trim() || creating) return;
    setCreating(true);
    setErrorMessage(null);
    try {
      await onCreate(kind, target, name.trim());
      onClose();
    } catch (error) {
      setErrorMessage(extractErrorMessage(error));
    } finally {
      setCreating(false);
    }
  }

  const label = kind === "folder" ? "folder" : "file";

  return (
    <Dialog open={kind !== null && target !== null} onOpenChange={(open) => !open && !creating && onClose()}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Tạo {label} mới</DialogTitle>
          <DialogDescription className="break-all">
            Tạo trong <code>{target?.path}</code>
          </DialogDescription>
        </DialogHeader>

        <div className="flex flex-col gap-2">
          <Label htmlFor="explorer-entry-name">Tên {label}</Label>
          <Input
            id="explorer-entry-name"
            autoFocus
            autoComplete="off"
            value={name}
            disabled={creating}
            placeholder={kind === "folder" ? "ten-folder" : "ten-file.md"}
            onChange={(event) => setName(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") {
                event.preventDefault();
                void handleCreate();
              }
            }}
          />
          <p className="text-xs text-muted-foreground">Chỉ nhập tên, không nhập đường dẫn.</p>
        </div>

        {errorMessage && (
          <Alert variant="destructive">
            <AlertTitle>Không tạo được {label}</AlertTitle>
            <AlertDescription className="break-all">{errorMessage}</AlertDescription>
          </Alert>
        )}

        <DialogFooter>
          <Button variant="ghost" onClick={onClose} disabled={creating}>
            Huỷ
          </Button>
          <Button onClick={() => void handleCreate()} disabled={!name.trim() || creating}>
            {creating ? "Đang tạo..." : "Tạo"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
