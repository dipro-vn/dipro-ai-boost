import { GitBranch } from "lucide-react";
import { Separator } from "@/components/ui/separator";
import {
  CONTRACT_LOCK_GATE_STAGE_ID,
  TRIGGER_GATE_STAGE_ID,
  type FeatureState,
  type PipelineDef,
  type SlotReadiness,
} from "@/lib/tauri-client";
import { slotDisplayName } from "@/lib/slot-label";
import type { TreeSelection } from "@/screens/board/PipelineTree";
import { AgentStepPanel } from "@/screens/board/AgentStepPanel";
import { BaStepPanel } from "@/screens/board/BaStepPanel";
import { ContractLockPanel } from "@/screens/board/ContractLockPanel";
import { TriggerGatePanel } from "@/screens/board/TriggerGatePanel";

/** Which slot gets `BaStepPanel` instead of the generic `AgentStepPanel`:
 * `ba` is the only one whose run starts from a folder-import form, so it
 * needs its own panel. Every slot is runnable — this is panel routing, not
 * a gate. */
const BA_SLOT = "ba";

interface ActionPanelProps {
  feature: string;
  selection: TreeSelection | null;
  featureState: FeatureState | null;
  /** For AC-E6-26's skip-dependents warning — panels compute who runs
   * short of input if a slot is skipped. */
  pipelineDef: PipelineDef | null;
  /** Presentation-only aliases keyed by slot id, so this panel names a node
   * exactly the way the tree does. */
  nodeNicknames: Record<string, string>;
  /** B22 — per-slot Run-button gating, keyed by slot id. */
  readiness: Record<string, SlotReadiness>;
  /** Re-asks the backend whether this slot may run — the Ecosystem is
   * re-read from disk on the way, so a just-cloned repo unblocks here. */
  onRecheckReadiness: () => void;
}

/**
 * Permanent action pane (1/3 of the Board) — replaces the old Sheet/drawer
 * overlay with an always-visible panel. Live logs are rendered separately by
 * `AgentConsoleDock`, so changing selection never unmounts another node's
 * terminal.
 */
export function ActionPanel({
  feature,
  selection,
  featureState,
  pipelineDef,
  nodeNicknames,
  readiness,
  onRecheckReadiness,
}: ActionPanelProps) {
  const isBa = selection?.agent?.id === BA_SLOT;

  if (!selection) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-2 p-6 text-center">
        <GitBranch className="size-8 text-muted-foreground" aria-hidden="true" />
        <p className="text-sm text-muted-foreground">
          Chọn 1 node trong tree bên phải để xem chi tiết và thao tác.
        </p>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col">
      <div className="p-4">
        <h2 className="text-sm font-semibold">
          {selection.agent
            ? slotDisplayName(selection.agent, nodeNicknames[selection.agent.id])
            : "Gate"}
        </h2>
        <p className="text-xs text-muted-foreground">{selection.stage.label}</p>
      </div>
      <Separator />
      <div className="flex-1 overflow-y-auto p-4">
        {selection.agent === null ? (
          selection.stage.id === TRIGGER_GATE_STAGE_ID ? (
            <TriggerGatePanel
              feature={feature}
              gateState={featureState?.gates[TRIGGER_GATE_STAGE_ID]}
            />
          ) : selection.stage.id === CONTRACT_LOCK_GATE_STAGE_ID ? (
            <ContractLockPanel
              feature={feature}
              contractLockState={featureState?.contractLock ?? undefined}
            />
          ) : (
            <p className="text-sm text-muted-foreground">
              Stage này cần thao tác thủ công ngoài app (vd deploy) — bản MVP
              hiện tại chỉ hiển thị trạng thái, chưa hỗ trợ thao tác trực tiếp.
            </p>
          )
        ) : isBa ? (
          <BaStepPanel
            feature={feature}
            agent={selection.agent}
            nickname={nodeNicknames[selection.agent.id]}
            nodeState={featureState?.nodes[selection.agent.id]}
            pipelineDef={pipelineDef}
            showConsole={false}
          />
        ) : (
          <AgentStepPanel
            feature={feature}
            agent={selection.agent}
            nickname={nodeNicknames[selection.agent.id]}
            nodeState={featureState?.nodes[selection.agent.id]}
            pipelineDef={pipelineDef}
            readiness={readiness[selection.agent.id]}
            onRecheckReadiness={onRecheckReadiness}
            showConsole={false}
          />
        )}
      </div>
    </div>
  );
}
