use serde::{Deserialize, Serialize};

/// One browsable root the folder explorer offers, from
/// `commands::explorer::get_explorer_roots`. Usually a single entry (the
/// common ancestor directory of all 3 project roots — "the whole project
/// folder", matching what the user sees outside the app), but falls back
/// to one entry per project root (agentsRoot/docsRoot/repositoryRoot) when
/// no meaningful common ancestor exists (e.g. roots on different drives —
/// `domain::project::ProjectPaths` itself warns the 3 are never guaranteed
/// to nest).
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct ExplorerRootEntry {
    pub label: String,
    pub path: String,
    /// Whether new files/folders may be created directly in this root.
    ///
    /// Not always true: the root the tree shows is the common ancestor of
    /// the 3 project roots, and when those are siblings that ancestor is a
    /// plain folder the project does not manage. The frontend needs to know
    /// before it offers "Tạo file" on the root row, rather than letting the
    /// user find out from a rejected command.
    #[serde(default)]
    pub can_modify: bool,
}

/// One entry from `commands::explorer::list_directory` — one level of
/// whatever `ExplorerRootEntry` the frontend is browsing, never a full
/// recursive tree (see `list_directory`'s own doc comment for why). `path`
/// is always absolute so it can be fed straight back into `list_directory`
/// (expand) or `read_artifact` (open) with no relative-path reconstruction
/// on either side.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct DirEntry {
    pub name: String,
    pub path: String,
    pub is_dir: bool,
    /// True when this path matches the project's restricted-paths deny
    /// list (`agentrun::import_filter::ImportFilter`). Mirrors
    /// `ImportPreview`'s "show it, mark it excluded" behavior — the
    /// filename is never hidden, only opening its content is refused
    /// (enforced again, independently, by `read_artifact`).
    pub is_restricted: bool,
    /// True when Explorer actions are allowed for this path. Browsing can
    /// include the common ancestor of the project roots, while writes are
    /// deliberately narrower and exclude protected directories.
    pub can_modify: bool,
}
