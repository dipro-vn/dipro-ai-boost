import { invoke } from "@tauri-apps/api/core";

/**
 * Structured error shape returned by every Rust command (see
 * `src-tauri/src/error.rs::AppError`). Every command call must go through
 * this file so the frontend never has to guess the error shape.
 */
export interface AppCommandError {
  code: string;
  message: string;
  details?: unknown;
}

export function isAppCommandError(value: unknown): value is AppCommandError {
  return (
    typeof value === "object" &&
    value !== null &&
    "code" in value &&
    "message" in value
  );
}

export type Theme = "light" | "dark";

export interface DetectedPaths {
  agentsRoot: string | null;
  docsRoot: string | null;
  repositoryRoot: string | null;
}

export interface ProjectPaths {
  agentsRoot: string;
  docsRoot: string;
  repositoryRoot: string;
}

export interface EcosystemRepo {
  name: string;
  declaredPath: string;
  /** The Vai trò cell verbatim, notes and all — shown as-is in the
   * Ecosystem table. */
  role: string;
  /** `role` reduced to a role the pipeline can target, or `null` when the
   * cell couldn't be read. Every role decision uses this, never `role`. */
  roleKey: string | null;
  stack: string;
  cloned: boolean;
}

/** Mirrors `store::kit_template::KitGroup` — một nhóm khung kit chưa có
 * trên đĩa. */
export interface KitGroup {
  id: string;
  label: string;
  root: "agentsRoot" | "docsRoot";
  missingCount: number;
  totalCount: number;
}

/** Mirrors `store::kit_template::ScaffoldReport`. `updated` chỉ chứa template
 * nguyên bản được migrate an toàn; file custom luôn nằm trong `skipped`. */
export interface ScaffoldReport {
  created: string[];
  updated: string[];
  skipped: string[];
}

export type ProjectInitStatus = "ready" | "needs-init" | "missing-kit" | "invalid";

export interface ProjectSummary {
  paths: ProjectPaths;
  label: string;
  readOnly: boolean;
  ecosystem: EcosystemRepo[];
  agentsFound: string[];
  warnings: string[];
  missingKit: KitGroup[];
  initStatus: ProjectInitStatus;
  initReasons: string[];
}

export interface RecentProjectEntry extends ProjectPaths {
  label: string;
  lastOpenedAt: string;
}

/** Mirrors `domain::config_file::Model` (`#[serde(rename_all = "lowercase")]`). */
export type AgentModel = "opus" | "sonnet" | "haiku";

/** Mirrors `domain::config_file::PermissionProfile` (`kebab-case`). */
export type AgentPermissionProfile = "read-only" | "write-scoped" | "full";

/** Mirrors `domain::config_file::AgentConfig`. NOTE: unlike every other
 * domain type, `AgentConfig` has NO `camelCase` serde attribute — its
 * on-disk/IPC keys are snake_case (`max_turns`, `newly_discovered`,
 * `timeout_minutes`). Do not "fix" these names here without changing the
 * Rust serde too. */
export interface AgentConfig {
  model: AgentModel;
  max_turns: number;
  permission: AgentPermissionProfile;
  stale: boolean;
  newly_discovered: boolean;
  timeout_minutes: number;
}

/** Mirrors `domain::config_file::ProjectConfig` (same snake_case caveat). */
export interface ProjectConfig {
  agents: Record<string, AgentConfig>;
  /** Display-only aliases keyed by pipeline slot id. Never used for spawn. */
  node_nicknames?: Record<string, string>;
  claude_auth?: ClaudeAuthConfig;
  max_retries: number;
  figma_mcp_server?: string | null;
  /** Absolute path to the `claude` binary, for installs auto-detection
   * cannot find. Empty/absent = auto-detect. */
  claude_cli_path?: string | null;
}

export type ClaudeAuthMode = "cli-default" | "subscription" | "console" | "api-key";

