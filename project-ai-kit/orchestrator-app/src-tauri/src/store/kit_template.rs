//! Bộ khung kit được nhúng thẳng vào binary (`include_dir!`), để app tự
//! dựng được một project mới thay vì bắt người dùng copy tay.
//!
//! Nhúng thay vì copy từ một thư mục ngoài: chỉ cần thêm một đường dẫn nữa
//! do người dùng khai là lại sinh ra đúng loại lỗi `repositoryRoot` — trỏ
//! sai, im lặng, chỉ lộ ra ở tận bước cuối.
//!
//! `.claude/skills/` (5.4 MB) và `.claude/scripts/` CỐ Ý không nhúng: flow
//! của app không đọc chúng, và chúng chiếm hơn 90% dung lượng kit.
//!
//! Mỗi thư mục con có một `include_dir!` riêng thay vì nhúng cả `.claude/`
//! rồi lọc — macro nhúng toàn bộ cây tại compile time, lọc về sau không làm
//! binary nhỏ đi.

use std::path::{Path, PathBuf};

use include_dir::{include_dir, Dir};

use crate::error::AppResult;

static AGENTS: Dir<'_> = include_dir!("$CARGO_MANIFEST_DIR/../../.claude/agents");
static RULES: Dir<'_> = include_dir!("$CARGO_MANIFEST_DIR/../../.claude/rules");
static COMMANDS: Dir<'_> = include_dir!("$CARGO_MANIFEST_DIR/../../.claude/commands");
static CONTEXT: Dir<'_> = include_dir!("$CARGO_MANIFEST_DIR/../../.claude/context");
static TEMPLATES: Dir<'_> = include_dir!("$CARGO_MANIFEST_DIR/../../.claude/templates");
static WORKFLOWS: Dir<'_> = include_dir!("$CARGO_MANIFEST_DIR/../../.claude/workflows");
static HOOKS: Dir<'_> = include_dir!("$CARGO_MANIFEST_DIR/../../.claude/hooks");
static CONFIG: Dir<'_> = include_dir!("$CARGO_MANIFEST_DIR/../../.claude/config");
static SCRIPTS: Dir<'_> = include_dir!("$CARGO_MANIFEST_DIR/../../.claude/scripts");

/// Mỗi skill một `include_dir!` thay vì nhúng cả `.claude/skills` rồi lọc:
/// macro nhúng toàn bộ cây tại compile time, lọc lúc materialize vẫn để
/// `ui-ux-pro-max` (3.5 MB) nằm chết trong binary.
///
/// Danh sách viết tay sẽ lệch khi kit thêm skill mới — `tests::
/// embedded_kit_has_every_skill_except_the_deliberately_excluded_one` đọc
/// thẳng `.claude/skills` trên đĩa để bắt đúng chỗ đó.
static SKILL_AUTOMATION_ENGINEER: Dir<'_> =
    include_dir!("$CARGO_MANIFEST_DIR/../../.claude/skills/automation_engineer");
static SKILL_BANNER_DESIGN: Dir<'_> =
    include_dir!("$CARGO_MANIFEST_DIR/../../.claude/skills/banner-design");
static SKILL_BRAND: Dir<'_> = include_dir!("$CARGO_MANIFEST_DIR/../../.claude/skills/brand");
static SKILL_BUG_REPORTER: Dir<'_> =
    include_dir!("$CARGO_MANIFEST_DIR/../../.claude/skills/bug_reporter");
static SKILL_BUSINESS_ANALYST: Dir<'_> =
    include_dir!("$CARGO_MANIFEST_DIR/../../.claude/skills/business-analyst");
static SKILL_COMPONENT_CHECKLIST: Dir<'_> =
    include_dir!("$CARGO_MANIFEST_DIR/../../.claude/skills/component_checklist");
static SKILL_DESIGN: Dir<'_> = include_dir!("$CARGO_MANIFEST_DIR/../../.claude/skills/design");
static SKILL_DESIGN_SYSTEM: Dir<'_> =
    include_dir!("$CARGO_MANIFEST_DIR/../../.claude/skills/design-system");
static SKILL_FIGMA_DESIGN: Dir<'_> =
    include_dir!("$CARGO_MANIFEST_DIR/../../.claude/skills/figma-design");
