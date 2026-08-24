import type { AgentSlot } from "@/lib/tauri-client";

/** The one place the display-name precedence lives, so the board, the
 * detail panel, the console dock and Reports can never disagree about what
 * a node is called:
 *
 *   nickname (user-set, per project) → label (kit default) → agentName
 *
 * `agentName` alone is not enough on its own: `qc-design` and `qc-testing`
 * both spawn `qc-agent`, so two nodes used to render identically. */
export function slotDisplayName(agent: AgentSlot, nickname?: string): string {
  const trimmed = nickname?.trim();
  if (trimmed) return trimmed;
  const label = agent.label?.trim();
  if (label) return label;
  return agent.agentName;
}

/** The real agent file name, to show underneath the display name — `null`
 * when it IS the display name, so nothing renders the same string twice. */
export function slotSubLabel(agent: AgentSlot, nickname?: string): string | null {
  return slotDisplayName(agent, nickname) === agent.agentName ? null : agent.agentName;
}
