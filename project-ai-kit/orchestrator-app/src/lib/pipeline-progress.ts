import {
  CONTRACT_LOCK_GATE_STAGE_ID,
  TRIGGER_GATE_STAGE_ID,
  type FeatureState,
  type PipelineDef,
} from "@/lib/tauri-client";

/** Presentation helper for the Pipeline Tree. Gate stages do not have
 * NodeState entries, so completion includes their applicable pass state while
 * leaving the pipeline/runtime topology untouched. */
export function isPipelineComplete(
  pipelineDef: PipelineDef,
  featureState: FeatureState | null,
): boolean {
  if (!featureState) return false;

  const agentSlots = pipelineDef.stages.flatMap((stage) => stage.agents);
  if (agentSlots.length === 0) return false;

  const allAgentsDone = agentSlots.every(
    (agent) => featureState.nodes[agent.id]?.status === "done",
  );
  if (!allAgentsDone) return false;

  const hasTriggerGate = pipelineDef.stages.some(
    (stage) => stage.id === TRIGGER_GATE_STAGE_ID,
  );
  const triggerPassed =
    !hasTriggerGate ||
    featureState.gates[TRIGGER_GATE_STAGE_ID]?.status === "approved";
  if (!triggerPassed) return false;

  const hasContractLockGate = pipelineDef.stages.some(
    (stage) => stage.id === CONTRACT_LOCK_GATE_STAGE_ID,
  );
  const contractLockStatus = featureState.contractLock?.status;
  const contractPassed =
    !hasContractLockGate ||
    contractLockStatus === "locked" ||
    contractLockStatus === "not-applicable";

  return contractPassed;
}
