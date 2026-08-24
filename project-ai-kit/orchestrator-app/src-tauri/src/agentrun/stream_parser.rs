//! Parses each line of `claude -p ... --output-format stream-json`'s output
//! into a normalized [`StreamEvent`]. Tolerant by design
//! (`ASSUMPTIONS-GAPS.md` A5): unknown `type`/`subtype` values become
//! [`StreamEvent::Unrecognized`] rather than a parse error, and a single raw
//! line's `content` array is NEVER assumed to be the complete message for
//! its `message_id` — a later line can carry more blocks for the same id
//! (observed directly: a `thinking` block and a `text` block for the same
//! message arrived as 2 separate lines, each a complete JSON object).

use serde::{Deserialize, Serialize};

/// `rename_all` on an enum renames only the VARIANT names — the fields
/// inside each variant need `rename_all_fields` as well. Without it this
/// type serialized `tool_name`/`is_error`/`estimated_tokens_delta` while
/// the TS mirror read `toolName`/`isError`/`estimatedTokensDelta`, so the
/// log console printed `undefined(...)` for every tool call and the
/// realtime cost estimate accumulated `NaN`. The tests below assert the
/// exact wire keys, not just a round-trip — a round-trip passes happily
/// with the wrong names.
#[derive(Debug, Clone, PartialEq, Serialize)]
#[serde(
    tag = "kind",
    rename_all = "camelCase",
    rename_all_fields = "camelCase"
)]
pub enum StreamEvent {
    SessionStarted {
        session_id: String,
        model: String,
    },
    ThinkingProgress {
        /// Cumulative WITHIN the current thinking block only — resets back
        /// down each time a new block starts (observed directly in the
        /// fixture: 137 then 1). NOT a running total for the whole run —
        /// use `estimated_tokens_delta` summed across every event for that.
        estimated_tokens: u64,
        /// The increment since the previous `thinking_tokens` event —
        /// AC-E2-07/AC-E6-19's realtime cost estimate sums this across the
        /// whole run, since `estimated_tokens` alone would undercount after
        /// any reset.
        estimated_tokens_delta: u64,
    },
    AssistantThinking {
        message_id: String,
        text: String,
    },
    AssistantText {
        message_id: String,
        text: String,
    },
    ToolCall {
        message_id: String,
        tool_use_id: String,
        tool_name: String,
        input: serde_json::Value,
    },
    ToolResult {
        tool_use_id: String,
        content: String,
        /// Only the success shape (no `is_error` key at all) has been
        /// observed for real — this defaults to `false` for that case but
        /// has NOT been verified against an actual tool-error response.
        is_error: bool,
    },
    RunFinished {
        is_error: bool,
        total_cost_usd: f64,
        session_id: String,
        stop_reason: Option<String>,
    },
    /// Any `type`/`subtype` not modeled above — every `hook_*` system
    /// event, `rate_limit_event`, and anything a future CLI version adds.
    /// Never a parse failure.
    Unrecognized {
        raw_type: String,
    },
}

// --- raw wire shapes (private, deserialize-only) ---

#[derive(Deserialize)]
#[serde(tag = "type")]
enum RawLine {
    #[serde(rename = "system")]
    System(RawSystem),
    #[serde(rename = "assistant")]
    Assistant(RawAssistant),
    #[serde(rename = "user")]
    User(RawUser),
    #[serde(rename = "result")]
    Result(RawResult),
    #[serde(other)]
    Other,
}

#[derive(Deserialize)]
struct RawSystem {
    subtype: Option<String>,
    session_id: Option<String>,
    model: Option<String>,
    estimated_tokens: Option<u64>,
    estimated_tokens_delta: Option<u64>,
}

#[derive(Deserialize)]
struct RawAssistant {
    message: RawAssistantMessage,
}

#[derive(Deserialize)]
struct RawAssistantMessage {
    id: String,
    content: Vec<RawContentBlock>,
}

#[derive(Deserialize)]
#[serde(tag = "type", rename_all = "snake_case")]
enum RawContentBlock {
    Thinking {
        thinking: String,
    },
    Text {
        text: String,
    },
    ToolUse {
        id: String,
        name: String,
        input: serde_json::Value,
    },
    #[serde(other)]
    Other,
}

