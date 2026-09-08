use std::path::{Path, PathBuf};

use git2::{Repository, Sort};

use crate::domain::version_ref::{VersionRef, VersionSource};
use crate::error::{AppError, AppResult};

/// How many commits back to scan looking for versions of one file — deep
/// enough to be useful, shallow enough to stay fast and keep the version
/// list from becoming a full `git log`. Not user-configurable in MVP1.
const MAX_COMMITS_SCANNED: usize = 20;

/// Canonicalizes `path` the same way the rest of the codebase does
/// (`dunce::canonicalize`, not `std::fs::canonicalize` — see
/// `store::orchestrator_dir::assert_within`'s Windows note). Required
/// here for a DIFFERENT reason that only shows up when actually running
/// git2 against a real repo: on macOS, `/var` is a symlink to
/// `/private/var`, and `Repository::workdir()` returns the resolved real
/// path — so comparing a non-canonicalized `path` against it with
/// `strip_prefix` silently fails. Caught by
/// `list_git_versions_returns_one_entry_per_actual_change_newest_first`
/// actually creating a repo under a tempdir, not by compilation.
fn canonicalize(path: &Path) -> AppResult<PathBuf> {
    Ok(dunce::canonicalize(path)?)
}

/// `git2::Repository::discover` (libgit2, in-process — NOT a shelled-out
/// `git` binary). MVP1's own definition is "no process spawning"; shelling
/// out to `git` would be the one violation of that, and isn't guaranteed
/// to exist in PATH anyway (especially on Windows).
fn discover(canonical_path: &Path) -> Option<Repository> {
    let dir = canonical_path.parent()?;
    Repository::discover(dir).ok()
}

/// True when git's index already holds at least one file under `dir`.
///
/// Adding a `.gitignore` does NOT untrack what git already tracks, so a
/// project opened by a build that predates `.ai-boost/`'s self-ignore
/// keeps committing agent transcripts — including the verbatim contents of
/// every file the agents read and wrote — until someone runs
/// `git rm -r --cached`. This is how the app notices and says so, rather
/// than quietly leaving the source code in the user's history.
///
/// Any failure (not a repo, unreadable index, `dir` outside the workdir)
/// answers `false`: this drives a warning, and a warning nobody can act on
/// is worse than none.
pub fn has_tracked_entries_under(dir: &Path) -> bool {
    let Ok(canonical) = canonicalize(dir) else {
        return false;
    };
    let Ok(repo) = Repository::discover(&canonical) else {
        return false;
    };
    let Ok(relative) = repo_relative_path(&canonical, &repo) else {
        return false;
    };
    let Ok(index) = repo.index() else {
        return false;
    };

    // Index paths are always `/`-separated and repo-relative. The trailing
    // slash keeps a sibling like `.ai-boost-notes/` from matching.
    let prefix = format!(
        "{}/",
        relative
            .components()
            .map(|c| c.as_os_str().to_string_lossy())
            .collect::<Vec<_>>()
            .join("/")
    );
    index
        .iter()
        .any(|entry| entry.path.starts_with(prefix.as_bytes()))
}

pub fn is_git_tracked(path: &Path) -> bool {
    let Ok(canonical) = canonicalize(path) else {
        return false;
    };
    discover(&canonical).is_some()
}

fn repo_relative_path<'a>(canonical_path: &'a Path, repo: &Repository) -> AppResult<&'a Path> {
    let workdir = repo.workdir().ok_or_else(|| AppError::Invalid {
        message: "git repo has no working directory (bare repo?)".to_string(),
    })?;
    canonical_path
        .strip_prefix(workdir)
        .map_err(|_| AppError::Invalid {
            message: format!(
                "{} không nằm trong repo git đã tìm thấy",
                canonical_path.display()
            ),
        })
}

fn format_commit_label(commit: &git2::Commit, short_sha: &str) -> String {
    let summary = commit.summary().ok().flatten().unwrap_or("");
    let timestamp = commit.time().seconds();
    let date = chrono::DateTime::from_timestamp(timestamp, 0)
        .map(|dt| dt.format("%Y-%m-%d %H:%M").to_string())
        .unwrap_or_default();
    format!("{date} · {short_sha} · {summary}")
}

