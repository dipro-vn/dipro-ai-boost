//! Read-only Backlog (Nulab) REST v2 client — the ONLY place this app
//! talks to Backlog over HTTP. Creating issues deliberately does not happen
//! here: that goes through `pm-agent` + the project's own Backlog MCP
//! server (see `commands::backlog`), so the app never re-implements the
//! kit's `backlog-workflow.md` conventions.
//!
//! Backlog v2 authenticates with an `apiKey` query parameter, which means
//! the secret ends up inside URLs. Every string that can reach a log, an
//! error message, or the frontend therefore goes through [`redact`] first —
//! that is the single most important rule in this module.

use serde_json::Value;

/// Everything that must never appear verbatim in output. Kept as a
/// function (not inline) so both the URL builder and the error paths use
/// the same definition.
const API_KEY_PARAM: &str = "apiKey=";

/// `https://<domain>/api/v2/<path>?apiKey=<key>`. `path` is a bare API
/// path without a leading slash, e.g. `users/myself` or `issues/PROJ-1`.
pub fn build_api_url(domain: &str, path: &str, api_key: &str) -> String {
    let domain = domain.trim().trim_end_matches('/');
    // A domain pasted with its scheme still works — users copy it out of
    // the browser bar more often than not.
    let host = domain
        .trim_start_matches("https://")
        .trim_start_matches("http://");
    format!(
        "https://{host}/api/v2/{path}?{API_KEY_PARAM}{}",
        urlencode(api_key)
    )
}

/// Minimal percent-encoding for the few characters that can legally appear
/// in a Backlog API key but would break a query string. Not a general URL
/// encoder — deliberately narrow, since the only value it ever sees is an
/// API key.
fn urlencode(value: &str) -> String {
    value
        .chars()
        .map(|c| match c {
            'A'..='Z' | 'a'..='z' | '0'..='9' | '-' | '_' | '.' | '~' => c.to_string(),
            other => other
                .to_string()
                .as_bytes()
                .iter()
                .map(|b| format!("%{b:02X}"))
                .collect(),
        })
        .collect()
}

/// Replaces every `apiKey=<value>` with `apiKey=***`. MUST wrap any text
/// derived from a request (URL, reqwest error, response body) before it is
/// logged, returned to the frontend, or written to disk.
pub fn redact(text: &str) -> String {
    let mut out = String::with_capacity(text.len());
    let mut rest = text;
    while let Some(idx) = rest.find(API_KEY_PARAM) {
        let (before, after) = rest.split_at(idx + API_KEY_PARAM.len());
        out.push_str(before);
        out.push_str("***");
        // The key ends at the next query/fragment/whitespace delimiter.
        let end = after
            .find(|c: char| c == '&' || c == '#' || c.is_whitespace() || c == '"')
            .unwrap_or(after.len());
        rest = &after[end..];
    }
    out.push_str(rest);
    out
}

/// `GET /users/myself` → the caller's display name, proving the key works
/// (AC-E1-20).
pub fn parse_myself(body: &Value) -> Option<String> {
    body.get("name")
        .and_then(Value::as_str)
        .or_else(|| body.get("userId").and_then(Value::as_str))
        .map(str::to_string)
}

/// `GET /issues/<key>` → the issue's status name as Backlog reports it
/// (one of the 9 statuses in `backlog-workflow.md`). The app deliberately
/// does not map these onto its own vocabulary — it shows what Backlog says.
pub fn parse_issue_status(body: &Value) -> Option<String> {
    body.get("status")
        .and_then(|status| status.get("name"))
        .and_then(Value::as_str)
        .map(str::to_string)
}

/// Outcome of one HTTP GET, already redacted.
pub enum FetchOutcome {
    Ok(Value),
    /// The resource is gone — AC-E5-17's `không tìm thấy`, distinct from a
    /// transport failure so the caller does not blame the network.
    NotFound,
    /// Anything else: transport error, auth failure, 5xx. Message is
    /// verbatim-but-redacted so AC-E1-21 can show the real reason.
    Failed(String),
}

