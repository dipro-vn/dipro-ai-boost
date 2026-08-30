import { describe, expect, it } from "vitest";
import { slotDisplayName, slotSubLabel } from "@/lib/slot-label";
import type { AgentSlot } from "@/lib/tauri-client";

const qcDesign: AgentSlot = {
  id: "qc-design",
  agentName: "qc-agent",
  label: "QC · Test Cases",
  afterSlots: [],
};
const unlabelled: AgentSlot = { id: "ba", agentName: "ba-agent", afterSlots: [] };

describe("slotDisplayName", () => {
  it("prefers the user's nickname over everything else", () => {
    expect(slotDisplayName(qcDesign, "Bộ TC release")).toBe("Bộ TC release");
    expect(slotDisplayName(unlabelled, "BA của tôi")).toBe("BA của tôi");
  });

  it("falls back to the kit label when there is no nickname", () => {
    expect(slotDisplayName(qcDesign)).toBe("QC · Test Cases");
    expect(slotDisplayName(qcDesign, "   ")).toBe("QC · Test Cases");
  });

  it("falls back to the agent name for a pipeline.json written before labels", () => {
    expect(slotDisplayName(unlabelled)).toBe("ba-agent");
  });

  /// Two slots sharing one agent file must still read differently on the
  /// board — the whole reason `label` exists.
  it("tells two slots sharing one agent file apart", () => {
    const qcTesting: AgentSlot = {
      id: "qc-testing",
      agentName: "qc-agent",
      label: "QC · Execution",
      afterSlots: [],
    };
    expect(slotDisplayName(qcDesign)).not.toBe(slotDisplayName(qcTesting));
  });
});

describe("slotSubLabel", () => {
  it("exposes the real agent file behind a label or nickname", () => {
    expect(slotSubLabel(qcDesign)).toBe("qc-agent");
    expect(slotSubLabel(unlabelled, "BA của tôi")).toBe("ba-agent");
  });

  it("is null when the display name already IS the agent name", () => {
    expect(slotSubLabel(unlabelled)).toBeNull();
  });
});
