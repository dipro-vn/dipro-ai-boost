import { useEffect, useRef, useState, type ReactNode } from "react";
import { Virtuoso, type VirtuosoHandle } from "react-virtuoso";
import { CircleHelp, Maximize2, Square } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Textarea } from "@/components/ui/textarea";
import { isAppCommandError, type PipelineDef, type StreamEvent } from "@/lib/tauri-client";
import { TerminalFrame } from "@/screens/board/TerminalFrame";
import { MarkdownRenderer } from "@/screens/viewer/MarkdownRenderer";
import { slotDisplayName } from "@/lib/slot-label";

/** Shared run-UI pieces used by both `BaStepPanel` (the `ba` slot, with its
 * import form) and `AgentStepPanel` (every other slot) — extracted so the
 * two panels can never drift on how a run's log/clock/kill looks. */

/** Fallback when `get_config` fails — mirrors
 * `domain::run_summary::DEFAULT_MAX_RETRIES`. The real limit is
 * `ProjectConfig.max_retries` (AC-E6-23, editable in Settings), fetched by
 * each panel when a slot fails. */
export const DEFAULT_MAX_RETRIES = 2;

/** `attempt` is 1-based (the first run isn't a retry) — Retry stays
 * enabled through `attempt <= 1 + maxRetries` (mirrors
 * `domain::run_summary::can_retry`). */
export function canRetry(attempt: number, maxRetries: number): boolean {
  return attempt <= 1 + maxRetries;
}

export function extractErrorMessage(err: unknown): string {
  if (isAppCommandError(err)) return err.message;
  if (err instanceof Error) return err.message;
  return String(err);
}

