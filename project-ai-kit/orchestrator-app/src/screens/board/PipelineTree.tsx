import { Fragment, forwardRef, useLayoutEffect, useRef, useState } from "react";
import {
  CircleCheck,
  Check,
  CircleSlash,
  Clock,
  Code,
  FileText,
  FlaskConical,
  ListChecks,
  Lock,
  Palette,
  Rocket,
  ShieldAlert,
  Trash2,
  type LucideIcon,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { isPipelineComplete } from "@/lib/pipeline-progress";
import { slotDisplayName, slotSubLabel } from "@/lib/slot-label";
import { statusMeta } from "@/lib/status-meta";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Popover, PopoverAnchor, PopoverContent } from "@/components/ui/popover";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import {
  CONTRACT_LOCK_GATE_STAGE_ID,
  isCheckpointStage,
  TRIGGER_GATE_STAGE_ID,
} from "@/lib/tauri-client";
import type {
  AgentSlot,
  ContractLockState,
  FeatureState,
  GateState,
  NodeState,
  PipelineDef,
  StageDef,
} from "@/lib/tauri-client";

export interface TreeSelection {
  stage: StageDef;
  /** `null` for a gate stage (no runnable agents — ④ Contract Lock, ⑧
   * Deploy in MVP2). */
  agent: AgentSlot | null;
}

interface PipelineTreeProps {
  pipelineDef: PipelineDef;
  featureState: FeatureState | null;
  selection: TreeSelection | null;
  onSelectNode: (selection: TreeSelection) => void;
  nodeNicknames: Record<string, string>;
  onNicknameChange: (slotId: string, nickname: string | null) => Promise<void>;
}

function nodeKey(stage: StageDef, agent: AgentSlot | null): string {
  return agent ? agent.id : `gate:${stage.id}`;
}

/** A small icon per stage type, so the tree reads as a pipeline of
 * distinct phases (input → design → build → test → deploy) rather than a
 * uniform list of identical cards. Purely decorative. */
const STAGE_ICON: Record<string, LucideIcon> = {
  S1_input: FileText,
  S2_design: Palette,
  S3_planning: ListChecks,
  S5_build: Code,
  S6_testing: FlaskConical,
  S7_deploy: Rocket,
};

function stageIcon(stage: StageDef): LucideIcon | null {
  return STAGE_ICON[stage.id] ?? null;
}

interface PhaseMeta {
  id: string;
  label: string;
  accent: string;
}

/** Visual grouping only. The pipeline definition remains the source of
 * truth for ordering and dependencies; these labels make the long tree
 * easier to scan without changing its topology. */
const PHASE_META: Record<string, PhaseMeta> = {
  discovery: { id: "discovery", label: "Discovery", accent: "border-info/40 text-info" },
  design: { id: "design", label: "Design", accent: "border-primary/40 text-primary" },
  planning: { id: "planning", label: "Planning & Contract", accent: "border-warning/50 text-warning" },
  build: { id: "build", label: "Build", accent: "border-success/50 text-success" },
  verify: { id: "verify", label: "Test", accent: "border-info/40 text-info" },
  release: { id: "release", label: "Release", accent: "border-border text-muted-foreground" },
};

function phaseForStage(stage: StageDef): PhaseMeta {
  if (stage.id === "S1_input" || stage.id === TRIGGER_GATE_STAGE_ID) return PHASE_META.discovery;
  if (stage.id === "S2_design") return PHASE_META.design;
  if (stage.id === "S3_planning" || stage.id === CONTRACT_LOCK_GATE_STAGE_ID) return PHASE_META.planning;
  if (stage.id === "S5_build") return PHASE_META.build;
  if (stage.id === "S6_testing") return PHASE_META.verify;
  return PHASE_META.release;
}

interface TreeNodeProps {
  agent: AgentSlot;
  nodeState: NodeState | undefined;
  nickname?: string;
  selected: boolean;
  onClick: () => void;
  onDoubleClick: () => void;
}

