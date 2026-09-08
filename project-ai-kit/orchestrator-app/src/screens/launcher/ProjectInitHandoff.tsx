import { useState } from "react";
import { Check, Copy, RefreshCw, Terminal } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import type { ProjectInitStatus } from "@/lib/tauri-client";

interface ProjectInitHandoffProps {
  projectName: string;
  agentsRoot: string;
  status: ProjectInitStatus;
  reasons: string[];
  refreshing?: boolean;
  onRefresh: () => void;
  /** Chỉ truyền ở màn hình nào có sẵn terminal init-kit — hiện tại là Launcher.
   * Có nó thì nút cuối alert đổi thành mở terminal và chạy init ngay trong app;
   * bỏ trống (Pipeline Board, hoặc project thiếu khung kit / read-only) thì giữ
   * nút kiểm tra lại cho luồng chạy thủ công. */
  onRunInitKit?: () => void;
}

function quotePath(path: string): string {
  return `"${path.replace(/"/g, '\\"')}"`;
}

export function ProjectInitHandoff({
  projectName,
  agentsRoot,
  status,
  reasons,
  refreshing = false,
  onRefresh,
  onRunInitKit,
}: ProjectInitHandoffProps) {
  const [copied, setCopied] = useState<"shell" | "prompt" | null>(null);
  const [copyError, setCopyError] = useState<string | null>(null);

  if (status === "ready" || status === "missing-kit") return null;

  const shellCommand = `cd ${quotePath(agentsRoot)}\nclaude`;
  const initPrompt = `/init-kit Tên dự án: ${projectName}`;

  async function copy(value: string, kind: "shell" | "prompt") {
    setCopyError(null);
    try {
      await navigator.clipboard.writeText(value);
      setCopied(kind);
      window.setTimeout(() => setCopied(null), 1600);
    } catch {
      setCopyError("Không copy được command. Hãy chọn và copy thủ công.");
    }
  }

  return (
    <Alert className="border-warning/50">
      <Terminal className="size-4" />
      <AlertTitle>
        {status === "needs-init"
          ? "Project chưa init"
          : "Cấu hình project cần kiểm tra"}
      </AlertTitle>
      <AlertDescription>
        <div className="flex flex-col gap-3">
          <p>
            {onRunInitKit ? (
              <>
                Project chưa chạy <code>/init-kit</code>. Bấm{" "}
                <strong>Chạy init-kit trong app</strong> để mở terminal và chạy
                ngay tại đây, hoặc tự chạy trong Claude Code:
              </>
            ) : (
              <>
                App đã tạo khung kit nhưng không tự chạy <code>/init-kit</code>.
                Hãy chạy lệnh này trong Claude Code tại <code>agentsRoot</code>:
              </>
            )}
          </p>
          {reasons.length > 0 && (
            <ul className="list-inside list-disc text-xs">
              {reasons.map((reason) => (
                <li key={reason}>{reason}</li>
              ))}
            </ul>
          )}
          <div className="flex flex-col gap-1">
            <span className="text-xs font-medium">1. Terminal</span>
            <div className="flex items-start gap-2">
              <pre className="min-w-0 flex-1 overflow-x-auto rounded bg-muted p-2 font-mono text-xs">
                {shellCommand}
              </pre>
              <Button
                type="button"
                variant="outline"
                size="icon-sm"
                onClick={() => void copy(shellCommand, "shell")}
                aria-label="Copy command mở Claude Code"
              >
                {copied === "shell" ? <Check /> : <Copy />}
              </Button>
            </div>
          </div>
          <div className="flex flex-col gap-1">
            <span className="text-xs font-medium">2. Trong Claude Code</span>
            <div className="flex items-start gap-2">
              <pre className="min-w-0 flex-1 overflow-x-auto rounded bg-muted p-2 font-mono text-xs">
                {initPrompt}
              </pre>
              <Button
                type="button"
                variant="outline"
                size="icon-sm"
                onClick={() => void copy(initPrompt, "prompt")}
                aria-label="Copy command init-kit"
              >
                {copied === "prompt" ? <Check /> : <Copy />}
              </Button>
            </div>
          </div>
          {copyError && <p className="text-xs text-destructive">{copyError}</p>}
          {onRunInitKit ? (
            <Button type="button" size="sm" onClick={onRunInitKit}>
              <Terminal />
              Chạy init-kit trong app
            </Button>
          ) : (
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={onRefresh}
              disabled={refreshing}
            >
              <RefreshCw className={refreshing ? "animate-spin" : undefined} />
              {refreshing ? "Đang kiểm tra..." : "Đã chạy init, kiểm tra lại"}
            </Button>
          )}
        </div>
      </AlertDescription>
    </Alert>
  );
}
