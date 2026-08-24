import { describe, expect, it } from "vitest";
import { estimateThinkingCostUsd } from "@/lib/pricing";

describe("estimateThinkingCostUsd", () => {
  it("matches known pricing tiers by substring, case-insensitively", () => {
    expect(estimateThinkingCostUsd("claude-haiku-4-5-20251001", 1_000_000)).toBe(5);
    expect(estimateThinkingCostUsd("claude-sonnet-4-5", 1_000_000)).toBe(10);
    expect(estimateThinkingCostUsd("Claude-Opus-4-5", 1_000_000)).toBe(25);
  });

  it("scales linearly with token count", () => {
    expect(estimateThinkingCostUsd("claude-haiku-4-5", 500_000)).toBeCloseTo(2.5);
    expect(estimateThinkingCostUsd("claude-haiku-4-5", 0)).toBe(0);
  });

  it("returns null for a model that doesn't match any known tier, never a guessed price", () => {
    expect(estimateThinkingCostUsd("some-future-model-xyz", 1_000_000)).toBeNull();
  });
});