fn commit_timestamp_rfc3339(commit: &git2::Commit) -> String {
    chrono::DateTime::from_timestamp(commit.time().seconds(), 0)
        .map(|dt| dt.to_rfc3339())
        .unwrap_or_default()
}

/// Lists the commits (newest first, capped at `MAX_COMMITS_SCANNED`) where
/// `path`'s content actually changed relative to that commit's first
/// parent — i.e. `git log --follow`-ish semantics, simplified: renames and
/// merge commits beyond the first parent are not specially handled, an
/// acceptable simplification for MVP1.
pub fn list_git_versions(path: &Path) -> AppResult<Vec<VersionRef>> {
    let canonical = canonicalize(path)?;
    let Some(repo) = discover(&canonical) else {
        return Ok(Vec::new());
    };
    let rel_path = repo_relative_path(&canonical, &repo)?;

    let mut revwalk = repo.revwalk()?;
    revwalk.push_head()?;
    revwalk.set_sorting(Sort::TIME)?;

    let mut versions = Vec::new();
    for oid_result in revwalk.take(MAX_COMMITS_SCANNED) {
        let oid = oid_result?;
        let commit = repo.find_commit(oid)?;
        let tree = commit.tree()?;
        let current_blob = tree.get_path(rel_path).ok().map(|entry| entry.id());

        let Some(current_blob) = current_blob else {
            continue; // file doesn't exist at this commit
        };

        let parent_blob = commit
            .parent(0)
            .ok()
            .and_then(|parent| parent.tree().ok())
            .and_then(|parent_tree| parent_tree.get_path(rel_path).ok())
            .map(|entry| entry.id());

        if Some(current_blob) != parent_blob {
            let oid_str = oid.to_string();
            let short_sha = &oid_str[..7.min(oid_str.len())];
            versions.push(VersionRef {
                id: oid_str.clone(),
                label: format_commit_label(&commit, short_sha),
                source: VersionSource::Git,
                timestamp: commit_timestamp_rfc3339(&commit),
            });
        }
    }

    Ok(versions)
}

/// Reads `path`'s content as it existed in `commit_id`.
pub fn read_at_commit(path: &Path, commit_id: &str) -> AppResult<String> {
    let canonical = canonicalize(path)?;
    let repo = discover(&canonical).ok_or_else(|| AppError::Invalid {
        message: format!("{} không nằm trong repo git nào", canonical.display()),
    })?;
    let rel_path = repo_relative_path(&canonical, &repo)?;

    let oid = git2::Oid::from_str(commit_id).map_err(|_| AppError::Invalid {
        message: format!("commit id không hợp lệ: {commit_id}"),
    })?;
    let commit = repo.find_commit(oid)?;
    let tree = commit.tree()?;
    let entry = tree.get_path(rel_path).map_err(|_| AppError::Invalid {
        message: format!(
            "{} không tồn tại tại commit {commit_id}",
            rel_path.display()
        ),
    })?;
    let object = entry.to_object(&repo)?;
    let blob = object.as_blob().ok_or_else(|| AppError::Invalid {
        message: format!("{} không phải blob (file thường)", rel_path.display()),
    })?;

    Ok(String::from_utf8_lossy(blob.content()).into_owned())
}

#[cfg(test)]
mod tests {
    use super::*;

    fn commit_file(
        repo: &Repository,
        relative_path: &str,
        content: &str,
        message: &str,
    ) -> git2::Oid {
        let workdir = repo.workdir().unwrap();
        let full_path = workdir.join(relative_path);
        std::fs::create_dir_all(full_path.parent().unwrap()).unwrap();
        std::fs::write(&full_path, content).unwrap();

        let mut index = repo.index().unwrap();
        index.add_path(Path::new(relative_path)).unwrap();
        index.write().unwrap();
        let tree_id = index.write_tree().unwrap();
        let tree = repo.find_tree(tree_id).unwrap();

        let sig = git2::Signature::now("Test", "test@example.com").unwrap();
        let parents: Vec<git2::Commit> = repo
            .head()
            .ok()
            .and_then(|head| head.peel_to_commit().ok())
            .into_iter()
            .collect();
        let parent_refs: Vec<&git2::Commit> = parents.iter().collect();

        repo.commit(Some("HEAD"), &sig, &sig, message, &tree, &parent_refs)
            .unwrap()
    }

