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
import { commands, isAppCommandError, type RunningSlot } from "@/lib/tauri-client";
import { useAppStore } from "@/state/app-store";

function extractErrorMessage(err: unknown): string {
  if (isAppCommandError(err)) return err.message;
  if (err instanceof Error) return err.message;
  return String(err);
}

interface SwitchProjectDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

/**
 * Leaving a project isn't just navigation: the backend holds that project's
 * roots, Ecosystem, file watcher and running processes. `close_project`
 * clears all of it, and refuses while agents are running — `RunKey` is only
 * `(feature, slot)`, so a run left tracked would be mistaken for the next
 * project's own, right down to the Kill button.
 *
 * So this asks first, naming exactly what is still running.
 */
export function SwitchProjectDialog({ open, onOpenChange }: SwitchProjectDialogProps) {
  const leaveProject = useAppStore((s) => s.leaveProject);
  const [running, setRunning] = useState<RunningSlot[] | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!open) return;
    setErrorMessage(null);
    setRunning(null);
    let cancelled = false;
    commands
      .listRunningSlots()
      .then((slots) => {
        if (!cancelled) setRunning(slots);
      })
      .catch(() => {
        // Can't enumerate: treat as "nothing known" and let the backend's
        // own refusal be the guard.
        if (!cancelled) setRunning([]);
      });
    return () => {
      cancelled = true;
    };
  }, [open]);

  async function handleSwitch(force: boolean) {
    setBusy(true);
    setErrorMessage(null);
    try {
      await commands.closeProject(force);
      leaveProject();
      onOpenChange(false);
    } catch (err) {
      setErrorMessage(extractErrorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  const hasRunning = (running?.length ?? 0) > 0;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>Đổi project</DialogTitle>
          <DialogDescription>
            Quay lại màn hình chọn project. Không có gì trên đĩa bị xoá — chỉ đóng project đang mở.
          </DialogDescription>
        </DialogHeader>

        {running === null ? (
          <p className="text-sm text-muted-foreground">Đang kiểm tra agent đang chạy...</p>
        ) : hasRunning ? (
          <Alert variant="destructive">
            <AlertTitle>Đang có {running.length} agent chạy</AlertTitle>
            <AlertDescription>
              <div className="flex flex-col gap-1">
                <div className="font-mono text-xs">
                  {running.map((r) => `${r.feature} / ${r.slot}`).join(", ")}
                </div>
                <span>
                  Đóng project sẽ <strong>kill</strong> những agent này — phần việc đang dở sẽ mất.
                  Muốn giữ thì Huỷ, đợi chúng chạy xong rồi đổi sau.
                </span>
              </div>
            </AlertDescription>
          </Alert>
        ) : (
          <p className="text-sm text-muted-foreground">Không có agent nào đang chạy.</p>
        )}

        {errorMessage && (
          <Alert variant="destructive">
            <AlertTitle>Không đóng được project</AlertTitle>
            <AlertDescription className="break-all">{errorMessage}</AlertDescription>
          </Alert>
        )}

        <DialogFooter>
          <Button variant="ghost" onClick={() => onOpenChange(false)} disabled={busy}>
            Huỷ
          </Button>
          <Button
            variant={hasRunning ? "destructive" : "default"}
            onClick={() => handleSwitch(hasRunning)}
            disabled={running === null || busy}
          >
            {busy ? "Đang đóng..." : hasRunning ? "Kill hết và đổi project" : "Đổi project"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
