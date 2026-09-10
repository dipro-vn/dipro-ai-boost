import { create } from "zustand";
import type { ProjectInitStatus } from "@/lib/tauri-client";

/**
 * Single desktop window, no router — a small fixed set of screens is
 * simpler than pulling in a routing dependency at this scope. Import Input
 * and the Log Console are no longer separate screens — they're embedded in
 * the Board's permanent action pane (`ActionPanel`/`BaStepPanel`) instead.
 */

export type Screen = "launcher" | "board" | "viewer" | "settings" | "reports";

/** A not-yet-submitted agent run input, kept per `${feature}:${slot}` so it
 * survives the Board screen unmounting (e.g. navigating to Settings and
 * back) instead of living in the component-local `useState` that used to
 * lose it. Cleared once the run it belongs to actually starts. */
export interface AgentDraft {
  sourceFolder: string;
  context: string;
  figmaUrl: string;
  /** BA only — `TARGET_PLATFORM` (ba-agent.md Bước 2b câu 0). Decides the
   * viewport of Figma Output 3 and the `## Responsive Requirements` table,
   * and the kit forbids the agent guessing it. */
  targetPlatform: string;
}

export const emptyAgentDraft: AgentDraft = {
  sourceFolder: "",
  context: "",
  figmaUrl: "",
  targetPlatform: "",
};

export function agentDraftKey(feature: string, slot: string): string {
  return `${feature}:${slot}`;
}

interface AppState {
  screen: Screen;
  /** Label of the open project, shown in the top bar. `null` on the
   * launcher — it is also the "is a project open" flag for the UI. */
  projectLabel: string | null;
  projectInitStatus: ProjectInitStatus | null;
  projectInitReasons: string[];
  projectAgentsRoot: string | null;
  activeFeature: string | null;
  /** Artifact path to open when navigating to the viewer screen. */
  viewerTarget: string | null;
  /** Whether the Board's folder-tree Explorer sidebar is open. Lives here
   * (not a `useState` in `PipelineBoardScreen`) so it stays open across a
   * navigate-away-and-back — it should only close on an explicit user
   * click, never as a side effect of unmounting the Board. */
  explorerOpen: boolean;
  /** Whether the Board's agent terminal/log console (a bottom sheet,
   * toggled by a floating button) is open. Same reasoning as
   * `explorerOpen` — lives in the store so it survives navigating away and
   * back instead of resetting to closed. */
  consoleOpen: boolean;
  /** Drafts for not-yet-submitted agent run inputs, keyed by
   * `agentDraftKey(feature, slot)`. See `AgentDraft`. */
  agentDrafts: Record<string, AgentDraft>;
  setScreen: (screen: Screen) => void;
  setProjectLabel: (label: string | null) => void;
  setProjectInit: (
    status: ProjectInitStatus | null,
    reasons: string[],
    agentsRoot: string | null,
  ) => void;
  setActiveFeature: (feature: string | null) => void;
  openArtifact: (path: string) => void;
  setExplorerOpen: (open: boolean | ((prev: boolean) => boolean)) => void;
  setConsoleOpen: (open: boolean | ((prev: boolean) => boolean)) => void;
  setAgentDraft: (feature: string, slot: string, patch: Partial<AgentDraft>) => void;
  clearAgentDraft: (feature: string, slot: string) => void;
  /** Drops everything scoped to the open project and returns to the
   * launcher. Every field here belongs to one project, so switching without
   * clearing them would carry a stale feature name (or an artifact path
   * under the old roots) into the next one. Pairs with the backend's
   * `close_project`, which clears its own half. */
  leaveProject: () => void;
}

export const useAppStore = create<AppState>((set) => ({
  screen: "launcher",
  projectLabel: null,
  projectInitStatus: null,
  projectInitReasons: [],
  projectAgentsRoot: null,
  activeFeature: null,
  viewerTarget: null,
  explorerOpen: false,
  consoleOpen: false,
  agentDrafts: {},
  setScreen: (screen) => set({ screen }),
  setProjectLabel: (projectLabel) => set({ projectLabel }),
  setProjectInit: (projectInitStatus, projectInitReasons, projectAgentsRoot) =>
    set({ projectInitStatus, projectInitReasons, projectAgentsRoot }),
  setActiveFeature: (activeFeature) => set({ activeFeature }),
  openArtifact: (path) => set({ viewerTarget: path, screen: "viewer" }),
  setExplorerOpen: (open) =>
    set((state) => ({
      explorerOpen: typeof open === "function" ? open(state.explorerOpen) : open,
    })),
  setConsoleOpen: (open) =>
    set((state) => ({
      consoleOpen: typeof open === "function" ? open(state.consoleOpen) : open,
    })),
  setAgentDraft: (feature, slot, patch) =>
    set((state) => {
      const key = agentDraftKey(feature, slot);
      return {
        agentDrafts: {
          ...state.agentDrafts,
          [key]: { ...emptyAgentDraft, ...state.agentDrafts[key], ...patch },
        },
      };
    }),
  clearAgentDraft: (feature, slot) =>
    set((state) => {
      const key = agentDraftKey(feature, slot);
      if (!(key in state.agentDrafts)) return state;
      const { [key]: _removed, ...rest } = state.agentDrafts;
      return { agentDrafts: rest };
    }),
  leaveProject: () =>
    set({
      screen: "launcher",
      projectLabel: null,
      projectInitStatus: null,
      projectInitReasons: [],
      projectAgentsRoot: null,
      activeFeature: null,
      viewerTarget: null,
      explorerOpen: false,
      consoleOpen: false,
      agentDrafts: {},
    }),
}));
