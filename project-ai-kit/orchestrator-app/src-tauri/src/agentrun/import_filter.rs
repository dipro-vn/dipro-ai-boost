//! File-exclusion filtering for Import Input (AC-E2-32) — reads the OPENED
//! PROJECT'S OWN `.claude/config/restricted-paths.json` (single source of
//! truth per `SECURITY.md`) instead of duplicating the pattern list, so
//! this stays in sync with whatever the kit itself considers a secret.
//! Falls back to a small built-in list when the project hasn't run a kit
//! version that ships this file.
//!
//! Mirrors `.claude/hooks/block-secret-read.js`'s exact semantics: allow
//! patterns checked first (any match → never excluded), then deny patterns
//! (first match wins, reported as the exclusion reason) — same order, same
//! "first match", same un-anchored substring regex behavior.

use std::path::Path;

use regex::Regex;
use serde::Deserialize;

/// Patterns in `restricted-paths.json` are written against `/`-separated
/// paths (`SECURITY.md`'s own examples) regardless of host OS. Shared by
/// every caller that needs a path relative to one of the project's roots
/// turned into what `ImportFilter::exclusion_reason` expects (Import
/// Input, `read_artifact`, the folder explorer's `list_directory`).
pub(crate) fn to_pattern_path(rel: &Path) -> String {
    rel.components()
        .map(|c| c.as_os_str().to_string_lossy().into_owned())
        .collect::<Vec<_>>()
        .join("/")
}

/// Used only when the opened project has no `restricted-paths.json` yet —
/// a conservative subset of the kit's own list (see `SECURITY.md`), not a
/// claim of parity with it.
const BUILTIN_DENY_PATTERNS: &[&str] = &[
    r"\.env(\..+)?$",
    r"(^|/)\.npmrc$",
    r"(^|/)\.netrc$",
    r"(^|/)\.ssh/",
    r"\.keystore$",
    r"\.jks$",
    r"\.p12$",
    r"\.pfx$",
    r"\.pem$",
    r"\.p8$",
    r"\.key$",
    r"google-services\.json$",
    r"GoogleService-Info\.plist$",
    r"credentials\.json$",
    r"(^|/)\.git/config$",
];

#[derive(Deserialize, Default)]
#[serde(rename_all = "camelCase")]
struct RestrictedPathsConfig {
    #[serde(default)]
    deny_read_patterns: Vec<String>,
    #[serde(default)]
    allow_exceptions: Vec<String>,
}

fn compile(patterns: &[String]) -> Vec<Regex> {
    patterns.iter().filter_map(|p| Regex::new(p).ok()).collect()
}

fn load_patterns(agents_root: &Path) -> (Vec<Regex>, Vec<Regex>) {
    let config_path = agents_root
        .join(".claude")
        .join("config")
        .join("restricted-paths.json");
    let parsed = std::fs::read_to_string(&config_path)
        .ok()
        .and_then(|raw| serde_json::from_str::<RestrictedPathsConfig>(&raw).ok());

    match parsed {
        Some(cfg) => (
            compile(&cfg.deny_read_patterns),
            compile(&cfg.allow_exceptions),
        ),
        None => {
            let builtin: Vec<String> = BUILTIN_DENY_PATTERNS
                .iter()
                .map(|s| s.to_string())
                .collect();
            (compile(&builtin), Vec::new())
        }
    }
}

pub struct ImportFilter {
    deny: Vec<Regex>,
    allow: Vec<Regex>,
}

impl ImportFilter {
    pub fn for_project(agents_root: &Path) -> Self {
        let (deny, allow) = load_patterns(agents_root);
        ImportFilter { deny, allow }
    }

    #[cfg(test)]
    fn from_patterns(deny: &[&str], allow: &[&str]) -> Self {
        ImportFilter {
            deny: deny.iter().map(|p| Regex::new(p).unwrap()).collect(),
            allow: allow.iter().map(|p| Regex::new(p).unwrap()).collect(),
        }
    }

    /// `relative_path` should use `/` separators regardless of host OS, to
    /// match what the patterns (written against Unix-style paths in
    /// `SECURITY.md`) expect.
    pub fn exclusion_reason(&self, relative_path: &str) -> Option<String> {
        if self.allow.iter().any(|r| r.is_match(relative_path)) {
            return None;
        }
        self.deny
            .iter()
            .find(|r| r.is_match(relative_path))
            .map(|r| format!("khớp pattern cấm đọc: {r}"))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn env_file_is_excluded_by_builtin_patterns() {
        let filter = ImportFilter::from_patterns(BUILTIN_DENY_PATTERNS, &[]);
        assert!(filter.exclusion_reason(".env").is_some());
        assert!(filter.exclusion_reason("backend/.env.production").is_some());
    }

    #[test]
    fn ordinary_markdown_file_is_never_excluded() {
        let filter = ImportFilter::from_patterns(BUILTIN_DENY_PATTERNS, &[]);
        assert!(filter.exclusion_reason("docs/SPEC.md").is_none());
    }

    #[test]
    fn allow_exception_wins_over_a_matching_deny_pattern() {
        let filter = ImportFilter::from_patterns(&[r"\.env$"], &[r"\.env\.example$"]);
        assert!(filter.exclusion_reason(".env.example").is_none());
        assert!(filter.exclusion_reason("real.env").is_some());
    }

    #[test]
    fn falls_back_to_builtin_list_when_project_has_no_restricted_paths_json() {
        let tmp = tempfile::tempdir().unwrap();
        let filter = ImportFilter::for_project(tmp.path());
        assert!(filter.exclusion_reason(".env").is_some());
        assert!(filter.exclusion_reason("README.md").is_none());
    }

    #[test]
    fn uses_the_projects_own_restricted_paths_json_when_present() {
        let tmp = tempfile::tempdir().unwrap();
        let config_dir = tmp.path().join(".claude/config");
        std::fs::create_dir_all(&config_dir).unwrap();
        std::fs::write(
            config_dir.join("restricted-paths.json"),
            r#"{"denyReadPatterns":["custom-secret\\.txt$"],"allowExceptions":[]}"#,
        )
        .unwrap();

        let filter = ImportFilter::for_project(tmp.path());
        assert!(filter.exclusion_reason("custom-secret.txt").is_some());
        // Not in the project's own list (unlike the builtin fallback) —
        // proves the project's file actually took effect, not the fallback.
        assert!(filter.exclusion_reason(".env").is_none());
    }
}
