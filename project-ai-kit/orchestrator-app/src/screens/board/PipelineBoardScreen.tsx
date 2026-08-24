import { useCallback, useEffect, useRef, useState } from "react";
import { Activity, CircleCheck, FolderTree, Upload } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import {
  commands,
  isAppCommandError,
  type FeatureState,
  type OrphanInfo,
  type ProjectConfig,
  type PipelineDef,
  type SlotReadiness,
} from "@/lib/tauri-client";
import {
  onAgentLogLine,
  onAgentRunFinished,
  onPipelineStateChanged,
  onPipelineWatchError,
} from "@/lib/events";
import { useAppStore } from "@/state/app-store";
import { useRunConsoleStore } from "@/state/run-console-store";
import { WorkflowSidebar } from "@/screens/board/WorkflowSidebar";
import { DeleteFeatureDialog } from "@/screens/board/DeleteFeatureDialog";
import { FolderExplorerSidebar } from "@/screens/board/FolderExplorerSidebar";
import { PipelineTree, type TreeSelection } from "@/screens/board/PipelineTree";
import { ActionPanel } from "@/screens/board/ActionPanel";
import { AgentConsoleDock } from "@/screens/board/AgentConsoleDock";

function extractErrorMessage(err: unknown): string {
  if (isAppCommandError(err)) return err.message;
  if (err instanceof Error) return err.message;
  return String(err);
}