static SKILL_FLUTTER_REVIEW: Dir<'_> =
    include_dir!("$CARGO_MANIFEST_DIR/../../.claude/skills/flutter-review");
static SKILL_FRONTEND_REVIEW: Dir<'_> =
    include_dir!("$CARGO_MANIFEST_DIR/../../.claude/skills/frontend-review");
static SKILL_NESTJS_BEST_PRACTICES: Dir<'_> =
    include_dir!("$CARGO_MANIFEST_DIR/../../.claude/skills/nestjs-best-practices");
static SKILL_POSTGRESQL: Dir<'_> =
    include_dir!("$CARGO_MANIFEST_DIR/../../.claude/skills/postgresql");
static SKILL_RBT_MANUAL_TESTING: Dir<'_> =
    include_dir!("$CARGO_MANIFEST_DIR/../../.claude/skills/rbt_manual_testing");
static SKILL_REACT_EXPERT: Dir<'_> =
    include_dir!("$CARGO_MANIFEST_DIR/../../.claude/skills/react-expert");
static SKILL_REDIS_DEVELOPMENT: Dir<'_> =
    include_dir!("$CARGO_MANIFEST_DIR/../../.claude/skills/redis-development");
static SKILL_REQUIREMENTS_ANALYZER: Dir<'_> =
    include_dir!("$CARGO_MANIFEST_DIR/../../.claude/skills/requirements_analyzer");
static SKILL_SCREEN_STRATEGY: Dir<'_> =
    include_dir!("$CARGO_MANIFEST_DIR/../../.claude/skills/screen_strategy");
static SKILL_SLIDES: Dir<'_> = include_dir!("$CARGO_MANIFEST_DIR/../../.claude/skills/slides");
static SKILL_SOLUTION_ARCHITECT: Dir<'_> =
    include_dir!("$CARGO_MANIFEST_DIR/../../.claude/skills/solution-architect");
static SKILL_TASK_DECOMPOSITION: Dir<'_> =
    include_dir!("$CARGO_MANIFEST_DIR/../../.claude/skills/task-decomposition");
static SKILL_TESTING_DIMENSIONS: Dir<'_> =
    include_dir!("$CARGO_MANIFEST_DIR/../../.claude/skills/testing_dimensions");
static SKILL_UI_STYLING: Dir<'_> =
    include_dir!("$CARGO_MANIFEST_DIR/../../.claude/skills/ui-styling");

pub static SETTINGS_JSON: &str = include_str!(concat!(
    env!("CARGO_MANIFEST_DIR"),
    "/../../.claude/settings.json"
));
static AGENTS_MD: &str = include_str!(concat!(env!("CARGO_MANIFEST_DIR"), "/../../AGENTS.md"));
static POLICIES_MD: &str = include_str!(concat!(env!("CARGO_MANIFEST_DIR"), "/../../POLICIES.md"));
static CLAUDE_MD: &str = include_str!(concat!(env!("CARGO_MANIFEST_DIR"), "/../../CLAUDE.md"));
/// File rời ngay dưới `.claude/skills/` — cách nhúng per-skill ở trên chỉ
/// lấy thư mục con nên sẽ bỏ sót nó nếu không khai riêng.
static SKILLS_README: &str = include_str!(concat!(
    env!("CARGO_MANIFEST_DIR"),
    "/../../.claude/skills/README.md"
));

const CURRENT_AGENTS_INIT_NOTICE: &str = "> **Chưa init?** App chỉ tạo khung kit. Mở Claude Code tại `agentsRoot`, nhập `/init-kit` để điền Ecosystem/Actors. Đây là slash command trong Claude Code, không phải lệnh shell. Setup A→Z ở `README.md`.";
const LEGACY_AGENTS_INIT_NOTICE: &str =
    "> **Chưa init?** Chạy `/init-kit` để điền Ecosystem/Actors. Setup A→Z ở `README.md`.";

/// Root nào của project chứa nhóm này. `agentsRoot`/`docsRoot` là hai cây
/// độc lập (có project chúng còn không phải anh em), nên không suy ra được.
#[derive(Debug, Clone, Copy, PartialEq, Eq, serde::Serialize, serde::Deserialize)]
#[serde(rename_all = "camelCase")]
pub enum KitRoot {
    AgentsRoot,
    DocsRoot,
}

