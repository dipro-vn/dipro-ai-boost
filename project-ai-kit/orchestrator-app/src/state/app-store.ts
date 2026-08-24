import { create } from "zustand";

/**
 * Single desktop window, no router — a small fixed set of screens is
 * simpler than pulling in a routing dependency at this scope. Import Input
 * and the Log Console are no longer separate screens — they're embedded in
 * the Board's permanent action pane (`ActionPanel`/`BaStepPanel`) instead.
 */
export type Screen = "launcher" | "board" | "viewer" | "settings" | "reports" | "backlog";

interface AppState {
  screen: Screen;
  /** Label of the open project, shown in the top bar. `null` on the
   * launcher — it is also the "is a project open" flag for the UI. */
  projectLabel: string | null;
  activeFeature: string | null;
  /** Artifact path to open when navigating to the viewer screen. */
  viewerTarget: string | null;
  setScreen: (screen: Screen) => void;
  setProjectLabel: (label: string | null) => void;
  setActiveFeature: (feature: string | null) => void;
  openArtifact: (path: string) => void;
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
  activeFeature: null,
  viewerTarget: null,
  setScreen: (screen) => set({ screen }),
  setProjectLabel: (projectLabel) => set({ projectLabel }),
  setActiveFeature: (activeFeature) => set({ activeFeature }),
  openArtifact: (path) => set({ viewerTarget: path, screen: "viewer" }),
  leaveProject: () =>
    set({
      screen: "launcher",
      projectLabel: null,
      activeFeature: null,
      viewerTarget: null,
    }),
}));
