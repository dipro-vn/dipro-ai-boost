import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { ClipboardList, RefreshCw } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  commands,
  type BacklogPushView,
  type BacklogStatusCache,
  type RunSummary,
} from "@/lib/tauri-client";
import { onAgentLogLine, onAgentRunFinished } from "@/lib/events";
import {
  extractErrorMessage,
  LiveLogView,
  manualLogLine,
  toLogLine,
  WaitingInputPanel,
  type LogLine,
} from "@/screens/board/agent-run-shared";
import { TerminalFrame } from "@/screens/board/TerminalFrame";
import { useAppStore } from "@/state/app-store";
import { ScreenHeader } from "@/components/shell/ScreenHeader";

/** Mirrors `commands::backlog::BACKLOG_PUSH_SLOT`. */
const PUSH_SLOT = "backlog-push";

/** AC-E5-15 — auto refresh cadence while this screen is open. */
const REFRESH_INTERVAL_MS = 15 * 60 * 1000;

function formatTimestamp(value: string): string {
  if (!value) return "chưa có";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString("vi-VN");
}

/**
 * `OR_INTG_001` — Backlog push + status (AC-E5-01..18).
 *
 * Deliberate deviation from the SPEC's structured modal (documented as B21
 * in ASSUMPTIONS-GAPS.md): issue creation runs through the kit's own
 * `pm-agent` over the project's Backlog MCP server, so the metadata
 * questions and the sample-issue confirmation happen in the agent's own
 * conversation — surfaced here with the same live-log + answer box every
 * other agent step uses.
 */
