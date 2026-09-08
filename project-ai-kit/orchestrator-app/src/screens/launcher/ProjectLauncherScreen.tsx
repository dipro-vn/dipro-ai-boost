import { useEffect, useRef, useState } from "react";
import { open } from "@tauri-apps/plugin-dialog";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { ArrowLeft, PackagePlus, Sparkles } from "lucide-react";
import {
  commands,
  isAppCommandError,
  type ProjectPaths,
  type ProjectSummary,
  type RecentProjectEntry,
} from "@/lib/tauri-client";
import { onInitKitFinished, onInitKitOutput } from "@/lib/events";
import { useAppStore } from "@/state/app-store";
import { RecentProjectList } from "@/screens/launcher/RecentProjectList";
import { ThreePathForm } from "@/screens/launcher/ThreePathForm";
import { EcosystemRepoTable } from "@/screens/launcher/EcosystemRepoTable";
import { ProjectInitHandoff } from "@/screens/launcher/ProjectInitHandoff";
import { CreateProjectForm } from "@/screens/launcher/CreateProjectForm";
import {
  InitKitTerminalDialog,
  type InitKitPhase,
} from "@/screens/launcher/InitKitTerminalDialog";

const EMPTY_PATHS: ProjectPaths = {
  agentsRoot: "",
  docsRoot: "",
  repositoryRoot: "",
};

type View = "recent" | "form" | "create" | "summary";

function extractErrorMessage(err: unknown): string {
  if (isAppCommandError(err)) return err.message;
  if (err instanceof Error) return err.message;
  return String(err);
}

