import { create } from "zustand";
import { commands, type RunSummary, type StreamEvent } from "@/lib/tauri-client";
import { toLogLine, type LogLine } from "@/screens/board/agent-run-shared";

const MAX_LIVE_LINES = 10_000;

export function runConsoleKey(feature: string, slot: string): string {
  return `${feature}/${slot}`;
}

export interface AgentConsoleState {
  feature: string;
  slot: string;
  lines: LogLine[];
  liveActive: boolean;
  hydrated: boolean;
  hydrating: boolean;
  startedAt: number;
  sessionId: string | null;
  sessionModel: string | null;
  thinkingTokens: number;
  lastSummary: RunSummary | null;
}

interface RunConsoleStore {
  consoles: Record<string, AgentConsoleState>;
  reset: () => void;
  ensureConsole: (feature: string, slot: string) => void;
  appendEvent: (feature: string, slot: string, event: StreamEvent) => void;
  markFinished: (feature: string, slot: string, summary: RunSummary) => void;
  hydrate: (feature: string, slot: string) => Promise<void>;
  clearFeature: (feature: string) => void;
  /** Resets one slot's console to blank and marks it `hydrated` so the next
   * `hydrate()` call (the dock re-mounting, a re-render) does not
   * re-populate it from the still-on-disk `log.jsonl` of the run being
   * abandoned — used by `BaStepPanel`'s Reset. */
  clearConsole: (feature: string, slot: string) => void;
}

export function createAgentConsoleState(feature: string, slot: string): AgentConsoleState {
  return {
    feature,
    slot,
    lines: [],
    liveActive: false,
    hydrated: false,
    hydrating: false,
    startedAt: Date.now(),
    sessionId: null,
    sessionModel: null,
    thinkingTokens: 0,
    lastSummary: null,
  };
}

function appendLine(lines: LogLine[], line: LogLine | null): LogLine[] {
  if (!line) return lines;
  const next = [...lines, line];
  return next.length > MAX_LIVE_LINES ? next.slice(-MAX_LIVE_LINES) : next;
}

export const useRunConsoleStore = create<RunConsoleStore>((set, get) => ({
  consoles: {},

  reset: () => set({ consoles: {} }),

  ensureConsole: (feature, slot) =>
    set((state) => {
      const key = runConsoleKey(feature, slot);
      if (state.consoles[key]) return state;
      return { consoles: { ...state.consoles, [key]: createAgentConsoleState(feature, slot) } };
    }),

  appendEvent: (feature, slot, event) =>
    set((state) => {
      const key = runConsoleKey(feature, slot);
      const current = state.consoles[key] ?? createAgentConsoleState(feature, slot);
      const isNewSession =
        event.kind === "sessionStarted" && current.sessionId !== event.sessionId;
      const base = isNewSession
        ? {
            ...createAgentConsoleState(feature, slot),
            hydrated: true,
            liveActive: true,
            sessionId: event.sessionId,
            sessionModel: event.model,
          }
        : {
            ...current,
            liveActive: true,
            hydrated: true,
          };

      const next: AgentConsoleState = {
        ...base,
        lines: appendLine(isNewSession ? [] : base.lines, toLogLine(event)),
        sessionModel: event.kind === "sessionStarted" ? event.model : base.sessionModel,
        sessionId: event.kind === "sessionStarted" ? event.sessionId : base.sessionId,
        thinkingTokens:
          event.kind === "thinkingProgress"
            ? base.thinkingTokens + event.estimatedTokensDelta
            : base.thinkingTokens,
      };

      return { consoles: { ...state.consoles, [key]: next } };
    }),

  markFinished: (feature, slot, summary) =>
    set((state) => {
      const key = runConsoleKey(feature, slot);
      const current = state.consoles[key] ?? createAgentConsoleState(feature, slot);
      return {
        consoles: {
          ...state.consoles,
          [key]: { ...current, liveActive: false, lastSummary: summary, hydrated: true },
        },
      };
    }),

  hydrate: async (feature, slot) => {
    const key = runConsoleKey(feature, slot);
    const current = get().consoles[key];
    if (current?.hydrated || current?.hydrating) return;

    set((state) => ({
      consoles: {
        ...state.consoles,
        [key]: { ...(state.consoles[key] ?? createAgentConsoleState(feature, slot)), hydrating: true },
      },
    }));

    try {
      const events = await commands.getRunLog(feature, slot);
      set((state) => {
        const latest = state.consoles[key] ?? createAgentConsoleState(feature, slot);
        if (latest.liveActive || latest.lines.length > 0) {
          return {
            consoles: {
              ...state.consoles,
              [key]: { ...latest, hydrated: true, hydrating: false },
            },
          };
        }
        return {
          consoles: {
            ...state.consoles,
            [key]: {
              ...latest,
              lines: events.map(toLogLine).filter((line): line is LogLine => line !== null),
              hydrated: true,
              hydrating: false,
            },
          },
        };
      });
    } catch {
      set((state) => ({
        consoles: {
          ...state.consoles,
          [key]: {
            ...(state.consoles[key] ?? createAgentConsoleState(feature, slot)),
            hydrated: true,
            hydrating: false,
          },
        },
      }));
    }
  },

  clearFeature: (feature) =>
    set((state) => ({
      consoles: Object.fromEntries(
        Object.entries(state.consoles).filter(([, console]) => console.feature !== feature),
      ),
    })),

  clearConsole: (feature, slot) =>
    set((state) => {
      const key = runConsoleKey(feature, slot);
      return {
        consoles: {
          ...state.consoles,
          [key]: { ...createAgentConsoleState(feature, slot), hydrated: true },
        },
      };
    }),
}));
