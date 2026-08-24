//! OS keychain access for integration credentials (AC-E1-19/22).
//!
//! There is deliberately NO file-based fallback here. If the keychain is
//! unavailable the app reports it and the caller disables the integration —
//! it never degrades to writing an API key to disk, in any encoding. That
//! is the whole point of AC-E1-22, and `save_api_key` has no code path that
//! touches the filesystem.

use crate::error::{AppError, AppResult};

/// Keychain service name. Reverse-DNS + a `backlog` suffix so a future
/// second integration gets its own service rather than sharing entries.
const SERVICE: &str = "vn.dipro.orchestrator-app.backlog";
const CLAUDE_SERVICE: &str = "vn.dipro.orchestrator-app.claude";

/// Probe account used only by `keychain_availability` — written and deleted
/// immediately, never left behind.
const PROBE_ACCOUNT: &str = "__availability_probe__";

fn entry(account: &str) -> AppResult<keyring::Entry> {
    keyring::Entry::new(SERVICE, account).map_err(|err| AppError::Invalid {
        message: format!("Không mở được OS keychain: {err}"),
    })
}

fn claude_entry(account: &str) -> AppResult<keyring::Entry> {
    keyring::Entry::new(CLAUDE_SERVICE, account).map_err(|err| AppError::Invalid {
        message: format!("Không mở được OS keychain cho Claude: {err}"),
    })
}

pub fn save_api_key(account: &str, api_key: &str) -> AppResult<()> {
    entry(account)?
        .set_password(api_key)
        .map_err(|err| AppError::Invalid {
            message: format!("Không lưu được API key vào OS keychain: {err}"),
        })
}

/// `Ok(None)` = no entry for this account (never saved, or deleted) — not
/// an error, since the Settings screen asks about a not-yet-configured
/// project all the time.
pub fn read_api_key(account: &str) -> AppResult<Option<String>> {
    match entry(account)?.get_password() {
        Ok(key) => Ok(Some(key)),
        Err(keyring::Error::NoEntry) => Ok(None),
        Err(err) => Err(AppError::Invalid {
            message: format!("Không đọc được API key từ OS keychain: {err}"),
        }),
    }
}

/// Deleting an entry that isn't there succeeds — "make sure it's gone" is
/// the caller's intent, and a missing entry already satisfies it.
pub fn delete_api_key(account: &str) -> AppResult<()> {
    match entry(account)?.delete_credential() {
        Ok(()) | Err(keyring::Error::NoEntry) => Ok(()),
        Err(err) => Err(AppError::Invalid {
            message: format!("Không xoá được API key khỏi OS keychain: {err}"),
        }),
    }
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

/// AC-E1-22 — a real round-trip probe (write, read back, delete) rather
/// than merely constructing an `Entry`, because on Linux the failure only
/// surfaces when the secret service is actually talked to. Returns the
/// verbatim error so the UI can show why the section is disabled.
pub fn keychain_availability() -> Result<(), String> {
    let entry = keyring::Entry::new(SERVICE, PROBE_ACCOUNT).map_err(|err| err.to_string())?;
    entry.set_password("probe").map_err(|err| err.to_string())?;
    let read_back = entry.get_password().map_err(|err| err.to_string())?;
    // Best-effort cleanup: a probe left behind is harmless, and failing to
    // delete it does not mean the keychain is unusable.
    let _ = entry.delete_credential();
    if read_back == "probe" {
        Ok(())
    } else {
        Err("keychain trả về giá trị khác giá trị vừa ghi".to_string())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    /// Round-trip against the real OS keychain. Skips cleanly (rather than
    /// failing) in environments without one — headless CI, for instance —
    /// mirroring how the live `claude` CLI tests skip when the binary is
    /// missing.
    #[test]
    fn api_key_round_trips_through_the_os_keychain() {
        if keychain_availability().is_err() {
            eprintln!("skipping: OS keychain not usable in this environment");
            return;
        }
        let account = "test-account.example.invalid";
        save_api_key(account, "test-value-not-a-real-key").unwrap();
        assert_eq!(
            read_api_key(account).unwrap().as_deref(),
            Some("test-value-not-a-real-key")
        );
        delete_api_key(account).unwrap();
        assert!(read_api_key(account).unwrap().is_none());
        // Deleting twice is still Ok — callers use it as "ensure absent".
        delete_api_key(account).unwrap();
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