export function ProjectLauncherScreen() {
  const setScreen = useAppStore((s) => s.setScreen);
  const setProjectLabel = useAppStore((s) => s.setProjectLabel);
  const setProjectInit = useAppStore((s) => s.setProjectInit);
  const leaveProject = useAppStore((s) => s.leaveProject);

  const [view, setView] = useState<View>("recent");
  const [recentEntries, setRecentEntries] = useState<RecentProjectEntry[]>([]);
  const [loadingRecent, setLoadingRecent] = useState(true);
  const [checkingCurrentProject, setCheckingCurrentProject] = useState(true);
  const [formInitial, setFormInitial] = useState<ProjectPaths>(EMPTY_PATHS);
  /** Thư mục gốc người dùng chọn ở bước trước — form dùng dựng bố cục mặc định. */
  const [rootHint, setRootHint] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [openingRecentLabel, setOpeningRecentLabel] = useState<string | null>(
    null,
  );
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [summary, setSummary] = useState<ProjectSummary | null>(null);
  const [scaffolding, setScaffolding] = useState(false);
  const [refreshingInit, setRefreshingInit] = useState(false);
  const [createdProject, setCreatedProject] = useState(false);
  const [initDialogOpen, setInitDialogOpen] = useState(false);
  const [initProjectName, setInitProjectName] = useState("");
  const [initSessionId, setInitSessionId] = useState<string | null>(null);
  const [initOutput, setInitOutput] = useState<string[]>([]);
  const [initPhase, setInitPhase] = useState<InitKitPhase>("starting");
  const [initStopped, setInitStopped] = useState(false);
  const [initError, setInitError] = useState<string | null>(null);
  const [leavingProject, setLeavingProject] = useState(false);
  const initSessionRef = useRef<string | null>(null);
  const initLaunchingRef = useRef(false);
  /** Lần cuối PTY xuất ra byte nào — tín hiệu duy nhất cho "Claude đã ngừng
   * nói", dùng để không cắt ngang init-agent khi nó còn đang ghi file. */
  const initLastOutputAtRef = useRef(Date.now());
  /** Chặn `completeInitKit` chạy hai lần: tick polling kế tiếp có thể nổ
   * trước khi `initPhase` kịp đổi và gỡ effect. */
  const initCompletingRef = useRef(false);
  const initNeedsCompletion = createdProject && summary?.initStatus !== "ready";

  /** Dựng phần khung kit còn thiếu rồi mở lại chính project đó — mở lại là
   * cách duy nhất làm mới `readOnly`/`agentsFound`/`ecosystem`, và
   * `summary` đã mang sẵn `paths` + `label` nên không cần state phụ. */
  async function scaffoldKit() {
    setScaffolding(true);
    setErrorMessage(null);
    try {
      await commands.scaffoldKit();
      const refreshed = await commands.refreshProject();
      setSummary(refreshed);
      setProjectLabel(refreshed.label);
      setProjectInit(
        refreshed.initStatus,
        refreshed.initReasons,
        refreshed.paths.agentsRoot,
      );
    } catch (err) {
      setErrorMessage(extractErrorMessage(err));
    } finally {
      setScaffolding(false);
    }
  }

  async function refreshRecent() {
    setLoadingRecent(true);
    try {
      setRecentEntries(await commands.listRecentProjects());
    } catch (err) {
      setErrorMessage(extractErrorMessage(err));
    } finally {
      setLoadingRecent(false);
    }
  }

  useEffect(() => {
    void refreshRecent();
  }, []);

  useEffect(() => {
    let cancelled = false;
    void commands
      .hasOpenProject()
      .then(async (hasOpenProject) => {
        if (!hasOpenProject) return;
        const result = await commands.refreshProject();
        if (cancelled) return;
        setProjectLabel(result.label);
        setProjectInit(
          result.initStatus,
          result.initReasons,
          result.paths.agentsRoot,
        );
        setSummary(result);
        setCreatedProject(false);
        if (result.initStatus === "ready") {
          setScreen("board");
        } else {
          setView("summary");
        }
      })
      .catch((err) => {
        if (!cancelled) setErrorMessage(extractErrorMessage(err));
      })
      .finally(() => {
        if (!cancelled) setCheckingCurrentProject(false);
      });

    return () => {
      cancelled = true;
    };
  }, [setProjectInit, setProjectLabel, setScreen]);

  useEffect(() => {
    const unlistenOutput = onInitKitOutput((payload) => {
      if (
        payload.sessionId !== initSessionRef.current &&
        !initLaunchingRef.current
      ) {
        return;
      }
      if (!initSessionRef.current) initSessionRef.current = payload.sessionId;
      initLastOutputAtRef.current = Date.now();
      setInitOutput((current) => [...current, payload.data].slice(-10_000));
    });
    const unlistenFinished = onInitKitFinished((payload) => {
      if (payload.sessionId !== initSessionRef.current) return;
      initLaunchingRef.current = false;
      setInitPhase("finished");
      setInitStopped(payload.stopped);
      void commands
        .refreshProject()
        .then((result) => {
          setSummary(result);
          setProjectLabel(result.label);
          setProjectInit(
            result.initStatus,
            result.initReasons,
            result.paths.agentsRoot,
          );
          if (result.initStatus !== "ready" && !payload.stopped) {
            setInitError(
              "Claude đã kết thúc nhưng project vẫn chưa hoàn tất init-kit. Kiểm tra terminal và chạy lại.",
            );
          }
        })
        .catch((err) => setInitError(extractErrorMessage(err)));
    });

    return () => {
      void unlistenOutput.then((unlisten) => unlisten());
      void unlistenFinished.then((unlisten) => unlisten());
    };
  }, [setProjectInit, setProjectLabel]);

  async function startNewProject() {
    setErrorMessage(null);
    const rootHint = await open({ directory: true, multiple: false });
    if (typeof rootHint !== "string") return; // user cancelled

    setRootHint(rootHint);
    const detected = await commands.detectProjectPaths(rootHint);
    setFormInitial({
      agentsRoot: detected.agentsRoot ?? "",
      docsRoot: detected.docsRoot ?? "",
      repositoryRoot: detected.repositoryRoot ?? "",
    });
    setView("form");
  }

  async function submitForm(paths: ProjectPaths, label: string) {
    setSubmitting(true);
    setErrorMessage(null);
    try {
      const result = await commands.openProject({ ...paths, label });
      setProjectLabel(result.label);
      setProjectInit(
        result.initStatus,
        result.initReasons,
        result.paths.agentsRoot,
      );
      setSummary(result);
      const canRunInitKit =
        result.initStatus === "needs-init" &&
        result.missingKit.length === 0 &&
        !result.readOnly;
      setCreatedProject(canRunInitKit);
      setView("summary");
      if (canRunInitKit) void startInitKit(result.label);
    } catch (err) {
      setErrorMessage(extractErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  async function startInitKit(projectName: string) {
    initLaunchingRef.current = true;
    initSessionRef.current = null;
    initCompletingRef.current = false;
    initLastOutputAtRef.current = Date.now();
    setInitProjectName(projectName);
    setInitSessionId(null);
    setInitOutput([]);
    setInitPhase("starting");
    setInitStopped(false);
    setInitError(null);
    setInitDialogOpen(true);
    try {
      const session = await commands.startInitKit(projectName);
      initLaunchingRef.current = false;
      initSessionRef.current = session.sessionId;
      setInitSessionId(session.sessionId);
      setInitPhase("running");
    } catch (err) {
      initLaunchingRef.current = false;
      setInitPhase("failed");
      setInitError(extractErrorMessage(err));
    }
  }

  /** Đóng lại phiên init-kit khi project đã thực sự `ready`: dừng Claude, ẩn
   * terminal, và để lộ thẻ summary với nút "Vào Pipeline Board" đã mở khoá.
   * `refreshed` là kết quả `refreshProject` vừa dùng để phát hiện `ready`, nên
   * không gọi lại lần nữa. */
  async function completeInitKit(refreshed: ProjectSummary, sessionId: string) {
    initCompletingRef.current = true;
    setSummary(refreshed);
    setProjectLabel(refreshed.label);
    setProjectInit(
      refreshed.initStatus,
      refreshed.initReasons,
      refreshed.paths.agentsRoot,
    );
    setInitPhase("finished");
    setInitDialogOpen(false);
    try {
      await commands.stopInitKit(sessionId);
    } catch {
      // Phiên có thể đã tự chết trước khi ta kịp dừng — project vẫn `ready`
      // nên không có gì để báo, và `init-kit://finished` sẽ dọn nốt state.
    }
  }

  /** `init-kit://finished` chỉ bắn khi tiến trình `claude` thoát hẳn (vòng đọc
   * PTY trong `initrun.rs` thoát ở EOF), mà Claude Code interactive quay về
   * prompt chứ không thoát sau khi chạy xong một slash command. Nên hoàn tất
   * init-kit phải tự phát hiện: đọc lại `AGENTS.md` qua `refreshProject` mỗi
   * `POLL_MS`, và chỉ tin kết quả khi terminal đã im `IDLE_MS` — trong lúc
   * init-agent còn ghi file thì output không im lâu tới vậy, còn khi Claude
   * kết thúc lượt thì nó im vĩnh viễn. */
  useEffect(() => {
    const POLL_MS = 3_000;
    const IDLE_MS = 10_000;
    if (initPhase !== "running" || !initSessionId) return;

    const timer = window.setInterval(() => {
      if (initCompletingRef.current) return;
      if (Date.now() - initLastOutputAtRef.current < IDLE_MS) return;
      void commands
        .refreshProject()
        .then((result) => {
          if (initCompletingRef.current) return;
          if (result.initStatus !== "ready") return;
          void completeInitKit(result, initSessionId);
        })
        .catch(() => {
          // Terminal vẫn mở và nút "Vào Pipeline Board" vẫn là đường thủ công,
          // nên một tick hỏng không cần báo gì — tick sau thử lại.
        });
    }, POLL_MS);

    return () => window.clearInterval(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initPhase, initSessionId]);

  async function submitCreateProject(name: string, parentPath: string) {
    setSubmitting(true);
    setErrorMessage(null);
    try {
      const result = await commands.createProject(parentPath, name);
      setProjectLabel(result.label);
      setProjectInit(
        result.initStatus,
        result.initReasons,
        result.paths.agentsRoot,
      );
      setSummary(result);
      setCreatedProject(true);
      setView("summary");
      if (result.missingKit.length > 0 || result.readOnly) {
        setInitPhase("failed");
        setInitError(
          "Không thể chạy init-kit vì khung kit chưa được tạo đầy đủ. Bổ sung khung kit rồi thử lại.",
        );
      } else {
        void startInitKit(result.label);
      }
    } catch (err) {
      setErrorMessage(extractErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  async function refreshCurrentProject() {
    setRefreshingInit(true);
    setErrorMessage(null);
    try {
      const result = await commands.refreshProject();
      setProjectLabel(result.label);
      setProjectInit(
        result.initStatus,
        result.initReasons,
        result.paths.agentsRoot,
      );
      setSummary(result);
    } catch (err) {
      setErrorMessage(extractErrorMessage(err));
    } finally {
      setRefreshingInit(false);
    }
  }

  async function backToProjectLauncher() {
    setLeavingProject(true);
    setErrorMessage(null);
    try {
      await commands.closeProject(true);
      leaveProject();
    } catch (err) {
      setErrorMessage(extractErrorMessage(err));
    } finally {
      setLeavingProject(false);
    }
  }

  // AC-E1-07: ready recent entries go straight to the board — no re-asking
  // the 3 paths. Uninitialized entries return to Summary for handoff. AF-5:
  // if the paths are no longer valid, drop into the form pre-filled with the
  // broken entry so the user can fix it instead of
  // silently failing.
  async function openRecent(entry: RecentProjectEntry) {
    setErrorMessage(null);
    setOpeningRecentLabel(entry.label);
    try {
      const result = await commands.openExistingProject({
        agentsRoot: entry.agentsRoot,
        docsRoot: entry.docsRoot,
        repositoryRoot: entry.repositoryRoot,
        label: entry.label,
      });
      setProjectLabel(result.label);
      setProjectInit(
        result.initStatus,
        result.initReasons,
        result.paths.agentsRoot,
      );
      setCreatedProject(false);
      if (result.initStatus === "ready") {
        setScreen("board");
      } else {
        setSummary(result);
        setView("summary");
      }
    } catch (err) {
      setErrorMessage(
        `Không mở được "${entry.label}": ${extractErrorMessage(err)}`,
      );
      setFormInitial({
        agentsRoot: entry.agentsRoot,
        docsRoot: entry.docsRoot,
        repositoryRoot: entry.repositoryRoot,
      });
      setView("form");
    } finally {
      setOpeningRecentLabel(null);
    }
  }

  async function removeRecent(entry: RecentProjectEntry) {
    try {
      await commands.removeRecentProject(entry);
      await refreshRecent();
    } catch (err) {
      setErrorMessage(extractErrorMessage(err));
    }
  }

  if (view === "create") {
    return (
      <div className="relative isolate min-h-full overflow-hidden bg-[#eef7fc] dark:bg-[#061b2b]">
        <div
          className="pointer-events-none absolute inset-0 opacity-70 dark:opacity-40"
          style={{
            backgroundImage:
              "linear-gradient(rgba(1,58,99,0.07) 1px, transparent 1px), linear-gradient(90deg, rgba(1,58,99,0.07) 1px, transparent 1px)",
            backgroundSize: "38px 38px",
            maskImage: "linear-gradient(to bottom, black, transparent 82%)",
          }}
        />
        <div className="pointer-events-none absolute -top-32 -right-24 size-96 rounded-full bg-[#4db6e6]/30 blur-3xl dark:bg-[#0e7490]/20" />
        <div className="pointer-events-none absolute -bottom-40 -left-32 size-[30rem] rounded-full bg-[#013a63]/15 blur-3xl dark:bg-[#075985]/25" />

        <div className="relative mx-auto grid min-h-[calc(100vh-3.5rem)] max-w-6xl items-center gap-8 px-6 py-10 sm:px-10 lg:grid-cols-[0.9fr_1.1fr] lg:gap-16 lg:px-16">
          <div className="max-w-md">
            <Button
              type="button"
              variant="ghost"
              className="mb-8 -ml-3 text-[#013a63] hover:bg-[#013a63]/10 dark:text-sky-200 dark:hover:bg-sky-200/10"
              onClick={() => setView("recent")}
            >
              <ArrowLeft />
              Quay lại danh sách project
            </Button>
            <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-[#013a63]/15 bg-white/60 px-3 py-1.5 text-xs font-medium text-[#013a63] shadow-sm backdrop-blur dark:border-sky-200/15 dark:bg-white/10 dark:text-sky-100">
              <Sparkles className="size-3.5" />
              New workspace
            </div>
            <h1 className="text-4xl font-semibold tracking-tight text-[#013a63] sm:text-5xl dark:text-white">
              Bắt đầu một project mới.
            </h1>
            <p className="mt-5 text-base leading-7 text-slate-600 dark:text-slate-300">
              Tạo không gian làm việc chuẩn cho Dipro AI Boost. Sau khi tạo, app
              sẽ dựng khung kit và mở Claude ngay trong terminal tích hợp.
            </p>
            <div className="mt-8 grid gap-3 text-sm text-slate-600 dark:text-slate-300">
              <div className="flex items-center gap-3">
                <span className="flex size-7 items-center justify-center rounded-full bg-[#013a63] text-xs font-semibold text-white">
                  1
                </span>
                <span>Tạo cấu trúc project chuẩn</span>
              </div>
              <div className="flex items-center gap-3">
                <span className="flex size-7 items-center justify-center rounded-full bg-[#0b6e99] text-xs font-semibold text-white">
                  2
                </span>
                <span>Khởi chạy Claude và init-kit</span>
              </div>
              <div className="flex items-center gap-3">
                <span className="flex size-7 items-center justify-center rounded-full bg-[#4db6e6] text-xs font-semibold text-[#013a63]">
                  3
                </span>
                <span>Sẵn sàng vào Pipeline Board</span>
              </div>
            </div>
          </div>

          <div className="flex flex-col gap-4">
            {errorMessage && (
              <Alert variant="destructive">
                <AlertTitle>Có lỗi xảy ra</AlertTitle>
                <AlertDescription>{errorMessage}</AlertDescription>
              </Alert>
            )}
            <Card className="border-white/70 bg-white/85 shadow-2xl shadow-[#013a63]/15 backdrop-blur-xl dark:border-white/15 dark:bg-slate-950/70 dark:shadow-black/30">
              <CardHeader className="border-b border-[#013a63]/10 pb-5 dark:border-white/10">
                <CardTitle className="text-[#013a63] dark:text-white">
                  Tạo project mới
                </CardTitle>
                <CardDescription>
                  Chọn thư mục cha. App sẽ tạo thư mục project, dựng khung kit
                  và mở terminal Claude để chạy init-kit.
                </CardDescription>
              </CardHeader>
              <CardContent className="pt-6">
                <CreateProjectForm
                  submitting={submitting}
                  onSubmit={(name, parentPath) =>
                    void submitCreateProject(name, parentPath)
                  }
                  onCancel={() => setView("recent")}
                />
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="relative isolate min-h-full overflow-hidden bg-[#eef7fc] dark:bg-[#061b2b]">
      <div
        className="pointer-events-none absolute inset-0 opacity-60 dark:opacity-35"
        style={{
          backgroundImage:
            "radial-gradient(circle at 20% 18%, rgba(77,182,230,0.22) 0 1px, transparent 1.5px), radial-gradient(circle at 78% 38%, rgba(1,58,99,0.18) 0 1px, transparent 1.5px), radial-gradient(circle at 62% 82%, rgba(77,182,230,0.18) 0 1px, transparent 1.5px)",
          backgroundSize: "130px 150px, 170px 190px, 210px 180px",
        }}
      />
      <div
        className="pointer-events-none absolute -right-48 top-16 h-[30rem] w-[30rem] opacity-45 sm:-right-32 lg:right-8 lg:top-20 lg:opacity-70"
        aria-hidden="true"
      >
        <div className="space-orbit space-orbit-one" />
        <div className="space-orbit space-orbit-two" />
        <div className="space-planet" />
        <div className="space-moon" />
      </div>

      <div className="relative mx-auto flex max-w-2xl flex-col gap-6 p-8">
        {errorMessage && (
          <Alert variant="destructive">
            <AlertTitle>Có lỗi xảy ra</AlertTitle>
            <AlertDescription>{errorMessage}</AlertDescription>
          </Alert>
        )}

        {view === "recent" && (
          <>
            <Card>
              <CardHeader>
                <CardTitle>Project gần đây</CardTitle>
              </CardHeader>
              <CardContent>
                <RecentProjectList
                  entries={recentEntries}
                  loading={loadingRecent}
                  openingLabel={openingRecentLabel}
                  onOpen={openRecent}
                  onRemove={removeRecent}
                />
              </CardContent>
            </Card>
            <div className="flex flex-col gap-2 sm:flex-row">
              <Button
                className="flex-1"
                disabled={checkingCurrentProject}
                onClick={() => void startNewProject()}
              >
                Mở project mới
              </Button>
              <Button
                className="flex-1"
                variant="outline"
                disabled={checkingCurrentProject}
                onClick={() => setView("create")}
              >
                Tạo project mới
              </Button>
            </div>
          </>
        )}

        {view === "form" && (
          <Card>
            <CardHeader>
              <CardTitle>Mở project</CardTitle>
              <CardDescription>
                Xác nhận hoặc chỉnh lại 3 đường dẫn — mỗi ô độc lập, không cần
                nằm trong nhau.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ThreePathForm
                initial={formInitial}
                rootHint={rootHint}
                submitting={submitting}
                onSubmit={submitForm}
                onCancel={() => setView("recent")}
              />
            </CardContent>
          </Card>
        )}

        {view === "summary" && summary && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                {summary.label}
                {summary.readOnly && <Badge variant="outline">read-only</Badge>}
                {summary.initStatus === "needs-init" && (
                  <Badge variant="outline">chưa init</Badge>
                )}
                {summary.initStatus === "missing-kit" && (
                  <Badge variant="destructive">thiếu kit</Badge>
                )}
                {summary.initStatus === "invalid" && (
                  <Badge variant="destructive">cấu hình lỗi</Badge>
                )}
              </CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col gap-4">
              {summary.warnings.length > 0 && (
                <Alert>
                  <AlertTitle>Lưu ý</AlertTitle>
                  <AlertDescription>
                    <ul className="list-inside list-disc">
                      {summary.warnings.map((w) => (
                        <li key={w}>{w}</li>
                      ))}
                    </ul>
                  </AlertDescription>
                </Alert>
              )}
              {createdProject &&
                (initPhase === "finished" || initPhase === "failed") && (
                  <Alert
                    variant={
                      summary.initStatus === "ready" ? "default" : "destructive"
                    }
                  >
                    <AlertTitle>
                      {summary.initStatus === "ready"
                        ? "Init-kit đã hoàn tất"
                        : "Init-kit chưa hoàn tất"}
                    </AlertTitle>
                    <AlertDescription>
                      <div className="flex flex-col gap-3">
                        <span>
                          {summary.initStatus === "ready"
                            ? "Project đã sẵn sàng. Bạn có thể vào Pipeline Board hoặc quay lại để chọn project khác."
                            : "Project chưa sẵn sàng để chạy pipeline. Bạn có thể xem lại terminal hoặc quay lại để chọn project khác."}
                        </span>
                        <div>
                          <Button
                            type="button"
                            variant="outline"
                            size="sm"
                            onClick={() => void backToProjectLauncher()}
                            disabled={leavingProject}
                          >
                            {leavingProject
                              ? "Đang quay lại..."
                              : "Quay lại chọn hoặc tạo project"}
                          </Button>
                        </div>
                      </div>
                    </AlertDescription>
                  </Alert>
                )}
              {!createdProject && (
                <ProjectInitHandoff
                  projectName={summary.label}
                  agentsRoot={summary.paths.agentsRoot}
                  status={summary.initStatus}
                  reasons={summary.initReasons}
                  refreshing={refreshingInit}
                  onRefresh={() => void refreshCurrentProject()}
                />
              )}
              {summary.missingKit.length > 0 && (
                <div className="flex flex-col gap-3 rounded-lg border border-warning p-3">
                  <div>
                    <p className="text-sm font-medium">
                      Project chưa đủ khung kit
                    </p>
                    <p className="text-xs text-muted-foreground">
                      Thiếu những phần dưới đây thì Board vẫn hiện đủ node nhưng
                      không node nào chạy được. Bổ sung khung kit chỉ tạo phần
                      còn thiếu, không ghi đè file nào đã có.
                    </p>
                  </div>
                  <ul className="flex flex-col gap-1">
                    {summary.missingKit.map((group) => (
                      <li
                        key={group.id}
                        className="flex items-center justify-between gap-2 text-xs"
                      >
                        <span className="truncate">{group.label}</span>
                        <span className="shrink-0 font-mono text-muted-foreground">
                          {group.missingCount}/{group.totalCount} · {group.root}
                        </span>
                      </li>
                    ))}
                  </ul>
                  <div className="flex justify-end">
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={scaffolding}
                      onClick={() => scaffoldKit()}
                    >
                      <PackagePlus />
                      {scaffolding ? "Đang bổ sung..." : "Bổ sung khung kit"}
                    </Button>
                  </div>
                </div>
              )}
              <EcosystemRepoTable repos={summary.ecosystem} />
              <div className="flex justify-end">
                {initNeedsCompletion && !initDialogOpen && (
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => setInitDialogOpen(true)}
                  >
                    Mở lại terminal init-kit
                  </Button>
                )}
                <Button
                  onClick={() => setScreen("board")}
                  disabled={initNeedsCompletion}
                >
                  Vào Pipeline Board
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        <InitKitTerminalDialog
          open={initDialogOpen}
          projectName={initProjectName}
          sessionId={initSessionId}
          output={initOutput}
          phase={initPhase}
          stopped={initStopped}
          errorMessage={initError}
          onOpenChange={setInitDialogOpen}
          onStop={() => {
            if (!initSessionRef.current) return;
            void commands
              .stopInitKit(initSessionRef.current)
              .then(() => {
                setInitPhase("finished");
                setInitStopped(true);
              })
              .catch((err) => setInitError(extractErrorMessage(err)));
          }}
          onRetry={() => void startInitKit(initProjectName)}
        />
      </div>
    </div>
  );
}
