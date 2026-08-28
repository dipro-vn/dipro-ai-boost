use std::collections::hash_map::DefaultHasher;
use std::hash::{Hash, Hasher};
use std::path::{Path, PathBuf};

use chrono::{DateTime, NaiveDateTime, Utc};

use crate::domain::version_ref::{VersionRef, VersionSource};
use crate::error::{AppError, AppResult};
use crate::store::atomic_write::write_text_atomic;
use crate::store::orchestrator_dir;

const SNAPSHOT_TIMESTAMP_FORMAT: &str = "%Y%m%dT%H%M%S%3fZ";

/// A short, filesystem-safe, deterministic id for an artifact's absolute
/// path. `DefaultHasher::default()` (unlike `HashMap`'s `RandomState`) uses
/// fixed keys, so this is stable across app restarts — required, since the
/// same artifact must always map back to the same snapshot directory.
fn slug_for(path: &Path) -> String {
    let mut hasher = DefaultHasher::new();
    path.to_string_lossy().hash(&mut hasher);
    format!("{:016x}", hasher.finish())
}

pub fn snapshot_dir(orchestrator_root: &Path, artifact_path: &Path) -> PathBuf {
    orchestrator_dir::snapshots_dir(orchestrator_root).join(slug_for(artifact_path))
}

fn parse_snapshot_timestamp(filename: &str) -> Option<DateTime<Utc>> {
    let stem = filename.strip_suffix(".md")?;
    NaiveDateTime::parse_from_str(stem, SNAPSHOT_TIMESTAMP_FORMAT)
        .ok()
        .map(|naive| naive.and_utc())
}

/// Snapshot ids are generated filenames, never arbitrary paths. Keeping this
/// check at the store boundary protects every caller from absolute-path and
/// `..` traversal even if a future command forgets its own validation.
pub fn is_valid_snapshot_id(id: &str) -> bool {
    Path::new(id).components().count() == 1 && parse_snapshot_timestamp(id).is_some()
}

/// Newest first. Filenames themselves encode the snapshot time (not
/// filesystem mtime, which copy/backup tools can disturb).
pub fn list_snapshot_versions(dir: &Path) -> Vec<VersionRef> {
    let mut entries: Vec<(String, DateTime<Utc>)> = std::fs::read_dir(dir)
        .into_iter()
        .flatten()
        .filter_map(|entry| entry.ok())
        .filter_map(|entry| {
            let filename = entry.file_name().to_string_lossy().into_owned();
            let timestamp = parse_snapshot_timestamp(&filename)?;
            Some((filename, timestamp))
        })
        .collect();
    entries.sort_by_key(|(_, timestamp)| std::cmp::Reverse(*timestamp));

    entries
        .into_iter()
        .map(|(filename, timestamp)| VersionRef {
            id: filename,
            label: timestamp.format("%Y-%m-%d %H:%M:%S").to_string(),
            source: VersionSource::Snapshot,
            timestamp: timestamp.to_rfc3339(),
        })
        .collect()
}

pub fn read_snapshot(dir: &Path, id: &str) -> AppResult<String> {
    if !is_valid_snapshot_id(id) {
        return Err(AppError::Invalid {
            message: format!("Snapshot ID không hợp lệ: {id}"),
        });
    }
    Ok(std::fs::read_to_string(dir.join(id))?)
}

/// Writes a new snapshot only if `content` differs from the most recent
/// one (or none exists yet) — returns whether a snapshot was actually
/// written. Called on every watcher tick for every non-git-tracked
/// artifact (`pipeline_state::compute_and_persist`), so this no-op path
/// matters: without it, every tick would write a new file regardless of
/// whether anything changed.
pub fn write_snapshot_if_changed(dir: &Path, content: &str) -> AppResult<bool> {
    if let Some(latest) = list_snapshot_versions(dir).first() {
        let latest_content = read_snapshot(dir, &latest.id)?;
        if latest_content == content {
            return Ok(false);
        }
    }

    let filename = format!("{}.md", Utc::now().format(SNAPSHOT_TIMESTAMP_FORMAT));
    write_text_atomic(&dir.join(filename), content)?;
    Ok(true)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn slug_is_deterministic_across_calls() {
        let path = Path::new("/some/project/docs/features/x/SPEC.md");
        assert_eq!(slug_for(path), slug_for(path));
    }

    #[test]
    fn slug_differs_for_different_paths() {
        let a = Path::new("/some/project/docs/features/x/SPEC.md");
        let b = Path::new("/some/project/docs/features/y/SPEC.md");
        assert_ne!(slug_for(a), slug_for(b));
    }

    #[test]
    fn first_snapshot_is_always_written() {
        let tmp = tempfile::tempdir().unwrap();
        let dir = tmp.path().join("snap");

        let wrote = write_snapshot_if_changed(&dir, "hello").unwrap();
        assert!(wrote);
        assert_eq!(list_snapshot_versions(&dir).len(), 1);
    }

    #[test]
    fn unchanged_content_does_not_create_a_new_snapshot() {
        let tmp = tempfile::tempdir().unwrap();
        let dir = tmp.path().join("snap");

        assert!(write_snapshot_if_changed(&dir, "hello").unwrap());
        assert!(!write_snapshot_if_changed(&dir, "hello").unwrap());
        assert_eq!(list_snapshot_versions(&dir).len(), 1);
    }

    #[test]
    fn changed_content_creates_a_new_snapshot_and_keeps_the_old_one() {
        let tmp = tempfile::tempdir().unwrap();
        let dir = tmp.path().join("snap");

        assert!(write_snapshot_if_changed(&dir, "v1").unwrap());
        // Sleep isn't ideal in tests, but the timestamp format has
        // millisecond resolution and two writes in the same test process
        // could otherwise collide on the filename.
        std::thread::sleep(std::time::Duration::from_millis(2));
        assert!(write_snapshot_if_changed(&dir, "v2").unwrap());

        let versions = list_snapshot_versions(&dir);
        assert_eq!(versions.len(), 2);
        // Newest first.
        assert_eq!(read_snapshot(&dir, &versions[0].id).unwrap(), "v2");
        assert_eq!(read_snapshot(&dir, &versions[1].id).unwrap(), "v1");
    }

    #[test]
    fn list_snapshot_versions_empty_for_missing_dir() {
        let tmp = tempfile::tempdir().unwrap();
        let dir = tmp.path().join("does-not-exist");
        assert!(list_snapshot_versions(&dir).is_empty());
    }

    /// Regression for the traversal hole `is_valid_snapshot_id` closes:
    /// before it existed, `read_snapshot` joined `id` straight into the
    /// filesystem path.
    #[test]
    fn read_snapshot_rejects_a_path_traversal_id() {
        let tmp = tempfile::tempdir().unwrap();
        let dir = tmp.path().join("snap");
        assert!(write_snapshot_if_changed(&dir, "hello").unwrap());

        for id in ["../../etc/passwd", "/etc/passwd", "..", "a/b.md"] {
            let err = read_snapshot(&dir, id).unwrap_err();
            assert!(format!("{err:?}").contains("Snapshot ID không hợp lệ"));
        }
    }
}
