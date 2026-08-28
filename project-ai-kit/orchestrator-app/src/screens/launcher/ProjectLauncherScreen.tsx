import { useEffect, useState } from "react";
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
import { PackagePlus } from "lucide-react";
import {
  commands,
  isAppCommandError,
  type ProjectPaths,
  type ProjectSummary,
  type RecentProjectEntry,
} from "@/lib/tauri-client";
import { useAppStore } from "@/state/app-store";
import { RecentProjectList } from "@/screens/launcher/RecentProjectList";
import { ThreePathForm } from "@/screens/launcher/ThreePathForm";
import { EcosystemRepoTable } from "@/screens/launcher/EcosystemRepoTable";
import { ProjectInitHandoff } from "@/screens/launcher/ProjectInitHandoff";

const EMPTY_PATHS: ProjectPaths = {
  agentsRoot: "",
  docsRoot: "",
  repositoryRoot: "",
};

type View = "recent" | "form" | "summary";

function extractErrorMessage(err: unknown): string {
  if (isAppCommandError(err)) return err.message;
  if (err instanceof Error) return err.message;
  return String(err);
}

export function ProjectLauncherScreen() {
  const setScreen = useAppStore((s) => s.setScreen);
  const setProjectLabel = useAppStore((s) => s.setProjectLabel);
  const setProjectInit = useAppStore((s) => s.setProjectInit);

  const [view, setView] = useState<View>("recent");
  const [recentEntries, setRecentEntries] = useState<RecentProjectEntry[]>([]);
  const [loadingRecent, setLoadingRecent] = useState(true);
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
      setProjectInit(refreshed.initStatus, refreshed.initReasons, refreshed.paths.agentsRoot);
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
      setProjectInit(result.initStatus, result.initReasons, result.paths.agentsRoot);
      setSummary(result);
      setView("summary");
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
      setProjectInit(result.initStatus, result.initReasons, result.paths.agentsRoot);
      setSummary(result);
    } catch (err) {
      setErrorMessage(extractErrorMessage(err));
    } finally {
      setRefreshingInit(false);
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
      setProjectInit(result.initStatus, result.initReasons, result.paths.agentsRoot);
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

  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-6 p-8">
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
          <Button onClick={() => void startNewProject()}>
            Mở project mới
          </Button>
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
              {summary.initStatus === "needs-init" && <Badge variant="outline">chưa init</Badge>}
              {summary.initStatus === "missing-kit" && <Badge variant="destructive">thiếu kit</Badge>}
              {summary.initStatus === "invalid" && <Badge variant="destructive">cấu hình lỗi</Badge>}
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
            <ProjectInitHandoff
              projectName={summary.label}
              agentsRoot={summary.paths.agentsRoot}
              status={summary.initStatus}
              reasons={summary.initReasons}
              refreshing={refreshingInit}
              onRefresh={() => void refreshCurrentProject()}
            />
            {summary.missingKit.length > 0 && (
              <div className="flex flex-col gap-3 rounded-lg border border-warning p-3">
                <div>
                  <p className="text-sm font-medium">Project chưa đủ khung kit</p>
                  <p className="text-xs text-muted-foreground">
                    Thiếu những phần dưới đây thì Board vẫn hiện đủ node nhưng không node
                    nào chạy được. Bổ sung khung kit chỉ tạo phần còn thiếu, không ghi đè file nào
                    đã có.
                  </p>
                </div>
                <ul className="flex flex-col gap-1">
                  {summary.missingKit.map((group) => (
                    <li key={group.id} className="flex items-center justify-between gap-2 text-xs">
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
              <Button onClick={() => setScreen("board")}>
                Vào Pipeline Board
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
