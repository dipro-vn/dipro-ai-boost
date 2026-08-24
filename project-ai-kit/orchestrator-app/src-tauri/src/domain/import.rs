use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct ExcludedFile {
    pub relative_path: String,
    pub reason: String,
}

/// AC-E2-22 — what Import Input shows before the user confirms. Flat lists
/// rather than a nested tree: the frontend already has everything it needs
/// to render a tree from `/`-separated relative paths, and a flat shape
/// keeps this type (and its tests) simple.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct ImportPreview {
    pub included: Vec<String>,
    pub excluded: Vec<ExcludedFile>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct ImportedRun {
    pub run_id: String,
    /// Absolute path to the copy under `.orchestrator/inputs/<run-id>/` —
    /// this is what goes into `ba-agent`'s prompt (AC-E2-23), not the
    /// user's original folder.
    pub copied_path: String,
    pub feature_name: String,
    /// Relative paths of everything actually copied, in the same order as
    /// `ImportPreview.included`.
    ///
    /// The prompt has to name these files one by one: `ba-agent`'s declared
    /// toolset (`Read`, `Write`, `Edit`, `tilth_*`) contains no directory
    /// listing tool that works without the tilth MCP server, so handing it
    /// only `copied_path` made it `Read` the directory (EISDIR) and then
    /// guess file names until it gave up — observed for real on the first
    /// `user-signup` run.
    pub files: Vec<String>,
}
