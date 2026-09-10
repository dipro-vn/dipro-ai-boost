import { useEffect, useMemo, useState } from "react";
import { open } from "@tauri-apps/plugin-dialog";
import { FolderOpen, RotateCcw, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import {
  commands,
  type AgentSlot,
  type ImportPreview,
  type NodeState,
  type PipelineDef,
  type RunSummary,
} from "@/lib/tauri-client";
import { onAgentLogLine, onAgentRunFinished } from "@/lib/events";
import { slotDisplayName } from "@/lib/slot-label";
import { estimateThinkingCostUsd } from "@/lib/pricing";
import { agentDraftKey, emptyAgentDraft, useAppStore } from "@/state/app-store";
import { useRunConsoleStore } from "@/state/run-console-store";
import {
  canRetry,
  computeSkipDependents,
  DEFAULT_MAX_RETRIES,
  extractErrorMessage,
  LiveLogView,
  manualLogLine,
  toLogLine,
  WaitingInputPanel,
  type LogLine,
} from "@/screens/board/agent-run-shared";
import { ArtifactModal } from "@/screens/board/ArtifactModal";
import { ArtifactSummary } from "@/screens/board/ArtifactSummary";
import { TerminalFrame } from "@/screens/board/TerminalFrame";

/**
 * Names every copied file explicitly instead of just pointing at the
 * folder. `ba-agent`'s declared toolset has no directory-listing tool that
 * works without the tilth MCP server, so a folder path alone made it `Read`
 * the directory (EISDIR) and then guess file names until it gave up —
 * observed on the first real `user-signup` run. Mirrors the same
 * list-the-real-files approach `build_backend_agent_prompt` uses in Rust.
 */
/** The 4 platforms `ba-agent.md` Bước 2b câu 0 allows, with the viewport
 * each one pins Figma Output 3 and `## Responsive Requirements` to. The kit
 * calls these "CHUẨN CỨNG (không tự đổi)", so they are reproduced verbatim
 * — a 390×844 here would silently contradict the agent's own table. */
export const TARGET_PLATFORMS = [
  { value: "Mobile app", viewport: "375×812" },
  { value: "Web app", viewport: "375×812" },
  { value: "Website", viewport: "1440×1024" },
  { value: "iPad/Tablet", viewport: "1024×768" },
] as const;

/** Only a Figma **Design** file can host Outputs 1-3: `/board/` is FigJam
 * (no real viewport, so Output 3's phone mockups cannot be to spec) and
 * `/file/` is the legacy URL shape. Blank is not invalid here — it just
 * means the run goes ahead without Outputs 1-3. */
export function isFigmaDesignPageUrl(url: string): boolean {
  const trimmed = url.trim();
  if (trimmed === "") return false;
  try {
    const parsed = new URL(trimmed);
    return (
      /(^|\.)figma\.com$/.test(parsed.hostname) && parsed.pathname.startsWith("/design/")
    );
  } catch {
    return false;
  }
}

export function buildBaPrompt(
  /** `null` when the user gave no requirements folder — the whole
   * requirement then lives in `context`. */
  copiedPath: string | null,
  files: string[],
  context: string,
  figmaUrl: string,
  targetPlatform: string,
): string {
  const trimmedContext = context.trim();
  const fileList = files.map((file) => `- ${copiedPath}/${file}`).join("\n");
  const viewport = TARGET_PLATFORMS.find((p) => p.value === targetPlatform)?.viewport;
  const trimmedUrl = figmaUrl.trim();
  // Two sources, either of which can be the only one. Say which case this
  // is up front: told to "analyse the copied input" with no folder, the
  // agent goes looking for files that do not exist instead of reading the
  // text it was given.
  const requirement = copiedPath
    ? [
        "Phân tích input đã được copy sẵn tại thư mục sau và thực hiện đúng quy trình của bạn:",
        copiedPath,
        "",
        files.length > 0
          ? `Danh sách file trong thư mục đó (đường dẫn tuyệt đối, đọc từng file bằng Read):\n${fileList}`
          : "(Thư mục này không có file nào đọc được.)",
      ].join("\n")
    : "Phân tích yêu cầu dưới đây và thực hiện đúng quy trình của bạn.\nNgười dùng KHÔNG cung cấp folder tài liệu — toàn bộ mô tả yêu cầu nằm ở mục \"Mô tả yêu cầu từ người dùng\" bên dưới. KHÔNG có file nào để đọc thêm, đừng đi tìm.";
  return [
    requirement,
    // Bước 2b câu 0 / 0.5 của ba-agent.md là hai câu hỏi BẮT BUỘC, nhưng
    // run này chạy headless — không ai trả lời được. Người dùng đã trả lời
    // sẵn ở panel, nên đưa thẳng câu trả lời vào thay vì để agent hỏi.
    `\nFIGMA_OUTPUT_URL (Bước 2b câu 0.5 — user đã cung cấp, KHÔNG hỏi lại, KHÔNG tự chọn file/page Figma khác, KHÔNG tự tạo page mới):\n${
      trimmedUrl !== ""
        ? trimmedUrl
        : "(Chưa có — BỎ QUA Output 1-3, ghi `❌ Skipped — user không cung cấp Figma URL` vào 3 row đó của `## BA Deliverables`, vẫn làm Output 0/4/5.)"
    }`,
    `\nTARGET_PLATFORM (Bước 2b câu 0 — KHÔNG tự suy diễn):\n${targetPlatform}${
      viewport ? ` — viewport ${viewport}` : ""
    }`,
    // Same text, different role: with a folder it supplements the files;
    // without one it IS the requirement, and mislabelling it "bối cảnh
    // thêm" would invite the agent to treat it as an aside.
    trimmedContext
      ? `\n${copiedPath ? "Bối cảnh thêm từ người dùng" : "Mô tả yêu cầu từ người dùng"}:\n${trimmedContext}`
      : "",
  ].join("\n");
}

interface ImportFormProps {
  feature: string;
  primary: boolean;
  onStart: (prompt: string) => void;
  disabled?: boolean;
}

/** The BA step's input form — the feature is already fixed to whichever
 * step this drawer belongs to, so (unlike the original standalone Import
 * Input screen) there is no separate feature-name field.
 *
 * Both requirement sources are optional individually and at least one is
 * mandatory together: a folder of documents to import, a free-text
 * description, or both. Neither the folder picker nor the text box may be
 * the only supported way in — a requirement that lives in someone's head is
 * as legitimate an input as one that lives in a folder of `.docx`.
 *
 * `sourceFolder`/`context` live in the global store as a draft (keyed by
 * feature, slot fixed to `"ba"`) instead of local `useState`, so navigating
 * away (e.g. to Settings) and back does not lose what the user already
 * typed — only an explicit clear or a successful submit does. */
function ImportForm({ feature, primary, onStart, disabled = false }: ImportFormProps) {
  const draft = useAppStore((s) => s.agentDrafts[agentDraftKey(feature, "ba")]) ?? emptyAgentDraft;
  const setAgentDraft = useAppStore((s) => s.setAgentDraft);
  const clearAgentDraft = useAppStore((s) => s.clearAgentDraft);
  const sourceFolder = draft.sourceFolder;
  const context = draft.context;
  const figmaUrl = draft.figmaUrl;
  const targetPlatform = draft.targetPlatform;
  const [preview, setPreview] = useState<ImportPreview | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewError, setPreviewError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  async function runPreview(path: string) {
    setPreview(null);
    setPreviewError(null);
    setPreviewLoading(true);
    try {
      const result = await commands.previewImport(path);
      setPreview(result);
    } catch (err) {
      setPreviewError(extractErrorMessage(err));
    } finally {
      setPreviewLoading(false);
    }
  }

  // Re-derives `preview` (not itself part of the draft — it's data fetched
  // from `sourceFolder`, not something the user typed) when a draft folder
  // survives a remount, so a restored `sourceFolder` doesn't leave Run
  // disabled behind a preview that looks like it was never fetched.
  useEffect(() => {
    if (draft.sourceFolder.trim() !== "") {
      runPreview(draft.sourceFolder);
    }
    // Only on mount — `browse()` re-fetches on its own for every later pick.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function browse() {
    const selected = await open({ directory: true, multiple: false });
    if (typeof selected !== "string") return;
    setAgentDraft(feature, "ba", { sourceFolder: selected });
    await runPreview(selected);
  }

  const folderChosen = sourceFolder.trim() !== "";
  const folderHasFiles = preview !== null && preview.included.length > 0;
  // The folder is optional, but SOMETHING has to describe the requirement:
  // either readable files or the text box. A folder that was picked yet
  // yields nothing still blocks — the user meant to use it, and silently
  // falling back to the text box would hide the mistake.
  const hasRequirementInput = folderChosen ? folderHasFiles : context.trim() !== "";

  // Cả platform lẫn Figma URL đều gate: ba-agent.md bắt DỪNG khi chưa biết
  // platform, và Output 1-3 phải vẽ vào đúng page user chỉ định — run headless
  // không có ai để hỏi cả hai thứ đó. Đi kèm gate MCP Figma ghi-được bên Rust:
  // có URL mà không có server vẽ được thì cũng vô nghĩa.
  const canSubmit =
    !disabled &&
    hasRequirementInput &&
    targetPlatform !== "" &&
    isFigmaDesignPageUrl(figmaUrl) &&
    !submitting;

  function clearFolder() {
    setAgentDraft(feature, "ba", { sourceFolder: "" });
    setPreview(null);
    setPreviewError(null);
  }

  async function handleRun() {
    if (!canSubmit) return;
    setSubmitting(true);
    setSubmitError(null);
    try {
      // No folder means nothing to copy: skip the import entirely rather
      // than importing an empty selection. `feature_dir` — the agent's cwd —
      // already exists either way, `create_feature_dir` made it.
      const run = folderChosen ? await commands.importFolder(sourceFolder, feature) : null;
      onStart(
        buildBaPrompt(
          run?.copiedPath ?? null,
          run?.files ?? [],
          context,
          figmaUrl,
          targetPlatform,
        ),
      );
      clearAgentDraft(feature, "ba");
    } catch (err) {
      setSubmitError(extractErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-col gap-1.5">
        <Label htmlFor={`source-folder-${feature}`}>
          Folder chứa mô tả yêu cầu (tuỳ chọn)
        </Label>
        <div className="flex gap-2">
          <Input
            id={`source-folder-${feature}`}
            value={sourceFolder}
            readOnly
            placeholder="Chưa chọn folder"
            className="font-mono text-xs"
          />
          <Button type="button" variant="outline" size="sm" onClick={browse}>
            <FolderOpen />
            Chọn
          </Button>
          {/* Optional means it must be undoable — without this a folder
              picked by mistake can never be taken back. */}
          {folderChosen && (
            <Button type="button" variant="ghost" size="sm" onClick={clearFolder}>
              <X />
              Bỏ chọn
            </Button>
          )}
        </div>
        {!folderChosen && (
          <p className="text-xs text-muted-foreground">
            Không chọn cũng được — khi đó BA phân tích dựa trên phần mô tả bạn viết bên dưới.
          </p>
        )}
      </div>

      {previewLoading && <p className="text-xs text-muted-foreground">Đang quét folder...</p>}

      {previewError && (
        <Alert variant="destructive">
          <AlertTitle>Không đọc được folder</AlertTitle>
          <AlertDescription>{previewError}</AlertDescription>
        </Alert>
      )}

      {preview && preview.included.length === 0 && (
        <Alert variant="destructive">
          <AlertTitle>Folder rỗng hoặc không có file đọc được</AlertTitle>
          <AlertDescription>
            Không có file nào sẽ được import. Chọn folder khác, hoặc bấm "Bỏ chọn" rồi mô tả
            yêu cầu trực tiếp bên dưới.
          </AlertDescription>
        </Alert>
      )}

      {preview && preview.included.length > 0 && (
        <div className="flex flex-col gap-2">
          <div className="flex items-center gap-2">
            <Badge variant="secondary">{preview.included.length} file sẽ đọc</Badge>
            {preview.excluded.length > 0 && (
              <Badge variant="outline">{preview.excluded.length} file bị bỏ qua</Badge>
            )}
          </div>
          <ScrollArea className="h-32 rounded-lg border border-border p-2">
            <div className="flex flex-col gap-1 font-mono text-xs">
              {preview.included.map((path) => (
                <div key={path}>{path}</div>
              ))}
              {preview.excluded.map((f) => (
                <div key={f.relativePath} className="text-muted-foreground line-through" title={f.reason}>
                  {f.relativePath}
                </div>
              ))}
            </div>
          </ScrollArea>
        </div>
      )}

      <div className="flex flex-col gap-1.5">
        <Label htmlFor={`platform-${feature}`}>Platform đích</Label>
        <select
          id={`platform-${feature}`}
          value={targetPlatform}
          onChange={(e) => setAgentDraft(feature, "ba", { targetPlatform: e.target.value })}
          className="rounded-lg border border-input bg-transparent px-3 py-2 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
        >
          <option value="">— chọn platform —</option>
          {TARGET_PLATFORMS.map((p) => (
            <option key={p.value} value={p.value}>
              {p.value} — {p.viewport}
            </option>
          ))}
        </select>
        <p className="text-xs text-muted-foreground">
          Quyết định viewport của mockup Figma và bảng Responsive Requirements. BA không được tự
          đoán, nên phải chọn trước khi chạy.
        </p>
      </div>

      <div className="flex flex-col gap-1.5">
        <Label htmlFor={`figma-url-${feature}`}>Figma Design page</Label>
        <Input
          id={`figma-url-${feature}`}
          value={figmaUrl}
          onChange={(e) => setAgentDraft(feature, "ba", { figmaUrl: e.target.value })}
          placeholder="https://www.figma.com/design/..."
          className="font-mono text-xs"
        />
        {figmaUrl.trim() === "" ? (
          <p className="text-xs text-muted-foreground">
            Output 1-3 được vẽ thẳng vào page này. App cũng kiểm tra MCP Figma ghi được ngay
            trước khi chạy — thiếu là node bị chặn kèm lệnh cài.
          </p>
        ) : !isFigmaDesignPageUrl(figmaUrl) ? (
          <p className="text-xs text-warning">
            Link này không phải Figma Design (`/design/`). FigJam (`/board/`) và link cũ
            (`/file/`) không đủ chuẩn viewport cho mockup Output 3.
          </p>
        ) : null}
      </div>

      {/* One field, two roles — the label follows whichever the folder
          leaves it. Calling it "bối cảnh thêm" while it is the only input
          would read as optional when it is the requirement. */}
      <div className="flex flex-col gap-1.5">
        <Label htmlFor={`context-${feature}`}>
          {folderChosen ? "Bối cảnh thêm (tuỳ chọn)" : "Mô tả yêu cầu"}
        </Label>
        <textarea
          id={`context-${feature}`}
          value={context}
          onChange={(e) => setAgentDraft(feature, "ba", { context: e.target.value })}
          placeholder={
            folderChosen
              ? "Ghi chú thêm cho BA Agent, để trống vẫn chạy được"
              : "Mô tả yêu cầu nghiệp vụ cần phân tích — actor, vấn đề, luồng chính..."
          }
          rows={folderChosen ? 3 : 6}
          className="rounded-lg border border-input bg-transparent px-3 py-2 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
        />
        {!folderChosen && context.trim() === "" && (
          <p className="text-xs text-muted-foreground">
            Chưa chọn folder thì đây là đầu vào duy nhất của BA — cần điền để chạy được.
          </p>
        )}
      </div>

      {submitError && (
        <Alert variant="destructive">
          <AlertTitle>Không tạo được run</AlertTitle>
          <AlertDescription>{submitError}</AlertDescription>
        </Alert>
      )}

      <Button disabled={!canSubmit} onClick={handleRun} variant={primary ? "default" : "outline"}>
        {submitting ? "Đang chuẩn bị..." : "Chạy BA Agent"}
      </Button>
    </div>
  );
}

interface BaStepPanelProps {
  feature: string;
  agent: AgentSlot;
  /** User-set alias for this slot, if any — see `@/lib/slot-label`. */
  nickname?: string;
  nodeState: NodeState | undefined;
  /** For AC-E6-26's skip-dependents warning. */
  pipelineDef: PipelineDef | null;
  /** The Board renders live output in AgentConsoleDock. */
  showConsole?: boolean;
  /** Project setup is completed through the external `/init-kit` handoff. */
  projectReady: boolean;
}

/**
 * The only step MVP2 can actually run. Consolidates what used to be 3
 * separate screens (Import Input, Log Console, Node Detail) into one
 * contextual drawer panel, driven mostly by `nodeState.status` (already
 * polled/pushed by the Board) rather than its own navigation state:
 *
 * - `idle` -> import form
 * - a run started this session and hasn't finished -> live log
 * - `waiting-input` -> question + answer box (works even after an app
 *   restart, since the backend resumes from the persisted session id)
 * - `failed` (a timeout also lands here, with `detail` saying so — there is
 *   no separate `NodeStatus` for it) -> error + retry-limit-aware re-import
 * - `done` / `done-incomplete` -> artifacts, with re-import collapsed
 */
export function BaStepPanel({
  feature,
  agent,
  nickname,
  nodeState,
  pipelineDef,
  projectReady,
  showConsole = true,
}: BaStepPanelProps) {
  const [liveActive, setLiveActive] = useState(false);
  const [liveLines, setLiveLines] = useState<LogLine[]>([]);
  const [startedAt, setStartedAt] = useState(() => Date.now());
  const [now, setNow] = useState(() => Date.now());
  const [startError, setStartError] = useState<string | null>(null);
  const [answer, setAnswer] = useState("");
  /** See `AgentStepPanel` — one auto-open of the question modal per run. */
  const [questionAutoOpened, setQuestionAutoOpened] = useState(false);
  const clearAgentDraft = useAppStore((s) => s.clearAgentDraft);
  const clearConsole = useRunConsoleStore((s) => s.clearConsole);
  /** Reset button's two-step confirm — only needed while there's something
   * live to lose (a running process, or a paused session waiting for an
   * answer). See `handleReset`. */
  const [confirmReset, setConfirmReset] = useState(false);
  /** Forces the idle import form regardless of `status` once Reset has run
   * — cleared again the moment a new run actually starts (`startRun`), so
   * that run's own status transitions render normally afterward. */
  const [forceReimport, setForceReimport] = useState(false);

  // Switching feature keeps this instance mounted, so the new feature's run
  // must not inherit a spent auto-open (or a spent Reset override).
  useEffect(() => {
    setQuestionAutoOpened(false);
    setForceReimport(false);
    setConfirmReset(false);
  }, [feature, agent.id]);
  const [refreshKey, setRefreshKey] = useState(0);
  /** Artifact shown in the read-in-place modal; null = closed. */
  const [modalArtifact, setModalArtifact] = useState<string | null>(null);
  const [lastSummary, setLastSummary] = useState<RunSummary | null>(null);
  const [showReimport, setShowReimport] = useState(false);
  // AC-E2-07/AC-E6-19 — running cost estimate for the current live run.
  // `sessionModel` comes from the `sessionStarted` event; `thinkingTokens`
  // accumulates `estimatedTokensDelta` from every `thinkingProgress` event
  // (never `estimatedTokens` alone — that resets per thinking block, see
  // `stream_parser.rs`'s doc comment on the field).
  const [sessionModel, setSessionModel] = useState<string | null>(null);
  const [thinkingTokens, setThinkingTokens] = useState(0);

  useEffect(() => {
    let cancelled = false;
    const unlistenLine = showConsole
      ? onAgentLogLine((payload) => {
          if (cancelled || payload.feature !== feature || payload.slot !== agent.id) return;
          const event = payload.event;
          if (event.kind === "sessionStarted") setSessionModel(event.model);
          if (event.kind === "thinkingProgress") {
            const delta = event.estimatedTokensDelta;
            setThinkingTokens((prev) => prev + delta);
          }
          const line = toLogLine(event);
          if (line) setLiveLines((prev) => [...prev, line]);
        })
      : Promise.resolve(() => undefined);
    const unlistenFinished = onAgentRunFinished((payload) => {
      if (cancelled || payload.feature !== feature || payload.slot !== agent.id) return;
      setLiveActive(false);
      setLastSummary(payload.summary);
      setRefreshKey((k) => k + 1);
    });
    return () => {
      cancelled = true;
      unlistenLine.then((f) => f());
      unlistenFinished.then((f) => f());
    };
  }, [feature, agent.id, showConsole]);

  // AC-E2-20 — re-hydrate the log console from `log.jsonl` on disk when the
  // panel mounts, so switching tabs or reopening the app doesn't lose a
  // prior run's history the way pure React state would. Only seeds when
  // nothing has streamed in live yet, so it never clobbers an active run.
  useEffect(() => {
    if (!showConsole) return;
    let cancelled = false;
    commands
      .getRunLog(feature, agent.id)
      .then((events) => {
        if (cancelled) return;
        setLiveLines((prev) => {
          if (prev.length > 0) return prev;
          return events
            .map(toLogLine)
            .filter((line): line is LogLine => line !== null);
        });
      })
      .catch(() => {
        // Best-effort — no persisted log yet, or the read failed; live
        // streaming behavior is unaffected either way.
      });
    return () => {
      cancelled = true;
    };
  }, [feature, agent.id, showConsole]);

  useEffect(() => {
    if (!liveActive) return;
    const id = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(id);
  }, [liveActive]);

  // Retry-limit check — only needed once the slot has actually failed.
  // `NodeStatus` has no separate "timeout" value — a timed-out run maps to
  // `failed` with `detail` saying so (see `domain::run_summary::RunOutcome`
  // vs `NodeStatus`), so checking `"failed"` alone covers both cases.
  const [attempt, setAttempt] = useState<number | null>(null);
  // AC-E2-13 — the failed run's original prompt, when the backend has one
  // persisted, so Retry can replay it directly instead of re-showing
  // `ImportForm`. `null` while loading or when there's genuinely nothing to
  // replay (no prior run persisted, or it predates this field).
  const [retryPrompt, setRetryPrompt] = useState<string | null>(null);
  const [maxRetries, setMaxRetries] = useState(DEFAULT_MAX_RETRIES);
  const status = nodeState?.status ?? "idle";
  /** What the status-driven branches below actually render — pinned to
   * `"idle"` after Reset regardless of the real backend `status`, so a
   * failed/interrupted/waiting-input/done node shows the blank import form
   * instead of picking back up where it left off. */
  const effectiveStatus = forceReimport ? "idle" : status;
  useEffect(() => {
    if (status !== "failed" && status !== "interrupted") {
      setAttempt(null);
      setRetryPrompt(null);
      setConfirmRetry(false);
      setConfirmSkip(false);
      return;
    }
    let cancelled = false;
    commands
      .getRunSummary(feature, agent.id)
      .then((summary) => {
        if (cancelled) return;
        setAttempt(summary?.attempt ?? 1);
        setRetryPrompt(summary?.prompt ?? null);
      })
      .catch(() => {
        if (!cancelled) setAttempt(1);
      });
    // AC-E6-23 — the retry ceiling comes from Settings, not a constant.
    commands
      .getConfig()
      .then((config) => {
        if (!cancelled) setMaxRetries(config.max_retries);
      })
      .catch(() => {
        // Fallback constant already in state.
      });
    return () => {
      cancelled = true;
    };
  }, [feature, agent.id, status, refreshKey]);

  const [confirmRetry, setConfirmRetry] = useState(false);
  const [confirmSkip, setConfirmSkip] = useState(false);
  const skipDependents = computeSkipDependents(pipelineDef, agent.id);

  // AC-E6-24 — a slot that already produced an artifact warns about
  // overwriting before rerunning (two-step confirm).
  async function handleRetryWithConfirm(prompt: string) {
    if (!confirmRetry) {
      const hasArtifacts = await commands
        .getNodeDetail(feature, agent.id)
        .then((d) => d.artifacts.length > 0)
        .catch(() => false);
      if (hasArtifacts) {
        setConfirmRetry(true);
        return;
      }
    }
    setConfirmRetry(false);
    startRun(prompt);
  }

  async function handleSkip() {
    // AC-E6-26 — two-step confirm naming who runs short of input.
    if (!confirmSkip) {
      setConfirmSkip(true);
      return;
    }
    setConfirmSkip(false);
    setStartError(null);
    try {
      await commands.skipRun(feature, agent.id);
    } catch (err) {
      setStartError(extractErrorMessage(err));
    }
  }

  function startRun(prompt: string) {
    setLiveActive(true);
    setLiveLines([]);
    setQuestionAutoOpened(false);
    setSessionModel(null);
    setThinkingTokens(0);
    setStartError(null);
    setStartedAt(Date.now());
    setNow(Date.now());
    // This run's own status transitions (waiting-input/failed/done...) must
    // render normally from here on, not stay pinned to the Reset override.
    setForceReimport(false);
    commands.startRun(feature, agent.id, prompt).catch((err) => {
      setLiveActive(false);
      setStartError(extractErrorMessage(err));
    });
  }

  /** Abandons whatever this slot is currently doing and returns to a blank
   * import form + empty console, ready to start over. Always attempts a
   * kill first — `killRun` is a safe no-op when nothing is running (see its
   * own doc comment), so this also covers a run that's live server-side but
   * that this panel instance's local `liveActive` hasn't caught up to yet
   * (e.g. right after mount). Two-step confirm only when that would
   * actually discard something live — a paused run waiting for an answer,
   * or one still streaming. */
  async function handleReset() {
    const needsConfirm = liveActive || status === "waiting-input" || status === "running";
    if (needsConfirm && !confirmReset) {
      setConfirmReset(true);
      return;
    }
    setConfirmReset(false);
    try {
      await commands.killRun(feature, agent.id);
    } catch {
      // Best-effort — the run may have already finished on its own.
    }
    setLiveActive(false);
    setLiveLines([]);
    setStartError(null);
    setAnswer("");
    setQuestionAutoOpened(false);
    setSessionModel(null);
    setThinkingTokens(0);
    setLastSummary(null);
    setConfirmRetry(false);
    setConfirmSkip(false);
    setAttempt(null);
    setRetryPrompt(null);
    setShowReimport(false);
    clearAgentDraft(feature, "ba");
    clearConsole(feature, agent.id);
    setForceReimport(true);
  }

  // AC-E6-05 — continue the interrupted run in its original session. A
  // backend refusal (e.g. no session id survived) lands in startError with
  // its own suggestion to Re-run (AC-E6-06).
  async function handleResume() {
    setLiveActive(true);
    setLiveLines([manualLogLine("— Resume phiên bị gián đoạn...")]);
    setQuestionAutoOpened(false);
    setSessionModel(null);
    setThinkingTokens(0);
    setStartError(null);
    setStartedAt(Date.now());
    setNow(Date.now());
    try {
      await commands.resumeRun(feature, agent.id);
    } catch (err) {
      setLiveActive(false);
      setStartError(extractErrorMessage(err));
    }
  }

  async function handleKill() {
    try {
      await commands.killRun(feature, agent.id);
    } catch {
      // Best-effort — the run may have already finished on its own.
    }
  }

  async function handleSendAnswer() {
    if (!answer.trim()) return;
    const toSend = answer.trim();
    setAnswer("");
    setLiveActive(true);
    setLiveLines([manualLogLine(`— Đã gửi câu trả lời: ${toSend}`)]);
    setSessionModel(null);
    setThinkingTokens(0);
    setStartError(null);
    setStartedAt(Date.now());
    setNow(Date.now());
    try {
      await commands.sendClarificationAnswer(feature, agent.id, toSend);
    } catch (err) {
      setLiveActive(false);
      setStartError(extractErrorMessage(err));
    }
  }

  const elapsedMs = useMemo(() => now - startedAt, [now, startedAt]);
  const estimatedCostUsd = useMemo(
    () => (sessionModel ? estimateThinkingCostUsd(sessionModel, thinkingTokens) : null),
    [sessionModel, thinkingTokens],
  );

  // Same button everywhere Reset is reachable (live view + the normal
  // panel) — one definition keeps the label/confirm state from drifting.
  const resetButton = (
    <Button variant="outline" size="sm" onClick={handleReset}>
      <RotateCcw />
      {confirmReset ? "Xác nhận Reset" : "Reset"}
    </Button>
  );

  if (liveActive && showConsole) {
    return (
      <LiveLogView
        title="ba-agent — đang chạy"
        lines={liveLines}
        elapsedMs={elapsedMs}
        estimatedCostUsd={estimatedCostUsd}
        onKill={handleKill}
        extraAction={resetButton}
      />
    );
  }

  return (
    <div className="flex flex-col gap-3">
      <div className="flex justify-end">{resetButton}</div>
      {confirmReset && effectiveStatus === "waiting-input" && (
        <p className="text-xs text-warning">
          Sẽ bỏ câu hỏi đang chờ trả lời và xoá console — nhấn lần nữa để xác nhận.
        </p>
      )}

      {startError && (
        <Alert variant="destructive">
          <AlertTitle>Không chạy được agent</AlertTitle>
          <AlertDescription>{startError}</AlertDescription>
        </Alert>
      )}

      {effectiveStatus === "idle" && (
        <ImportForm feature={feature} primary onStart={startRun} disabled={!projectReady} />
      )}

      {effectiveStatus === "waiting-input" && (
        <WaitingInputPanel
          question={nodeState?.detail}
          agentLabel={slotDisplayName(agent, nickname)}
          value={answer}
          onChange={setAnswer}
          onSend={handleSendAnswer}
          autoOpen={!questionAutoOpened}
          onAutoOpened={() => setQuestionAutoOpened(true)}
        />
      )}

      {effectiveStatus === "failed" && (
        <div className="flex flex-col gap-2 rounded-lg border border-destructive/40 p-3">
          <p className="text-sm text-destructive">
            {nodeState?.detail ?? "Agent kết thúc với lỗi."}
          </p>
          {attempt !== null && !canRetry(attempt, maxRetries) ? (
            <p className="text-xs text-muted-foreground">
              Đã hết số lần thử lại (tối đa {maxRetries} lần thử lại).
            </p>
          ) : retryPrompt ? (
            // AC-E2-13 — replays the exact original input; no re-picking a
            // folder. `ImportForm` only reappears for a run that predates
            // the persisted prompt (or was never actually spawned).
            <>
              {confirmRetry && (
                  <p className="text-xs text-warning">
                  Slot này đã có artifact — chạy lại sẽ ghi đè. Nhấn lần nữa để xác nhận.
                </p>
              )}
              <Button onClick={() => handleRetryWithConfirm(retryPrompt)}>
                {confirmRetry ? "Xác nhận chạy lại (ghi đè artifact)" : "Thử lại"}
              </Button>
            </>
          ) : (
            <ImportForm feature={feature} primary onStart={startRun} disabled={!projectReady} />
          )}
          {confirmSkip && (
            <p className="text-xs text-warning">
              {skipDependents.length > 0
                ? `Bỏ qua slot này thì các agent sau sẽ chạy thiếu đầu vào: ${skipDependents.join(", ")}. Nhấn lần nữa để xác nhận.`
                : "Bỏ qua slot này — pipeline sẽ đi tiếp không có output của nó. Nhấn lần nữa để xác nhận."}
            </p>
          )}
          <Button variant="outline" onClick={handleSkip}>
            {confirmSkip ? "Xác nhận bỏ qua" : "Skip"}
          </Button>
        </div>
      )}

      {effectiveStatus === "interrupted" && (
        <div className="flex flex-col gap-2 rounded-lg border border-amber-500/40 p-3">
          {/* AC-E6-04/05 — distinct from failed: the choice here is Resume
              (same session) vs Re-run (from scratch), not Retry. */}
          <p className="text-sm text-warning">
            {nodeState?.detail ?? "Run bị gián đoạn khi app đóng."}
          </p>
          <Button onClick={handleResume}>Resume (chạy tiếp phiên cũ)</Button>
          {retryPrompt ? (
            <>
              {confirmRetry && (
                  <p className="text-xs text-warning">
                  Slot này đã có artifact — chạy lại từ đầu sẽ ghi đè. Nhấn lần nữa để xác
                  nhận.
                </p>
              )}
              <Button variant="outline" onClick={() => handleRetryWithConfirm(retryPrompt)}>
                {confirmRetry ? "Xác nhận Re-run (ghi đè artifact)" : "Re-run từ đầu"}
              </Button>
            </>
          ) : (
            <ImportForm
              feature={feature}
              primary={false}
              onStart={startRun}
              disabled={!projectReady}
            />
          )}
        </div>
      )}

      <Separator />
      <ArtifactSummary
        feature={feature}
        slotId={agent.id}
        refreshKey={refreshKey}
        onOpenArtifact={setModalArtifact}
      />
      <ArtifactModal path={modalArtifact} onClose={() => setModalArtifact(null)} />

      {!forceReimport && (status === "done" || status === "done-incomplete") && (
        <div className="flex flex-col gap-2">
          <Button variant="outline" size="sm" onClick={() => setShowReimport((v) => !v)}>
            {showReimport ? "Ẩn form import" : "Chạy lại với input khác"}
          </Button>
          {showReimport && (
            <ImportForm
              feature={feature}
              primary={false}
              onStart={startRun}
              disabled={!projectReady}
            />
          )}
        </div>
      )}

      {lastSummary && (
        <p className="text-xs text-muted-foreground">
          Lần chạy gần nhất: ${lastSummary.costUsd.toFixed(4)}
        </p>
      )}

      <Separator />
      {showConsole && liveLines.length > 0 && (
        <TerminalFrame title="ba-agent — log">
          <div className="max-h-80 overflow-y-auto py-1">
            {liveLines.map((line) => (
              <div
                key={line.id}
                className={`px-3 py-0.5 font-mono text-xs whitespace-pre-wrap ${
                  line.isError ? "text-red-400" : line.muted ? "text-zinc-500" : "text-zinc-100"
                }`}
              >
                {line.text}
              </div>
            ))}
          </div>
        </TerminalFrame>
      )}
    </div>
  );
}