const TreeNode = forwardRef<HTMLButtonElement, TreeNodeProps>(function TreeNode(
  { agent, nodeState, nickname, selected, onClick, onDoubleClick },
  ref,
) {
  const meta = statusMeta(nodeState?.status ?? "idle");
  const Icon = meta.icon;
  const status = nodeState?.status ?? "idle";
  const isDone = status === "done";
  const isRunning = status === "running";
  const displayName = slotDisplayName(agent, nickname);
  const subLabel = slotSubLabel(agent, nickname);

  return (
    <button
      ref={ref}
      type="button"
      onClick={onClick}
      onDoubleClick={onDoubleClick}
      aria-current={selected ? "step" : undefined}
      title={subLabel ? `${displayName} (${subLabel})` : `${displayName} — double-click để đặt nickname`}
      className={cn(
        "relative z-10 flex w-36 flex-col items-center gap-1.5 rounded-xl border-2 bg-card px-3 py-2.5 text-center transition-all hover:bg-muted hover:shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
        selected ? "border-primary shadow-sm" : "border-border",
        isRunning && "ring-2 ring-info/40",
      )}
    >
      <span
        // `key` on the status circle remounts it on every status change,
        // replaying the pop animation so a transition idle→running→done
        // is visible, not just a snap.
        key={status}
        className={cn(
          "flex size-7 items-center justify-center rounded-full animate-node-pop",
          isDone ? "bg-success text-white" : cn("bg-muted", meta.colorClass),
        )}
      >
        <Icon className={cn("size-4", meta.spin && "animate-spin")} aria-hidden="true" />
      </span>
      <span className="truncate text-xs font-medium">{displayName}</span>
      {subLabel && <span className="truncate font-mono text-[10px] text-muted-foreground">{subLabel}</span>}
      <span className="truncate text-[11px] text-muted-foreground">{meta.label}</span>
    </button>
  );
});

interface GateNodeProps {
  selected: boolean;
  onClick: () => void;
  /** `null` for a gate with no approval concept (S7_deploy). */
  gateState: GateState | undefined;
  contractLockState: ContractLockState | undefined;
  stageId: string;
}

/** The visual state a gate node shows — derived purely from the gate's
 * own state (already computed server-side), mirroring what the panel
 * beside it says, so the tree and the panel never disagree. */
type GateVisual =
  | "approved"
  | "pending"
  | "locked"
  | "violated"
  | "notApplicable"
  | "blocked"
  | "neutral";

function gateVisual(stageId: string, gateState: GateState | undefined, contractLockState: ContractLockState | undefined): GateVisual {
  if (stageId === TRIGGER_GATE_STAGE_ID) {
    const status = gateState?.status;
    if (status === "approved") return "approved";
    if (status === "pending-review") return "pending";
    return "neutral";
  }
  if (stageId === CONTRACT_LOCK_GATE_STAGE_ID) {
    const status = contractLockState?.status;
    if (status === "locked") return "locked";
    if (status === "violated") return "violated";
    if (status === "pending-review") return "pending";
    // Không gộp vào `neutral`: icon ổ khoá + "Chưa mở" khiến gate trông như
    // đang chờ được mở, trong khi ở trạng thái này chẳng có gì để mở — nó đã
    // được bỏ qua và stage ⑤ chạy tiếp bình thường.
    if (status === "not-applicable") return "notApplicable";
    // `not-ready` cũng KHÔNG gộp vào `neutral`, cùng lý do ngược lại: ổ
    // khoá xám "Chưa mở" trông y hệt node ⑧ Deploy chưa tới lượt, trong khi
    // gate này đang chặn cứng cả stage ⑤ trở đi và cần người xử lý. Người
    // dùng không nên phải bấm vào mới biết mình đang bế tắc.
    if (status === "not-ready") return "blocked";
    return "neutral";
  }
  return "neutral";
}

