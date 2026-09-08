//! Turns ⑤ Build's three static role slots into one slot per repo declared
//! in `AGENTS.md`'s Ecosystem table.
//!
//! Why per repo and not per role: the role vocabulary is only
//! `backend`/`frontend`/`mobile`, so a project with four web apps had all
//! four collapse into a single "Frontend" node — one status, one run log,
//! and `resolve_repo_readiness`'s `.find()` silently judging the whole role
//! by whichever repo happened to be listed first.
//!
//! The expansion is computed at read time and **never written to
//! `pipeline.json`**: that file stays the static template. Persisting the
//! expansion would freeze one moment's Ecosystem into the project, so a
//! repo added later would never get a node.

use crate::domain::pipeline_def::{slot_after, PipelineDef};
use crate::domain::project::EcosystemRepo;

pub const BUILD_STAGE_ID: &str = "S5_build";
pub const BUILD_SLOT_PREFIX: &str = "build-";

/// `store::orchestrator_dir::validate_run_id`'s cap. Slot ids are directory
/// names (`agent-runs/<feature>/<slot>/`) and the tail of the
/// `{feature}--{slot}` run id, so they must satisfy that validator exactly:
/// `[a-z0-9-]`, no leading/trailing `-`, no `--`.
const MAX_SLOT_ID_LEN: usize = 100;

/// Whether a slot id belongs to a per-repo build slot.
///
/// Deliberately a string test rather than an Ecosystem lookup: a run log
/// written for a repo that has since been removed from `AGENTS.md` must
/// still be classified as a build run, not silently reinterpreted.
pub fn is_build_slot(slot_id: &str) -> bool {
    slot_id.starts_with(BUILD_SLOT_PREFIX)
}

/// Repo name → the `[a-z0-9-]` core of its slot id.
fn repo_slug(repo_name: &str) -> String {
    let mut slug = String::with_capacity(repo_name.len());
    let mut pending_dash = false;
    for ch in repo_name.chars() {
        if ch.is_ascii_alphanumeric() {
            if pending_dash && !slug.is_empty() {
                slug.push('-');
            }
            pending_dash = false;
            slug.push(ch.to_ascii_lowercase());
        } else {
            pending_dash = true;
        }
    }
    if slug.is_empty() {
        // A name made entirely of characters the validator rejects (CJK, an
        // emoji, punctuation) still needs an id. `-2`-style disambiguation
        // in `build_slot_ids` keeps several of them apart.
        slug.push_str("repo");
    }
    slug
}

fn truncate_slug(mut slug: String, budget: usize) -> String {
    if slug.len() > budget {
        slug.truncate(budget);
        while slug.ends_with('-') {
            slug.pop();
        }
    }
    slug
}

/// The slot id for one repo, ignoring collisions with other repos.
///
/// Production code always goes through `build_slot_ids`: only the whole
/// table can disambiguate two repos whose names slugify identically. Kept
/// public so the slug rules can be tested on their own.
#[cfg_attr(not(test), allow(dead_code))]
pub fn build_slot_id(repo_name: &str) -> String {
    let budget = MAX_SLOT_ID_LEN - BUILD_SLOT_PREFIX.len();
    format!(
        "{BUILD_SLOT_PREFIX}{}",
        truncate_slug(repo_slug(repo_name), budget)
    )
}

/// Slot ids for every repo in the table, positionally aligned with it.
///
/// Collisions (`web-admin` vs `Web Admin`, or two long names sharing a
/// truncated prefix) get a `-2`, `-3`… suffix in table order, so the ids are
/// deterministic for an unchanged `AGENTS.md`.
pub fn build_slot_ids(ecosystem: &[EcosystemRepo]) -> Vec<String> {
    let budget = MAX_SLOT_ID_LEN - BUILD_SLOT_PREFIX.len();
    let mut taken: Vec<String> = Vec::with_capacity(ecosystem.len());
    for repo in ecosystem {
        let base = truncate_slug(repo_slug(&repo.name), budget);
        let mut slug = base.clone();
        let mut n = 1_u32;
        while taken.contains(&slug) {
            n += 1;
            let suffix = format!("-{n}");
            let trimmed = truncate_slug(base.clone(), budget - suffix.len());
            slug = format!("{trimmed}{suffix}");
        }
        taken.push(slug);
    }
    taken
        .into_iter()
        .map(|slug| format!("{BUILD_SLOT_PREFIX}{slug}"))
        .collect()
}

