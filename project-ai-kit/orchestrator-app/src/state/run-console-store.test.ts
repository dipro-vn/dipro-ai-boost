import { beforeEach, describe, expect, it } from "vitest";
import type { RunSummary, StreamEvent } from "@/lib/tauri-client";
import { runConsoleKey, useRunConsoleStore } from "@/state/run-console-store";

const sessionStarted = (sessionId: string, model = "sonnet"): StreamEvent => ({
  kind: "sessionStarted",
  sessionId,
  model,
});

const assistantText = (text: string): StreamEvent => ({
  kind: "assistantText",
  messageId: `${text}-message`,
  text,
});

const summary: RunSummary = {
  outcome: "done",
  sessionId: "session-1",
  costUsd: 0.12,
  startedAt: "2026-08-20T00:00:00Z",
  endedAt: "2026-08-20T00:01:00Z",
  attempt: 1,
};

describe("run console store", () => {
  beforeEach(() => {
    useRunConsoleStore.setState({ consoles: {} });
  });

  it("keeps concurrent node events in separate buffers", () => {
    const store = useRunConsoleStore.getState();
    store.appendEvent("feature-a", "backend", sessionStarted("backend-session"));
    store.appendEvent("feature-a", "frontend", sessionStarted("frontend-session"));
    store.appendEvent("feature-a", "backend", assistantText("backend output"));
    store.appendEvent("feature-a", "frontend", assistantText("frontend output"));

    const state = useRunConsoleStore.getState().consoles;
    expect(state[runConsoleKey("feature-a", "backend")].lines.map((line) => line.text)).toEqual([
      "▶ Bắt đầu (model: sonnet)",
      "backend output",
    ]);
    expect(state[runConsoleKey("feature-a", "frontend")].lines.map((line) => line.text)).toEqual([
      "▶ Bắt đầu (model: sonnet)",
      "frontend output",
    ]);
  });

  it("resets the buffer when the same node starts a new session", () => {
    const store = useRunConsoleStore.getState();
    store.appendEvent("feature-a", "backend", sessionStarted("session-1"));
    store.appendEvent("feature-a", "backend", assistantText("old output"));
    store.appendEvent("feature-a", "backend", sessionStarted("session-2", "opus"));
    store.appendEvent("feature-a", "backend", assistantText("new output"));

    const consoleState = useRunConsoleStore.getState().consoles["feature-a/backend"];
    expect(consoleState.sessionId).toBe("session-2");
    expect(consoleState.sessionModel).toBe("opus");
    expect(consoleState.lines.map((line) => line.text)).toEqual([
      "▶ Bắt đầu (model: opus)",
      "new output",
    ]);
  });

  it("marks only the finished node inactive", () => {
    const store = useRunConsoleStore.getState();
    store.appendEvent("feature-a", "backend", sessionStarted("backend-session"));
    store.appendEvent("feature-a", "frontend", sessionStarted("frontend-session"));
    store.markFinished("feature-a", "backend", summary);

    const state = useRunConsoleStore.getState().consoles;
    expect(state["feature-a/backend"].liveActive).toBe(false);
    expect(state["feature-a/backend"].lastSummary).toEqual(summary);
    expect(state["feature-a/frontend"].liveActive).toBe(true);
  });
});
