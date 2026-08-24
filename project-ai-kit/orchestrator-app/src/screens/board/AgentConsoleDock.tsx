import { useEffect, useMemo } from "react";
import { Terminal } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { commands, type FeatureState, type PipelineDef } from "@/lib/tauri-client";
import type { TreeSelection } from "@/screens/board/PipelineTree";
import { AgentConsoleCard } from "@/screens/board/AgentConsoleCard";
import {
  createAgentConsoleState,
  runConsoleKey,
  useRunConsoleStore,
} from "@/state/run-console-store";

interface AgentConsoleDockProps {
  feature: string;
  pipelineDef: PipelineDef;
  featureState: FeatureState | null;
  /** Presentation-only aliases keyed by slot id, so a card names its agent
   * exactly the way the tree node does. */
  nodeNicknames: Record<string, string>;
  onSelectNode: (selection: TreeSelection) => void;
}

export function AgentConsoleDock({
  feature,
  pipelineDef,
  featureState,
  nodeNicknames,
  onSelectNode,
}: AgentConsoleDockProps) {
  const consoles = useRunConsoleStore((state) => state.consoles);
  const ensureConsole = useRunConsoleStore((state) => state.ensureConsole);
  const hydrate = useRunConsoleStore((state) => state.hydrate);

  const agents = useMemo(
    () => pipelineDef.stages.flatMap((stage) => stage.agents.map((agent) => ({ stage, agent }))),
    [pipelineDef],
  );

  useEffect(() => {
    for (const { agent } of agents) {
      ensureConsole(feature, agent.id);
      void hydrate(feature, agent.id);
    }
  }, [agents, ensureConsole, feature, hydrate]);

  const visibleAgents = agents.filter(({ agent }) => {
    const status = featureState?.nodes[agent.id]?.status;
    const consoleState = consoles[runConsoleKey(feature, agent.id)];
    return (
      status === "running" ||
      status === "waiting-input" ||
      status === "failed" ||
      status === "interrupted" ||
      !!consoleState?.liveActive ||
      (consoleState?.lines.length ?? 0) > 0
    );
  });

  if (visibleAgents.length === 0) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-2 p-6 text-center">
        <Terminal className="size-7 text-muted-foreground/50" aria-hidden="true" />
        <p className="text-xs text-muted-foreground">Chưa có terminal/log của agent.</p>
      </div>
    );
  }

  return (
    <div className="flex h-full min-h-0 flex-col">
      <div className="flex items-center gap-2 border-b border-border px-3 py-2">
        <Terminal className="size-4 text-muted-foreground" aria-hidden="true" />
        <span className="text-xs font-semibold">Agent terminals</span>
        <Badge variant="secondary">{visibleAgents.length}</Badge>
      </div>
      <div className="min-h-0 flex-1 overflow-y-auto p-2">
        <div className="flex flex-col gap-2">
          {visibleAgents.map(({ stage, agent }) => {
            const key = runConsoleKey(feature, agent.id);
            const consoleState = consoles[key] ?? createAgentConsoleState(feature, agent.id);
            return (
              <AgentConsoleCard
                key={key}
                agent={agent}
                nickname={nodeNicknames[agent.id]}
                stageLabel={stage.label}
                nodeState={featureState?.nodes[agent.id]}
                consoleState={consoleState}
                onKill={() => {
                  void commands.killRun(feature, agent.id);
                }}
                onSelect={() => onSelectNode({ stage, agent })}
              />
            );
          })}
        </div>
      </div>
    </div>
  );
}