const GATE_VISUAL_META: Record<GateVisual, { icon: LucideIcon; label: string; border: string; iconBg: string; iconColor: string }> = {
  approved: { icon: CircleCheck, label: "Đã duyệt", border: "border-success", iconBg: "bg-success/15", iconColor: "text-success" },
  locked: { icon: CircleCheck, label: "Đã khoá", border: "border-success", iconBg: "bg-success/15", iconColor: "text-success" },
  pending: { icon: Clock, label: "Chờ duyệt", border: "border-warning", iconBg: "bg-warning/15", iconColor: "text-warning" },
  violated: { icon: ShieldAlert, label: "Vi phạm", border: "border-destructive", iconBg: "bg-destructive/15", iconColor: "text-destructive" },
  notApplicable: { icon: CircleSlash, label: "Không áp dụng", border: "border-border", iconBg: "bg-muted", iconColor: "text-muted-foreground" },
  blocked: { icon: Lock, label: "Chưa mở được", border: "border-warning", iconBg: "bg-warning/15", iconColor: "text-warning" },
  neutral: { icon: Lock, label: "Chưa mở", border: "border-border", iconBg: "bg-muted", iconColor: "text-muted-foreground" },
};

const GateNode = forwardRef<HTMLButtonElement, GateNodeProps>(function GateNode(
  { selected, onClick, gateState, contractLockState, stageId },
  ref,
) {
  const visual = gateVisual(stageId, gateState, contractLockState);
  const meta = GATE_VISUAL_META[visual];
  const Icon = meta.icon;

  return (
    <button
      ref={ref}
      type="button"
      onClick={onClick}
      aria-current={selected ? "step" : undefined}
      className={cn(
        "relative z-10 flex w-36 flex-col items-center gap-1.5 rounded-xl border-2 border-dashed bg-muted/40 px-3 py-2.5 text-center transition-all hover:bg-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
        meta.border,
        selected && "ring-2 ring-ring/40",
      )}
    >
      <span className={cn("flex size-7 items-center justify-center rounded-full", meta.iconBg)}>
        <Icon className={cn("size-4", meta.iconColor)} aria-hidden="true" />
      </span>
      <span className="text-xs font-medium">Gate</span>
      <span className={cn("truncate text-[11px]", meta.iconColor)}>{meta.label}</span>
    </button>
  );
});

export interface Segment {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  /** `in` = a source node feeding the junction; `out` = the junction
   * feeding a node of the next stage. Kept so each edge can be coloured by
   * the thing that actually flows along it. */
  kind: "in" | "out";
  /** Stage the flow comes FROM — both kinds share it. */
  fromStageId: string;
  /** Source node, for `in` segments only (an `out` segment starts at the
   * shared junction, which belongs to the whole stage). */
  fromSlotId?: string;
}

/** Whether an edge is "carrying" anything yet, from the status of whatever
 * feeds it: the source node for a fan-in, the whole source stage for a
 * fan-out (that bundle is what makes ba-agent visibly feed all three
 * stage-② agents). */
