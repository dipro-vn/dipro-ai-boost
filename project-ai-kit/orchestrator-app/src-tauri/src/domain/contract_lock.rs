use serde::{Deserialize, Serialize};

/// AC-E4-08..20 (Contract Lock, Phase 2a). Deliberately its own field on
/// `FeatureState` rather than another entry in `gates: BTreeMap<..,
/// GateState>` (the Trigger gate's map) — the data shape here (files,
/// checksums, roles, content) has nothing in common with `GateState`, and
/// there is only ever one Contract Lock gate per feature, so a map buys
/// nothing.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "kebab-case")]
pub enum ContractLockStatus {
    /// No `DESIGN.md` anywhere for this feature has a recognizable API
    /// Definition table yet (AC-E4-08).
    NotReady,
    /// Contract Lock doesn't apply to this feature. Three ways to get
    /// here: the feature touches only one repo (AC-E4-11); its scope has
    /// no `backend` repo paired with a `frontend`/`mobile` one, so there
    /// is no API contract between two sides to freeze (AC-E4-11a); or the
    /// PM explicitly marked it skipped (AC-E4-11b). `not_applicable_reason`
    /// says which.
    NotApplicable,
    /// Open condition met — waiting for role confirmation + Lock.
    PendingReview,
    /// Locked, and every locked file's checksum still matches what was
    /// captured at lock time.
    Locked,
    /// AC-E4-21/22 — at least one locked file's checksum no longer matches
    /// (edited) or the file is gone (deleted). Re-computed fresh on every
    /// `compute_and_persist`, so reverting content back to the locked
    /// checksum clears this on its own (AC-E4-26) — nothing "remembers"
    /// a past violation in this field; `store::contract_lock`'s
    /// `ViolationEvent` log is what retains that history.
    Violated,
}

/// AC-E4-11b — the PM's explicit "this feature doesn't need a Contract
/// Lock" override, for the case inference cannot decide on its own: the
/// feature really does span backend + frontend, but this particular change
/// defines no new endpoint, so no `DESIGN.md` has an API Definition table
/// and the gate would otherwise dead-end at `NotReady` forever.
///
/// Deliberately NOT part of the immutable lock history in
/// `store::contract_lock`: a lock/violation is an event worth keeping
/// forever, while this is current state the PM can take back (see
/// `commands::agentrun::unskip_contract_lock`).
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct ContractLockSkip {
    pub skipped_by: String,
    pub reason: String,
    pub skipped_at: String,
}

/// AC-E4-21 vs AC-E4-22 — a locked file's content changed vs. it being gone
/// entirely need different messaging ("nêu rõ file nào đã biến mất").
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "kebab-case")]
pub enum ViolationKind {
    Modified,
    Deleted,
}

/// One locked file that no longer matches its checksum — `locked_content`
/// is what `LockedFile.content` had at lock time (always present, even for
/// `Deleted` — it's "what it used to say", not "what it says now"), used
/// for AC-E4-25's diff. Current content (when the file still exists) is
/// read live by the frontend via `readArtifact`, not duplicated here.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct FileViolation {
    pub path: String,
    pub kind: ViolationKind,
    pub locked_content: String,
}

/// AC-E4-26 — persisted the moment a violation is first detected (a
/// transition into `Violated`, never re-written on every recompute while
/// still violated), so the event survives even after the violation
/// self-heals. See `store::contract_lock` for the on-disk convention
/// (mirrors `ContractLockRecord`: one immutable timestamped file).
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct ViolationEvent {
    pub detected_at: String,
    pub files: Vec<FileViolation>,
}

/// A file about to be (or already) locked, without its content — cheap
/// enough to include in every `compute_and_persist` poll (AC-E4-16's
/// pre-lock preview). Contrast with `LockedFile`, which additionally
/// carries the frozen content and only ever lives inside a persisted
/// `ContractLockRecord`.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct LockedFileRef {
    pub path: String,
    pub checksum_sha256: String,
}

/// A locked file's content is captured directly here at lock time —
/// deliberately NOT a reference into the general git/snapshot versioning
/// system (`domain::version_ref`). A git-tracked `DESIGN.md` can have
/// uncommitted changes at lock time; storing only a version reference
/// would risk a captured id resolving to content that doesn't match the
/// checksum computed from disk at that same moment. Storing the raw
/// content directly guarantees the two always agree, with no git-state
/// edge cases to reason about.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct LockedFile {
    pub path: String,
    pub checksum_sha256: String,
    pub content: String,
}

/// Persisted verbatim, once per Lock/Re-lock — AC-E4-19: never overwritten,
/// history retained. See `store::contract_lock` for the on-disk convention
/// (one timestamped file per record, mirroring `store::snapshot`).
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct ContractLockRecord {
    pub locked_at: String,
    pub approved_by: String,
    /// Subset of `ALL_ROLES` that were ticked when Lock was clicked
    /// (AC-E4-12). No identity verification in v1 (AC-E4-15) — this is a
    /// recorded commitment, not a verified one.
    pub confirmed_roles: Vec<String>,
    pub files: Vec<LockedFile>,
}

/// The 5 roles AC-E4-12 lists, in the order the SPEC lists them. PM and QC
/// always apply; BE/FE/Mobile only apply if the project's Ecosystem has a
/// repo of that role (AC-E4-14).
pub const ALL_ROLES: &[&str] = &["BE", "FE", "Mobile", "PM", "QC"];

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct ContractLockState {
    pub status: ContractLockStatus,
    /// AC-E4-08a — every `<repo>/DESIGN.md` path checked while looking for
    /// an API Definition table, so the gate can name them when none has one
    /// (only populated when `status == NotReady`).
    #[serde(default)]
    pub checked_design_md_paths: Vec<String>,
    /// AC-E4-10 — required API Definition columns missing from the table
    /// that WAS found (empty when nothing's missing, or when `status` is
    /// `NotReady`/`NotApplicable` and there's no table to check).
    #[serde(default)]
    pub missing_columns: Vec<String>,
    /// AC-E4-11b — `true` when `NotApplicable` came from the PM clicking
    /// skip rather than from an inferred rule. The panel needs the
    /// difference: only a manual skip can be taken back, and only that one
    /// should offer the undo button.
    #[serde(default)]
    pub manually_skipped: bool,
    /// AC-E4-11 — set only when `status == NotApplicable`.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub not_applicable_reason: Option<String>,
    /// AC-E4-14 — which of `ALL_ROLES` apply to this project.
    #[serde(default)]
    pub applicable_roles: Vec<String>,
    /// AC-E4-16 — pre-lock preview (path + checksum only, no content).
    #[serde(default)]
    pub candidate_files: Vec<LockedFileRef>,
    /// The most recent lock, if any.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub current_lock: Option<ContractLockRecord>,
    /// AC-E4-21/22/25 — non-empty only when `status == Violated`.
    #[serde(default)]
    pub violated_files: Vec<FileViolation>,
    /// AC-E4-24 — `true` when `backend-agent` has a live process for this
    /// feature at the same time `status == Violated`. Scoped to `backend`
    /// only (see this phase's plan doc) — no other stage-⑤+ slot has a
    /// real spawn path yet.
    #[serde(default)]
    pub running_on_old_contract: bool,
}