export interface ClaudeAuthConfig {
  mode: ClaudeAuthMode;
  credential_ref?: string | null;
}

export type ClaudeAuthStatusKind =
  | "cli-not-found"
  | "not-authenticated"
  | "subscription"
  | "console"
  | "api-key"
  | "api-key-override"
  | "expired"
  | "unknown";

export interface ClaudeAuthStatus {
  cliAvailable: boolean;
  cliVersion?: string | null;
  /** Which binary the backend resolved — shown so a wrong auto-detection
   * is visible instead of only surfacing as "không tìm thấy CLI". */
  cliPath?: string | null;
  authenticated: boolean;
  method: string;
  account?: string | null;
  organization?: string | null;
  envOverrides: string[];
  configuredMode: ClaudeAuthMode;
  status: ClaudeAuthStatusKind;
  checkedAt: string;
}

/** Mirrors `domain::run_history::RunHistoryRecord`. */
export interface RunHistoryRecord {
  feature: string;
  slot: string;
  /** Actual model used (from the run's SessionStarted event) — absent for
   * runs that never started a session. */
  model?: string | null;
  outcome: RunOutcome;
  /** AC-E6-13 — absent = "không có số liệu", NEVER treat as 0. */
  costUsd?: number | null;
  startedAt: string;
  endedAt: string;
  attempt: number;
}

/** Mirrors `store::mcp_config::McpServer`. */
export interface McpServer {
  name: string;
  kind: "stdio" | "http";
  detail: string;
  figmaCandidate: boolean;
}

/**
 * Mirrors `domain::node_status::NodeStatus`. Only `idle`, `done`, and
 * `done-incomplete` are reachable from MVP1's pure file-system inference —
 * the rest require a live agent runner (MVP2+). Modeled in full now so the
 * contract doesn't change under the frontend later.
 */
export type NodeStatus =
  | "idle"
  | "running"
  | "waiting-input"
  | "done"
  | "done-incomplete"
  | "failed"
  | "blocked"
  | "skipped"
  | "interrupted";

export interface NodeState {
  status: NodeStatus;
  detail?: string;
}

/** Mirrors `agentrun::recovery::OrphanInfo` — a still-live agent process
 * left behind by a previous app instance (AC-E6-10). */
export interface OrphanInfo {
  feature: string;
  slot: string;
  pid: number;
}

/** Mirrors `domain::gate_state::GateStatus` (`#[serde(rename_all =
 * "kebab-case")]`). */
export type GateStatus = "not-ready" | "pending-review" | "approved";

/** Mirrors `domain::gate_state::GateState`. */
export interface GateState {
  status: GateStatus;
  approvedBy?: string | null;
  approvedAt?: string | null;
  missingSections: string[];
}

/** Mirrors `domain::contract_lock::ContractLockStatus`. */
export type ContractLockStatus =
  | "not-ready"
  | "not-applicable"
  | "pending-review"
  | "locked"
  | "violated";

/** Mirrors `domain::contract_lock::ViolationKind`. */
export type ViolationKind = "modified" | "deleted";

/** Mirrors `domain::contract_lock::FileViolation`. */
export interface FileViolation {
  path: string;
  kind: ViolationKind;
  lockedContent: string;
}

/** Mirrors `domain::contract_lock::ViolationEvent`. */
export interface ViolationEvent {
  detectedAt: string;
  files: FileViolation[];
}

/** Mirrors `domain::contract_lock::LockedFileRef` — pre-lock preview,
 * no content (AC-E4-16). */
export interface LockedFileRef {
  path: string;
  checksumSha256: string;
}

/** Mirrors `domain::contract_lock::LockedFile` — inside a persisted
 * `ContractLockRecord` only, content captured directly at lock time. */
export interface LockedFile {
  path: string;
  checksumSha256: string;
  content: string;
}

/** Mirrors `domain::contract_lock::ContractLockRecord`. */
export interface ContractLockRecord {
  lockedAt: string;
  approvedBy: string;
  confirmedRoles: string[];
  files: LockedFile[];
}

