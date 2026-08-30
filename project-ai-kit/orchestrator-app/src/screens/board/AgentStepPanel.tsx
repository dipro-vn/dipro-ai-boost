import { useEffect, useMemo, useRef, useState } from "react";
import { Play, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { cn } from "@/lib/utils";
import { isPreviewableArtifact } from "@/lib/artifact-preview";
import { slotDisplayName } from "@/lib/slot-label";
import { statusMeta } from "@/lib/status-meta";
import {
  commands,
  readinessReason,
  type AgentSlot,
  type NodeState,
  type PipelineDef,
  type RunSummary,
  type SlotReadiness,
} from "@/lib/tauri-client";
import { onAgentLogLine, onAgentRunFinished } from "@/lib/events";
import { estimateThinkingCostUsd } from "@/lib/pricing";
import { agentDraftKey, useAppStore } from "@/state/app-store";
import {
  canRetry,
  computeSkipDependents,
  DEFAULT_MAX_RETRIES,
  extractErrorMessage,
  LiveLogView,
  manualLogLine,
  toLogLine,
  WaitingInputPanel,
  type LogLine,
} from "@/screens/board/agent-run-shared";
import { ArtifactModal } from "@/screens/board/ArtifactModal";
import { ArtifactSummary } from "@/screens/board/ArtifactSummary";
import { TerminalFrame } from "@/screens/board/TerminalFrame";

interface AgentStepPanelProps {
  feature: string;
  agent: AgentSlot;
  /** User-set alias for this slot, if any — see `@/lib/slot-label`. */
  nickname?: string;
  nodeState: NodeState | undefined;
  /** For AC-E6-26's skip-dependents warning. */
  pipelineDef: PipelineDef | null;
  /** B22 — whether this slot may be run yet, and why not if it can't. */
  readiness: SlotReadiness | undefined;
  /** Project setup is completed through the external `/init-kit` handoff. */
  projectReady: boolean;
  /** Re-asks the backend, re-reading the Ecosystem from disk on the way. */
  onRecheckReadiness: () => void;
  /** The Board renders live output in AgentConsoleDock. */
  showConsole?: boolean;
}

/**
 * Interactive panel for every agent slot EXCEPT `ba` (which keeps its own
 * `BaStepPanel` for the folder-import step no other slot has). Replaces the
 * old read-only `GenericStepPanel`, which left a stage-② agent that asked a
 * clarification question permanently stuck with no way to answer
 * (AC-E2-16/18/19 apply to every slot, not just `ba` — the backend was
 * already fully slot-generic).
 *
 * B22 — this panel now owns starting a run too: the Run button is the only
 * way a pipeline agent spawns (gates record approvals, they no longer fan
 * out), gated by `readiness` so a slot can't jump its queue.
 */
export function AgentStepPanel({
  feature,
  agent,
  nickname,
  nodeState,
  pipelineDef,
  readiness,
  projectReady,
  onRecheckReadiness,
  showConsole = true,
}: AgentStepPanelProps) {
  const [liveActive, setLiveActive] = useState(false);
  const [liveLines, setLiveLines] = useState<LogLine[]>([]);
  const [confirmRetry, setConfirmRetry] = useState(false);
  const [confirmSkip, setConfirmSkip] = useState(false);
  const [confirmForceDone, setConfirmForceDone] = useState(false);
  const [startedAt, setStartedAt] = useState(() => Date.now());
  const [now, setNow] = useState(() => Date.now());
  const [actionError, setActionError] = useState<string | null>(null);
  const [answer, setAnswer] = useState("");
  const displayName = slotDisplayName(agent, nickname);
  /** Each run auto-opens the question modal once, for its FIRST question;
   * later questions in the same run wait for the expand button. Owned here
   * because `WaitingInputPanel` unmounts between two questions. */
  const [questionAutoOpened, setQuestionAutoOpened] = useState(false);

  // Selecting another node reuses this same component instance, so without
  // this the newly selected node would inherit the previous one's spent
  // auto-open.
  useEffect(() => {
    setQuestionAutoOpened(false);
  }, [feature, agent.id]);
  const [refreshKey, setRefreshKey] = useState(0);
  const [lastSummary, setLastSummary] = useState<RunSummary | null>(null);
  const [sessionModel, setSessionModel] = useState<string | null>(null);
  const [thinkingTokens, setThinkingTokens] = useState(0);
  /** Only used by the `design-analyst` slot — see the Run block below. Lives
   * in the global store (not local `useState`) so it survives navigating
   * away and back before the run is started; cleared once the run starts. */
  const setAgentDraft = useAppStore((s) => s.setAgentDraft);
  const clearAgentDraft = useAppStore((s) => s.clearAgentDraft);
  const figmaUrl =
    useAppStore((s) => s.agentDrafts[agentDraftKey(feature, agent.id)]?.figmaUrl) ?? "";
  /** Artifact shown in the read-in-place modal; null = closed. */
  const [modalArtifact, setModalArtifact] = useState<string | null>(null);
  // Mirrors `liveActive` synchronously so the listener below can detect the
  // inactive→active transition within a single event batch (an effect-based
  // reset would run AFTER the first event and wipe the model it just set).
  const liveActiveRef = useRef(false);

  function beginLiveRun(initialLines: LogLine[]) {
    liveActiveRef.current = true;
    setLiveActive(true);
    setLiveLines(initialLines);
    setStartedAt(Date.now());
    setNow(Date.now());
    setSessionModel(null);
    setThinkingTokens(0);
  }

  useEffect(() => {
    let cancelled = false;
    const unlistenLine = showConsole
      ? onAgentLogLine((payload) => {
          if (cancelled || payload.feature !== feature || payload.slot !== agent.id) return;
          // A line arriving means a run is active for this slot even if it was
          // started elsewhere (gate approve, chaining) — flip to the live view,
          // resetting the clock/cost/log exactly once per run.
          if (!liveActiveRef.current) {
            beginLiveRun([]);
          }
          const event = payload.event;
          if (event.kind === "sessionStarted") setSessionModel(event.model);
          if (event.kind === "thinkingProgress") {
            const delta = event.estimatedTokensDelta;
            setThinkingTokens((prev) => prev + delta);
          }
          const line = toLogLine(event);
          if (line) setLiveLines((prev) => [...prev, line]);
        })
      : Promise.resolve(() => undefined);
    const unlistenFinished = onAgentRunFinished((payload) => {
      if (cancelled || payload.feature !== feature || payload.slot !== agent.id) return;
      liveActiveRef.current = false;
      setLiveActive(false);
      setLastSummary(payload.summary);
      setRefreshKey((k) => k + 1);
      // A finished run that produced something: put it on screen instead of
      // making the user hunt for the file it just wrote. `get_node_detail`
      // only reports artifacts already on disk, so this reads what exists.
      if (payload.summary.outcome === "done") {
        commands
          .getNodeDetail(feature, agent.id)
          .then((detail) => {
            // Skip binary assets (`design-resources/*.png`): the viewer
            // reads artifacts as UTF-8, so auto-opening one would greet the
            // user with an encoding error instead of the doc just written.
            const previewable = detail.artifacts.find((a) =>
              isPreviewableArtifact(a.path),
            );
            if (!cancelled && previewable) {
              setModalArtifact(previewable.path);
            }
          })
          .catch(() => {
            // No artifact list — nothing to pop up, the panel still updates.
          });
      }
    });
    return () => {
      cancelled = true;
      unlistenLine.then((f) => f());
      unlistenFinished.then((f) => f());
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [feature, agent.id, showConsole]);

  // AC-E2-20 — re-hydrate the log console from `log.jsonl` on disk on
  // mount, same as `BaStepPanel` (the old `GenericStepPanel` claimed no
  // log existed while the file sat right there on disk).
  useEffect(() => {
    if (!showConsole) return;
    let cancelled = false;
    commands
      .getRunLog(feature, agent.id)
      .then((events) => {
        if (cancelled) return;
        setLiveLines((prev) => {
          if (prev.length > 0) return prev;
          return events
            .map(toLogLine)
            .filter((line): line is LogLine => line !== null);
        });
      })
      .catch(() => {
        // Best-effort — no persisted log yet, or the read failed.
      });
    return () => {
      cancelled = true;
    };
  }, [feature, agent.id, showConsole]);

  useEffect(() => {
    if (!liveActive) return;
    const id = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(id);
  }, [liveActive]);

  const status = nodeState?.status ?? "idle";

  // This component instance is reused across nodes/status changes (see the
  // note above `handleRun`) — without this, a pending Force Done confirm
  // could survive into a different slot's render.
  useEffect(() => {
    if (status !== "waiting-input") setConfirmForceDone(false);
  }, [status]);

  // Retry-limit + persisted-prompt lookup, needed once the slot has failed
  // (or was interrupted — Re-run replays the same persisted prompt).
  const [attempt, setAttempt] = useState<number | null>(null);
  const [retryPrompt, setRetryPrompt] = useState<string | null>(null);
  const [maxRetries, setMaxRetries] = useState(DEFAULT_MAX_RETRIES);
  useEffect(() => {
    if (status !== "failed" && status !== "interrupted") {
      setAttempt(null);
      setRetryPrompt(null);
      setConfirmRetry(false);
      setConfirmSkip(false);
      return;
    }
    let cancelled = false;
    commands
      .getRunSummary(feature, agent.id)
      .then((summary) => {
        if (cancelled) return;
        setAttempt(summary?.attempt ?? 1);
        setRetryPrompt(summary?.prompt ?? null);
      })
      .catch(() => {
        if (!cancelled) setAttempt(1);
      });
    // AC-E6-23 — the retry ceiling comes from Settings, not a constant.
    commands
      .getConfig()
      .then((config) => {
        if (!cancelled) setMaxRetries(config.max_retries);
      })
      .catch(() => {
        // Fallback constant already in state.
      });
    return () => {
      cancelled = true;
    };
  }, [feature, agent.id, status, refreshKey]);

  const isDesignAnalyst = agent.id === "design-analyst";

  // The URL the user gave last time, read back from `.orchestrator/`. The
  // draft it fills is what stage ⑤ ultimately gets, so showing it beats an
  // empty box: the user sees what Frontend/Mobile will be handed, and a
  // re-run does not mean hunting the link down in Figma again. Only fills a
  // draft that is still empty — anything half-typed belongs to the user.
  useEffect(() => {
    if (!isDesignAnalyst) return;
    let cancelled = false;
    commands
      .getDesignRef(feature)
      .then((ref) => {
        if (cancelled || !ref?.url) return;
        const { agentDrafts } = useAppStore.getState();
        if (agentDrafts[agentDraftKey(feature, agent.id)]?.figmaUrl) return;
        setAgentDraft(feature, agent.id, { figmaUrl: ref.url });
      })
      .catch(() => {
        // Nothing stored, or no project open — the empty box is correct.
      });
    return () => {
      cancelled = true;
    };
  }, [feature, agent.id, isDesignAnalyst, setAgentDraft, refreshKey]);

  const blockedReason = projectReady
    ? readinessReason(readiness)
    : "Project chưa init — chạy /init-kit trong Claude Code rồi kiểm tra lại";
  /** Chỉ lỗi repo mới tự hết sau khi người dùng đi làm việc bên ngoài app
   * (clone repo về) — mọi lý do chặn khác đều tự cập nhật qua state event. */
  const canRecheck = readiness?.kind === "repoNotCloned";

  async function handleRun() {
    beginLiveRun([manualLogLine(`— Bắt đầu chạy ${displayName}...`)]);
    setQuestionAutoOpened(false);
    setActionError(null);
    try {
      await commands.runSlot(
        feature,
        agent.id,
        isDesignAnalyst ? figmaUrl.trim() || undefined : undefined,
      );
      clearAgentDraft(feature, agent.id);
    } catch (err) {
      liveActiveRef.current = false;
      setLiveActive(false);
      setActionError(extractErrorMessage(err));
    }
  }

  async function handleKill() {
    try {
      await commands.killRun(feature, agent.id);
    } catch {
      // Best-effort — the run may have already finished on its own.
    }
  }

  async function handleSendAnswer() {
    if (!answer.trim()) return;
    const toSend = answer.trim();
    setAnswer("");
    beginLiveRun([manualLogLine(`— Đã gửi câu trả lời: ${toSend}`)]);
    setActionError(null);
    try {
      await commands.sendClarificationAnswer(feature, agent.id, toSend);
    } catch (err) {
      liveActiveRef.current = false;
      setLiveActive(false);
      setActionError(extractErrorMessage(err));
    }
  }

  async function handleRetry() {
    if (!retryPrompt) return;
    // AC-E6-24 — a slot that already produced an artifact warns about
    // overwriting before rerunning (two-step confirm).
    if (!confirmRetry) {
      const hasArtifacts = await commands
        .getNodeDetail(feature, agent.id)
        .then((d) => d.artifacts.length > 0)
        .catch(() => false);
      if (hasArtifacts) {
        setConfirmRetry(true);
        return;
      }
    }
    setConfirmRetry(false);
    beginLiveRun([]);
    setQuestionAutoOpened(false);
    setActionError(null);
    commands.startRun(feature, agent.id, retryPrompt).catch((err) => {
      liveActiveRef.current = false;
      setLiveActive(false);
      setActionError(extractErrorMessage(err));
    });
  }

  const skipDependents = computeSkipDependents(pipelineDef, agent.id);

  async function handleSkip() {
    // AC-E6-26 — two-step confirm naming who runs short of input.
    if (!confirmSkip) {
      setConfirmSkip(true);
      return;
    }
    setConfirmSkip(false);
    setActionError(null);
    try {
      await commands.skipRun(feature, agent.id);
    } catch (err) {
      setActionError(extractErrorMessage(err));
    }
  }

  // Only backend/frontend/mobile ever get stuck `waiting-input` on a
  // convention mismatch (see `force_done_run`'s doc comment on the Rust
  // side) — every other slot's Done status comes from the artifact it
  // produced actually existing on disk, so Force Done would be a no-op
  // there on the next recompute.
  const isDevRepoSlot = ["backend", "frontend", "mobile"].includes(agent.id);

  async function handleForceDone() {
    if (!confirmForceDone) {
      setConfirmForceDone(true);
      return;
    }
    setConfirmForceDone(false);
    setActionError(null);
    try {
      await commands.forceDoneRun(feature, agent.id);
    } catch (err) {
      setActionError(extractErrorMessage(err));
    }
  }

  // AC-E2-41/42 — re-runs a `done`/`done-incomplete` node so it picks up
  // whatever upstream artifacts changed since it last ran. Deliberately
  // goes through `run_slot` (same as `handleRun`), NOT `start_run`:
  // `start_run` replays a literal saved prompt and is restricted to the
  // `ba` slot on the backend (`"start_run chỉ dành cho BA..."`), while
  // `run_slot` rebuilds the prompt from the CURRENT on-disk state and still
  // runs the readiness checks — exactly what "pick up the latest input"
  // needs, for any slot.
  async function handleReRun() {
    if (!confirmRetry) {
      const hasArtifacts = await commands
        .getNodeDetail(feature, agent.id)
        .then((d) => d.artifacts.length > 0)
        .catch(() => false);
      if (hasArtifacts) {
        setConfirmRetry(true);
        return;
      }
    }
    setConfirmRetry(false);
    await handleRun();
  }

  // AC-E6-05 — continue the interrupted run in its original session. A
  // backend refusal (e.g. no session id survived) lands in actionError
  // with its own suggestion to Re-run (AC-E6-06).
  async function handleResume() {
    beginLiveRun([manualLogLine("— Resume phiên bị gián đoạn...")]);
    setQuestionAutoOpened(false);
    setActionError(null);
    try {
      await commands.resumeRun(feature, agent.id);
    } catch (err) {
      liveActiveRef.current = false;
      setLiveActive(false);
      setActionError(extractErrorMessage(err));
    }
  }

  const elapsedMs = useMemo(() => now - startedAt, [now, startedAt]);
  const estimatedCostUsd = useMemo(
    () => (sessionModel ? estimateThinkingCostUsd(sessionModel, thinkingTokens) : null),
    [sessionModel, thinkingTokens],
  );

  if (liveActive && showConsole) {
    return (
      <LiveLogView
        title={`${displayName} — đang chạy`}
        lines={liveLines}
        elapsedMs={elapsedMs}
        estimatedCostUsd={estimatedCostUsd}
        onKill={handleKill}
      />
    );
  }

  const meta = statusMeta(status);
  const Icon = meta.icon;

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center gap-2">
        <Icon
          className={cn("size-4 shrink-0", meta.colorClass, meta.spin && "animate-spin")}
          aria-hidden="true"
        />
        <div className="flex min-w-0 flex-1 flex-col">
          <span className="truncate text-sm font-medium">{displayName}</span>
          <span className="truncate text-xs text-muted-foreground">
            {meta.label}
            {nodeState?.detail ? ` — ${nodeState.detail}` : ""}
          </span>
        </div>
      </div>

      {actionError && (
        <Alert variant="destructive">
          <AlertTitle>Không thực hiện được</AlertTitle>
          <AlertDescription>{actionError}</AlertDescription>
        </Alert>
      )}

      {/* B22 — nothing runs by itself; this is the only way a pipeline
          agent starts. Disabled with the exact reason when upstream isn't
          ready, so the user never has to guess what is missing. */}
      {status === "idle" && (
        <div className="flex flex-col gap-2 rounded-lg border border-border p-3">
          {isDesignAnalyst && (
            <div className="flex flex-col gap-1">
              <Label htmlFor="figma-url">URL Figma (selection)</Label>
              <Input
                id="figma-url"
                value={figmaUrl}
                placeholder="https://figma.com/design/...?node-id=..."
                onChange={(e) => setAgentDraft(feature, agent.id, { figmaUrl: e.target.value })}
              />
              <p className="text-xs text-muted-foreground">
                Chuột phải vào frame trong Figma → Copy link to selection. Bỏ trống thì agent sẽ
                dừng lại hỏi.
              </p>
            </div>
          )}
          <Button onClick={handleRun} disabled={blockedReason !== null}>
            <Play />
            Run agent
          </Button>
          {blockedReason && <p className="text-xs text-muted-foreground">{blockedReason}</p>}
          {canRecheck && (
            <Button variant="outline" size="sm" onClick={onRecheckReadiness}>
              <RefreshCw />
              Kiểm tra lại
            </Button>
          )}
        </div>
      )}

      {/* `skipped`/`blocked` are recorded for conditions that get fixed
          later — the agent file gets added to the kit, the repo gets
          cloned, the contract gets re-locked. Nothing used to clear them,
          so a node stayed frozen with no button at all and looked like it
          had been removed from the app. Once readiness says the slot may
          run again, offer exactly that; the run's own summary overwrites
          the stale one when it finishes. */}
      {(status === "skipped" || status === "blocked") && (
        <div className="flex flex-col gap-2 rounded-lg border border-border p-3">
          <p className="text-sm text-muted-foreground">
            {nodeState?.detail ??
              (status === "skipped" ? "Slot này đã bị bỏ qua." : "Slot này đang bị chặn.")}
          </p>
          {blockedReason ? (
            <>
              <p className="text-xs text-muted-foreground">{blockedReason}</p>
              {canRecheck && (
                <Button variant="outline" size="sm" onClick={onRecheckReadiness}>
                  <RefreshCw />
                  Kiểm tra lại
                </Button>
              )}
            </>
          ) : (
            <>
              <p className="text-xs text-muted-foreground">
                Điều kiện đã thoả trở lại — chạy được ngay bây giờ.
              </p>
              {isDesignAnalyst && (
                <div className="flex flex-col gap-1">
                  <Label htmlFor="figma-url-rerun">URL Figma (selection)</Label>
                  <Input
                    id="figma-url-rerun"
                    value={figmaUrl}
                    placeholder="https://figma.com/design/...?node-id=..."
                    onChange={(e) => setAgentDraft(feature, agent.id, { figmaUrl: e.target.value })}
                  />
                </div>
              )}
              <Button onClick={handleRun}>
                <Play />
                Chạy lại agent
              </Button>
            </>
          )}
        </div>
      )}

      {status === "waiting-input" && (
        <>
          <WaitingInputPanel
            question={nodeState?.detail}
            agentLabel={displayName}
            value={answer}
            onChange={setAnswer}
            onSend={handleSendAnswer}
            autoOpen={!questionAutoOpened}
            onAutoOpened={() => setQuestionAutoOpened(true)}
          />
          {isDevRepoSlot && (
            <div className="flex flex-col gap-2 rounded-lg border border-border p-3">
              <p className="text-xs text-muted-foreground">
                Việc thực ra đã xong nhưng agent không kết thúc bằng thông báo hoàn thành chuẩn?
                Đánh dấu Done thủ công — bỏ qua kiểm tra tự động.
              </p>
              {confirmForceDone && (
                <p className="text-xs text-warning">
                  Sẽ dừng session hiện tại (nếu còn) và đánh dấu {displayName} là Done. Nhấn lần
                  nữa để xác nhận.
                </p>
              )}
              <Button variant="outline" onClick={handleForceDone}>
                {confirmForceDone ? "Xác nhận Force Done" : "Force Done"}
              </Button>
            </div>
          )}
        </>
      )}

      {status === "failed" && (
        <div className="flex flex-col gap-2 rounded-lg border border-destructive/40 p-3">
          <p className="text-sm text-destructive">
            {nodeState?.detail ?? "Agent kết thúc với lỗi."}
          </p>
          {attempt !== null && !canRetry(attempt, maxRetries) ? (
            <p className="text-xs text-muted-foreground">
              Đã hết số lần thử lại (tối đa {maxRetries} lần thử lại).
            </p>
          ) : retryPrompt ? (
            <>
              {confirmRetry && (
                <p className="text-xs text-warning">
                  Slot này đã có artifact — chạy lại sẽ ghi đè. Nhấn lần nữa để xác nhận.
                </p>
              )}
              <Button onClick={handleRetry}>
                {confirmRetry ? "Xác nhận chạy lại (ghi đè artifact)" : "Thử lại"}
              </Button>
            </>
          ) : (
            <p className="text-xs text-muted-foreground">
              Không tìm thấy input ban đầu để thử lại tự động — spawn lại qua gate/stage
              tương ứng.
            </p>
          )}
          {confirmSkip && (
            <p className="text-xs text-warning">
              {skipDependents.length > 0
                ? `Bỏ qua slot này thì các agent sau sẽ chạy thiếu đầu vào: ${skipDependents.join(", ")}. Nhấn lần nữa để xác nhận.`
                : "Bỏ qua slot này — pipeline sẽ đi tiếp không có output của nó. Nhấn lần nữa để xác nhận."}
            </p>
          )}
          <Button variant="outline" onClick={handleSkip}>
            {confirmSkip ? "Xác nhận bỏ qua" : "Skip"}
          </Button>
        </div>
      )}

      {status === "interrupted" && (
        <div className="flex flex-col gap-2 rounded-lg border border-amber-500/40 p-3">
          {/* AC-E6-04/05 — distinct from failed: the choice here is Resume
              (same session) vs Re-run (from scratch), not Retry. */}
          <p className="text-sm text-warning">
            {nodeState?.detail ?? "Run bị gián đoạn khi app đóng."}
          </p>
          <Button onClick={handleResume}>Resume (chạy tiếp phiên cũ)</Button>
          {retryPrompt ? (
            <>
              {confirmRetry && (
                <p className="text-xs text-warning">
                  Slot này đã có artifact — chạy lại từ đầu sẽ ghi đè. Nhấn lần nữa để xác
                  nhận.
                </p>
              )}
              <Button variant="outline" onClick={handleRetry}>
                {confirmRetry ? "Xác nhận Re-run (ghi đè artifact)" : "Re-run từ đầu"}
              </Button>
            </>
          ) : (
            <p className="text-xs text-muted-foreground">
              Không tìm thấy input ban đầu để Re-run tự động — spawn lại qua gate/stage
              tương ứng.
            </p>
          )}
        </div>
      )}

      {(status === "done" || status === "done-incomplete") && (
        <div className="flex flex-col gap-2 rounded-lg border border-border p-3">
          {/* AC-E2-41/42 — a completed node can be re-run when upstream input
              changed (e.g. `ba-agent` re-ran with a different SPEC). Goes
              through `run_slot` (`handleReRun` → `handleRun`), which rebuilds
              the prompt from the CURRENT on-disk state and re-checks
              readiness — NOT `start_run`, which only ever accepts the `ba`
              slot. Deliberately does NOT check `canRetry(attempt,
              maxRetries)` — that limit is for retrying after failure, not
              for a deliberate re-run of a node that already succeeded. */}
          {isDesignAnalyst && (
            <div className="flex flex-col gap-1">
              <Label htmlFor="figma-url-rerun-done">URL Figma (selection)</Label>
              <Input
                id="figma-url-rerun-done"
                value={figmaUrl}
                placeholder="https://figma.com/design/...?node-id=..."
                onChange={(e) => setAgentDraft(feature, agent.id, { figmaUrl: e.target.value })}
              />
              <p className="text-xs text-muted-foreground">
                Bỏ trống thì agent sẽ dừng lại hỏi.
              </p>
            </div>
          )}
          {confirmRetry && (
            <p className="text-xs text-warning">
              Slot này đã có artifact — chạy lại sẽ ghi đè. Nhấn lần nữa để xác nhận.
            </p>
          )}
          <Button variant="outline" onClick={handleReRun} disabled={blockedReason !== null}>
            <RefreshCw />
            {confirmRetry ? "Xác nhận chạy lại (ghi đè artifact)" : "Re-run"}
          </Button>
          {blockedReason && <p className="text-xs text-muted-foreground">{blockedReason}</p>}
          {canRecheck && (
            <Button variant="outline" size="sm" onClick={onRecheckReadiness}>
              <RefreshCw />
              Kiểm tra lại
            </Button>
          )}
        </div>
      )}

      <Separator />
      <ArtifactSummary
        feature={feature}
        slotId={agent.id}
        refreshKey={refreshKey}
        onOpenArtifact={setModalArtifact}
      />
      <ArtifactModal path={modalArtifact} onClose={() => setModalArtifact(null)} />

      {lastSummary && (
        <p className="text-xs text-muted-foreground">
          Lần chạy gần nhất: ${lastSummary.costUsd.toFixed(4)}
        </p>
      )}

      <Separator />
      {showConsole && liveLines.length > 0 && (
        <TerminalFrame title={`${displayName} — log`}>
          <div className="max-h-80 overflow-y-auto py-1">
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
      )}
    </div>
  );
}