export function formatElapsed(ms: number): string {
  const totalSeconds = Math.floor(ms / 1000);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes}:${seconds.toString().padStart(2, "0")}`;
}

/** AC-E6-26 — who runs short of input if this slot is skipped: same-stage
 * slots waiting on it via `afterSlots`, plus the successor stage's agents
 * (they consume this stage's output). Empty when nothing downstream
 * depends on it. */
export function computeSkipDependents(def: PipelineDef | null, slotId: string): string[] {
  if (!def) return [];
  const stageIdx = def.stages.findIndex((s) => s.agents.some((a) => a.id === slotId));
  if (stageIdx < 0) return [];
  const stage = def.stages[stageIdx];

  const dependents: string[] = stage.agents
    .filter((a) => a.afterSlots.includes(slotId))
    .map((a) => slotDisplayName(a));

  const successor = def.stages.find((s) => s.dependsOn === stage.id) ?? def.stages[stageIdx + 1];
  if (successor && successor.agents.length > 0) {
    dependents.push(...successor.agents.map((a) => slotDisplayName(a)));
  }
  return Array.from(new Set(dependents));
}

interface WaitingInputPanelProps {
  /** Agent's question — real markdown from the run, not a one-liner. */
  question: string | undefined;
  /** Shown in the header so it's clear who is asking. */
  agentLabel: string;
  value: string;
  onChange: (value: string) => void;
  onSend: () => void;
  /** `true` while this run has not auto-opened the modal yet. The flag lives
   * in the parent, not here: this panel unmounts between two questions (it
   * renders only for `waiting-input`, and the status passes through
   * `running` in between), so local state could never remember. */
  autoOpen?: boolean;
  /** Spends the run's single auto-open, so the run's SECOND question opens
   * only when the user asks for it. */
  onAutoOpened?: () => void;
}

/** The question itself. Shared by the inline block and the expanded modal so
 * the two can't drift on how an agent's markdown renders. */
function QuestionBody({ question }: { question: string | undefined }) {
  if (!question) {
    return <p className="text-sm text-muted-foreground">(Không có nội dung câu hỏi)</p>;
  }
  return <MarkdownRenderer content={question} />;
}

interface AnswerFormProps {
  value: string;
  rows: number;
  onChange: (value: string) => void;
  onSend: () => void;
}

function AnswerForm({ value, rows, onChange, onSend }: AnswerFormProps) {
  return (
    <div className="flex flex-col gap-1.5">
      <Textarea
        value={value}
        rows={rows}
        placeholder="Nhập câu trả lời... (trả lời được nhiều dòng)"
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={(e) => {
          // Enter inserts a newline — these answers are usually several
          // lines — so sending needs the explicit modifier.
          if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
            e.preventDefault();
            onSend();
          }
        }}
      />
      <div className="flex items-center justify-between gap-2">
        <span className="text-xs text-muted-foreground">⌘/Ctrl + Enter để gửi</span>
        <Button size="sm" onClick={onSend} disabled={!value.trim()}>
          Gửi câu trả lời
        </Button>
      </div>
    </div>
  );
}

/**
 * The "agent is waiting for an answer" block, shared by every panel that
 * can host a run (`AgentStepPanel`, `BaStepPanel`).
 *
 * Agents ask real questions — the first `user-signup` run came back with
 * headings, a table and four numbered items. That was previously rendered
 * as raw text inside a `<p>`, and answered through a single-line `<input>`.
 * So: render the question as markdown in its own bounded scroll area (a
 * long question must not push the answer box off screen), and answer in a
 * textarea where a multi-part reply actually fits.
 *
 * That bounded area is still far too small to read in place: it sits inside
 * `ActionPanel`'s own scroll region, which is 42% of a one-third column, so
 * a question with a table arrives as a ~120px box with a nested scrollbar.
 * Hence the expand button and the modal — the same escape hatch `PreviewBox`
 * gives the gate panels, which have exactly this problem.
 */
export function WaitingInputPanel({
  question,
  agentLabel,
  value,
  onChange,
  onSend,
  autoOpen = false,
  onAutoOpened,
}: WaitingInputPanelProps) {
  const [expanded, setExpanded] = useState(false);
  // `StrictMode` runs mount effects twice in dev; the guard keeps the
  // auto-open a single event either way.
  const autoOpenHandled = useRef(false);

  useEffect(() => {
    if (autoOpenHandled.current) return;
    autoOpenHandled.current = true;
    if (!autoOpen || !question) return;
    setExpanded(true);
    onAutoOpened?.();
    // Mount-only: a question arriving later means a new mount, and whether
    // this run has spent its auto-open is the parent's to decide.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function sendFromModal() {
    onSend();
    setExpanded(false);
  }

  return (
    <div className="flex flex-col gap-3 rounded-lg border border-yellow-500/40 p-3">
      <div className="flex items-center gap-2">
        <CircleHelp className="size-4 shrink-0 text-warning" aria-hidden="true" />
        <span className="min-w-0 flex-1 truncate text-sm font-medium">
          {agentLabel} đang chờ bạn trả lời
        </span>
        <Button
          variant="ghost"
          size="icon-sm"
          onClick={() => setExpanded(true)}
          disabled={!question}
          aria-label="Mở rộng để đọc và trả lời"
          title="Mở rộng để đọc và trả lời"
        >
          <Maximize2 />
        </Button>
      </div>

      <div className="max-h-80 overflow-y-auto rounded-md border border-border bg-muted/30 px-3 py-2">
        <QuestionBody question={question} />
      </div>

      <AnswerForm value={value} rows={4} onChange={onChange} onSend={onSend} />

      <Dialog open={expanded} onOpenChange={setExpanded}>
        <DialogContent className="flex h-[85vh] max-w-4xl flex-col overflow-hidden sm:max-w-4xl">
          <DialogHeader className="pr-8">
            <DialogTitle className="truncate">{agentLabel} đang chờ bạn trả lời</DialogTitle>
            <DialogDescription className="text-xs">
              Đọc câu hỏi đầy đủ rồi trả lời ngay tại đây — câu trả lời dùng chung với ô nhập ở panel.
            </DialogDescription>
          </DialogHeader>

          <div className="min-h-0 flex-1 overflow-y-auto rounded-lg border border-border bg-muted/30 px-4 py-3">
            <QuestionBody question={question} />
          </div>

          <div className="shrink-0">
            <AnswerForm value={value} rows={6} onChange={onChange} onSend={sendFromModal} />
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}

export interface LogLine {
  id: string;
  text: string;
  muted?: boolean;
  isError?: boolean;
}

let nextLineId = 0;

/** A hand-written log line (e.g. "— Đã gửi câu trả lời: ..."), sharing the
 * same id counter as parsed lines so keys never collide. */
export function manualLogLine(text: string): LogLine {
  return { id: `${nextLineId++}`, text, muted: true };
}

/** "This path isn't there" — an agent looking for something optional, not
 * a failure. Matched on the CLI's own wording for a missing file and on
 * `EISDIR` (reading a directory as a file). */
export function isMissingPathError(content: string): boolean {
  return /file does not exist|no such file|EISDIR/i.test(content);
}

/** Turns one `StreamEvent` into a displayable log line — thinking-token
 * progress and raw system/unrecognized noise are filtered out entirely. */
export function toLogLine(event: StreamEvent): LogLine | null {
  switch (event.kind) {
    case "sessionStarted":
      return { id: `${nextLineId++}`, text: `▶ Bắt đầu (model: ${event.model})`, muted: true };
    case "assistantThinking":
      return { id: `${nextLineId++}`, text: `💭 ${event.text}`, muted: true };
    case "assistantText":
      return { id: `${nextLineId++}`, text: event.text };
    case "toolCall":
      return {
        id: `${nextLineId++}`,
        text: `🔧 ${event.toolName}(${JSON.stringify(event.input)})`,
        muted: true,
      };
    case "toolResult": {
      // Agents legitimately probe for optional files — reading a kit
      // context file that this project doesn't ship, or checking whether an
      // artifact already exists before writing it. Those come back as tool
      // errors, and painting them red made a perfectly healthy run look
      // broken (observed on the first `user-signup` run). Show them, but
      // don't cry wolf.
      const benign = event.isError && isMissingPathError(event.content);
      return {
        id: `${nextLineId++}`,
        text: `${event.isError ? (benign ? "·" : "✗") : "✓"} ${event.content}`,
        muted: !event.isError || benign,
        isError: event.isError && !benign,
      };
    }
    case "thinkingProgress":
    case "runFinished":
    case "unrecognized":
      return null;
  }
}

interface LiveLogViewProps {
  title: string;
  lines: LogLine[];
  elapsedMs: number;
  /** AC-E2-07/AC-E6-19 — app-side estimate, `null` until a model is known
   * or when the model doesn't match a known pricing tier. Always labeled
   * as an estimate — never presented as the exact figure the terminal
   * `result` line will eventually report. */
  estimatedCostUsd: number | null;
  onKill: () => void;
  /** Extra control rendered next to Kill (e.g. `BaStepPanel`'s Reset,
   * which needs to be reachable even while a run is live). `undefined` for
   * every other caller — this panel is otherwise identical for all slots. */
  extraAction?: ReactNode;
}

export function LiveLogView({
  title,
  lines,
  elapsedMs,
  estimatedCostUsd,
  onKill,
  extraAction,
}: LiveLogViewProps) {
  const virtuosoRef = useRef<VirtuosoHandle>(null);

  useEffect(() => {
    if (lines.length > 0) {
      virtuosoRef.current?.scrollToIndex({ index: lines.length - 1, behavior: "auto" });
    }
  }, [lines.length]);

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center gap-2">
        <Badge variant="secondary">⏱ {formatElapsed(elapsedMs)}</Badge>
        {estimatedCostUsd !== null && (
          <Badge variant="secondary" title="Ước tính từ thinking token — không phải số chính xác">
            ~${estimatedCostUsd.toFixed(4)} (ước tính)
          </Badge>
        )}
        <Button variant="destructive" size="sm" onClick={onKill}>
          <Square />
          Kill
        </Button>
        {extraAction}
      </div>
      <TerminalFrame title={title}>
        <div className="h-[28rem]">
          <Virtuoso
            ref={virtuosoRef}
            style={{ height: "100%" }}
            data={lines}
            itemContent={(_index, line) => (
              <div
                className={`px-3 py-0.5 font-mono text-xs whitespace-pre-wrap ${
                  line.isError
                    ? "text-red-400"
                    : line.muted
                      ? "text-zinc-500"
                      : "text-zinc-100"
                }`}
              >
                {line.text}
              </div>
            )}
          />
        </div>
      </TerminalFrame>
    </div>
  );
}