export function BacklogScreen() {
  const setScreen = useAppStore((s) => s.setScreen);
  const feature = useAppStore((s) => s.activeFeature);

  const [view, setView] = useState<BacklogPushView | null>(null);
  const [statusCache, setStatusCache] = useState<BacklogStatusCache | null>(null);
  const [configured, setConfigured] = useState<boolean | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const [liveActive, setLiveActive] = useState(false);
  const liveActiveRef = useRef(false);
  const [liveLines, setLiveLines] = useState<LogLine[]>([]);
  const [startedAt, setStartedAt] = useState(() => Date.now());
  const [now, setNow] = useState(() => Date.now());
  const [lastSummary, setLastSummary] = useState<RunSummary | null>(null);
  const [answer, setAnswer] = useState("");
  /** See `AgentStepPanel` — one auto-open of the question modal per push. */
  const [questionAutoOpened, setQuestionAutoOpened] = useState(false);

  const reloadView = useCallback(() => {
    if (!feature) return;
    commands
      .getBacklogPushView(feature)
      .then(setView)
      .catch((err) => setErrorMessage(extractErrorMessage(err)));
  }, [feature]);

  useEffect(() => {
    reloadView();
    commands
      .getBacklogStatus()
      .then((status) => setConfigured(status.configured))
      .catch(() => setConfigured(false));
    if (!feature) return;

    commands
      .getBacklogStatusCache(feature)
      .then((cache) => setStatusCache(cache))
      .catch(() => {
        // No cache yet — the table simply shows "chưa làm mới".
      });

    // The 5 metadata questions span several visits to this screen, so the
    // pending question has to survive navigating away: both the summary
    // (which carries the question text) and the log come off disk, exactly
    // like the pipeline panels do.
    commands
      .getRunSummary(feature, PUSH_SLOT)
      .then((summary) => setLastSummary(summary))
      .catch(() => {
        // Never pushed for this feature yet.
      });
    commands
      .getRunLog(feature, PUSH_SLOT)
      .then((events) => {
        setLiveLines((prev) => {
          if (prev.length > 0) return prev;
          return events.map(toLogLine).filter((line): line is LogLine => line !== null);
        });
      })
      .catch(() => {
        // No persisted log yet.
      });
  }, [feature, reloadView]);

  // Live log + completion, filtered to this feature's push slot.
  useEffect(() => {
    if (!feature) return;
    let cancelled = false;
    const unlistenLine = onAgentLogLine((payload) => {
      if (cancelled || payload.feature !== feature || payload.slot !== PUSH_SLOT) return;
      if (!liveActiveRef.current) {
        liveActiveRef.current = true;
        setLiveActive(true);
        setStartedAt(Date.now());
        setNow(Date.now());
      }
      const line = toLogLine(payload.event);
      if (line) setLiveLines((prev) => [...prev, line]);
    });
    const unlistenFinished = onAgentRunFinished((payload) => {
      if (cancelled || payload.feature !== feature || payload.slot !== PUSH_SLOT) return;
      liveActiveRef.current = false;
      setLiveActive(false);
      setLastSummary(payload.summary);
      reloadView();
    });
    return () => {
      cancelled = true;
      void unlistenLine.then((f) => f());
      void unlistenFinished.then((f) => f());
    };
  }, [feature, reloadView]);

  useEffect(() => {
    if (!liveActive) return;
    const id = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(id);
  }, [liveActive]);

  const handleRefresh = useCallback(async () => {
    if (!feature) return;
    setRefreshing(true);
    try {
      setStatusCache(await commands.refreshBacklogStatus(feature));
    } catch (err) {
      setErrorMessage(extractErrorMessage(err));
    } finally {
      setRefreshing(false);
    }
  }, [feature]);

  // AC-E5-15 — automatic 15-minute refresh while the screen is open, on top
  // of the manual button.
  useEffect(() => {
    if (!feature) return;
    const id = setInterval(() => void handleRefresh(), REFRESH_INTERVAL_MS);
    return () => clearInterval(id);
  }, [feature, handleRefresh]);

  function beginLive(initialLines: LogLine[]) {
    liveActiveRef.current = true;
    setLiveActive(true);
    setLiveLines(initialLines);
    setStartedAt(Date.now());
    setNow(Date.now());
  }

  async function handlePush() {
    if (!feature) return;
    setErrorMessage(null);
    setQuestionAutoOpened(false);
    beginLive([manualLogLine("— Bắt đầu đẩy task lên Backlog qua pm-agent...")]);
    try {
      await commands.pushToBacklog(feature);
    } catch (err) {
      liveActiveRef.current = false;
      setLiveActive(false);
      setErrorMessage(extractErrorMessage(err));
    }
  }

  async function handleAnswer() {
    if (!feature || !answer.trim()) return;
    const toSend = answer.trim();
    setAnswer("");
    setErrorMessage(null);
    beginLive([manualLogLine(`— Đã gửi câu trả lời: ${toSend}`)]);
    try {
      await commands.pushToBacklog(feature, toSend);
    } catch (err) {
      liveActiveRef.current = false;
      setLiveActive(false);
      setErrorMessage(extractErrorMessage(err));
    }
  }

  async function handleKill() {
    if (!feature) return;
    try {
      await commands.killRun(feature, PUSH_SLOT);
    } catch {
      // Best-effort — the run may have finished on its own.
    }
  }

  const statusByTaskFile = useMemo(() => {
    const map = new Map<string, BacklogStatusCache["issues"][number]>();
    for (const issue of statusCache?.issues ?? []) map.set(issue.taskFile, issue);
    return map;
  }, [statusCache]);

  const issuesByPhase = useMemo(() => {
    const groups = new Map<string, { issueKey: string; taskFile: string }[]>();
    for (const link of view?.mapping.issues ?? []) {
      const key = link.phase != null ? `Phase ${link.phase}` : "Không rõ phase";
      const list = groups.get(key) ?? [];
      list.push({ issueKey: link.issueKey, taskFile: link.taskFile });
      groups.set(key, list);
    }
    return [...groups.entries()].sort(([a], [b]) => a.localeCompare(b));
  }, [view]);

  if (!feature) {
    return (
      <div className="flex h-full items-center justify-center p-6 text-center text-sm text-muted-foreground">
        Chưa chọn feature nào — quay lại Pipeline Board và chọn một feature trước.
      </div>
    );
  }

  const waitingForAnswer = lastSummary?.outcome === "waiting-input";
  const elapsedMs = now - startedAt;

  return (
    <div className="flex h-full flex-col gap-4 overflow-y-auto p-6">
      <ScreenHeader
        title={`Backlog — ${feature}`}
        description="Đẩy issue qua pm-agent + MCP Backlog của project. Phần kéo trạng thái dùng API key trong Settings › Integrations."
        icon={ClipboardList}
        onBack={() => setScreen("board")}
      />

      {errorMessage && (
        <Alert variant="destructive">
          <AlertTitle>Có lỗi</AlertTitle>
          <AlertDescription className="break-all">{errorMessage}</AlertDescription>
        </Alert>
      )}

      {view?.warning && (
        <Alert>
          <AlertTitle>Cảnh báo mapping</AlertTitle>
          <AlertDescription>{view.warning}</AlertDescription>
        </Alert>
      )}

      {liveActive ? (
        <LiveLogView
          title="pm-agent — đang đẩy Backlog"
          lines={liveLines}
          elapsedMs={elapsedMs}
          estimatedCostUsd={null}
          onKill={handleKill}
        />
      ) : (
        <>
          {waitingForAnswer && (
            <WaitingInputPanel
              question={lastSummary?.lastMessage ?? undefined}
              agentLabel="pm-agent"
              value={answer}
              onChange={setAnswer}
              onSend={handleAnswer}
              autoOpen={!questionAutoOpened}
              onAutoOpened={() => setQuestionAutoOpened(true)}
            />
          )}

          <div className="flex flex-wrap items-center gap-2">
            <Button onClick={handlePush} disabled={!view || view.pending.length === 0}>
              {view && view.mapping.issues.length > 0 ? "Đẩy các task còn lại" : "Push to Backlog"}
            </Button>
            <Button variant="outline" onClick={handleRefresh} disabled={refreshing}>
              <RefreshCw className={refreshing ? "animate-spin" : undefined} />
              {refreshing ? "Đang làm mới..." : "Làm mới trạng thái"}
            </Button>
            {view && view.pending.length === 0 && view.tasks.length > 0 && (
              <span className="text-xs text-muted-foreground">
                Mọi task đã có issue — không còn gì để đẩy.
              </span>
            )}
          </div>
        </>
      )}

      {/* AC-E5-12 — the warning has to sit where the PM decides to push. */}
      {view && view.missingEstimate.length > 0 && (
        <Alert>
          <AlertTitle>Thiếu Estimated Hours</AlertTitle>
          <AlertDescription>
            {view.missingEstimate.length} task file chưa có Estimate — Backlog yêu cầu trường này.
            Bổ sung trong task file, hoặc trả lời agent khi nó hỏi.
          </AlertDescription>
        </Alert>
      )}

      {view && (
        <div className="grid gap-3 sm:grid-cols-3">
          <div className="rounded-xl border border-border bg-card p-3">
            <p className="text-xs text-muted-foreground">Tổng task</p>
            <p className="mt-1 text-lg font-semibold tabular-nums">{view.tasks.length}</p>
          </div>
          <div className="rounded-xl border border-border bg-card p-3">
            <p className="text-xs text-muted-foreground">Đã tạo issue</p>
            <p className="mt-1 text-lg font-semibold tabular-nums">{view.mapping.issues.length}</p>
          </div>
          <div className="rounded-xl border border-border bg-card p-3">
            <p className="text-xs text-muted-foreground">Còn chờ push</p>
            <p className="mt-1 text-lg font-semibold tabular-nums">{view.pending.length}</p>
          </div>
        </div>
      )}

      <Separator />

      <div className="flex flex-col gap-2">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold">Task &amp; issue</h2>
          {/* AC-E5-16 — always say when the numbers are from. */}
          <span className="text-xs text-muted-foreground">
            {statusCache
              ? `Số liệu lúc ${formatTimestamp(statusCache.fetchedAt)}${statusCache.stale ? " (số liệu cũ — làm mới thất bại)" : ""}`
              : "Chưa làm mới trạng thái lần nào"}
          </span>
        </div>

        {statusCache?.stale && statusCache.error && (
          <p className="text-xs text-warning break-all">{statusCache.error}</p>
        )}

        {view === null ? (
          <div className="flex flex-col gap-2">
            <div className="skeleton h-9 w-full" />
            <div className="skeleton h-9 w-full" />
            <div className="skeleton h-9 w-full" />
          </div>
        ) : view.tasks.length === 0 ? (
          <div className="flex flex-col items-center gap-2 rounded-xl border border-dashed border-border bg-muted/20 py-8 text-center">
            <ClipboardList className="size-8 text-muted-foreground/40" aria-hidden="true" />
            <p className="text-sm text-muted-foreground">
              Feature này chưa có file <code>tasks/task-*.md</code> nào.
            </p>
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Task file</TableHead>
                <TableHead>Phase</TableHead>
                <TableHead>Estimate</TableHead>
                <TableHead>Issue</TableHead>
                <TableHead>Trạng thái</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {view.tasks.map((task) => {
                const link = view.mapping.issues.find(
                  (issue) => issue.taskFile === task.relativePath,
                );
                const status = statusByTaskFile.get(task.relativePath);
                const hashAtPush = statusCache?.taskHashes[task.relativePath];
                return (
                  <TableRow key={task.relativePath}>
                    <TableCell className="font-mono text-xs">{task.relativePath}</TableCell>
                    <TableCell>{task.phase ?? "—"}</TableCell>
                    <TableCell>
                      {task.estimate ?? (
                          <Badge variant="outline" className="text-warning">
                          thiếu
                        </Badge>
                      )}
                    </TableCell>
                    <TableCell className="font-mono text-xs">
                      {link ? link.issueKey : <span className="text-muted-foreground">chưa đẩy</span>}
                    </TableCell>
                    <TableCell>
                      {!link ? (
                        "—"
                      ) : status?.notFound ? (
                        <Badge variant="destructive">không tìm thấy</Badge>
                      ) : status?.statusName ? (
                        <div className="flex items-center gap-1">
                          <Badge variant="secondary">{status.statusName}</Badge>
                          {/* AC-E5-18 — drift is reported, never auto-synced. */}
                          {hashAtPush && <DriftBadge feature={feature} task={task.relativePath} hashAtPush={hashAtPush} />}
                        </div>
                      ) : (
                        <span className="text-xs text-muted-foreground">chưa làm mới</span>
                      )}
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        )}
      </div>

      {/* AC-E5-09 — issue keys grouped by phase after a push. */}
      {issuesByPhase.length > 0 && (
        <>
          <Separator />
          <div className="flex flex-col gap-2">
            <h2 className="text-sm font-semibold">Issue đã tạo (theo phase)</h2>
            {issuesByPhase.map(([phase, issues]) => (
              <div key={phase} className="flex flex-wrap items-center gap-2">
                <span className="text-xs font-medium text-muted-foreground">{phase}:</span>
                {issues.map((issue) => (
                  <Badge key={issue.issueKey} variant="outline" className="font-mono">
                    {issue.issueKey}
                  </Badge>
                ))}
              </div>
            ))}
            {view?.mapping.parentIssue && (
              <p className="text-xs text-muted-foreground">
                Parent Issue: <code>{view.mapping.parentIssue}</code>
              </p>
            )}
          </div>
        </>
      )}

      {!liveActive && liveLines.length > 0 && (
        <>
          <Separator />
          <TerminalFrame title="pm-agent — log lần đẩy gần nhất">
            <div className="max-h-56 overflow-y-auto py-1">
              {liveLines.map((line) => (
                <div
                  key={line.id}
                  className={`px-3 py-0.5 font-mono text-xs whitespace-pre-wrap ${
                    line.isError ? "text-red-400" : line.muted ? "text-zinc-500" : "text-zinc-100"
                  }`}
                >
                  {line.text}
                </div>
              ))}
            </div>
          </TerminalFrame>
        </>
      )}

      {configured === false && (
        <Alert>
          <AlertTitle>Chưa cấu hình Backlog cho phần kéo trạng thái</AlertTitle>
          <AlertDescription>
            Vào Settings › Integrations nhập domain + project key + API key để app đọc được trạng
            thái issue. Việc đẩy issue vẫn chạy được vì đi qua MCP của project.
          </AlertDescription>
        </Alert>
      )}
    </div>
  );
}

/** AC-E5-18 — compares the task file's current content against the hash
 * captured at the last successful refresh. Reads the file through the
 * existing artifact command so no new backend surface is needed. */
function DriftBadge({
  feature,
  task,
  hashAtPush,
}: {
  feature: string;
  task: string;
  hashAtPush: string;
}) {
  const [drifted, setDrifted] = useState(false);

  useEffect(() => {
    let cancelled = false;
    commands
      .hashTaskFile(feature, task)
      .then((hash) => {
        if (!cancelled) setDrifted(hash !== null && hash !== hashAtPush);
      })
      .catch(() => {
        // Unreadable file — say nothing rather than claim drift.
      });
    return () => {
      cancelled = true;
    };
  }, [feature, task, hashAtPush]);

  if (!drifted) return null;
  return (
    <Badge variant="outline" className="text-warning" title="Task file đã đổi sau khi tạo issue">
      lệch
    </Badge>
  );
}
