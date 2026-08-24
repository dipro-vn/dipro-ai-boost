import { listen, type UnlistenFn } from "@tauri-apps/api/event";
import type { FeatureState, RunSummary, StreamEvent } from "@/lib/tauri-client";

/** Mirrors `fswatch::watcher::EVENT_STATE_CHANGED` / `EVENT_WATCH_ERROR`. */
const EVENT_STATE_CHANGED = "pipeline://state-changed";
const EVENT_WATCH_ERROR = "pipeline://watch-error";

/** Mirrors `agentrun::runner::EVENT_LOG_LINE` /
 * `commands::agentrun::EVENT_RUN_FINISHED`. */
const EVENT_LOG_LINE = "agentrun://log-line";
const EVENT_RUN_FINISHED = "agentrun://run-finished";

export interface StateChangedPayload {
  feature: string;
  state: FeatureState;
  /** AC-E3-06 / AC-E6-08 — non-fatal warnings (deleted artifact, corrupted
   * state.json backed up, ...). Empty in the common case. */
  warnings: string[];
}

export interface WatchErrorPayload {
  path: string;
  message: string;
}

export interface LogLinePayload {
  feature: string;
  slot: string;
  event: StreamEvent;
}

export interface RunFinishedPayload {
  feature: string;
  slot: string;
  summary: RunSummary;
}

export function onPipelineStateChanged(
  handler: (payload: StateChangedPayload) => void,
): Promise<UnlistenFn> {
  return listen<StateChangedPayload>(EVENT_STATE_CHANGED, (event) =>
    handler(event.payload),
  );
}

export function onPipelineWatchError(
  handler: (payload: WatchErrorPayload) => void,
): Promise<UnlistenFn> {
  return listen<WatchErrorPayload>(EVENT_WATCH_ERROR, (event) =>
    handler(event.payload),
  );
}

export function onAgentLogLine(
  handler: (payload: LogLinePayload) => void,
): Promise<UnlistenFn> {
  return listen<LogLinePayload>(EVENT_LOG_LINE, (event) =>
    handler(event.payload),
  );
}

export function onAgentRunFinished(
  handler: (payload: RunFinishedPayload) => void,
): Promise<UnlistenFn> {
  return listen<RunFinishedPayload>(EVENT_RUN_FINISHED, (event) =>
    handler(event.payload),
  );
}
