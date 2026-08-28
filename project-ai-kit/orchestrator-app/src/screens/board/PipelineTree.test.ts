import { describe, expect, it } from "vitest";
import { edgeState, type Segment } from "./PipelineTree";
import type { ContractLockState, FeatureState, StageDef } from "@/lib/tauri-client";

const stages: StageDef[] = [
  {
    id: "S3_planning",
    label: "③ Planning",
    agents: [{ id: "techlead-tasks", agentName: "techlead-tasks-agent", afterSlots: [] }],
  },
  {
    id: "S4_contract_lock",
    label: "④ Contract Lock",
    agents: [],
    dependsOn: "S3_planning",
  },
  {
    id: "S5_build",
    label: "⑤ Build",
    agents: [
      { id: "backend", agentName: "backend-agent", afterSlots: [] },
      { id: "frontend", agentName: "frontend-agent", afterSlots: ["backend"] },
      { id: "mobile", agentName: "mobile-agent", afterSlots: ["backend"] },
    ],
    dependsOn: "S4_contract_lock",
  },
];

const outSegment: Segment = {
  x1: 0,
  y1: 0,
  x2: 0,
  y2: 0,
  kind: "out",
  fromStageId: "S4_contract_lock",
};

function contractLock(status: ContractLockState["status"]): ContractLockState {
  return {
    status,
    checkedDesignMdPaths: [],
    missingColumns: [],
    manuallySkipped: false,
    applicableRoles: [],
    candidateFiles: [],
    violatedFiles: [],
    runningOnOldContract: false,
  };
}

function state(
  planningStatus: FeatureState["nodes"][string]["status"],
  contractLockStatus: ContractLockState["status"],
): FeatureState {
  return {
    nodes: { "techlead-tasks": { status: planningStatus } },
    gates: {},
    contractLock: contractLock(contractLockStatus),
    updatedAt: "2026-08-27T00:00:00Z",
  };
}

describe("edgeState — Contract Lock gate edges", () => {
  it("turns green once the gate is locked, regardless of Planning's status", () => {
    expect(edgeState(outSegment, stages, state("idle", "locked"))).toBe("done");
  });

  it("stays idle while a skipped gate's predecessor stage hasn't started", () => {
    expect(edgeState(outSegment, stages, state("idle", "not-applicable"))).toBe("idle");
  });

  it("flows while a skipped gate's predecessor stage is still running", () => {
    expect(edgeState(outSegment, stages, state("running", "not-applicable"))).toBe("flowing");
  });

  it("turns green once a skipped gate's predecessor stage is done — the gate is transparent, not a blocker", () => {
    expect(edgeState(outSegment, stages, state("done", "not-applicable"))).toBe("done");
  });

  it("stays idle for a violated or not-yet-ready gate even if Planning is done", () => {
    expect(edgeState(outSegment, stages, state("done", "violated"))).toBe("idle");
    expect(edgeState(outSegment, stages, state("done", "not-ready"))).toBe("idle");
  });
});