/// The thin I/O shell. Everything interesting (URL shape, redaction,
/// parsing) lives in the pure functions above and is unit-tested; this
/// function is verified by the user against a real Backlog space.
pub async fn get_json(url: &str) -> FetchOutcome {
    let client = match reqwest::Client::builder()
        .timeout(std::time::Duration::from_secs(20))
        .build()
    {
        Ok(client) => client,
        Err(err) => return FetchOutcome::Failed(redact(&err.to_string())),
    };

    let response = match client.get(url).send().await {
        Ok(response) => response,
        Err(err) => return FetchOutcome::Failed(redact(&err.to_string())),
    };

    let status = response.status();
    if status == reqwest::StatusCode::NOT_FOUND {
        return FetchOutcome::NotFound;
    }

    let body = response.text().await.unwrap_or_default();
    if !status.is_success() {
        // AC-E1-21 — the raw error code and body are what the user needs to
        // fix a bad key or a wrong domain; only the key itself is stripped.
        return FetchOutcome::Failed(format!("HTTP {status}: {}", redact(body.trim())));
    }

    match serde_json::from_str::<Value>(&body) {
        Ok(value) => FetchOutcome::Ok(value),
        Err(err) => FetchOutcome::Failed(format!(
            "Phản hồi không phải JSON hợp lệ: {}",
            redact(&err.to_string())
        )),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn builds_v2_url_from_a_bare_domain() {
        let url = build_api_url("example.backlog.com", "users/myself", "abc123");
        assert_eq!(
            url,
            "https://example.backlog.com/api/v2/users/myself?apiKey=abc123"
        );
    }

    #[test]
    fn tolerates_a_domain_pasted_with_scheme_or_trailing_slash() {
        for domain in [
            "https://example.backlog.com",
            "http://example.backlog.com/",
            "example.backlog.com/",
        ] {
            let url = build_api_url(domain, "issues/PROJ-1", "k");
            assert_eq!(
                url,
                "https://example.backlog.com/api/v2/issues/PROJ-1?apiKey=k"
            );
        }
    }

    #[test]
    fn percent_encodes_key_characters_that_would_break_the_query() {
        let url = build_api_url("d.backlog.com", "users/myself", "a+b/c=d&e");
        assert!(url.ends_with("apiKey=a%2Bb%2Fc%3Dd%26e"));
    }

    /// The rule this module exists to enforce.
    #[test]
    fn redact_strips_the_key_from_every_shape_it_can_appear_in() {
        let key = "supersecretkey";
        let cases = [
            format!("https://d.backlog.com/api/v2/users/myself?apiKey={key}"),
            format!("error sending request for url (https://d.backlog.com/api/v2/issues?apiKey={key}&count=1)"),
            format!("HTTP 401: {{\"url\":\"?apiKey={key}\"}}"),
            format!("apiKey={key} some trailing words"),
            format!("apiKey={key}#fragment"),
        ];
        for case in cases {
            let redacted = redact(&case);
            assert!(
                !redacted.contains(key),
                "key leaked through redact(): {redacted}"
            );
            assert!(redacted.contains("apiKey=***"));
        }
    }

    #[test]
    fn redact_keeps_everything_after_the_key_intact() {
        let redacted = redact("https://d.backlog.com/api/v2/issues?apiKey=k1&count=100");
        assert_eq!(
            redacted,
            "https://d.backlog.com/api/v2/issues?apiKey=***&count=100"
        );
    }

    #[test]
    fn redact_is_a_noop_without_a_key() {
        assert_eq!(redact("kết nối thất bại"), "kết nối thất bại");
    }

    #[test]
    fn parses_display_name_and_issue_status() {
        let myself = serde_json::json!({ "id": 1, "userId": "pm", "name": "Nguyen PM" });
        assert_eq!(parse_myself(&myself).as_deref(), Some("Nguyen PM"));

        let issue = serde_json::json!({
            "issueKey": "PROJ-12",
            "status": { "id": 2, "name": "In-Progress" }
        });
        assert_eq!(parse_issue_status(&issue).as_deref(), Some("In-Progress"));

        // Missing/odd shapes are None, never a panic — Backlog plans differ.
        assert!(parse_issue_status(&serde_json::json!({})).is_none());
    }
}
