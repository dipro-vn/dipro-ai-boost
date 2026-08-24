use std::path::Path;

use serde::Serialize;

use crate::error::AppResult;

/// Serializes `value` as pretty JSON and writes it to `path` atomically:
/// write to a temp file in the SAME directory as `path` (required for the
/// rename to be atomic — cross-filesystem renames are not), then persist
/// over the destination. A crash mid-write leaves the previous `path`
/// untouched — there is never a partially-written file to read back.
///
/// This is the ONLY sanctioned way to write JSON state in this codebase —
/// every module that persists JSON (recent projects, config, pipeline
/// def, feature state) must go through this, never call `std::fs::write`
/// directly.
pub fn write_json_atomic<T: Serialize>(path: &Path, value: &T) -> AppResult<()> {
    let contents = serde_json::to_vec_pretty(value)?;
    write_bytes_atomic(path, &contents)
}

/// Same guarantee as [`write_json_atomic`], for plain text — used by
/// snapshots (`store::snapshot`), which store raw markdown, not JSON.
pub fn write_text_atomic(path: &Path, content: &str) -> AppResult<()> {
    write_bytes_atomic(path, content.as_bytes())
}

fn write_bytes_atomic(path: &Path, contents: &[u8]) -> AppResult<()> {
    let dir = path
        .parent()
        .ok_or_else(|| crate::error::AppError::Invalid {
            message: format!("path has no parent directory: {}", path.display()),
        })?;
    std::fs::create_dir_all(dir)?;

    let mut tmp = tempfile::NamedTempFile::new_in(dir)?;
    std::io::Write::write_all(&mut tmp, contents)?;
    tmp.persist(path).map_err(|e| e.error)?;

    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde::Deserialize;

    #[derive(Serialize, Deserialize, PartialEq, Debug)]
    struct Sample {
        value: u32,
    }

    #[test]
    fn write_json_atomic_creates_parent_dirs_and_round_trips() {
        let tmp = tempfile::tempdir().unwrap();
        let path = tmp.path().join("nested/dir/data.json");

        write_json_atomic(&path, &Sample { value: 42 }).unwrap();

        let raw = std::fs::read_to_string(&path).unwrap();
        let parsed: Sample = serde_json::from_str(&raw).unwrap();
        assert_eq!(parsed, Sample { value: 42 });
    }

    #[test]
    fn write_json_atomic_overwrites_existing_file() {
        let tmp = tempfile::tempdir().unwrap();
        let path = tmp.path().join("data.json");

        write_json_atomic(&path, &Sample { value: 1 }).unwrap();
        write_json_atomic(&path, &Sample { value: 2 }).unwrap();

        let raw = std::fs::read_to_string(&path).unwrap();
        let parsed: Sample = serde_json::from_str(&raw).unwrap();
        assert_eq!(parsed, Sample { value: 2 });
    }

    #[test]
    fn write_text_atomic_round_trips_plain_content() {
        let tmp = tempfile::tempdir().unwrap();
        let path = tmp.path().join("snapshots/abc/20260814T000000000Z.md");

        write_text_atomic(&path, "# Hello\n\nworld").unwrap();

        assert_eq!(std::fs::read_to_string(&path).unwrap(), "# Hello\n\nworld");
    }
}
