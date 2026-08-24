//! Best-effort prefill for the 3 path fields on the Project Launcher
//! (AC-E1-02). Every function here is allowed to return `None` — and MUST,
//! rather than guess, whenever there is more than one equally plausible
//! candidate (AC-E1-03: "không dò ra được → để trống, KHÔNG đoán"). None of
//! this validates or constrains what the user can browse to manually; it
//! only prefills.

use std::path::{Path, PathBuf};

const MAX_CANDIDATES_BEFORE_AMBIGUOUS: usize = 2;

/// Directories that are never worth descending into while searching —
/// purely a performance/noise bound, not a correctness requirement.
const SKIP_DIR_NAMES: &[&str] = &[
    "node_modules",
    "target",
    ".git",
    "dist",
    "build",
    ".next",
    ".venv",
    "vendor",
];

fn should_descend(dir_name: &str) -> bool {
    !SKIP_DIR_NAMES.contains(&dir_name)
}

fn subdirectories(dir: &Path) -> Vec<PathBuf> {
    std::fs::read_dir(dir)
        .into_iter()
        .flatten()
        .filter_map(|entry| entry.ok())
        .map(|entry| entry.path())
        .filter(|path| path.is_dir())
        .filter(|path| {
            path.file_name()
                .and_then(|n| n.to_str())
                .map(should_descend)
                .unwrap_or(false)
        })
        .collect()
}

/// Breadth-first search from `root_hint` (inclusive) up to `max_depth`,
/// collecting every directory for which `predicate` returns true. Depth 0
/// is `root_hint` itself.
fn bfs_find_all(
    root_hint: &Path,
    max_depth: u32,
    predicate: impl Fn(&Path) -> bool,
) -> Vec<PathBuf> {
    let mut matches = Vec::new();
    let mut frontier = vec![root_hint.to_path_buf()];
    let mut depth = 0;

    while !frontier.is_empty() && depth <= max_depth {
        let mut next_frontier = Vec::new();
        for dir in &frontier {
            if predicate(dir) {
                matches.push(dir.clone());
            }
            if depth < max_depth {
                next_frontier.extend(subdirectories(dir));
            }
        }
        frontier = next_frontier;
        depth += 1;
    }

    matches
}

/// Returns `Some(path)` only if the search found exactly one candidate;
/// `None` for zero OR multiple (ambiguous) matches.
fn unambiguous(mut candidates: Vec<PathBuf>) -> Option<PathBuf> {
    candidates.truncate(MAX_CANDIDATES_BEFORE_AMBIGUOUS);
    match candidates.len() {
        1 => candidates.pop(),
        _ => None,
    }
}

pub fn detect_agents_root(root_hint: &Path) -> Option<PathBuf> {
    let candidates = bfs_find_all(root_hint, 4, |dir| {
        dir.join(".claude").join("agents").is_dir()
    });
    unambiguous(candidates)
}

pub fn detect_docs_root(root_hint: &Path) -> Option<PathBuf> {
    let candidates = bfs_find_all(root_hint, 4, |dir| dir.join("features").is_dir());
    unambiguous(candidates)
}

/// A "repository root" candidate is a directory containing at least one
/// child that itself looks like a cloned repo (`.git` present).
pub fn detect_repository_root(root_hint: &Path) -> Option<PathBuf> {
    let candidates = bfs_find_all(root_hint, 3, |dir| {
        subdirectories(dir)
            .iter()
            .any(|child| child.join(".git").exists())
    });
    unambiguous(candidates)
}

/// How many of `declared_paths` resolve to a real directory under `base`.
fn declared_repos_present(base: &Path, declared_paths: &[String]) -> usize {
    declared_paths
        .iter()
        .filter(|declared| base.join(declared).is_dir())
        .count()
}

