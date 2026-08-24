/**
 * AC-E2-07 / AC-E6-19 — the Claude CLI only reports real cost once, on the
 * terminal `result` line (`StreamEvent.runFinished.totalCostUsd`); there is
 * no incremental cost signal while a run is in progress. This gives the Log
 * Console a running *estimate* instead, computed app-side from thinking-
 * token volume — it is not, and cannot be, the exact figure.
 *
 * Verified 2026-08-17 against https://platform.claude.com/docs/en/about-claude/pricing
 * (output-token rate for the CURRENT latest model in each tier — `spawn.rs`
 * passes the CLI the generic `--model opus|sonnet|haiku` alias, which
 * resolves to whichever model is newest in that tier at the time). Update
 * this table if Anthropic's published pricing changes.
 */
const OUTPUT_PRICE_PER_MILLION_TOKENS_USD: Record<"opus" | "sonnet" | "haiku", number> = {
  opus: 25, // Claude Opus 5
  sonnet: 10, // Claude Sonnet 5
  haiku: 5, // Claude Haiku 4.5
};

function pricingTierOf(model: string): "opus" | "sonnet" | "haiku" | null {
  const lower = model.toLowerCase();
  if (lower.includes("opus")) return "opus";
  if (lower.includes("sonnet")) return "sonnet";
  if (lower.includes("haiku")) return "haiku";
  return null;
}

/**
 * Estimates cost from thinking-token volume alone (billed as output
 * tokens) — it deliberately does NOT account for prompt/tool-result input
 * tokens or non-thinking output text, since the running stream carries no
 * signal for those. Always an undercount of the real total, never an exact
 * figure — callers must label it as an estimate. `null` when `model`
 * doesn't match any known pricing tier (never silently guess a price).
 */
export function estimateThinkingCostUsd(model: string, thinkingTokens: number): number | null {
  const tier = pricingTierOf(model);
  if (tier === null) return null;
  return (thinkingTokens / 1_000_000) * OUTPUT_PRICE_PER_MILLION_TOKENS_USD[tier];
}