    #[test]
    fn tracked_entries_are_found_under_a_committed_directory() {
        let tmp = tempfile::tempdir().unwrap();
        let repo = Repository::init(tmp.path()).unwrap();
        commit_file(
            &repo,
            ".ai-boost/agent-runs/f/ba/log.jsonl",
            "{}",
            "oops",
        );

        assert!(has_tracked_entries_under(&tmp.path().join(".ai-boost")));
    }

    /// The common case after the self-ignore lands: the directory exists and
    /// is full of transcripts, but git never took it — no warning is due.
    #[test]
    fn an_untracked_directory_reports_nothing_tracked() {
        let tmp = tempfile::tempdir().unwrap();
        let repo = Repository::init(tmp.path()).unwrap();
        commit_file(&repo, "SPEC.md", "v1", "initial");

        let orchestrator = tmp.path().join(".ai-boost");
        std::fs::create_dir_all(orchestrator.join("agent-runs")).unwrap();
        std::fs::write(orchestrator.join("agent-runs/log.jsonl"), "{}").unwrap();

        assert!(!has_tracked_entries_under(&orchestrator));
    }

    /// Prefix matching must not fire on a sibling whose name merely starts
    /// the same way.
    #[test]
    fn a_sibling_with_a_similar_name_does_not_count_as_tracked() {
        let tmp = tempfile::tempdir().unwrap();
        let repo = Repository::init(tmp.path()).unwrap();
        commit_file(&repo, ".ai-boost-notes/README.md", "hi", "notes");

        let orchestrator = tmp.path().join(".ai-boost");
        std::fs::create_dir_all(&orchestrator).unwrap();

        assert!(!has_tracked_entries_under(&orchestrator));
    }

    #[test]
    fn not_git_tracked_when_no_repo_anywhere_in_ancestry() {
        let tmp = tempfile::tempdir().unwrap();
        let file = tmp.path().join("SPEC.md");
        std::fs::write(&file, "content").unwrap();

        assert!(!is_git_tracked(&file));
        assert!(list_git_versions(&file).unwrap().is_empty());
    }

    #[test]
    fn is_git_tracked_true_inside_a_real_repo() {
        let tmp = tempfile::tempdir().unwrap();
        let repo = Repository::init(tmp.path()).unwrap();
        commit_file(&repo, "SPEC.md", "v1", "initial");

        assert!(is_git_tracked(&tmp.path().join("SPEC.md")));
    }

    #[test]
    fn list_git_versions_returns_one_entry_per_actual_change_newest_first() {
        let tmp = tempfile::tempdir().unwrap();
        let repo = Repository::init(tmp.path()).unwrap();

        commit_file(&repo, "SPEC.md", "v1", "add SPEC");
        // A commit that touches a DIFFERENT file must not add a version
        // for SPEC.md — only actual content changes to the requested path
        // count.
        commit_file(&repo, "OTHER.md", "unrelated", "unrelated change");
        commit_file(&repo, "SPEC.md", "v2", "update SPEC");

        let file = tmp.path().join("SPEC.md");
        let versions = list_git_versions(&file).unwrap();

        assert_eq!(versions.len(), 2);
        assert_eq!(versions[0].source, VersionSource::Git);
        // Newest first: the "update SPEC" commit comes before "add SPEC".
        assert_eq!(read_at_commit(&file, &versions[0].id).unwrap(), "v2");
        assert_eq!(read_at_commit(&file, &versions[1].id).unwrap(), "v1");
    }

    #[test]
    fn read_at_commit_rejects_invalid_commit_id() {
        let tmp = tempfile::tempdir().unwrap();
        let repo = Repository::init(tmp.path()).unwrap();
        commit_file(&repo, "SPEC.md", "v1", "initial");

        let file = tmp.path().join("SPEC.md");
        assert!(read_at_commit(&file, "not-a-real-sha").is_err());
    }
}