/// `repositoryRoot` dò theo bảng Ecosystem của `AGENTS.md`: thư mục nào
/// chứa nhiều repo được khai nhất thì đó là nó.
///
/// `detect_repository_root` một mình không đủ — nó đòi thư mục con có
/// `.git`, nên bó tay với repo chưa clone, repo lấy về bằng cách khác, hay
/// project ví dụ (thư mục repo là thật nhưng không phải git repo). Đó chính
/// là lý do người dùng dễ để `repositoryRoot` trỏ nhầm sang `agentsRoot` và
/// chỉ phát hiện ra khi agent backend bị chặn.
///
/// Hai điều chỉnh, cả hai đều do cấu trúc docs của kit gây ra:
/// - Loại các ứng viên nằm trong `docs_root`. `<DOCS_ROOT>/features/<feature>/`
///   có đúng một thư mục con mỗi repo — trùng tên y hệt, nên nó ăn điểm
///   ngang với thư mục repo thật. Đây là quy ước của kit, tức mọi project
///   dùng kit đều dính, không riêng project ví dụ.
/// - Hoà điểm thì thư mục NÔNG hơn thắng: `repositoryRoot` nằm gần gốc,
///   còn thư mục docs trùng tên luôn nằm sâu dưới `features/<feature>/`.
///
/// Vẫn hoà sau cả hai = không đoán (AC-E1-03) → rơi về heuristic `.git`,
/// bản thân nó cũng trả `None` khi mơ hồ.
pub fn detect_repository_root_by_declared_repos(
    root_hint: &Path,
    declared_paths: &[String],
    docs_root: Option<&Path>,
) -> Option<PathBuf> {
    if declared_paths.is_empty() {
        return detect_repository_root(root_hint);
    }

    let depth_of = |dir: &Path| {
        dir.strip_prefix(root_hint)
            .map(|rest| rest.components().count())
            .unwrap_or(usize::MAX)
    };

    let mut scored: Vec<(PathBuf, usize, usize)> = bfs_find_all(root_hint, 3, |dir| {
        declared_repos_present(dir, declared_paths) > 0
    })
    .into_iter()
    .filter(|dir| docs_root.is_none_or(|docs| !dir.starts_with(docs)))
    .map(|dir| {
        let score = declared_repos_present(&dir, declared_paths);
        let depth = depth_of(&dir);
        (dir, score, depth)
    })
    .collect();
    scored.sort_by(|a, b| b.1.cmp(&a.1).then(a.2.cmp(&b.2)));

    match scored.split_first() {
        // Chỉ nhận khi ứng viên đầu hơn hẳn ứng viên thứ hai.
        Some(((best, best_score, best_depth), rest)) => match rest.first() {
            None => Some(best.clone()),
            Some((_, score, depth)) if (best_score, best_depth) != (score, depth) => {
                Some(best.clone())
            }
            Some(_) => detect_repository_root(root_hint),
        },
        None => detect_repository_root(root_hint),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn touch_dir(path: &Path) {
        std::fs::create_dir_all(path).unwrap();
    }

    /// Synthetic fixture mirroring the A1 finding: `agentsRoot` is NOT an
    /// ancestor of `repositoryRoot` (they're siblings), and `docsRoot` is
    /// nested several levels below `agentsRoot`. No real project data —
    /// generic names only.
    ///
    ///   workspace/
    ///   ├── agents-repo/.claude/agents/some-agent.md
    ///   ├── agents-repo/agents-repo/docs/features/some-feature/
    ///   └── source-repo/
    ///       ├── app-one/.git
    ///       └── app-two/.git
    fn build_nested_fixture() -> tempfile::TempDir {
        let tmp = tempfile::tempdir().unwrap();
        let root = tmp.path();

        touch_dir(&root.join("agents-repo/.claude/agents"));
        std::fs::write(root.join("agents-repo/.claude/agents/some-agent.md"), "").unwrap();
        touch_dir(&root.join("agents-repo/agents-repo/docs/features/some-feature"));

        touch_dir(&root.join("source-repo/app-one/.git"));
        touch_dir(&root.join("source-repo/app-two/.git"));

        tmp
    }

    /// Repo thật không phải git repo (project ví dụ đúng như vậy) —
    /// heuristic `.git` mù hoàn toàn, bảng Ecosystem thì không.
    #[test]
    fn declared_repos_locate_a_repository_root_that_holds_no_git_repo() {
        let tmp = tempfile::tempdir().unwrap();
        let root = tmp.path();
        touch_dir(&root.join("repos/some-api"));
        touch_dir(&root.join("repos/some-web"));
        touch_dir(&root.join("kit/.claude/agents"));

        let declared = vec!["some-api".to_string(), "some-web".to_string()];
        assert_eq!(detect_repository_root(root), None);
        assert_eq!(
            detect_repository_root_by_declared_repos(root, &declared, None),
            Some(root.join("repos"))
        );
    }

    /// `<DOCS_ROOT>/features/<feature>/` có một thư mục con MỖI repo, trùng
    /// tên y hệt — quy ước của kit, nên mọi project dùng kit đều tạo ra ứng
    /// viên giả này. Không loại nó ra thì điểm hoà và không dò được gì.
    #[test]
    fn the_docs_feature_tree_does_not_masquerade_as_the_repository_root() {
        let tmp = tempfile::tempdir().unwrap();
        let root = tmp.path();
        touch_dir(&root.join("repos/some-api"));
        touch_dir(&root.join("repos/some-web"));
        touch_dir(&root.join("docs/features"));
        touch_dir(&root.join("docs/features/login/some-api"));
        touch_dir(&root.join("docs/features/login/some-web"));

        let declared = vec!["some-api".to_string(), "some-web".to_string()];
        assert_eq!(
            detect_repository_root_by_declared_repos(root, &declared, Some(&root.join("docs"))),
            Some(root.join("repos"))
        );
        // Kể cả khi chưa dò ra `docsRoot`, thư mục nông hơn vẫn phải thắng.
        assert_eq!(
            detect_repository_root_by_declared_repos(root, &declared, None),
            Some(root.join("repos"))
        );
    }

    /// Bảng Ecosystem rỗng (project chưa `/init-kit`) → giữ nguyên hành vi cũ.
    #[test]
    fn no_declared_repos_falls_back_to_the_git_heuristic() {
        let tmp = tempfile::tempdir().unwrap();
        let root = tmp.path();
        touch_dir(&root.join("source-repo/app-one/.git"));

        assert_eq!(
            detect_repository_root_by_declared_repos(root, &[], None),
            detect_repository_root(root)
        );
    }

    #[test]
    fn detects_agents_root_despite_not_being_an_ancestor_of_repository_root() {
        let fixture = build_nested_fixture();
        let found = detect_agents_root(fixture.path()).expect("exactly one match");
        assert_eq!(found, fixture.path().join("agents-repo"));
    }

    #[test]
    fn detects_docs_root_nested_two_levels_below_agents_root() {
        let fixture = build_nested_fixture();
        let found = detect_docs_root(fixture.path()).expect("exactly one match");
        assert_eq!(found, fixture.path().join("agents-repo/agents-repo/docs"));
    }

    #[test]
    fn detects_repository_root_as_sibling_of_agents_root() {
        let fixture = build_nested_fixture();
        let found = detect_repository_root(fixture.path()).expect("exactly one match");
        assert_eq!(found, fixture.path().join("source-repo"));
    }

    #[test]
    fn ambiguous_agents_root_yields_none_not_a_guess() {
        let tmp = tempfile::tempdir().unwrap();
        touch_dir(&tmp.path().join("first/.claude/agents"));
        touch_dir(&tmp.path().join("second/.claude/agents"));

        assert!(detect_agents_root(tmp.path()).is_none());
    }

    #[test]
    fn no_match_anywhere_yields_none() {
        let tmp = tempfile::tempdir().unwrap();
        touch_dir(&tmp.path().join("unrelated/stuff"));

        assert!(detect_agents_root(tmp.path()).is_none());
        assert!(detect_docs_root(tmp.path()).is_none());
        assert!(detect_repository_root(tmp.path()).is_none());
    }

    #[test]
    fn does_not_descend_into_skipped_directories() {
        let tmp = tempfile::tempdir().unwrap();
        // A `.claude/agents` sitting inside `node_modules` must never be found.
        touch_dir(&tmp.path().join("node_modules/some-pkg/.claude/agents"));

        assert!(detect_agents_root(tmp.path()).is_none());
    }
}