enum Source {
    /// Cây thư mục nhúng, trải ra dưới `prefix`.
    Tree {
        prefix: &'static str,
        dir: &'static Dir<'static>,
    },
    Text {
        path: &'static str,
        content: &'static str,
    },
    /// Chỉ cần thư mục tồn tại, không có nội dung nhúng.
    EmptyDir { path: &'static str },
}

struct GroupDef {
    id: &'static str,
    label: &'static str,
    root: KitRoot,
    sources: &'static [Source],
}

/// `POLICIES.md` + `CLAUDE.md` đi cùng nhóm với `AGENTS.md`: `CLAUDE.md`
/// `@import` cả hai file kia, seed mỗi `AGENTS.md` sẽ để lại tham chiếu gãy.
static GROUPS: &[GroupDef] = &[
    GroupDef {
        id: "agents",
        label: "Sub-agent (.claude/agents/)",
        root: KitRoot::AgentsRoot,
        sources: &[Source::Tree {
            prefix: ".claude/agents",
            dir: &AGENTS,
        }],
    },
    GroupDef {
        id: "root-docs",
        label: "AGENTS.md · POLICIES.md · CLAUDE.md",
        root: KitRoot::AgentsRoot,
        sources: &[
            Source::Text {
                path: "AGENTS.md",
                content: AGENTS_MD,
            },
            Source::Text {
                path: "POLICIES.md",
                content: POLICIES_MD,
            },
            Source::Text {
                path: "CLAUDE.md",
                content: CLAUDE_MD,
            },
        ],
    },
    GroupDef {
        id: "conventions",
        label: "Quy ước (rules · commands · context · templates · workflows)",
        root: KitRoot::AgentsRoot,
        sources: &[
            Source::Tree {
                prefix: ".claude/rules",
                dir: &RULES,
            },
            Source::Tree {
                prefix: ".claude/commands",
                dir: &COMMANDS,
            },
            Source::Tree {
                prefix: ".claude/context",
                dir: &CONTEXT,
            },
            Source::Tree {
                prefix: ".claude/templates",
                dir: &TEMPLATES,
            },
            Source::Tree {
                prefix: ".claude/workflows",
                dir: &WORKFLOWS,
            },
            Source::Tree {
                prefix: ".claude/scripts",
                dir: &SCRIPTS,
            },
        ],
    },
    GroupDef {
        id: "guardrails",
        label: "Hook bảo mật H01–H05 (.claude/hooks · config · settings.json)",
        root: KitRoot::AgentsRoot,
        sources: &[
            Source::Tree {
                prefix: ".claude/hooks",
                dir: &HOOKS,
            },
            Source::Tree {
                prefix: ".claude/config",
                dir: &CONFIG,
            },
            Source::Text {
                path: ".claude/settings.json",
                content: SETTINGS_JSON,
            },
        ],
    },
    GroupDef {
        id: "skills",
        label: "Skill (.claude/skills/)",
        root: KitRoot::AgentsRoot,
        sources: &[
            Source::Text {
                path: ".claude/skills/README.md",
                content: SKILLS_README,
            },
            Source::Tree {
                prefix: ".claude/skills/automation_engineer",
                dir: &SKILL_AUTOMATION_ENGINEER,
            },
            Source::Tree {
                prefix: ".claude/skills/banner-design",
                dir: &SKILL_BANNER_DESIGN,
            },
            Source::Tree {
                prefix: ".claude/skills/brand",
                dir: &SKILL_BRAND,
            },
            Source::Tree {
                prefix: ".claude/skills/bug_reporter",
                dir: &SKILL_BUG_REPORTER,
            },
            Source::Tree {
                prefix: ".claude/skills/business-analyst",
                dir: &SKILL_BUSINESS_ANALYST,
            },
            Source::Tree {
                prefix: ".claude/skills/component_checklist",
                dir: &SKILL_COMPONENT_CHECKLIST,
            },
            Source::Tree {
                prefix: ".claude/skills/design",
                dir: &SKILL_DESIGN,
            },
            Source::Tree {
                prefix: ".claude/skills/design-system",
                dir: &SKILL_DESIGN_SYSTEM,
            },
            Source::Tree {
                prefix: ".claude/skills/figma-design",
                dir: &SKILL_FIGMA_DESIGN,
            },
            Source::Tree {
                prefix: ".claude/skills/flutter-review",
                dir: &SKILL_FLUTTER_REVIEW,
            },
            Source::Tree {
                prefix: ".claude/skills/frontend-review",
                dir: &SKILL_FRONTEND_REVIEW,
            },
            Source::Tree {
                prefix: ".claude/skills/nestjs-best-practices",
                dir: &SKILL_NESTJS_BEST_PRACTICES,
            },
            Source::Tree {
                prefix: ".claude/skills/postgresql",
                dir: &SKILL_POSTGRESQL,
            },
            Source::Tree {
                prefix: ".claude/skills/rbt_manual_testing",
                dir: &SKILL_RBT_MANUAL_TESTING,
            },
            Source::Tree {
                prefix: ".claude/skills/react-expert",
                dir: &SKILL_REACT_EXPERT,
            },
            Source::Tree {
                prefix: ".claude/skills/redis-development",
                dir: &SKILL_REDIS_DEVELOPMENT,
            },
            Source::Tree {
                prefix: ".claude/skills/requirements_analyzer",
                dir: &SKILL_REQUIREMENTS_ANALYZER,
            },
            Source::Tree {
                prefix: ".claude/skills/screen_strategy",
                dir: &SKILL_SCREEN_STRATEGY,
            },
            Source::Tree {
                prefix: ".claude/skills/slides",
                dir: &SKILL_SLIDES,
            },
            Source::Tree {
                prefix: ".claude/skills/solution-architect",
                dir: &SKILL_SOLUTION_ARCHITECT,
            },
            Source::Tree {
                prefix: ".claude/skills/task-decomposition",
                dir: &SKILL_TASK_DECOMPOSITION,
            },
            Source::Tree {
                prefix: ".claude/skills/testing_dimensions",
                dir: &SKILL_TESTING_DIMENSIONS,
            },
            Source::Tree {
                prefix: ".claude/skills/ui-styling",
                dir: &SKILL_UI_STYLING,
            },
        ],
    },
    GroupDef {
        id: "docs-features",
        label: "Thư mục feature (<docsRoot>/features/)",
        root: KitRoot::DocsRoot,
        sources: &[Source::EmptyDir { path: "features" }],
    },
];

/// Một nhóm còn thiếu, đủ để Launcher hiện một dòng.
#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct KitGroup {
    pub id: String,
    pub label: String,
    pub root: KitRoot,
    pub missing_count: usize,
    pub total_count: usize,
}

