import { describe, expect, it } from "vitest";
import { STATUS_META } from "@/lib/status-meta";
import type { NodeStatus } from "@/lib/tauri-client";

const ALL_STATUSES: NodeStatus[] = [
  "idle",
  "running",
  "waiting-input",
  "done",
  "done-incomplete",
  "failed",
  "blocked",
  "skipped",
];

describe("STATUS_META", () => {
  it("has an entry for every NodeStatus value", () => {
    // The failure mode this guards against: MVP2 adds a reachable status
    // (e.g. `running` once the agent runner exists) and someone forgets to
    // give it an icon/color here — the Board would then render `undefined`.
    for (const status of ALL_STATUSES) {
      expect(STATUS_META[status]).toBeDefined();
    }
  });

  it("every entry has a non-empty label, an icon, and a color class", () => {
    for (const status of ALL_STATUSES) {
      const meta = STATUS_META[status];
      expect(meta.label.length).toBeGreaterThan(0);
      expect(meta.icon).toBeDefined();
      expect(meta.colorClass.length).toBeGreaterThan(0);
    }
  });

  it("exactly idle, done, and done-incomplete are marked reachable in MVP1", () => {
    const reachable = ALL_STATUSES.filter(
      (status) => STATUS_META[status].reachableInMvp1,
    );
    expect(reachable.sort()).toEqual(["done", "done-incomplete", "idle"]);
  });
});
