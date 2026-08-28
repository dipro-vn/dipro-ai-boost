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
import { commands, type FeatureDeletionPreview } from "@/lib/tauri-client";
import { extractErrorMessage } from "@/screens/board/agent-run-shared";

interface DeleteFeatureDialogProps {
  /** `null` closes the dialog. */
  feature: string | null;
  onClose: () => void;
  onDeleted: (features: string[]) => void;
}

/**
 * Confirms the single most destructive action in the app: deleting a
 * feature removes `<docsRoot>/features/<name>/` — SPEC.md, DESIGN.md,
 * tasks/, test-cases/ — with no undo and no trash.
 *
 * So it never fires from one click: the inventory of what will be lost is
 * fetched and shown first, and the user has to retype the feature name.
 * The backend re-checks that name and refuses while any agent is running,
 * so neither of those guarantees depends on this component being correct.
 */
export function DeleteFeatureDialog({
  feature,
  onClose,
  onDeleted,
}: DeleteFeatureDialogProps) {
  const [preview, setPreview] = useState<FeatureDeletionPreview | null>(null);
  const [typed, setTyped] = useState("");
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setPreview(null);
    setTyped("");
    setError(null);
    if (!feature) return;
    let cancelled = false;
    commands
      .previewDeleteFeature(feature)
      .then((result) => {
        if (!cancelled) setPreview(result);
      })
      .catch((err) => {
        if (!cancelled) setError(extractErrorMessage(err));
      });
    return () => {
      cancelled = true;
    };
  }, [feature]);

  async function handleDelete() {
    if (!feature) return;
    setDeleting(true);
    setError(null);
    try {
      onDeleted(await commands.deleteFeature(feature, typed.trim()));
      onClose();
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setDeleting(false);
    }
  }

  const blocked = (preview?.runningSlots.length ?? 0) > 0;
  const canDelete = !!feature && !blocked && typed.trim() === feature && !deleting;

  return (
    <Dialog open={feature !== null} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>Xoá feature “{feature}”?</DialogTitle>
          <DialogDescription>
            Thao tác này <strong>không hoàn tác được</strong> và không đi qua Thùng rác.
          </DialogDescription>
        </DialogHeader>

        {preview === null && !error ? (
          <div className="flex flex-col gap-3">
            <div className="skeleton h-5 w-40" />
            <div className="skeleton h-20 w-full" />
            <div className="skeleton h-9 w-full" />
          </div>
        ) : preview ? (
          <div className="flex flex-col gap-3">
            {blocked && (
              <Alert variant="destructive">
                <AlertTitle>Đang có agent chạy</AlertTitle>
                <AlertDescription>
                  {preview.runningSlots.join(", ")} — dừng (Kill) trước khi xoá.
                </AlertDescription>
              </Alert>
            )}

            <div className="flex flex-col gap-1 rounded-lg border border-destructive/40 p-3">
              <p className="text-sm font-medium">Sẽ bị xoá vĩnh viễn:</p>
              <ul className="list-inside list-disc text-sm text-muted-foreground">
                <li>
                  <strong className="text-foreground">{preview.docFileCount}</strong> file tài
                  liệu trong <code>features/{feature}/</code>
                </li>
                {preview.runCount > 0 && <li>Log và kết quả của {preview.runCount} slot đã chạy</li>}
                {preview.inputCopyCount > 0 && (
                  <li>{preview.inputCopyCount} bản copy input đã import</li>
                )}
                {preview.hasContractLock && <li>Lịch sử Contract Lock</li>}
              </ul>

              {preview.notableArtifacts.length > 0 && (
                <div className="mt-1 max-h-32 overflow-y-auto rounded border border-border bg-muted/30 p-2">
                  {preview.notableArtifacts.map((path) => (
                    <div key={path} className="font-mono text-xs">
                      {path}
                    </div>
                  ))}
                </div>
              )}

              <p className="mt-1 text-xs text-muted-foreground">
                Số liệu chi phí trong Reports được giữ lại.
              </p>
            </div>

            <div className="flex flex-col gap-1">
              <Label htmlFor="delete-confirm">
                Gõ lại <code>{feature}</code> để xác nhận
              </Label>
              <Input
                id="delete-confirm"
                autoFocus
                autoComplete="off"
                value={typed}
                disabled={blocked || deleting}
                onChange={(e) => setTyped(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && canDelete) void handleDelete();
                }}
              />
            </div>
          </div>
        ) : null}

        {error && (
          <Alert variant="destructive">
            <AlertTitle>Không xoá được</AlertTitle>
            <AlertDescription className="break-all">{error}</AlertDescription>
          </Alert>
        )}

        <DialogFooter>
          <Button variant="ghost" onClick={onClose} disabled={deleting}>
            Huỷ
          </Button>
          <Button variant="destructive" onClick={handleDelete} disabled={!canDelete}>
            {deleting ? "Đang xoá..." : "Xoá vĩnh viễn"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