/** Mirrors `domain::contract_lock::ContractLockState`. */
export interface ContractLockState {
  status: ContractLockStatus;
  /** AC-E4-08a — every `<repo>/DESIGN.md` path checked while looking for an
   * API Definition table; populated only when `status === "not-ready"`. */
  checkedDesignMdPaths: string[];
  missingColumns: string[];
  /** AC-E4-11b — `true` when `not-applicable` came from the PM clicking skip
   * rather than from an inferred rule; only that one can be undone. */
  manuallySkipped: boolean;
  notApplicableReason?: string | null;
  applicableRoles: string[];
  candidateFiles: LockedFileRef[];
  currentLock?: ContractLockRecord | null;
  violatedFiles: FileViolation[];
  runningOnOldContract: boolean;
}

export interface FeatureState {
  /** Keyed by slot id — see `AgentSlot.id` in `PipelineDef`. */
  nodes: Record<string, NodeState>;
  /** Keyed by gate stage id (e.g. `"S1b_trigger"`, `domain::pipeline_def::gate::TRIGGER`). */
  gates: Record<string, GateState>;
  /** The Contract Lock gate (`domain::pipeline_def::gate::CONTRACT_LOCK`) —
   * `null`/absent before it's ever been computed. */
  contractLock?: ContractLockState | null;
  updatedAt: string;
}

export interface AgentSlot {
  id: string;
  agentName: string;
  /** Display name for this slot — separate from `agentName` because two
   * slots can share one agent file (`qc-design`/`qc-testing` → `qc-agent`).
   * Absent on a `pipeline.json` written before labels existed; read it
   * through `slotDisplayName` in `@/lib/slot-label`, never directly. */
  label?: string | null;
  /** AC-E2-03 — same-stage slots this one waits for (FE/Mobile → backend). */
  afterSlots: string[];
}

export interface StageDef {
  id: string;
  label: string;
  agents: AgentSlot[];
  /** AC-E2-01 — predecessor stage id; absent for the first stage. */
  dependsOn?: string | null;
}

export interface PipelineDef {
  stages: StageDef[];
}

export interface ArtifactRef {
  path: string;
  label: string;
}

export interface NodeDetail {
  artifacts: ArtifactRef[];
  updatedAt?: string;
  /** Absent when no agent run has happened for this slot yet. */
  costUsd?: number;
}

export interface ArtifactContent {
  content: string;
  sizeBytes: number;
  lineCount: number;
}

/** Mirrors `domain::explorer::ExplorerRootEntry`. Usually a single entry
 * ("Project", the common ancestor of all 3 project roots); falls back to
 * one entry per root when they share none. */
export interface ExplorerRootEntry {
  label: string;
  path: string;
}

/** Mirrors `domain::explorer::DirEntry`. `path` is always absolute — feed
 * it straight back into `listDirectory` (expand) or `readArtifact` (open),
 * no relative-path reconstruction needed on this side either. */
export interface DirEntry {
  name: string;
  path: string;
  isDir: boolean;
  isRestricted: boolean;
  canModify: boolean;
}

export interface ExplorerDeletePreview {
  path: string;
  name: string;
  fileCount: number;
  folderCount: number;
  runningSlots: string[];
  lockedFiles: string[];
  protectedPaths: string[];
  symlinkPaths: string[];
}

/** Mirrors `domain::version_ref::VersionSource` (`#[serde(rename_all = "lowercase")]`). */
export type VersionSource = "git" | "snapshot" | "current";

export interface VersionRef {
  id: string;
  label: string;
  source: VersionSource;
  timestamp: string;
}

export interface DiffResult {
  fromContent: string;
  toContent: string;
  source: VersionSource;
}

export interface ExcludedFile {
  relativePath: string;
  reason: string;
}

