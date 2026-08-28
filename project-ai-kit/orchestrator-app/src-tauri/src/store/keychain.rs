//! OS keychain access for the Claude API key (AC-E1-22).
//!
//! There is deliberately NO file-based fallback here. If the keychain is
//! unavailable the app reports it — it never degrades to writing an API key
//! to disk, in any encoding. That is the whole point of AC-E1-22, and
//! `save_claude_api_key` has no code path that touches the filesystem.

use crate::error::{AppError, AppResult};

/// Service the removed Backlog integration saved its API key under. Kept
/// solely so `store::legacy_cleanup` can reclaim those orphaned entries.
const LEGACY_BACKLOG_SERVICE: &str = "vn.dipro.orchestrator-app.backlog";
const CLAUDE_SERVICE: &str = "vn.dipro.orchestrator-app.claude";

fn claude_entry(account: &str) -> AppResult<keyring::Entry> {
    keyring::Entry::new(CLAUDE_SERVICE, account).map_err(|err| AppError::Invalid {
        message: format!("Không mở được OS keychain cho Claude: {err}"),
    })
}

pub fn save_claude_api_key(account: &str, api_key: &str) -> AppResult<()> {
    claude_entry(account)?
        .set_password(api_key)
        .map_err(|err| AppError::Invalid {
            message: format!("Không lưu được Claude API key vào OS keychain: {err}"),
        })
}

pub fn read_claude_api_key(account: &str) -> AppResult<Option<String>> {
    match claude_entry(account)?.get_password() {
        Ok(key) => Ok(Some(key)),
        Err(keyring::Error::NoEntry) => Ok(None),
        Err(err) => Err(AppError::Invalid {
            message: format!("Không đọc được Claude API key từ OS keychain: {err}"),
        }),
    }
}

pub fn delete_claude_api_key(account: &str) -> AppResult<()> {
    match claude_entry(account)?.delete_credential() {
        Ok(()) | Err(keyring::Error::NoEntry) => Ok(()),
        Err(err) => Err(AppError::Invalid {
            message: format!("Không xoá được Claude API key khỏi OS keychain: {err}"),
        }),
    }
}

/// Removes the API key the removed Backlog integration left in the OS
/// keychain. Best-effort: a missing entry, or a keychain that cannot be
/// opened at all, both count as "already gone".
pub fn delete_legacy_backlog_api_key(account: &str) -> bool {
    let Ok(entry) = keyring::Entry::new(LEGACY_BACKLOG_SERVICE, account) else {
        return false;
    };
    matches!(entry.delete_credential(), Ok(()))
}

#[cfg(test)]
mod tests {
    use super::*;

    /// Round-trip against the real OS keychain. Skips cleanly (rather than
    /// failing) in environments without one — headless CI, for instance —
    /// mirroring how the live `claude` CLI tests skip when the binary is
    /// missing.
    #[test]
    fn claude_api_key_round_trips_through_the_os_keychain() {
        let account = "test-account.example.invalid";
        if save_claude_api_key(account, "probe").is_err() {
            eprintln!("skipping: OS keychain not usable in this environment");
            return;
        }
        save_claude_api_key(account, "test-value-not-a-real-key").unwrap();
        assert_eq!(
            read_claude_api_key(account).unwrap().as_deref(),
            Some("test-value-not-a-real-key")
        );
        delete_claude_api_key(account).unwrap();
        assert!(read_claude_api_key(account).unwrap().is_none());
        // Deleting twice is still Ok — callers use it as "ensure absent".
        delete_claude_api_key(account).unwrap();
    }

    /// AC-E1-22 — the guarantee that matters most: this module has no way
    /// to persist a secret anywhere except the keychain. Scans the real
    /// code only (everything above `#[cfg(test)]`), since this test's own
    /// forbidden-word list would otherwise match itself.
    #[test]
    fn module_has_no_filesystem_fallback() {
        let source = include_str!("keychain.rs");
        let code = source
            .split_once("#[cfg(test)]")
            .expect("test module marker must exist")
            .0;
        let body: String = code
            .lines()
            .filter(|line| !line.trim_start().starts_with("//"))
            .collect::<Vec<_>>()
            .join("\n");
        for forbidden in [
            "std::fs",
            "write_json_atomic",
            "write_text_atomic",
            "File::",
        ] {
            assert!(
                !body.contains(forbidden),
                "keychain.rs must never gain a filesystem path ({forbidden})"
            );
        }
    }
}