#[derive(Deserialize)]
struct RawUser {
    message: RawUserMessage,
}

#[derive(Deserialize)]
struct RawUserMessage {
    content: Vec<RawUserContentBlock>,
}

#[derive(Deserialize)]
struct RawUserContentBlock {
    #[serde(rename = "type")]
    kind: Option<String>,
    tool_use_id: Option<String>,
    content: Option<ToolResultContent>,
    #[serde(default)]
    is_error: bool,
}

/// `tool_result.content` has only ever been observed as a plain string —
/// the `Other` arm exists so a structured-content shape degrades to a
/// JSON-stringified fallback instead of failing the whole line.
#[derive(Deserialize)]
#[serde(untagged)]
enum ToolResultContent {
    Text(String),
    Other(serde_json::Value),
}

#[derive(Deserialize)]
struct RawResult {
    is_error: bool,
    total_cost_usd: f64,
    session_id: String,
    stop_reason: Option<String>,
}

fn raw_type_of(trimmed: &str) -> String {
    serde_json::from_str::<serde_json::Value>(trimmed)
        .ok()
        .and_then(|v| v.get("type").and_then(|t| t.as_str()).map(str::to_owned))
        .unwrap_or_else(|| "unknown".to_string())
}

/// Parses one JSONL line into 0, 1, or more events — a line's content array
/// can in principle hold multiple blocks (only single-block lines observed
/// so far, but nothing in the format guarantees that stays true).
pub fn parse_line(line: &str) -> Vec<StreamEvent> {
    let trimmed = line.trim();
    if trimmed.is_empty() {
        return Vec::new();
    }

    let Ok(parsed) = serde_json::from_str::<RawLine>(trimmed) else {
        return vec![StreamEvent::Unrecognized {
            raw_type: raw_type_of(trimmed),
        }];
    };

    match parsed {
        RawLine::System(sys) => match sys.subtype.as_deref() {
            Some("init") => match (sys.session_id, sys.model) {
                (Some(session_id), Some(model)) => {
                    vec![StreamEvent::SessionStarted { session_id, model }]
                }
                _ => vec![StreamEvent::Unrecognized {
                    raw_type: "system.init".to_string(),
                }],
            },
            Some("thinking_tokens") => match (sys.estimated_tokens, sys.estimated_tokens_delta) {
                (Some(estimated_tokens), Some(estimated_tokens_delta)) => {
                    vec![StreamEvent::ThinkingProgress {
                        estimated_tokens,
                        estimated_tokens_delta,
                    }]
                }
                _ => vec![StreamEvent::Unrecognized {
                    raw_type: "system.thinking_tokens".to_string(),
                }],
            },
            other => vec![StreamEvent::Unrecognized {
                raw_type: format!("system.{}", other.unwrap_or("unknown")),
            }],
        },
        RawLine::Assistant(asst) => {
            let message_id = asst.message.id;
            asst.message
                .content
                .into_iter()
                .map(|block| match block {
                    RawContentBlock::Thinking { thinking } => StreamEvent::AssistantThinking {
                        message_id: message_id.clone(),
                        text: thinking,
                    },
                    RawContentBlock::Text { text } => StreamEvent::AssistantText {
                        message_id: message_id.clone(),
                        text,
                    },
                    RawContentBlock::ToolUse { id, name, input } => StreamEvent::ToolCall {
                        message_id: message_id.clone(),
                        tool_use_id: id,
                        tool_name: name,
                        input,
                    },
                    RawContentBlock::Other => StreamEvent::Unrecognized {
                        raw_type: "assistant.content.other".to_string(),
                    },
                })
                .collect()
        }
        RawLine::User(user) => user
            .message
            .content
            .into_iter()
            .filter_map(|block| {
                if block.kind.as_deref() != Some("tool_result") {
                    return None;
                }
                let tool_use_id = block.tool_use_id?;
                let content = match block.content {
                    Some(ToolResultContent::Text(s)) => s,
                    Some(ToolResultContent::Other(v)) => v.to_string(),
                    None => String::new(),
                };
                Some(StreamEvent::ToolResult {
                    tool_use_id,
                    content,
                    is_error: block.is_error,
                })
            })
            .collect(),
        RawLine::Result(result) => vec![StreamEvent::RunFinished {
            is_error: result.is_error,
            total_cost_usd: result.total_cost_usd,
            session_id: result.session_id,
            stop_reason: result.stop_reason,
        }],
        RawLine::Other => vec![StreamEvent::Unrecognized {
            raw_type: raw_type_of(trimmed),
        }],
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::path::PathBuf;

    /// Real `stream-json` output (`claude` CLI v2.1.232, model haiku,
    /// `--permission-mode bypassPermissions --tools "Read Grep Glob Write
    /// Edit"`), captured once and checked in — not hand-written. Covers
    /// `hook_started`/`hook_response`/`init`/`thinking_tokens`,
    /// thinking+tool_use+text assistant blocks split across separate
    /// `assistant` lines, a `tool_result`, `rate_limit_event`, and the
    /// final `result`.
    fn fixture() -> String {
        let path = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
            .join("tests/fixtures/stream_json_tool_run.jsonl");
        std::fs::read_to_string(path).expect("fixture must exist")
    }

    fn events() -> Vec<StreamEvent> {
        fixture().lines().flat_map(parse_line).collect()
    }

    #[test]
    fn empty_line_yields_no_events() {
        assert!(parse_line("").is_empty());
        assert!(parse_line("   ").is_empty());
    }

    #[test]
    fn garbage_line_degrades_to_unrecognized_not_a_panic() {
        let out = parse_line("not json at all");
        assert_eq!(
            out,
            vec![StreamEvent::Unrecognized {
                raw_type: "unknown".to_string()
            }]
        );
    }

    #[test]
    fn unknown_type_degrades_to_unrecognized_with_its_real_type_name() {
        let out = parse_line(r#"{"type":"something_from_a_future_cli_version"}"#);
        assert_eq!(
            out,
            vec![StreamEvent::Unrecognized {
                raw_type: "something_from_a_future_cli_version".to_string()
            }]
        );
    }

    #[test]
    fn hook_and_rate_limit_lines_are_unrecognized_but_never_panic() {
        let evs = events();
        assert!(evs
            .iter()
            .any(|e| matches!(e, StreamEvent::Unrecognized { raw_type } if raw_type == "system.hook_started")));
        assert!(evs
            .iter()
            .any(|e| matches!(e, StreamEvent::Unrecognized { raw_type } if raw_type == "rate_limit_event")));
    }

    #[test]
    fn thinking_progress_carries_both_cumulative_and_delta_and_resets_across_blocks() {
        let evs = events();
        let progress: Vec<(u64, u64)> = evs
            .iter()
            .filter_map(|e| match e {
                StreamEvent::ThinkingProgress {
                    estimated_tokens,
                    estimated_tokens_delta,
                } => Some((*estimated_tokens, *estimated_tokens_delta)),
                _ => None,
            })
            .collect();
        assert!(!progress.is_empty());
        // AC-E2-07/AC-E6-19's realtime cost estimate must sum deltas, not
        // trust `estimated_tokens` as a whole-run running total — the
        // fixture's own data resets `estimated_tokens` mid-run (a new
        // thinking block starting), which summing deltas is immune to.
        assert!(
            progress.windows(2).any(|w| w[1].0 < w[0].0),
            "fixture must contain a reset (a later estimated_tokens lower than an earlier one) \
             for this test to actually exercise the case deltas guard against"
        );
        let summed_delta: u64 = progress.iter().map(|(_, delta)| delta).sum();
        assert!(summed_delta > 0);
    }

    #[test]
    fn session_started_parsed_from_init_line() {
        let evs = events();
        let started = evs
            .iter()
            .find_map(|e| match e {
                StreamEvent::SessionStarted { session_id, model } => {
                    Some((session_id.clone(), model.clone()))
                }
                _ => None,
            })
            .expect("must find a SessionStarted event");
        assert!(!started.0.is_empty());
        assert_eq!(started.1, "claude-haiku-4-5-20251001");
    }

    #[test]
    fn thinking_and_text_blocks_for_the_same_message_id_both_appear() {
        // The exact scenario A5 flagged: 1 message_id, 2 separate raw
        // lines, 2 different block types — the parser must not lose either.
        let evs = events();
        let thinking_id = evs.iter().find_map(|e| match e {
            StreamEvent::AssistantThinking { message_id, .. } => Some(message_id.clone()),
            _ => None,
        });
        let text_id = evs.iter().find_map(|e| match e {
            StreamEvent::AssistantText { message_id, .. } => Some(message_id.clone()),
            _ => None,
        });
        assert!(thinking_id.is_some());
        assert!(text_id.is_some());
    }

    #[test]
    fn tool_call_and_matching_tool_result_both_parsed() {
        let evs = events();
        let call_id = evs
            .iter()
            .find_map(|e| match e {
                StreamEvent::ToolCall {
                    tool_use_id,
                    tool_name,
                    ..
                } if tool_name == "Write" => Some(tool_use_id.clone()),
                _ => None,
            })
            .expect("must find the Write tool call");

        let result = evs
            .iter()
            .find_map(|e| match e {
                StreamEvent::ToolResult {
                    tool_use_id,
                    content,
                    is_error,
                } if *tool_use_id == call_id => Some((content.clone(), *is_error)),
                _ => None,
            })
            .expect("must find the matching tool_result");

        assert!(result.0.contains("File created successfully"));
        assert!(!result.1);
    }

    #[test]
    fn run_finished_parsed_from_result_line_with_real_cost() {
        let evs = events();
        let finished = evs
            .iter()
            .find_map(|e| match e {
                StreamEvent::RunFinished {
                    is_error,
                    total_cost_usd,
                    ..
                } => Some((*is_error, *total_cost_usd)),
                _ => None,
            })
            .expect("must find RunFinished");
        assert!(!finished.0);
        assert!(finished.1 > 0.0);
    }

    #[test]
    fn every_line_in_the_fixture_produces_at_least_one_event() {
        // No line is silently swallowed — everything becomes either a
        // modeled event or Unrecognized.
        for line in fixture().lines().filter(|l| !l.trim().is_empty()) {
            assert!(
                !parse_line(line).is_empty(),
                "line produced 0 events: {line}"
            );
        }
    }

    /// The wire contract with the frontend. Asserts the exact JSON keys
    /// rather than round-tripping, because a round-trip stays green even
    /// when the names are wrong — which is exactly how `tool_name` vs
    /// `toolName` shipped and made the log console print `undefined(...)`.
    #[test]
    fn serializes_variant_fields_in_camel_case_for_the_frontend() {
        let tool_call = StreamEvent::ToolCall {
            message_id: "msg_1".to_string(),
            tool_use_id: "toolu_1".to_string(),
            tool_name: "Read".to_string(),
            input: serde_json::json!({ "file_path": "/tmp/a.md" }),
        };
        let value = serde_json::to_value(&tool_call).unwrap();
        assert_eq!(value["kind"], "toolCall");
        assert_eq!(value["toolName"], "Read");
        assert_eq!(value["messageId"], "msg_1");
        assert_eq!(value["toolUseId"], "toolu_1");
        assert!(
            value.get("tool_name").is_none(),
            "snake_case key must not exist"
        );

        // `estimatedTokensDelta` feeds the realtime cost estimate — when it
        // was `estimated_tokens_delta` the frontend summed `undefined`.
        let progress = StreamEvent::ThinkingProgress {
            estimated_tokens: 137,
            estimated_tokens_delta: 42,
        };
        let value = serde_json::to_value(&progress).unwrap();
        assert_eq!(value["estimatedTokensDelta"], 42);
        assert_eq!(value["estimatedTokens"], 137);

        // `isError` drives the red styling of failed tool results.
        let tool_result = StreamEvent::ToolResult {
            tool_use_id: "toolu_1".to_string(),
            content: "EISDIR".to_string(),
            is_error: true,
        };
        let value = serde_json::to_value(&tool_result).unwrap();
        assert_eq!(value["isError"], true);

        let finished = StreamEvent::RunFinished {
            is_error: false,
            total_cost_usd: 1.5,
            session_id: "sess".to_string(),
            stop_reason: None,
        };
        let value = serde_json::to_value(&finished).unwrap();
        assert_eq!(value["totalCostUsd"], 1.5);
        assert_eq!(value["sessionId"], "sess");
    }
}