/** Mirrors `agentrun::stream_parser::StreamEvent` (`#[serde(tag = "kind",
 * rename_all = "camelCase")]`) — one event per parsed `stream-json` line
 * (or content block). `Unrecognized` covers everything not modeled here
 * (hook_* system events, rate_limit_event, future CLI additions) so the
 * Log Console never breaks on an unfamiliar line. */
export type StreamEvent =
  | { kind: "sessionStarted"; sessionId: string; model: string }
  | { kind: "thinkingProgress"; estimatedTokens: number; estimatedTokensDelta: number }
  | { kind: "assistantThinking"; messageId: string; text: string }
  | { kind: "assistantText"; messageId: string; text: string }
  | {
      kind: "toolCall";
      messageId: string;
      toolUseId: string;
      toolName: string;
      input: unknown;
    }
  | { kind: "toolResult"; toolUseId: string; content: string; isError: boolean }
  | {
      kind: "runFinished";
      isError: boolean;
      totalCostUsd: number;
      sessionId: string;
      stopReason: string | null;
    }
  | { kind: "unrecognized"; rawType: string };

/** Mirrors `domain::run_summary::RunOutcome` (`#[serde(rename_all =
 * "kebab-case")]`). */
export type RunOutcome =
  | "done"
  | "failed"
  | "timeout"
  | "waiting-input"
  | "blocked"
  | "skipped"
  | "interrupted";

export interface RunSummary {
  outcome: RunOutcome;
  sessionId: string;
  costUsd: number;
  startedAt: string;
  endedAt: string;
  lastMessage?: string | null;
  attempt: number;
  /** AC-E2-13 — the exact prompt this run was started with, when known
   * (absent for a run that was never actually spawned, or one persisted
   * before this field existed). Lets Retry replay it without re-picking a
   * folder. */
  prompt?: string | null;
}

/** Mirrors `commands::pipeline::PipelineStateResult`. */
export interface PipelineStateResult {
  state: FeatureState;
  warnings: string[];
}

export interface ImportPreview {
  included: string[];
  excluded: ExcludedFile[];
}

/** Mirrors `store::mcp_status::McpConnectionStatus` (kebab-case). */
export type McpConnectionStatus = "connected" | "needs-auth" | "failed";

/** Mirrors `store::mcp_status::McpStatusEntry` — live status of every MCP
 * server the spawned agents can reach (global config + every `.mcp.json`
 * up the tree), health-checked by `claude mcp list`. */
export interface McpStatusEntry {
  name: string;
  /** Command or URL; secret-looking `KEY=value` fragments are masked. */
  detail: string;
  status: McpConnectionStatus;
  /** The CLI's own wording, so a failure reason isn't lost. */
  rawStatus: string;
}

/** Mirrors `commands::project::RunningSlot`. */
export interface RunningSlot {
  feature: string;
  slot: string;
}

/** Mirrors `agentrun::readiness::SlotReadiness`. Drives each node's Run
 * button: `ready` enables it, everything else disables it with a reason
 * (B22 — nothing auto-spawns any more). */
export type SlotReadiness =
  | { kind: "ready" }
  | { kind: "waiting"; blockedBy: string[] }
  | { kind: "gateNotPassed"; gateLabel: string }
  | { kind: "agentMissing"; agentName: string }
  | { kind: "repoNotCloned"; repoName: string; declaredPath: string }
  | { kind: "repoRoleMissing"; role: string }
  | {
      kind: "repoRoleUnreadable";
      role: string;
      entries: { repoName: string; declaredRole: string }[];
    }
  | { kind: "noWorkInFeature"; role: string }
  | { kind: "unknownSlot" };

