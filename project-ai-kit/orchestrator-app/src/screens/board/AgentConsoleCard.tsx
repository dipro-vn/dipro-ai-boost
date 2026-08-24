import { useEffect, useState } from "react";
import { ChevronDown, ChevronRight, Square } from "lucide-react";
import { Virtuoso } from "react-virtuoso";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { estimateThinkingCostUsd } from "@/lib/pricing";
import { slotDisplayName } from "@/lib/slot-label";
import { statusMeta } from "@/lib/status-meta";
import type { AgentSlot, NodeState } from "@/lib/tauri-client";
import { formatElapsed } from "@/screens/board/agent-run-shared";
import { TerminalFrame } from "@/screens/board/TerminalFrame";
import type { AgentConsoleState } from "@/state/run-console-store";

interface AgentConsoleCardProps {
  agent: AgentSlot;
  /** User-set alias for this slot, if any — see `@/lib/slot-label`. */
  nickname?: string;
  stageLabel: string;
  nodeState: NodeState | undefined;
  consoleState: AgentConsoleState;
  onKill: () => void;
  onSelect: () => void;
}

export function AgentConsoleCard({
  agent,
  nickname,
  stageLabel,
  nodeState,
  consoleState,
  onKill,
  onSelect,
}: AgentConsoleCardProps) {
  const status = nodeState?.status ?? (consoleState.liveActive ? "running" : "idle");
  const meta = statusMeta(status);
  const Icon = meta.icon;
  const [collapsed, setCollapsed] = useState(status !== "running");
  const displayName = slotDisplayName(agent, nickname);
  const [now, setNow] = useState(() => Date.now());

  useEffect(() => {
    if (!consoleState.liveActive && status !== "running") return;
    const interval = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(interval);
  }, [consoleState.liveActive, status]);

  const elapsedMs = now - consoleState.startedAt;
  const estimatedCostUsd = consoleState.sessionModel
    ? estimateThinkingCostUsd(consoleState.sessionModel, consoleState.thinkingTokens)
    : null;
  const isRunning = consoleState.liveActive || status === "running";

  return (
    <div className="rounded-lg border border-border bg-card p-2">
      <div className="flex items-center gap-2">
        <button
          type="button"
          className="flex min-w-0 flex-1 items-center gap-2 rounded-md p-1 text-left hover:bg-muted/60"
          onClick={onSelect}
        >
          {collapsed ? (
            <ChevronRight className="size-3.5 shrink-0 text-muted-foreground" aria-hidden="true" />
          ) : (
            <ChevronDown className="size-3.5 shrink-0 text-muted-foreground" aria-hidden="true" />
          )}
          <Icon className={cn("size-4 shrink-0", meta.colorClass, meta.spin && "animate-spin")} />
          <span className="min-w-0 truncate text-xs font-medium">{displayName}</span>
          <span className="truncate text-[11px] text-muted-foreground">{stageLabel}</span>
        </button>
        <Badge variant={isRunning ? "default" : "secondary"}>{meta.label}</Badge>
        {isRunning && (
          <Button variant="destructive" size="icon-sm" onClick={onKill} aria-label={`Kill ${displayName}`}>
            <Square />
          </Button>
        )}
        <Button
          variant="ghost"
          size="icon-sm"
          onClick={() => setCollapsed((value) => !value)}
          aria-label={collapsed ? `Mở log ${displayName}` : `Thu gọn log ${displayName}`}
        >
          {collapsed ? <ChevronRight /> : <ChevronDown />}
        </Button>
      </div>

      {!collapsed && (
        <div className="mt-2 flex flex-col gap-2">
          <div className="flex flex-wrap items-center gap-1.5 px-1">
            {isRunning && <Badge variant="secondary">⏱ {formatElapsed(elapsedMs)}</Badge>}
            {estimatedCostUsd !== null && (
              <Badge variant="secondary">~${estimatedCostUsd.toFixed(4)} (ước tính)</Badge>
            )}
            {consoleState.lastSummary && (
              <span className="text-[11px] text-muted-foreground">
                Lần chạy gần nhất: ${consoleState.lastSummary.costUsd.toFixed(4)}
              </span>
            )}
          </div>

          {status === "waiting-input" && (
            <Alert>
              <AlertTitle>{displayName} đang chờ trả lời</AlertTitle>
              <AlertDescription>
                Chọn node để xem câu hỏi và gửi câu trả lời.
              </AlertDescription>
            </Alert>
          )}

          <TerminalFrame title={`${displayName} — ${meta.label}`}>
            <div className="h-48">
              {consoleState.lines.length > 0 ? (
                <Virtuoso
                  style={{ height: "100%" }}
                  data={consoleState.lines}
                  followOutput="smooth"
                  itemContent={(_index, line) => (
                    <div
                      className={cn(
                        "px-3 py-0.5 font-mono text-xs whitespace-pre-wrap",
                        line.isError
                          ? "text-red-400"
                          : line.muted
                            ? "text-zinc-500"
                            : "text-zinc-100",
                      )}
                    >
                      {line.text}
                    </div>
                  )}
                />
              ) : (
                <div className="flex h-full items-center justify-center px-3 font-mono text-xs text-zinc-500">
                  Chưa có log...
                </div>
              )}
            </div>
          </TerminalFrame>
        </div>
      )}
    </div>
  );
}
