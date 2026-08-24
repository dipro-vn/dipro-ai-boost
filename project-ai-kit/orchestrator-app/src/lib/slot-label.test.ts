import { describe, expect, it } from "vitest";
import { slotDisplayName, slotSubLabel } from "@/lib/slot-label";
import type { AgentSlot } from "@/lib/tauri-client";

const qcTesting: AgentSlot = {
  id: "qc-testing",
  agentName: "qc-agent",
  label: "QC · Execution",
  afterSlots: [],
};
const unlabelled: AgentSlot = { id: "ba", agentName: "ba-agent", afterSlots: [] };

describe("slotDisplayName", () => {
  it("prefers the user's nickname over everything else", () => {
    expect(slotDisplayName(qcTesting, "Checklist release")).toBe("Checklist release");
    expect(slotDisplayName(unlabelled, "BA của tôi")).toBe("BA của tôi");
  });

  it("falls back to the kit label when there is no nickname", () => {
    expect(slotDisplayName(qcTesting)).toBe("QC · Execution");
    expect(slotDisplayName(qcTesting, "   ")).toBe("QC · Execution");
  });

  it("falls back to the agent name for a pipeline.json written before labels", () => {
    expect(slotDisplayName(unlabelled)).toBe("ba-agent");
  });

  it("tells the two qc-agent slots apart", () => {
    const qcDesign: AgentSlot = {
      id: "qc-design",
      agentName: "qc-agent",
      label: "QC · Test Cases",
      afterSlots: [],
    };
    expect(slotDisplayName(qcDesign)).not.toBe(slotDisplayName(qcTesting));
  });
});

describe("slotSubLabel", () => {
  it("exposes the real agent file behind a label or nickname", () => {
    expect(slotSubLabel(qcTesting)).toBe("qc-agent");
    expect(slotSubLabel(unlabelled, "BA của tôi")).toBe("ba-agent");
  });

  it("is null when the display name already IS the agent name", () => {
    expect(slotSubLabel(unlabelled)).toBeNull();
  });
});