/** Vietnamese explanation of why a node can't run yet — `null` when it can. */
export function readinessReason(readiness: SlotReadiness | undefined): string | null {
  if (!readiness || readiness.kind === "ready") return null;
  switch (readiness.kind) {
    case "waiting":
      return `Đang chờ: ${readiness.blockedBy.join(", ")}`;
    case "gateNotPassed":
      return `Cần duyệt gate "${readiness.gateLabel}" trước`;
    case "agentMissing":
      return `Kit chưa có .claude/agents/${readiness.agentName}.md`;
    // Sai `repositoryRoot` trông y hệt chưa clone, và thực tế hay gặp hơn —
    // nêu luôn đường dẫn AGENTS.md khai để phân biệt được hai trường hợp.
    case "repoNotCloned":
      return `Không tìm thấy repo "${readiness.repoName}" (AGENTS.md khai "${readiness.declaredPath}") — kiểm tra repositoryRoot của project, hoặc clone repo về`;
    case "repoRoleMissing":
      return `Project không có repo vai trò "${readiness.role}" — agent này không áp dụng`;
    // Tách khỏi `repoRoleMissing`: nói "project không có repo frontend" khi
    // repo đó đang nằm ngay đó chỉ vì ô Vai trò ghi kèm ghi chú là đổ lỗi
    // sai chỗ. Trích nguyên văn ô sai để sửa được ngay.
    case "repoRoleUnreadable": {
      const listed = readiness.entries
        .map((e) => `"${e.repoName}" (vai trò: "${e.declaredRole}")`)
        .join(", ");
      return `AGENTS.md không khai repo nào vai trò "${readiness.role}" đọc được. Ô "Vai trò" của ${listed} không đọc ra được backend/frontend/mobile — sửa ô đó thành đúng một từ trong bảng Ecosystem`;
    }
    // Khác `repoRoleMissing` (project không có repo vai trò đó) và khác Skip
    // thủ công (người dùng tự quyết): ở đây kế hoạch đơn giản không có việc
    // cho slot này trong feature này.
    case "noWorkInFeature":
      return `Feature này không có task nào cho ${readiness.role} — agent này không áp dụng`;
    case "unknownSlot":
      return "Slot không có trong pipeline";
  }
}

/** Mirrors `commands::pipeline::FeatureDeletionPreview` — the inventory
 * shown before an irreversible delete. */
export interface FeatureDeletionPreview {
  docFileCount: number;
  notableArtifacts: string[];
  runCount: number;
  hasContractLock: boolean;
  inputCopyCount: number;
  /** Non-empty blocks deletion — an agent is still running. */
  runningSlots: string[];
}

export interface ImportedRun {
  runId: string;
  copiedPath: string;
  featureName: string;
  /** Relative paths actually copied — the BA prompt names each one, since
   * the agent has no directory-listing tool to discover them itself. */
  files: string[];
}