export function edgeState(
  segment: Segment,
  stages: StageDef[],
  featureState: FeatureState | null,
): "flowing" | "done" | "idle" {
  const statusOf = (slotId: string) => featureState?.nodes[slotId]?.status ?? "idle";

  if (segment.kind === "in" && segment.fromSlotId) {
    const status = statusOf(segment.fromSlotId);
    if (status === "running") return "flowing";
    return status === "done" || status === "skipped" ? "done" : "idle";
  }

  const fromStage = stages.find((s) => s.id === segment.fromStageId);
  // A gate stage has no agents to derive a status from — colour its
  // outgoing edges by the gate's own approval state instead of leaving
  // them neutral forever. Otherwise an approved Trigger / Contract Lock
  // gate never turns its connector lines green, even though the panel
  // beside it already says "Đã duyệt" / "Đã khoá".
  if (!fromStage) return "idle";
  if (isCheckpointStage(fromStage.id)) {
    if (fromStage.id === TRIGGER_GATE_STAGE_ID) {
      return featureState?.gates?.[TRIGGER_GATE_STAGE_ID]?.status === "approved"
        ? "done"
        : "idle";
    }
    if (fromStage.id === CONTRACT_LOCK_GATE_STAGE_ID) {
      const status = featureState?.contractLock?.status;
      if (status === "locked") return "done";
      if (status === "not-applicable") {
        // Skipped gate is transparent, not an unlock (readiness.rs mirrors
        // this): look through to the stage feeding Contract Lock (S3_planning)
        // instead of turning green regardless of its progress.
        const predecessor = fromStage.dependsOn
          ? stages.find((s) => s.id === fromStage.dependsOn)
          : undefined;
        if (!predecessor || predecessor.agents.length === 0) return "idle";
        if (predecessor.agents.some((a) => statusOf(a.id) === "running")) return "flowing";
        const complete = predecessor.agents.every((a) => {
          const st = statusOf(a.id);
          return st === "done" || st === "skipped";
        });
        return complete ? "done" : "idle";
      }
      return "idle";
    }
    // S7_deploy and any future gate without a panel — no approval state
    // to read, stay neutral.
    return "idle";
  }
  if (fromStage.agents.some((a) => statusOf(a.id) === "running")) return "flowing";
  const complete = fromStage.agents.every((a) => {
    const status = statusOf(a.id);
    return status === "done" || status === "skipped";
  });
  return complete ? "done" : "idle";
}

/**
 * Real branching tree — one node per agent (not one row per stage), with
 * fan-out/fan-in connector lines between stages instead of a single
 * straight rail. A stage transition always funnels through one shared
 * junction point rather than drawing a full mesh between every previous
 * node and every next node: `PipelineDef` has no per-agent dependency data
 * (only "these agents belong to this stage"), so a mesh would imply
 * fine-grained dependencies that don't actually exist.
 *
 * Connector positions are measured from the real DOM (ref + ResizeObserver)
 * rather than computed from a fixed grid, so they stay correct regardless
 * of how status-label text width changes node sizing or how the window/
 * sidebar resizes.
 */