#[derive(Debug, Clone, Default, serde::Serialize)]
#[serde(rename_all = "camelCase")]
pub struct ScaffoldReport {
    pub created: Vec<String>,
    /// Existing files that were still the original kit template and were
    /// safely updated with the current project name.
    pub updated: Vec<String>,
    /// File đã có sẵn — bỏ qua, KHÔNG ghi đè.
    pub skipped: Vec<String>,
}

/// Một mục cần có trên đĩa: `None` = thư mục, `Some` = file kèm nội dung.
type Entry = (PathBuf, Option<&'static [u8]>);

fn collect_tree(dir: &'static Dir<'static>, prefix: &str, out: &mut Vec<Entry>) {
    for file in dir.files() {
        out.push((Path::new(prefix).join(file.path()), Some(file.contents())));
    }
    for sub in dir.dirs() {
        collect_tree(sub, prefix, out);
    }
}

fn entries_of(group: &GroupDef) -> Vec<Entry> {
    let mut out = Vec::new();
    for source in group.sources {
        match source {
            Source::Tree { prefix, dir } => collect_tree(dir, prefix, &mut out),
            Source::Text { path, content } => {
                out.push((PathBuf::from(path), Some(content.as_bytes())))
            }
            Source::EmptyDir { path } => out.push((PathBuf::from(path), None)),
        }
    }
    out
}

fn root_for(group: &GroupDef, agents_root: &Path, docs_root: &Path) -> PathBuf {
    match group.root {
        KitRoot::AgentsRoot => agents_root.to_path_buf(),
        KitRoot::DocsRoot => docs_root.to_path_buf(),
    }
}

fn exists(base: &Path, relative: &Path, is_file: bool) -> bool {
    let target = base.join(relative);
    if is_file {
        target.is_file()
    } else {
        target.is_dir()
    }
}

/// Chỉ những nhóm còn thiếu ít nhất một mục. Trả rỗng = project đã đủ khung.
pub fn missing_groups(agents_root: &Path, docs_root: &Path) -> Vec<KitGroup> {
    GROUPS
        .iter()
        .filter_map(|group| {
            let base = root_for(group, agents_root, docs_root);
            let entries = entries_of(group);
            let missing_count = entries
                .iter()
                .filter(|(relative, contents)| !exists(&base, relative, contents.is_some()))
                .count();
            (missing_count > 0).then(|| KitGroup {
                id: group.id.to_string(),
                label: group.label.to_string(),
                root: group.root,
                missing_count,
                total_count: entries.len(),
            })
        })
        .collect()
}

/// Ghi ra đĩa mọi mục còn thiếu. **Không bao giờ ghi đè** — người dùng có
/// thể đã sửa `AGENTS.md` hoặc thêm agent riêng, và mất thứ đó thì không
/// lấy lại được.
///
/// Đường dẫn đích luôn là root + hằng số lấy từ `include_dir` (cố định lúc
/// compile, không thể chứa `..`), không có input nào từ frontend — nếu sau
/// này thêm input thì phải qua `orchestrator_dir::assert_within`.
#[allow(dead_code)]
pub fn materialize(agents_root: &Path, docs_root: &Path) -> AppResult<ScaffoldReport> {
    materialize_for_project(agents_root, docs_root, None)
}

fn render_project_name(relative: &Path, bytes: &[u8], project_name: Option<&str>) -> Vec<u8> {
    let Some(project_name) = project_name else {
        return bytes.to_vec();
    };

    let renderable = matches!(
        relative.to_str(),
        Some("AGENTS.md")
            | Some(".claude/context/specification.md")
            | Some(".claude/context/technical.md")
            | Some(".claude/context/designer-context.md")
            | Some(".claude/templates/docs-index.md")
    );
    if !renderable {
        return bytes.to_vec();
    }

    let safe_name = project_name.replace(['\r', '\n'], " ").trim().to_string();
    String::from_utf8_lossy(bytes)
        .replace("\\<PROJECT_NAME\\>", &safe_name)
        .replace("<PROJECT_NAME>", &safe_name)
        .replace("<TEN_DU_AN>", &safe_name)
        .into_bytes()
}

fn matches_original_template(relative: &Path, existing: &[u8], template: &[u8]) -> bool {
    if existing == template {
        return true;
    }
    if relative != Path::new("AGENTS.md") {
        return false;
    }

    String::from_utf8_lossy(existing)
        .replace(LEGACY_AGENTS_INIT_NOTICE, CURRENT_AGENTS_INIT_NOTICE)
        .as_bytes()
        == template
}

/// Ghi ra đĩa phần kit còn thiếu và render project name vào các template
/// project-facing. File custom không bao giờ bị ghi đè; chỉ template nguyên
/// bản của kit mới được migrate an toàn.
pub fn materialize_for_project(
    agents_root: &Path,
    docs_root: &Path,
    project_name: Option<&str>,
) -> AppResult<ScaffoldReport> {
    let mut report = ScaffoldReport::default();

    for group in GROUPS {
        let base = root_for(group, agents_root, docs_root);
        for (relative, contents) in entries_of(group) {
            let target = base.join(&relative);
            let label = relative.display().to_string();

            match contents {
                None => {
                    if target.is_dir() {
                        report.skipped.push(label);
                    } else {
                        std::fs::create_dir_all(&target)?;
                        report.created.push(label);
                    }
                }
                Some(bytes) => {
                    let rendered = render_project_name(&relative, bytes, project_name);
                    if target.is_file() {
                        if rendered != bytes
                            && std::fs::read(&target).ok().is_some_and(|existing| {
                                matches_original_template(&relative, &existing, bytes)
                            })
                        {
                            std::fs::write(&target, &rendered)?;
                            report.updated.push(label);
                        } else {
                            report.skipped.push(label);
                        }
                        continue;
                    }
                    if let Some(parent) = target.parent() {
                        std::fs::create_dir_all(parent)?;
                    }
                    std::fs::write(&target, rendered)?;
                    report.created.push(label);
                }
            }
        }
    }

    Ok(report)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::domain::pipeline_def::PipelineDef;

    fn probe() -> (tempfile::TempDir, PathBuf, PathBuf) {
        let tmp = tempfile::tempdir().unwrap();
        let agents_root = tmp.path().join("app");
        let docs_root = tmp.path().join("docs");
        std::fs::create_dir_all(&agents_root).unwrap();
        std::fs::create_dir_all(&docs_root).unwrap();
        (tmp, agents_root, docs_root)
    }

    /// Buộc kit nhúng khớp với `pipeline.json` mặc định. Bắt được cả đường
    /// dẫn `include_dir!` sai (nhúng nhầm thư mục rỗng vẫn compile được)
    /// lẫn việc kit đánh rơi một agent mà pipeline vẫn tham chiếu.
    /// Skill CỐ Ý không nhúng: 3.5 MB trên tổng 5.4 MB của `.claude/skills`,
    /// phần lớn là data font/icon.
    const EXCLUDED_SKILL: &str = "ui-ux-pro-max";

    fn source_claude_dir() -> PathBuf {
        PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../../.claude")
    }

    fn subdirs_of(dir: &Path) -> Vec<String> {
        std::fs::read_dir(dir)
            .unwrap()
            .filter_map(|entry| entry.ok())
            .filter(|entry| entry.path().is_dir())
            .filter_map(|entry| entry.file_name().to_str().map(str::to_owned))
            .collect()
    }

    /// Mọi prefix mà `GROUPS` phủ (kể cả file lẻ như `.claude/settings.json`).
    fn covered_prefixes() -> Vec<String> {
        GROUPS
            .iter()
            .flat_map(|group| group.sources.iter())
            .filter_map(|source| match source {
                Source::Tree { prefix, .. } => Some(prefix.to_string()),
                Source::Text { path, .. } => Some(path.to_string()),
                Source::EmptyDir { .. } => None,
            })
            .collect()
    }

    /// Danh sách 24 skill viết tay sẽ lệch âm thầm khi kit thêm skill mới —
    /// binary vẫn build, project mới chỉ đơn giản là thiếu skill đó. Test
    /// đọc thẳng `.claude/skills` trên đĩa nên bắt được ngay.
    #[test]
    fn embedded_kit_has_every_skill_except_the_deliberately_excluded_one() {
        let covered = covered_prefixes();
        let is_covered = |name: &str| {
            covered
                .iter()
                .any(|p| p == &format!(".claude/skills/{name}"))
        };

        for skill in subdirs_of(&source_claude_dir().join("skills")) {
            if skill == EXCLUDED_SKILL {
                assert!(
                    !is_covered(&skill),
                    "{skill} bị loại trừ có chủ đích nhưng lại đang được nhúng"
                );
            } else {
                assert!(
                    is_covered(&skill),
                    "kit có skill \"{skill}\" mà binary không nhúng — thêm một dòng \
                     include_dir! trong kit_template.rs"
                );
            }
        }
    }

    /// `.claude/skills/` nhúng theo từng thư mục con, nên file rời nằm ngay
    /// dưới nó (hiện có `README.md`) rất dễ bị bỏ quên — và đã bị bỏ quên
    /// một lần.
    #[test]
    fn embedded_kit_has_the_loose_files_directly_under_skills() {
        let covered = covered_prefixes();
        let skills_dir = source_claude_dir().join("skills");

        for entry in std::fs::read_dir(&skills_dir).unwrap() {
            let path = entry.unwrap().path();
            if !path.is_file() {
                continue;
            }
            let name = path.file_name().unwrap().to_str().unwrap();
            let expected = format!(".claude/skills/{name}");
            assert!(
                covered.iter().any(|p| p == &expected),
                "`{expected}` của kit không được nhúng"
            );
        }
    }

    /// Kit thêm hẳn một thư mục cấp 1 mới (ngang hàng `agents/`, `rules/`)
    /// cũng phải lộ ra, không chỉ riêng skill.
    #[test]
    fn embedded_kit_covers_every_top_level_dir_of_the_source_claude() {
        let covered = covered_prefixes();

        for dir in subdirs_of(&source_claude_dir()) {
            let prefix = format!(".claude/{dir}");
            assert!(
                covered.iter().any(|p| p.starts_with(&prefix)),
                "`.claude/{dir}` của kit không được nhóm nào trong GROUPS phủ"
            );
        }
    }

    #[test]
    fn embedded_kit_has_every_agent_the_pipeline_references() {
        for stage in PipelineDef::default().stages {
            for agent in stage.agents {
                let file = format!("{}.md", agent.agent_name);
                assert!(
                    AGENTS.get_file(&file).is_some(),
                    "kit nhúng thiếu {file} — slot \"{}\" sẽ luôn báo AgentMissing",
                    agent.id
                );
            }
        }
    }

    /// Nhúng `settings.json` vào binary nghĩa là mọi giá trị trong đó đi
    /// theo bản phát hành. Một máy dev điền `BACKLOG_API_KEY` thật rồi
    /// build là key đó nằm luôn trong binary gửi đi.
    #[test]
    fn embedded_settings_json_carries_no_filled_in_secret() {
        let parsed: serde_json::Value = serde_json::from_str(SETTINGS_JSON).unwrap();
        let risky = regex::Regex::new("(?i)key|token|secret|password|credential").unwrap();

        fn walk(node: &serde_json::Value, path: &str, risky: &regex::Regex) {
            match node {
                serde_json::Value::Object(map) => {
                    for (key, value) in map {
                        walk(value, &format!("{path}.{key}"), risky);
                    }
                }
                serde_json::Value::Array(items) => {
                    for item in items {
                        walk(item, &format!("{path}[]"), risky);
                    }
                }
                serde_json::Value::String(text) if risky.is_match(path) => {
                    assert!(
                        text.is_empty() || text.starts_with('$'),
                        "{path} trong settings.json nhúng đang có giá trị thật — \
                         build sẽ ship secret đó trong binary"
                    );
                }
                _ => {}
            }
        }
        walk(&parsed, "", &risky);
    }

    #[test]
    fn missing_groups_reports_every_group_for_an_empty_project() {
        let (_tmp, agents_root, docs_root) = probe();
        let groups = missing_groups(&agents_root, &docs_root);

        assert_eq!(groups.len(), GROUPS.len());
        for group in &groups {
            assert_eq!(
                group.missing_count, group.total_count,
                "{} phải thiếu toàn bộ",
                group.id
            );
            assert!(group.total_count > 0, "{} không có mục nào", group.id);
        }
    }

    #[test]
    fn nothing_is_missing_after_materialize() {
        let (_tmp, agents_root, docs_root) = probe();
        materialize(&agents_root, &docs_root).unwrap();

        assert!(missing_groups(&agents_root, &docs_root).is_empty());
        assert!(agents_root.join(".claude/agents/ba-agent.md").is_file());
        assert!(agents_root
            .join(".claude/config/restricted-paths.json")
            .is_file());
        assert!(agents_root.join("AGENTS.md").is_file());
        assert!(agents_root.join(".claude/scripts/md_to_xlsx.py").is_file());
        assert!(agents_root.join(".claude/skills/brand").is_dir());
        assert!(agents_root.join(".claude/skills/README.md").is_file());
        assert!(
            !agents_root.join(".claude/skills/ui-ux-pro-max").exists(),
            "skill bị loại trừ không được xuất hiện trong project"
        );
        assert!(docs_root.join("features").is_dir());
    }

    #[test]
    fn materialize_renders_project_name_in_project_facing_templates() {
        let (_tmp, agents_root, docs_root) = probe();

        let report = materialize_for_project(&agents_root, &docs_root, Some("Shop Admin")).unwrap();

        assert!(!report.created.is_empty());
        assert!(std::fs::read_to_string(agents_root.join("AGENTS.md"))
            .unwrap()
            .contains("# Shop Admin — Project Rules for AI Agents"));
        assert!(
            std::fs::read_to_string(agents_root.join(".claude/context/specification.md"))
                .unwrap()
                .contains("# Shop Admin — Business Specification Memory")
        );
        assert!(
            std::fs::read_to_string(agents_root.join(".claude/agents/init-agent.md"))
                .unwrap()
                .contains("<PROJECT_NAME>")
        );
        let agents_content = std::fs::read_to_string(agents_root.join("AGENTS.md")).unwrap();
        let (status, _) = crate::agents_reader::assess_init_status(Some(&agents_content), true);
        assert_eq!(status, crate::domain::project::ProjectInitStatus::NeedsInit);
    }

    #[test]
    fn materialize_updates_only_an_untouched_old_template() {
        let (_tmp, agents_root, docs_root) = probe();
        materialize(&agents_root, &docs_root).unwrap();

        let report = materialize_for_project(&agents_root, &docs_root, Some("Shop")).unwrap();

        assert!(report.updated.iter().any(|path| path == "AGENTS.md"));
        assert!(std::fs::read_to_string(agents_root.join("AGENTS.md"))
            .unwrap()
            .contains("# Shop — Project Rules for AI Agents"));
    }

    #[test]
    fn materialize_migrates_the_previous_agents_notice_without_overwriting_custom_text() {
        let (_tmp, agents_root, docs_root) = probe();
        let legacy = String::from_utf8_lossy(AGENTS_MD.as_bytes())
            .replace(CURRENT_AGENTS_INIT_NOTICE, LEGACY_AGENTS_INIT_NOTICE);
        std::fs::write(agents_root.join("AGENTS.md"), legacy).unwrap();

        let report = materialize_for_project(&agents_root, &docs_root, Some("Shop")).unwrap();

        assert!(report.updated.iter().any(|path| path == "AGENTS.md"));
        assert!(std::fs::read_to_string(agents_root.join("AGENTS.md"))
            .unwrap()
            .contains("# Shop — Project Rules for AI Agents"));
    }

    /// Người dùng có thể đã sửa `AGENTS.md` hoặc thêm agent riêng — mất thứ
    /// đó thì không lấy lại được.
    #[test]
    fn materialize_never_overwrites_an_existing_file() {
        let (_tmp, agents_root, docs_root) = probe();
        std::fs::create_dir_all(agents_root.join(".claude/agents")).unwrap();
        std::fs::write(agents_root.join(".claude/agents/ba-agent.md"), "CỦA TÔI").unwrap();
        std::fs::write(agents_root.join("AGENTS.md"), "BẢNG THẬT").unwrap();

        let report = materialize(&agents_root, &docs_root).unwrap();

        assert_eq!(
            std::fs::read_to_string(agents_root.join(".claude/agents/ba-agent.md")).unwrap(),
            "CỦA TÔI"
        );
        assert_eq!(
            std::fs::read_to_string(agents_root.join("AGENTS.md")).unwrap(),
            "BẢNG THẬT"
        );
        assert!(report.skipped.iter().any(|p| p.ends_with("ba-agent.md")));
        assert!(report.skipped.iter().any(|p| p == "AGENTS.md"));
        assert!(!report.created.is_empty(), "phần còn lại vẫn phải được tạo");
    }

    /// Bấm Khởi tạo lần hai không được đụng vào gì.
    #[test]
    fn a_second_materialize_creates_nothing() {
        let (_tmp, agents_root, docs_root) = probe();
        materialize(&agents_root, &docs_root).unwrap();

        let second = materialize(&agents_root, &docs_root).unwrap();
        assert!(
            second.created.is_empty(),
            "đã tạo lại: {:?}",
            second.created
        );
        assert!(!second.skipped.is_empty());
    }

    /// Cây con phải được trải ra, không bị bỏ ở tầng một.
    #[test]
    fn nested_directories_inside_a_tree_are_materialized() {
        let (_tmp, agents_root, docs_root) = probe();
        materialize(&agents_root, &docs_root).unwrap();

        let nested = agents_root.join(".claude/context/business-flows");
        assert!(nested.is_dir(), "thiếu cây con {}", nested.display());
    }
}