export const commands = {
  getTheme: () => invoke<Theme>("get_theme"),
  setTheme: (theme: Theme) => invoke<void>("set_theme", { theme }),

  detectProjectPaths: (rootHint: string) =>
    invoke<DetectedPaths>("detect_project_paths", { rootHint }),

  scaffoldKit: () => invoke<ScaffoldReport>("scaffold_kit"),

  refreshProject: () => invoke<ProjectSummary>("refresh_project"),

  openProject: (params: ProjectPaths & { label: string }) =>
    invoke<ProjectSummary>("open_project", { ...params }),

  openExistingProject: (params: ProjectPaths & { label: string }) =>
    invoke<ProjectSummary>("open_existing_project", { ...params }),

  listRecentProjects: () =>
    invoke<RecentProjectEntry[]>("list_recent_projects"),

  removeRecentProject: (paths: ProjectPaths) =>
    invoke<void>("remove_recent_project", { ...paths }),

  listFeatures: () => invoke<string[]>("list_features"),

  getPipelineDefinition: () =>
    invoke<PipelineDef>("get_pipeline_definition"),

  getPipelineState: (feature: string) =>
    invoke<PipelineStateResult>("get_pipeline_state", { feature }),

  getNodeDetail: (feature: string, slotId: string) =>
    invoke<NodeDetail>("get_node_detail", { feature, slotId }),

  startWatching: (feature: string) =>
    invoke<void>("start_watching", { feature }),

  stopWatching: () => invoke<void>("stop_watching"),

  readArtifact: (path: string) =>
    invoke<ArtifactContent>("read_artifact", { path }),

  listArtifactVersions: (path: string) =>
    invoke<VersionRef[]>("list_artifact_versions", { path }),

  diffArtifact: (path: string, fromId: string, toId: string) =>
    invoke<DiffResult>("diff_artifact", { path, fromId, toId }),

  killRun: (feature: string, slot: string) =>
    invoke<boolean>("kill_run", { feature, slot }),

  previewImport: (sourceFolder: string) =>
    invoke<ImportPreview>("preview_import", { sourceFolder }),

  importFolder: (sourceFolder: string, featureName: string) =>
    invoke<ImportedRun>("import_folder", { sourceFolder, featureName }),

  startRun: (feature: string, slot: string, prompt: string) =>
    invoke<void>("start_run", { feature, slot, prompt }),

  sendClarificationAnswer: (feature: string, slot: string, answer: string) =>
    invoke<void>("send_clarification_answer", { feature, slot, answer }),

  getRunSummary: (feature: string, slot: string) =>
    invoke<RunSummary | null>("get_run_summary", { feature, slot }),

  getRunLog: (feature: string, slot: string) =>
    invoke<StreamEvent[]>("read_run_log", { feature, slot }),

  approveTriggerGate: (feature: string, approvedBy: string) =>
    invoke<void>("approve_trigger_gate", { feature, approvedBy }),

  lockContract: (feature: string, approvedBy: string, confirmedRoles: string[]) =>
    invoke<void>("lock_contract", { feature, approvedBy, confirmedRoles }),

  skipContractLock: (feature: string, skippedBy: string, reason: string) =>
    invoke<void>("skip_contract_lock", { feature, skippedBy, reason }),

  unskipContractLock: (feature: string) =>
    invoke<void>("unskip_contract_lock", { feature }),

  listContractLocks: (feature: string) =>
    invoke<ContractLockRecord[]>("list_contract_locks", { feature }),

  listContractViolations: (feature: string) =>
    invoke<ViolationEvent[]>("list_contract_violations", { feature }),

  getConfig: () => invoke<ProjectConfig>("get_config"),

  setConfig: (config: ProjectConfig) => invoke<void>("set_config", { config }),

  getMcpServers: () => invoke<McpServer[]>("get_mcp_servers"),

  /** Live MCP connection status. Slow (~8s — it health-checks every
   * server), so always render a loading state around it. */
  getMcpStatus: () => invoke<McpStatusEntry[]>("get_mcp_status"),

  getClaudeAuthStatus: () => invoke<ClaudeAuthStatus>("get_claude_auth_status"),

  setClaudeAuthMode: (mode: ClaudeAuthMode) =>
    invoke<ProjectConfig>("set_claude_auth_mode", { mode }),

  saveClaudeApiKey: (apiKey: string) =>
    invoke<ProjectConfig>("save_claude_api_key", { apiKey }),

  clearClaudeApiKey: () => invoke<ProjectConfig>("clear_claude_api_key"),

  startClaudeLogin: (mode: "subscription" | "console") =>
    invoke<void>("start_claude_login", { mode }),

  logoutClaude: () => invoke<void>("logout_claude"),

  listRunHistory: () => invoke<RunHistoryRecord[]>("list_run_history"),

  exportCostCsv: (path: string) => invoke<void>("export_cost_csv", { path }),

  clearRunLogs: () => invoke<number>("clear_run_logs"),

  skipRun: (feature: string, slot: string) => invoke<void>("skip_run", { feature, slot }),

  // Force-marks a backend/frontend/mobile slot done, killing its live
  // process first if any — the escape hatch when the agent finished the
  // real work but its last message drifted off the "✅ ..." convention
  // `classify_outcome` relies on, so the slot got stuck `waiting-input`.
  forceDoneRun: (feature: string, slot: string) =>
    invoke<void>("force_done_run", { feature, slot }),

  // AC-E6-05 — continue an interrupted run in its original CLI session.
  resumeRun: (feature: string, slot: string) => invoke<void>("resume_run", { feature, slot }),

  // AC-E6-10 — orphan processes left by a previous app instance.
  listOrphans: () => invoke<OrphanInfo[]>("list_orphans"),

  resolveOrphan: (feature: string, slot: string, action: "attach" | "kill") =>
    invoke<void>("resolve_orphan", { feature, slot, action }),

  /** AC-E2-24 — creates `<docsRoot>/features/<name>/` and returns the
   * refreshed feature list. Rejects non-kebab-case and existing names. */
  createFeature: (name: string) => invoke<string[]>("create_feature", { name }),

  /** Runs still alive in the open project — named in the switch-project
   * confirm so the user sees what would be killed. */
  listRunningSlots: () => invoke<RunningSlot[]>("list_running_slots"),

  /** Releases the open project so another can be opened. Refuses while any
   * agent runs unless `force` (which kills them first) — `RunKey` has no
   * project id, so a run left tracked would look like the next project's. */
  closeProject: (force: boolean) => invoke<void>("close_project", { force }),

  /** The folder explorer's browsable root(s) — usually one entry, "the
   * whole project folder" (the common ancestor of all 3 project roots),
   * falling back to one entry per root when they share no common ancestor
   * (see `domain::explorer::ExplorerRootEntry`). */
  getExplorerRoots: () => invoke<ExplorerRootEntry[]>("get_explorer_roots"),

  /** One level of a directory under one of `getExplorerRoots`'s entries.
   * Lazy, not recursive — call again for each folder the user expands.
   * Rejects any path outside those root(s). */
  listDirectory: (path: string) => invoke<DirEntry[]>("list_directory", { path }),

  createExplorerFile: (parentPath: string, name: string) =>
    invoke<DirEntry>("create_explorer_file", { parentPath, name }),

  createExplorerFolder: (parentPath: string, name: string) =>
    invoke<DirEntry>("create_explorer_folder", { parentPath, name }),

  previewDeleteExplorerEntry: (path: string) =>
    invoke<ExplorerDeletePreview>("preview_delete_explorer_entry", { path }),

  deleteExplorerEntry: (path: string, confirmation: string) =>
    invoke<void>("delete_explorer_entry", { path, confirmation }),

  /** B22 — per-slot readiness for every node of a feature, one call. */
  getSlotReadiness: (feature: string) =>
    invoke<Record<string, SlotReadiness>>("get_slot_readiness", { feature }),

  /** B22 — the only way a pipeline agent starts. The prompt is built in the
   * backend from upstream artifacts; `extraInput` is slot-specific text
   * (today: the Figma selection URL for `design-analyst`). */
  runSlot: (feature: string, slot: string, extraInput?: string) =>
    invoke<void>("run_slot", { feature, slot, extraInput: extraInput ?? null }),

  /** What deleting would destroy — shown before the user confirms. */
  previewDeleteFeature: (name: string) =>
    invoke<FeatureDeletionPreview>("preview_delete_feature", { name }),

  /** Irreversible. `confirmation` must equal `name` (the backend re-checks,
   * so a UI bug can't delete the wrong feature). Returns the refreshed
   * feature list. */
  deleteFeature: (name: string, confirmation: string) =>
    invoke<string[]>("delete_feature", { name, confirmation }),
};

/** Mirrors `domain::pipeline_def::gate::TRIGGER`. */
export const TRIGGER_GATE_STAGE_ID = "S1b_trigger";

/** Mirrors `domain::pipeline_def::gate::CONTRACT_LOCK`. */
export const CONTRACT_LOCK_GATE_STAGE_ID = "S4_contract_lock";