export function PipelineTree({
  pipelineDef,
  featureState,
  selection,
  onSelectNode,
  nodeNicknames,
  onNicknameChange,
}: PipelineTreeProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const nodeRefs = useRef(new Map<string, HTMLElement>());
  const [segments, setSegments] = useState<Segment[]>([]);
  const [svgSize, setSvgSize] = useState({ width: 0, height: 0 });
  const [editingSlotId, setEditingSlotId] = useState<string | null>(null);
  const [draftNickname, setDraftNickname] = useState("");
  const [nicknameError, setNicknameError] = useState<string | null>(null);
  const [savingNickname, setSavingNickname] = useState(false);
  const pipelineComplete = isPipelineComplete(pipelineDef, featureState);
  const segmentStates = segments.map((segment) =>
    edgeState(segment, pipelineDef.stages, featureState),
  );
  const firstIdleStageIndex = segments.reduce((first, segment, index) => {
    if (segmentStates[index] !== "idle") return first;
    const stageIndex = pipelineDef.stages.findIndex((stage) => stage.id === segment.fromStageId);
    return stageIndex >= 0 ? Math.min(first, stageIndex) : first;
  }, Number.POSITIVE_INFINITY);
  const snakeEnabled =
    featureState !== null && !pipelineComplete && firstIdleStageIndex !== Number.POSITIVE_INFINITY;
  const remainingTransitions = Math.max(
    1,
    pipelineDef.stages.length - 1 - firstIdleStageIndex,
  );
  const snakeTransitionMs = 5000 / remainingTransitions;

  function openNicknameEditor(slotId: string) {
    setEditingSlotId(slotId);
    setDraftNickname(nodeNicknames[slotId] ?? "");
    setNicknameError(null);
  }

  function closeNicknameEditor() {
    if (savingNickname) return;
    setEditingSlotId(null);
    setDraftNickname("");
    setNicknameError(null);
  }

  async function saveNickname(value = draftNickname) {
    if (!editingSlotId) return;
    const trimmed = value.trim();
    if (trimmed.length > 40) {
      setNicknameError("Nickname tối đa 40 ký tự.");
      return;
    }

    setSavingNickname(true);
    setNicknameError(null);
    try {
      await onNicknameChange(editingSlotId, trimmed || null);
      setEditingSlotId(null);
      setDraftNickname("");
    } catch (err) {
      setNicknameError(err instanceof Error ? err.message : String(err));
    } finally {
      setSavingNickname(false);
    }
  }

  useLayoutEffect(() => {
    function measure() {
      const container = containerRef.current;
      if (!container) return;
      const containerRect = container.getBoundingClientRect();
      setSvgSize({ width: containerRect.width, height: containerRect.height });

      const nextSegments: Segment[] = [];
      for (let i = 0; i < pipelineDef.stages.length - 1; i++) {
        const current = pipelineDef.stages[i];
        const next = pipelineDef.stages[i + 1];
        const currentKeys =
          current.agents.length === 0 ? [nodeKey(current, null)] : current.agents.map((a) => a.id);
        const nextKeys =
          next.agents.length === 0 ? [nodeKey(next, null)] : next.agents.map((a) => a.id);

        // Keep the slot id alongside each measured point — that identity is
        // what lets an edge be coloured by its own source rather than every
        // line looking the same.
        const bottoms = currentKeys
          .map((k) => ({ key: k, rect: nodeRefs.current.get(k)?.getBoundingClientRect() }))
          .filter((m): m is { key: string; rect: DOMRect } => m.rect != null)
          .map(({ key, rect }) => ({
            key,
            x: rect.left + rect.width / 2 - containerRect.left,
            y: rect.bottom - containerRect.top,
          }));
        const tops = nextKeys
          .map((k) => nodeRefs.current.get(k)?.getBoundingClientRect())
          .filter((r): r is DOMRect => r != null)
          .map((r) => ({ x: r.left + r.width / 2 - containerRect.left, y: r.top - containerRect.top }));

        if (bottoms.length === 0 || tops.length === 0) continue;

        const junctionY =
          (Math.max(...bottoms.map((b) => b.y)) + Math.min(...tops.map((t) => t.y))) / 2;
        const junctionX = containerRect.width / 2;

        for (const b of bottoms) {
          nextSegments.push({
            x1: b.x,
            y1: b.y,
            x2: junctionX,
            y2: junctionY,
            kind: "in",
            fromStageId: current.id,
            // Gate stages key on `gate:<stageId>`, not a slot id.
            fromSlotId: current.agents.length === 0 ? undefined : b.key,
          });
        }
        for (const t of tops) {
          nextSegments.push({
            x1: junctionX,
            y1: junctionY,
            x2: t.x,
            y2: t.y,
            kind: "out",
            fromStageId: current.id,
          });
        }
      }
      setSegments(nextSegments);
    }

    measure();
    const ro = new ResizeObserver(measure);
    if (containerRef.current) ro.observe(containerRef.current);
    window.addEventListener("resize", measure);
    return () => {
      ro.disconnect();
      window.removeEventListener("resize", measure);
    };
  }, [pipelineDef, featureState]);

  return (
    <div ref={containerRef} className="relative flex flex-col items-center gap-8 py-4">
      <svg
        className="pointer-events-none absolute left-0 top-0 z-0"
        width={svgSize.width}
        height={svgSize.height}
        aria-hidden="true"
      >
        <defs>
          {/* Arrowhead markers, one per edge colour so the head always
             matches its line. `out` segments point down into a node. */}
          <marker id="arrow-done" markerWidth="7" markerHeight="7" refX="5" refY="3.5" orient="auto" markerUnits="strokeWidth">
            <path d="M0,0 L6,3.5 L0,7 Z" className="edge-arrow-done" />
          </marker>
          <marker id="arrow-flowing" markerWidth="7" markerHeight="7" refX="5" refY="3.5" orient="auto" markerUnits="strokeWidth">
            <path d="M0,0 L6,3.5 L0,7 Z" className="edge-arrow-flowing" />
          </marker>
          <marker id="arrow-idle" markerWidth="7" markerHeight="7" refX="5" refY="3.5" orient="auto" markerUnits="strokeWidth">
            <path d="M0,0 L6,3.5 L0,7 Z" className="edge-arrow-idle" />
          </marker>
        </defs>
        {segments.map((s, i) => {
          const state = segmentStates[i];
          return (
            <line
              key={i}
              x1={s.x1}
              y1={s.y1}
              x2={s.x2}
              y2={s.y2}
              strokeWidth={state === "idle" ? 2 : 2.5}
              strokeLinecap="round"
              markerEnd={s.kind === "out" ? `url(#arrow-${state})` : undefined}
              className={cn(
                "transition-colors",
                state === "done" && "stroke-success",
                state === "flowing" && "edge-flow stroke-info",
                state === "idle" && "stroke-border",
              )}
            />
          );
        })}
      </svg>

      <svg
        className="pointer-events-none absolute left-0 top-0 z-[1]"
        width={svgSize.width}
        height={svgSize.height}
        aria-hidden="true"
      >
        {snakeEnabled && segments.map((segment, index) => {
          if (segmentStates[index] !== "idle") return null;
          const stageIndex = pipelineDef.stages.findIndex(
            (stage) => stage.id === segment.fromStageId,
          );
          if (stageIndex < firstIdleStageIndex) return null;

          const relativeStageIndex = stageIndex - firstIdleStageIndex;
          const phaseOffset =
            relativeStageIndex * snakeTransitionMs +
            (segment.kind === "out" ? snakeTransitionMs / 2 : 0);
          const animationDelay = -(5000 - phaseOffset);

          return (
            <line
              key={`snake-${index}`}
              x1={segment.x1}
              y1={segment.y1}
              x2={segment.x2}
              y2={segment.y2}
              pathLength={1}
              className="edge-snake"
              style={{ animationDelay: `${animationDelay}ms` }}
            />
          );
        })}
      </svg>

      {pipelineDef.stages.map((stage, index) => {
        const isGate = isCheckpointStage(stage.id);
        const StageIcon = stageIcon(stage);
        const phase = phaseForStage(stage);
        const previousPhase = index > 0 ? phaseForStage(pipelineDef.stages[index - 1]) : null;
        const isPhaseStart = phase.id !== previousPhase?.id;
        return (
          <Fragment key={stage.id}>
            {isPhaseStart && (
              <div className={cn("mt-1 flex w-full max-w-xl items-center gap-3 border-b pb-1 text-[10px] font-semibold uppercase tracking-[0.16em]", phase.accent)}>
                <span>{phase.label}</span>
                <span className="h-px flex-1 bg-border/60" aria-hidden="true" />
              </div>
            )}
            <div className="relative z-10 flex flex-col items-center gap-2">
              <span className="flex items-center gap-1.5 text-xs font-medium text-muted-foreground">
                {StageIcon && <StageIcon className="size-3.5" aria-hidden="true" />}
                {stage.label}
              </span>
              <div className="flex flex-wrap items-stretch justify-center gap-4">
                {isGate ? (
                  <GateNode
                    ref={(el) => {
                      if (el) nodeRefs.current.set(nodeKey(stage, null), el);
                    }}
                    selected={selection?.stage.id === stage.id && selection.agent === null}
                    onClick={() => onSelectNode({ stage, agent: null })}
                    gateState={featureState?.gates?.[stage.id]}
                    contractLockState={featureState?.contractLock ?? undefined}
                    stageId={stage.id}
                  />
                ) : stage.agents.length === 0 ? (
                  // ⑤ Build sinh slot từ bảng Ecosystem, nên "chưa khai repo
                  // nào" là trạng thái có thật. Nói thẳng ra, đừng để stage
                  // trống trơn khiến người dùng tưởng board hỏng.
                  <div className="max-w-xs rounded-lg border border-dashed border-border px-3 py-2 text-center text-xs text-muted-foreground">
                    Chưa có repo nào trong bảng Ecosystem của AGENTS.md — chạy{" "}
                    <code className="font-mono">/init-kit</code> hoặc bổ sung bảng{" "}
                    <code className="font-mono">## Repos</code>.
                  </div>
                ) : (
                  stage.agents.map((agent) => {
                    const nickname = nodeNicknames[agent.id];
                    const isEditing = editingSlotId === agent.id;
                    return (
                      <Popover
                        key={agent.id}
                        open={isEditing}
                        onOpenChange={(open) => {
                          if (!open) closeNicknameEditor();
                        }}
                      >
                        <PopoverAnchor asChild>
                          <div className="relative">
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <TreeNode
                                  ref={(el) => {
                                    if (el) nodeRefs.current.set(agent.id, el);
                                  }}
                                  agent={agent}
                                  nickname={nickname}
                                  nodeState={featureState?.nodes[agent.id]}
                                  selected={selection?.agent?.id === agent.id}
                                  onClick={() => onSelectNode({ stage, agent })}
                                  onDoubleClick={() => openNicknameEditor(agent.id)}
                                />
                              </TooltipTrigger>
                              <TooltipContent side="right" sideOffset={8} className="flex-col items-start">
                                <span className="font-medium">{slotDisplayName(agent, nickname)}</span>
                                <span className="font-mono text-[10px] opacity-70">
                                  {agent.agentName} · {agent.id}
                                </span>
                                <span className="text-[10px] opacity-70">
                                  {nickname ? "Double-click để sửa nickname" : "Double-click để đặt nickname"}
                                </span>
                              </TooltipContent>
                            </Tooltip>
                          </div>
                        </PopoverAnchor>
                        <PopoverContent side="right" align="start" sideOffset={12}>
                          <div className="flex flex-col gap-3">
                            <div>
                              <p className="text-sm font-semibold">Đặt nickname</p>
                              <p className="mt-0.5 font-mono text-[11px] text-muted-foreground">
                                {agent.agentName} · {agent.id}
                              </p>
                            </div>
                            <Input
                              autoFocus
                              value={draftNickname}
                              maxLength={40}
                              placeholder={slotDisplayName(agent)}
                              aria-label={`Nickname cho ${slotDisplayName(agent)}`}
                              disabled={savingNickname}
                              onChange={(event) => setDraftNickname(event.target.value)}
                              onKeyDown={(event) => {
                                if (event.key === "Enter") {
                                  event.preventDefault();
                                  void saveNickname();
                                }
                                if (event.key === "Escape") {
                                  event.preventDefault();
                                  closeNicknameEditor();
                                }
                              }}
                            />
                            {nicknameError && <p className="text-xs text-destructive">{nicknameError}</p>}
                            <p className="text-[11px] text-muted-foreground">
                              Để trống rồi bấm Xoá để quay về tên mặc định ({slotDisplayName(agent)}).
                            </p>
                            <div className="flex items-center justify-between gap-2">
                              <Button
                                type="button"
                                variant="ghost"
                                size="sm"
                                disabled={savingNickname || !nickname}
                                onClick={() => {
                                  setDraftNickname("");
                                  void saveNickname("");
                                }}
                              >
                                <Trash2 />
                                Xoá
                              </Button>
                              <div className="flex gap-2">
                                <Button type="button" variant="ghost" size="sm" disabled={savingNickname} onClick={closeNicknameEditor}>
                                  Huỷ
                                </Button>
                                <Button type="button" size="sm" disabled={savingNickname} onClick={() => void saveNickname()}>
                                  <Check />
                                  {savingNickname ? "Đang lưu..." : "Lưu"}
                                </Button>
                              </div>
                            </div>
                          </div>
                        </PopoverContent>
                      </Popover>
                    );
                  })
                )}
              </div>
            </div>
          </Fragment>
        );
      })}
    </div>
  );
}