export function PipelineBoardScreen() {
  const activeFeature = useAppStore((s) => s.activeFeature);
  const projectLabel = useAppStore((s) => s.projectLabel);
  const setActiveFeature = useAppStore((s) => s.setActiveFeature);
  const setScreen = useAppStore((s) => s.setScreen);
  const [backlogPushable, setBacklogPushable] = useState(false);
  /** Feature awaiting delete confirmation — `null` means the dialog is closed. */
  const [pendingDelete, setPendingDelete] = useState<string | null>(null);
  /** Toggled by the floating bottom-left button — resets to closed on every
   * remount (leaving the Board and coming back), same as every other
   * screen's local UI state in this app. */
  const [explorerOpen, setExplorerOpen] = useState(false);
  /** B22 — which slots may be run right now, keyed by slot id. */
  const [readiness, setReadiness] = useState<Record<string, SlotReadiness>>({});

  const [pipelineDef, setPipelineDef] = useState<PipelineDef | null>(null);
  const [projectConfig, setProjectConfig] = useState<ProjectConfig | null>(null);
  const [features, setFeatures] = useState<string[]>([]);
  const [featureState, setFeatureState] = useState<FeatureState | null>(null);
  const [loading, setLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [watchWarning, setWatchWarning] = useState<string | null>(null);
  const [selection, setSelection] = useState<TreeSelection | null>(null);

  /** B22 — readiness is derived from the same state, so it has to be
   * refetched whenever that state moves: finishing a run is exactly what
   * unlocks the next node's Run button. Hoisted out of the watch effect so
   * a panel can also ask for a re-check on demand — `get_slot_readiness`
   * re-reads the Ecosystem from disk, which is how a repo cloned while the
   * app is open stops blocking its agent without reopening the project. */
  const refreshReadiness = useCallback((feature: string) => {
    commands
      .getSlotReadiness(feature)
      .then((next) => {
        if (requestFeatureRef.current === feature) setReadiness(next);
      })
      .catch(() => {
        // Leaving the previous map in place only risks a stale disabled
        // button; `run_slot` re-checks server-side either way.
      });
  }, []);

  // Guards against a stale `getPipelineState` response overwriting newer
  // state if the user switches feature again before the first call returns.
  const requestFeatureRef = useRef<string | null>(null);

  // AC-E6-10 — agent processes a previous app instance left alive. Keyed
  // `feature/slot`; `attached` rows stay listed (the marker survives an
  // attach, so a refetch would resurface them) but flip to a "watching"
  // label instead of buttons.
  const [orphans, setOrphans] = useState<OrphanInfo[]>([]);
  const [confirmKillKey, setConfirmKillKey] = useState<string | null>(null);
  const [attachedKeys, setAttachedKeys] = useState<Set<string>>(new Set());

  const refreshOrphans = useCallback(() => {
    commands
      .listOrphans()
      .then(setOrphans)
      .catch(() => {
        // Best-effort — no project open yet, or scan failed; the Board
        // works fine without the banner.
      });
  }, []);

  useEffect(() => {
    refreshOrphans();
  }, [refreshOrphans]);

  const appendConsoleEvent = useRunConsoleStore((state) => state.appendEvent);
  const markConsoleFinished = useRunConsoleStore((state) => state.markFinished);
  const resetRunConsoles = useRunConsoleStore((state) => state.reset);

  useEffect(() => {
    resetRunConsoles();
  }, [projectLabel, resetRunConsoles]);

  // One listener at Board level keeps every node's console alive while the
  // user changes selection. The payload's feature/slot pair is the routing
  // key, so events from concurrent agents never share a line buffer.
  useEffect(() => {
    const unlistenLine = onAgentLogLine((payload) => {
      appendConsoleEvent(payload.feature, payload.slot, payload.event);
    });
    const unlistenFinished = onAgentRunFinished((payload) => {
      markConsoleFinished(payload.feature, payload.slot, payload.summary);
    });

    return () => {
      void unlistenLine.then((unlisten) => unlisten());
      void unlistenFinished.then((unlisten) => unlisten());
    };
  }, [appendConsoleEvent, markConsoleFinished]);

  // The feature list is read once on mount, but features also appear from
  // outside the app (`/create-spec` in Claude Code creates the directory).
  // Refetching on window focus keeps the sidebar honest without a watcher
  // on the whole `features/` tree — the app's own watcher is per-feature.
  useEffect(() => {
    function refetchFeatures() {
      commands
        .listFeatures()
        .then(setFeatures)
        .catch(() => {
          // Project closed or unreadable — the existing list stays.
        });
    }
    window.addEventListener("focus", refetchFeatures);
    return () => window.removeEventListener("focus", refetchFeatures);
  }, []);

  // AC-E5-01 — a feature with no task files has nothing to push.
  useEffect(() => {
    if (!activeFeature) {
      setBacklogPushable(false);
      return;
    }
    let cancelled = false;
    commands
      .getBacklogPushView(activeFeature)
      .then((view) => {
        if (!cancelled) setBacklogPushable(view.tasks.length > 0);
      })
      .catch(() => {
        if (!cancelled) setBacklogPushable(false);
      });
    return () => {
      cancelled = true;
    };
  }, [activeFeature]);

  async function handleResolveOrphan(orphan: OrphanInfo, action: "attach" | "kill") {
    const orphanKey = `${orphan.feature}/${orphan.slot}`;
    if (action === "kill" && confirmKillKey !== orphanKey) {
      setConfirmKillKey(orphanKey);
      return;
    }
    setConfirmKillKey(null);
    try {
      await commands.resolveOrphan(orphan.feature, orphan.slot, action);
      if (action === "attach") {
        setAttachedKeys((prev) => new Set(prev).add(orphanKey));
      } else {
        setOrphans((prev) => prev.filter((o) => `${o.feature}/${o.slot}` !== orphanKey));
      }
    } catch (err) {
      setWatchWarning(extractErrorMessage(err));
    }
  }

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      setErrorMessage(null);
      try {
        const [def, featureIds, config] = await Promise.all([
          commands.getPipelineDefinition(),
          commands.listFeatures(),
          commands.getConfig(),
        ]);
        if (cancelled) return;
        setPipelineDef(def);
        setProjectConfig(config);
        setFeatures(featureIds);
        if (featureIds.length > 0) {
          const currentlyActive = useAppStore.getState().activeFeature;
          setActiveFeature(
            currentlyActive && featureIds.includes(currentlyActive)
              ? currentlyActive
              : featureIds[0],
          );
        } else {
          setActiveFeature(null);
        }
      } catch (err) {
        if (!cancelled) setErrorMessage(extractErrorMessage(err));
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    void load();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!activeFeature) {
      setFeatureState(null);
      return;
    }

    requestFeatureRef.current = activeFeature;
    let cancelled = false;

    commands
      .getPipelineState(activeFeature)
      .then((result) => {
        if (!cancelled && requestFeatureRef.current === activeFeature) {
          setFeatureState(result.state);
          setWatchWarning(result.warnings.length > 0 ? result.warnings.join(" ") : null);
        }
      })
      .catch((err) => {
        if (!cancelled) setErrorMessage(extractErrorMessage(err));
      });

    void commands.startWatching(activeFeature).catch((err) => {
      if (!cancelled) setErrorMessage(extractErrorMessage(err));
    });

    refreshReadiness(activeFeature);

    const unlistenState = onPipelineStateChanged(({ feature, state, warnings }) => {
      if (feature === requestFeatureRef.current) {
        setFeatureState(state);
        setWatchWarning(warnings.length > 0 ? warnings.join(" ") : null);
        refreshReadiness(feature);
      }
    });
    const unlistenError = onPipelineWatchError(({ message }) => {
      setWatchWarning(message);
    });

    return () => {
      cancelled = true;
      void commands.stopWatching();
      void unlistenState.then((f) => f());
      void unlistenError.then((f) => f());
    };
  }, [activeFeature, refreshReadiness]);

  const handleSelectFeature = useCallback(
    (feature: string) => {
      setActiveFeature(feature);
      setSelection(null);
    },
    [setActiveFeature],
  );

  /** The deleted feature may have been the active one — fall back to
   * whatever is left rather than leaving the board pointed at a directory
   * that no longer exists. */
  const handleFeatureDeleted = useCallback(
    (remaining: string[]) => {
      setFeatures(remaining);
      const stillOpen = useAppStore.getState().activeFeature;
      if (!stillOpen || !remaining.includes(stillOpen)) {
        setActiveFeature(remaining[0] ?? null);
        setSelection(null);
      }
    },
    [setActiveFeature],
  );

  /** AC-E2-24 — creating a feature is just creating its directory; every
   * node then infers as `idle`. Selecting the first stage's first agent
   * right away puts the import form (the actual first step) on screen
   * instead of leaving the user on an empty board wondering what's next. */
  const handleCreateFeature = useCallback(
    async (name: string) => {
      const updated = await commands.createFeature(name);
      setFeatures(updated);
      setActiveFeature(name);
      const firstStage = pipelineDef?.stages.find((stage) => stage.agents.length > 0);
      setSelection(
        firstStage ? { stage: firstStage, agent: firstStage.agents[0] } : null,
      );
    },
    [pipelineDef, setActiveFeature],
  );

  /** Nicknames are presentation metadata only. Update the mounted Board
   * optimistically so the node changes immediately, then persist through the
   * existing project config command. Runtime identity remains the slot id and
   * real agent name from PipelineDef. */
  const handleNicknameChange = useCallback(
    async (slotId: string, nickname: string | null) => {
      if (!projectConfig) {
        throw new Error("Cấu hình project chưa tải xong, vui lòng thử lại.");
      }

      const previous = projectConfig;
      const nextNicknames = { ...(previous.node_nicknames ?? {}) };
      const trimmed = nickname?.trim() ?? "";
      if (trimmed) {
        nextNicknames[slotId] = trimmed;
      } else {
        delete nextNicknames[slotId];
      }

      const next = { ...previous, node_nicknames: nextNicknames };
      setProjectConfig(next);
      try {
        await commands.setConfig(next);
      } catch (err) {
        setProjectConfig(previous);
        throw err;
      }
    },
    [projectConfig],
  );

  if (loading) {
    return (
      <div className="flex h-full">
        <div className="flex w-56 shrink-0 flex-col gap-2 border-r border-border p-3">
          <div className="skeleton h-4 w-20" />
          <div className="skeleton h-8 w-full" />
          <div className="skeleton h-8 w-full" />
        </div>
        <div className="flex flex-1 flex-col items-center justify-center gap-4 p-6">
          <div className="skeleton h-16 w-40 rounded-xl" />
          <div className="skeleton h-4 w-56" />
          <div className="skeleton h-4 w-40" />
        </div>
      </div>
    );
  }

  if (errorMessage) {
    return (
      <div className="p-6">
        <Alert variant="destructive">
          <AlertTitle>Có lỗi xảy ra</AlertTitle>
          <AlertDescription>{errorMessage}</AlertDescription>
        </Alert>
      </div>
    );
  }

  // The sidebar owns feature creation, so it has to render even with no
  // feature selected (or none existing at all) — only the board content to
  // its right depends on there being an active feature.
  const sidebar = (
    <>
      {explorerOpen && <FolderExplorerSidebar onClose={() => setExplorerOpen(false)} />}
      <Button
        variant="secondary"
        size="icon"
        className="fixed bottom-4 left-4 z-40 rounded-full shadow-md"
        onClick={() => setExplorerOpen((open) => !open)}
        aria-label={explorerOpen ? "Đóng Explorer" : "Mở Explorer"}
        title="Explorer"
      >
        <FolderTree />
      </Button>
      <WorkflowSidebar
        features={features}
        activeFeature={activeFeature}
        onSelect={handleSelectFeature}
        onCreate={handleCreateFeature}
        onRequestDelete={setPendingDelete}
      />
      <DeleteFeatureDialog
        feature={pendingDelete}
        onClose={() => setPendingDelete(null)}
        onDeleted={handleFeatureDeleted}
      />
    </>
  );

  if (!pipelineDef || !activeFeature) {
    return (
      <div className="flex h-full">
        {sidebar}
        <div className="flex flex-1 flex-col items-center justify-center gap-3 p-6 text-center">
          <FolderTree className="size-10 text-muted-foreground/40" aria-hidden="true" />
          {features.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              Chưa có feature nào trong DOCS_ROOT/features/ — bấm + ở cột Workflow để tạo feature đầu tiên.
            </p>
          ) : (
            <p className="text-sm text-muted-foreground">
              Chọn một feature ở cột Workflow để xem pipeline.
            </p>
          )}
        </div>
      </div>
    );
  }

  const agentIds = pipelineDef.stages.flatMap((stage) => stage.agents.map((agent) => agent.id));
  const completedAgents = agentIds.filter((id) => {
    const status = featureState?.nodes[id]?.status;
    return status === "done" || status === "skipped";
  }).length;
  const runningAgents = agentIds.filter((id) => featureState?.nodes[id]?.status === "running").length;

  return (
    <div className="flex h-full">
      {sidebar}
      <div className="flex min-w-0 flex-1 flex-col">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border bg-muted/20 px-4 py-3">
          <div className="flex min-w-0 items-center gap-2.5">
            <span className="flex size-8 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <Activity className="size-4" aria-hidden="true" />
            </span>
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold">{activeFeature}</p>
              <p className="flex items-center gap-1.5 text-xs text-muted-foreground">
                <CircleCheck className="size-3.5 text-success" aria-hidden="true" />
                {completedAgents}/{agentIds.length} agent hoàn thành
                {runningAgents > 0 && <span className="text-info">· {runningAgents} đang chạy</span>}
              </p>
            </div>
          </div>
          {/* AC-E5-01 — disabled with an explanation until the feature has
              task files to push. Credentials are NOT a precondition here: the
              push runs through the project's Backlog MCP server, not the
              app's own API key (see B21 in ASSUMPTIONS-GAPS.md). */}
          <Button
            variant="outline"
            size="sm"
            disabled={!backlogPushable}
            title={
              backlogPushable
                ? "Đẩy task lên Backlog qua pm-agent"
                : "Feature này chưa có file tasks/task-*.md để đẩy"
            }
            onClick={() => setScreen("backlog")}
          >
            <Upload />
            Push to Backlog
          </Button>
        </div>
    
        {watchWarning && (
          <div className="p-4 pb-0">
            <Alert>
              <AlertTitle>Cảnh báo</AlertTitle>
              <AlertDescription>{watchWarning}</AlertDescription>
            </Alert>
          </div>
        )}
    
        {orphans.length > 0 && (
          <div className="p-4 pb-0">
            <Alert>
              <AlertTitle>Process agent từ phiên trước vẫn đang chạy</AlertTitle>
              <AlertDescription>
                <div className="flex flex-col gap-2">
                  {orphans.map((orphan) => {
                    const orphanKey = `${orphan.feature}/${orphan.slot}`;
                    const attached = attachedKeys.has(orphanKey);
                    return (
                      <div key={orphanKey} className="flex items-center gap-2">
                        <span className="text-sm">
                          {orphan.feature} / {orphan.slot} (PID {orphan.pid})
                        </span>
                        {attached ? (
                          <span className="text-xs text-muted-foreground">
                            Đang theo dõi — trạng thái sẽ tự cập nhật khi process kết thúc.
                          </span>
                        ) : (
                          <>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleResolveOrphan(orphan, "attach")}
                            >
                              Gắn lại (theo dõi)
                            </Button>
                            <Button
                              variant="destructive"
                              size="sm"
                              onClick={() => handleResolveOrphan(orphan, "kill")}
                            >
                              {confirmKillKey === orphanKey ? "Xác nhận kill" : "Kill"}
                            </Button>
                          </>
                        )}
                      </div>
                    );
                  })}
                </div>
              </AlertDescription>
            </Alert>
          </div>
        )}
    
        <div className="flex flex-1 flex-col overflow-hidden lg:flex-row">
          <div className="min-h-0 min-w-0 flex-1 overflow-auto p-4 lg:p-6">
            <PipelineTree
              pipelineDef={pipelineDef}
              featureState={featureState}
              selection={selection}
              onSelectNode={setSelection}
              nodeNicknames={projectConfig?.node_nicknames ?? {}}
              onNicknameChange={handleNicknameChange}
            />
          </div>
          <div className="flex h-[70vh] max-h-[70vh] w-full shrink-0 min-h-0 flex-col overflow-hidden border-t border-border lg:h-auto lg:max-h-none lg:w-1/3 lg:min-w-80 lg:border-l lg:border-t-0">
            <div className="min-h-0 flex-[0_0_42%] overflow-hidden border-b border-border">
              <ActionPanel
                feature={activeFeature}
                selection={selection}
                featureState={featureState}
                pipelineDef={pipelineDef}
                nodeNicknames={projectConfig?.node_nicknames ?? {}}
                readiness={readiness}
                onRecheckReadiness={() => activeFeature && refreshReadiness(activeFeature)}
              />
            </div>
            <div className="min-h-0 flex-1 overflow-hidden">
              <AgentConsoleDock
                feature={activeFeature}
                pipelineDef={pipelineDef}
                featureState={featureState}
                nodeNicknames={projectConfig?.node_nicknames ?? {}}
                onSelectNode={setSelection}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
