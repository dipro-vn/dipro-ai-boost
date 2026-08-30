//! Reads and writes `.orchestrator/design-refs/<feature>.json` — the Figma
//! selection URL `design-analyst` was given, kept so stage ⑤'s
//! `frontend-agent`/`mobile-agent` can reach the same design.
//!
//! Same shape as `store::contract_lock`'s `skip.json`: one mutable JSON
//! file, written atomically, read tolerantly. A missing or corrupt file is
//! `None`, never an error — nothing here is load-bearing enough to fail a
//! run over.

use std::path::Path;

use crate::domain::design_ref::DesignRef;
use crate::error::AppResult;
use crate::store::atomic_write::write_json_atomic;
use crate::store::orchestrator_dir;

pub fn read(project_root: &Path, feature: &str) -> Option<DesignRef> {
    let raw =
        std::fs::read_to_string(orchestrator_dir::design_ref_path(project_root, feature)).ok()?;
    serde_json::from_str(&raw).ok()
}

/// Overwrites whatever URL was stored — a newer selection always wins.
/// A blank `url` is a no-op rather than an error or an empty record: the
/// callers pass user input straight through, and "the user left the box
/// empty" must not wipe a URL they gave earlier.
pub fn write(project_root: &Path, feature: &str, url: &str, source_slot: &str) -> AppResult<()> {
    let url = url.trim();
    if url.is_empty() {
        return Ok(());
    }
    let path = orchestrator_dir::design_ref_path(project_root, feature);
    write_json_atomic(
        &path,
        &DesignRef {
            url: url.to_string(),
            updated_at: chrono::Utc::now().to_rfc3339(),
            source_slot: source_slot.to_string(),
        },
    )
}

/// The first Figma URL inside a free-text answer — for the clarification
/// path (AC-E2-35), where the user pastes the URL into the answer box
/// rather than the dedicated field, usually with a sentence around it.
///
/// Deliberately a whitespace scan rather than a regex: the crate has no
/// regex dependency, and "a token that starts with http and mentions
/// figma.com" is the whole rule. Trailing punctuation from prose (`.`,
/// `,`, `)`, quotes) is trimmed — a URL at the end of a sentence is the
/// common case, and Figma's own links never end in those characters.
pub fn extract_figma_url(text: &str) -> Option<&str> {
    text.split_whitespace()
        .map(|token| token.trim_end_matches(['.', ',', ';', ':', ')', ']', '"', '\'', '>']))
        .find(|token| token.starts_with("http") && token.to_ascii_lowercase().contains("figma.com"))
}

#[cfg(test)]
mod tests {
    use super::*;

    const URL: &str = "https://www.figma.com/design/abc123/App?node-id=12-34";

    #[test]
    fn write_then_read_round_trips_and_a_newer_url_replaces_the_old_one() {
        let tmp = tempfile::tempdir().unwrap();
        assert!(
            read(tmp.path(), "user-login").is_none(),
            "nothing stored yet"
        );

        write(tmp.path(), "user-login", URL, "design-analyst").unwrap();
        let stored = read(tmp.path(), "user-login").expect("just written");
        assert_eq!(stored.url, URL);
        assert_eq!(stored.source_slot, "design-analyst");

        let newer = "https://www.figma.com/design/abc123/App?node-id=99-1";
        write(tmp.path(), "user-login", newer, "design-analyst").unwrap();
        assert_eq!(read(tmp.path(), "user-login").unwrap().url, newer);
    }

    /// The box left empty must not erase a URL given earlier — `run_slot`
    /// calls this unconditionally with whatever the user typed.
    #[test]
    fn a_blank_url_leaves_an_existing_record_alone() {
        let tmp = tempfile::tempdir().unwrap();
        write(tmp.path(), "user-login", URL, "design-analyst").unwrap();

        write(tmp.path(), "user-login", "   ", "design-analyst").unwrap();

        assert_eq!(read(tmp.path(), "user-login").unwrap().url, URL);
    }

    #[test]
    fn urls_are_trimmed_and_kept_per_feature() {
        let tmp = tempfile::tempdir().unwrap();
        write(
            tmp.path(),
            "user-login",
            &format!("  {URL}\n"),
            "design-analyst",
        )
        .unwrap();

        assert_eq!(read(tmp.path(), "user-login").unwrap().url, URL);
        assert!(read(tmp.path(), "payment-checkout").is_none());
    }

    #[test]
    fn a_corrupt_file_reads_as_nothing_stored_rather_than_an_error() {
        let tmp = tempfile::tempdir().unwrap();
        let path = orchestrator_dir::design_ref_path(tmp.path(), "user-login");
        std::fs::create_dir_all(path.parent().unwrap()).unwrap();
        std::fs::write(&path, "{ not json").unwrap();

        assert!(read(tmp.path(), "user-login").is_none());
    }

    #[test]
    fn extract_figma_url_finds_the_link_inside_a_sentence() {
        assert_eq!(
            extract_figma_url(&format!("Đây nhé: {URL} — phân tích màn Login giúp mình.")),
            Some(URL)
        );
        // Trailing sentence punctuation is not part of the URL.
        assert_eq!(extract_figma_url(&format!("Link: {URL}.")), Some(URL));
        assert_eq!(extract_figma_url(&format!("(xem {URL})")), Some(URL));
    }

    #[test]
    fn extract_figma_url_ignores_answers_with_no_figma_link() {
        assert_eq!(
            extract_figma_url("chưa có link, để mình hỏi lại designer"),
            None
        );
        assert_eq!(extract_figma_url("https://example.com/design/abc"), None);
        assert_eq!(extract_figma_url(""), None);
    }
}
