import { describe, expect, it } from "vitest";
import { isPipelineComplete } from "@/lib/pipeline-progress";
import type { FeatureState, PipelineDef } from "@/lib/tauri-client";

const pipeline: PipelineDef = {
  stages: [
    { id: "S1_input", label: "Input", agents: [{ id: "ba", agentName: "ba-agent", afterSlots: [] }] },
    { id: "S1b_trigger", label: "Trigger", agents: [] },
    { id: "S2_design", label: "Design", agents: [{ id: "qc-design", agentName: "qc-agent", afterSlots: [] }] },
    { id: "S4_contract_lock", label: "Contract Lock", agents: [] },
  ],
};

function state(
  ba: FeatureState["nodes"][string]["status"],
  qc: FeatureState["nodes"][string]["status"],
  trigger: "not-ready" | "pending-review" | "approved" = "approved",
  contract: "not-ready" | "not-applicable" | "pending-review" | "locked" | "violated" = "not-applicable",
): FeatureState {
  return {
    nodes: {
      ba: { status: ba },
      "qc-design": { status: qc },
    },
    gates: { S1b_trigger: { status: trigger, missingSections: [] } },
    contractLock: {
      status: contract,
      missingColumns: [],
      planMdMissing: false,
      applicableRoles: [],
      candidateFiles: [],
      violatedFiles: [],
      runningOnOldContract: false,
    },
    updatedAt: "2026-08-18T00:00:00Z",
  };
}

describe("isPipelineComplete", () => {
  it("stays incomplete while any node is idle", () => {
    expect(isPipelineComplete(pipeline, state("done", "idle"))).toBe(false);
  });

  it("requires every agent node to be done", () => {
    expect(isPipelineComplete(pipeline, state("done", "done-incomplete"))).toBe(false);
    expect(isPipelineComplete(pipeline, state("done", "skipped"))).toBe(false);
  });

  it("requires applicable gates to pass", () => {
    expect(isPipelineComplete(pipeline, state("done", "done", "pending-review"))).toBe(false);
    expect(isPipelineComplete(pipeline, state("done", "done", "approved", "violated"))).toBe(false);
  });

  it("stops the idle-edge animation when agents and gates are complete", () => {
    expect(isPipelineComplete(pipeline, state("done", "done"))).toBe(true);
    expect(isPipelineComplete(pipeline, state("done", "done", "approved", "locked"))).toBe(true);
  });

  it("returns false before pipeline state is available", () => {
    expect(isPipelineComplete(pipeline, null)).toBe(false);
  });
});