/// The Ecosystem row a build slot targets.
///
/// Resolved by recomputing the id list rather than parsing the id, so the
/// `-2` disambiguation can never be misread as part of a repo's name.
pub fn slot_repo<'a>(ecosystem: &'a [EcosystemRepo], slot_id: &str) -> Option<&'a EcosystemRepo> {
    if !is_build_slot(slot_id) {
        return None;
    }
    build_slot_ids(ecosystem)
        .iter()
        .position(|id| id == slot_id)
        .map(|index| &ecosystem[index])
}

fn agent_name_for_role(role_key: &str) -> Option<&'static str> {
    match role_key {
        "backend" => Some("backend-agent"),
        "frontend" => Some("frontend-agent"),
        "mobile" => Some("mobile-agent"),
        _ => None,
    }
}

fn role_label(role_key: &str) -> &'static str {
    match role_key {
        "backend" => "Backend",
        "frontend" => "Frontend",
        "mobile" => "Mobile",
        _ => "Repo",
    }
}

/// Replaces ⑤ Build's slots with one per Ecosystem repo.
///
/// Returns the warnings the caller must surface: a repo whose Vai trò cell
/// doesn't read as a role the kit has an agent for gets **no** build slot,
/// and saying nothing is how a repo silently vanishes from the board.
///
/// Falls back to the static role slots when no repo yields one. That is not
/// cosmetic: an empty ⑤ Build reads to `agentrun::readiness` as a stage
/// with nothing incomplete, which would unlock ⑥ Testing for a project that
/// has not even run `/init-kit`.
pub fn expand_build_stage(
    mut def: PipelineDef,
    ecosystem: &[EcosystemRepo],
) -> (PipelineDef, Vec<String>) {
    let Some(stage) = def
        .stages
        .iter_mut()
        .find(|stage| stage.id == BUILD_STAGE_ID)
    else {
        return (def, Vec::new());
    };

    let ids = build_slot_ids(ecosystem);
    let backend_ids: Vec<String> = ecosystem
        .iter()
        .zip(ids.iter())
        .filter(|(repo, _)| repo.role_key.as_deref() == Some("backend"))
        .map(|(_, id)| id.clone())
        .collect();

    let mut slots = Vec::new();
    let mut warnings = Vec::new();
    for (repo, id) in ecosystem.iter().zip(ids.iter()) {
        let Some(role_key) = repo.role_key.as_deref() else {
            warnings.push(format!(
                "Repo \"{}\" không có node Build: ô Vai trò đọc là \"{}\", phải là đúng một từ backend/frontend/mobile.",
                repo.name, repo.role
            ));
            continue;
        };
        let Some(agent_name) = agent_name_for_role(role_key) else {
            warnings.push(format!(
                "Repo \"{}\" không có node Build: kit chưa có agent cho vai trò \"{role_key}\".",
                repo.name
            ));
            continue;
        };
        // Frontend and mobile wait for every backend that has work in the
        // feature; `readiness` drops the ones without any, so a backend
        // repo untouched by this feature never blocks anyone.
        let after: Vec<&str> = if role_key == "backend" {
            Vec::new()
        } else {
            backend_ids.iter().map(String::as_str).collect()
        };
        slots.push(slot_after(
            id,
            agent_name,
            &format!("{} · {}", role_label(role_key), repo.name),
            &after,
        ));
    }

    if !slots.is_empty() {
        stage.agents = slots;
    }
    (def, warnings)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::domain::pipeline_def::AgentSlot;

    fn repo(name: &str, role: &str) -> EcosystemRepo {
        EcosystemRepo {
            name: name.to_string(),
            declared_path: name.to_string(),
            role: role.to_string(),
            role_key: crate::agents_reader::canonical_role(role).map(str::to_string),
            stack: "x".to_string(),
            cloned: true,
            resolved_path: Some(format!("/tmp/{name}")),
        }
    }

    fn build_slots(def: &PipelineDef) -> &[AgentSlot] {
        &def.stages
            .iter()
            .find(|stage| stage.id == BUILD_STAGE_ID)
            .unwrap()
            .agents
    }

    /// The shape this whole change exists for: two web repos used to share
    /// one Frontend node, so only the first was ever judged.
    #[test]
    fn every_repo_gets_its_own_slot_even_when_roles_repeat() {
        let eco = vec![
            repo("shop-api", "backend"),
            repo("shop-web-user", "frontend"),
            repo("shop-web-admin", "frontend"),
            repo("shop-app", "mobile"),
        ];
        let (def, warnings) = expand_build_stage(PipelineDef::default(), &eco);
        let slots = build_slots(&def);

        assert!(warnings.is_empty(), "{warnings:?}");
        assert_eq!(slots.len(), 4);
        assert_eq!(
            slots.iter().map(|s| s.id.as_str()).collect::<Vec<_>>(),
            [
                "build-shop-api",
                "build-shop-web-user",
                "build-shop-web-admin",
                "build-shop-app"
            ]
        );
        // Both web repos map to the same agent file but stay separate
        // slots — the exact case `AgentSlot::label` was introduced for.
        assert_eq!(slots[1].agent_name, "frontend-agent");
        assert_eq!(slots[2].agent_name, "frontend-agent");
        assert_eq!(slots[2].label.as_deref(), Some("Frontend · shop-web-admin"));
    }

    #[test]
    fn non_backend_slots_wait_for_every_backend() {
        let eco = vec![
            repo("api-core", "backend"),
            repo("api-payments", "backend"),
            repo("web", "frontend"),
        ];
        let (def, _) = expand_build_stage(PipelineDef::default(), &eco);
        let slots = build_slots(&def);

        assert!(slots[0].after_slots.is_empty());
        assert!(slots[1].after_slots.is_empty());
        assert_eq!(
            slots[2].after_slots,
            vec!["build-api-core".to_string(), "build-api-payments".to_string()]
        );
    }

    /// An empty ⑤ Build would read to `readiness` as "nothing incomplete"
    /// and unlock ⑥ Testing for a project that never ran `/init-kit`.
    #[test]
    fn an_empty_ecosystem_keeps_the_static_role_slots() {
        let (def, warnings) = expand_build_stage(PipelineDef::default(), &[]);
        let slots = build_slots(&def);

        assert!(warnings.is_empty());
        assert_eq!(
            slots.iter().map(|s| s.id.as_str()).collect::<Vec<_>>(),
            ["backend", "frontend", "mobile"]
        );
    }

    #[test]
    fn an_unreadable_role_is_reported_not_silently_dropped() {
        let eco = vec![
            repo("api", "backend"),
            repo("mystery", "Company Admin Web (E02)"),
        ];
        let (def, warnings) = expand_build_stage(PipelineDef::default(), &eco);

        assert_eq!(build_slots(&def).len(), 1);
        assert_eq!(warnings.len(), 1);
        assert!(warnings[0].contains("mystery"), "{warnings:?}");
    }

    #[test]
    fn slot_ids_survive_names_the_run_id_validator_would_reject() {
        assert_eq!(build_slot_id("ES_Kitchen Web"), "build-es-kitchen-web");
        assert_eq!(build_slot_id("--weird--"), "build-weird");
        assert_eq!(build_slot_id("東京"), "build-repo");

        let long = "a".repeat(200);
        let id = build_slot_id(&long);
        assert_eq!(id.len(), MAX_SLOT_ID_LEN);
        assert!(crate::store::orchestrator_dir::validate_run_ids("feat", &id).is_ok());
    }

    #[test]
    fn colliding_names_get_distinct_ids() {
        let eco = vec![
            repo("web-admin", "frontend"),
            repo("Web Admin", "frontend"),
            repo("web admin", "frontend"),
        ];
        let ids = build_slot_ids(&eco);
        assert_eq!(
            ids,
            [
                "build-web-admin",
                "build-web-admin-2",
                "build-web-admin-3"
            ]
        );
        // And the mapping back must not read "-2" as part of a repo name.
        assert_eq!(slot_repo(&eco, "build-web-admin-2").unwrap().name, "Web Admin");
    }

    #[test]
    fn every_generated_id_passes_the_run_id_validator() {
        let eco = vec![
            repo("shop-api", "backend"),
            repo("ES_Kitchen Web", "frontend"),
            repo("東京", "mobile"),
        ];
        for id in build_slot_ids(&eco) {
            assert!(
                crate::store::orchestrator_dir::validate_run_ids("feat", &id).is_ok(),
                "{id} rejected"
            );
        }
    }
}
