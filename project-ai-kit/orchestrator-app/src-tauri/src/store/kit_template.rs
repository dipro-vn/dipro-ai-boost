//! Bộ khung kit được nhúng thẳng vào binary (`include_dir!`), để app tự
//! dựng được một project mới thay vì bắt người dùng copy tay.
//!
//! Nhúng thay vì copy từ một thư mục ngoài: chỉ cần thêm một đường dẫn nữa
//! do người dùng khai là lại sinh ra đúng loại lỗi `repositoryRoot` — trỏ
//! sai, im lặng, chỉ lộ ra ở tận bước cuối.
//!
//! Skill `ui-ux-pro-max` (3.5 MB trên tổng 5.4 MB của `.claude/skills`,
//! phần lớn là data font/icon) và `.claude/memory/` CỐ Ý không nhúng: flow
//! của app không đọc cái đầu, còn cái sau là nhật ký phát triển của chính
//! kit chứ không phải nội dung kit.
//!
//! Mỗi thư mục con có một `include_dir!` riêng thay vì nhúng cả `.claude/`
//! rồi lọc — macro nhúng toàn bộ cây tại compile time, lọc về sau không làm
//! binary nhỏ đi.

use std::path::{Path, PathBuf};

use include_dir::{include_dir, Dir};
use sha2::{Digest, Sha256};

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
/// Phần thân workflow mà `ba-agent.md` lazy-load (`spec-template.md`,
/// `recheck.md`, `figma-outputs/*`). Vô dụng nếu thiếu `ba-agent.md`, nên
/// đi chung nhóm "agents" với nó.
static BA_AGENT: Dir<'_> = include_dir!("$CARGO_MANIFEST_DIR/../../.claude/ba-agent");

/// Mỗi skill một `include_dir!` thay vì nhúng cả `.claude/skills` rồi lọc:
/// macro nhúng toàn bộ cây tại compile time, lọc lúc materialize vẫn để
/// `ui-ux-pro-max` (3.5 MB) nằm chết trong binary.
///
/// Danh sách viết tay sẽ lệch khi kit thêm skill mới — `tests::
/// embedded_kit_has_every_skill_except_the_deliberately_excluded_one` đọc
/// thẳng `.claude/skills` trên đĩa để bắt đúng chỗ đó.
static SKILL_AUTOMATION_ENGINEER: Dir<'_> =
    include_dir!("$CARGO_MANIFEST_DIR/../../.claude/skills/automation_engineer");
static SKILL_BA_FIGMA_OUTPUT: Dir<'_> =
    include_dir!("$CARGO_MANIFEST_DIR/../../.claude/skills/ba-figma-output");
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
        label: "Sub-agent (.claude/agents/ · .claude/ba-agent/)",
        root: KitRoot::AgentsRoot,
        sources: &[
            Source::Tree {
                prefix: ".claude/agents",
                dir: &AGENTS,
            },
            Source::Tree {
                prefix: ".claude/ba-agent",
                dir: &BA_AGENT,
            },
        ],
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
                prefix: ".claude/skills/ba-figma-output",
                dir: &SKILL_BA_FIGMA_OUTPUT,
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

/// Băm SHA-256 của những bản kit ĐÃ TỪNG phát hành cho một file.
///
/// File trên đĩa khớp một băm ở đây nghĩa là người dùng chưa đụng vào, chỉ
/// đang giữ bản cũ — làm mới an toàn. Không khớp nghĩa là file đã bị sửa,
/// và file custom thì không bao giờ được ghi đè. Nhờ vậy project tạo từ
/// trước vẫn nhận được sửa đổi của kit mà không mất công sửa tay.
///
/// **Chỉ dùng cho file `render_project_name` không đụng tới.** Băm ở đây so
/// với template CHƯA render, nên file có render (`AGENTS.md`,
/// `.claude/context/*.md`, `.claude/templates/docs-index.md`) sẽ không bao
/// giờ khớp — chúng đi đường migrate riêng của `matches_original_template`.
///
/// Mỗi lần sửa một file kit: thêm băm của bản VỪA BỊ THAY vào đây, nếu không
/// project cũ sẽ kẹt lại ở bản đó mãi.
const SUPERSEDED_KIT_FILES: &[(&str, &str)] = &[
    // Bản trước khi thêm mục "Dừng ở đây" — bản cũ kết thúc bằng gợi ý chạy
    // BA, làm Claude nói tiếp sau khi init xong nên terminal init-kit của app
    // không bao giờ im đủ lâu để tự đóng.
    (
        ".claude/agents/init-agent.md",
        "7c1446693cb37cf1387f2fa15fc7d04ca33299dded66b0e5b14cfbe6d9d454f8",
    ),
    // MỌI bản `ba-agent.md` đã từng phát hành, tính đến bản khai `tools:`
    // Figma sai prefix (`mcp__plugin_figma_figma__*`) — bản đó không gọi nổi
    // Figma nên Output 1-3 im lặng không bao giờ chạy. Không biết được bản
    // `.dmg` nào đang nằm trên máy ai, nên khai hết cho chắc.
    // 82619eb
    (
        ".claude/agents/ba-agent.md",
        "c8a69325ea1ec4dfb00b727ffac89e927bfa4c8b6c1054ccd5af1ac2aa3ec00c",
    ),
    // 90da36f
    (
        ".claude/agents/ba-agent.md",
        "3a2f1094c7b19eaa68af641b568d073f47b1a09977a00d7730ee98d81638135c",
    ),
    // fd306cb
    (
        ".claude/agents/ba-agent.md",
        "ad5da004244a565ee0daae908f7600705c23f57fa8a935a96a8a7631c3237926",
    ),
    // db516e7
    (
        ".claude/agents/ba-agent.md",
        "227bd3e41054fa23f6cf6e7c954d2e829b0f26375ea6d7b1f96adf792e794ff9",
    ),
    // d61dee0
    (
        ".claude/agents/ba-agent.md",
        "c9df8d0222745dd79d334645a2482b71870988f09c056a0e1060268a645d0f0d",
    ),
    // 901a841
    (
        ".claude/agents/ba-agent.md",
        "a8d447c6ef3daf6b2982313c57c1c5cd6c629c86355d46aecba4cb1d7ddaf8b9",
    ),
    // db082c1
    (
        ".claude/agents/ba-agent.md",
        "ca848d7bf2ddea815ea60ebafcc550a5c1469660b625f17249a56e403a616229",
    ),
    // e9a71d6
    (
        ".claude/agents/ba-agent.md",
        "5a929ba0224b0c90e4552e5ad89826621be5498bceb1f5fda501d26332fdc2a8",
    ),
    // Bản trước khi sửa prefix MCP Figma. Bản cũ hoặc khai `mcp__figma__*`
    // thiếu (cài server remote bằng lệnh chính thức là mất Figma, im lặng),
    // hoặc khai tool GHI cho `figma-bridge` — server đó chỉ có tool đọc.
    // block `mcpServers` inert — Claude Code không nạp mcpServers từ settings.json
    (
        ".claude/settings.json",
        "be95c4fe74b7d110c245abce7e9d8bda8a079a2818aaa335d2ad1e1d97f1a58b",
    ),
    (
        ".claude/agents/ba-agent.md",
        "f7443d05e7bd41c8d97ef6b7cb22d5908545087ff5506a73a099c3c20dee6288",
    ),
    (
        ".claude/agents/designer-agent.md",
        "eea1580a2e829aa5e3ffd652e5efa251ba7aa6b25cdb425a40628b6cda45d2c8",
    ),
    (
        ".claude/agents/design-analyst-agent.md",
        "1e5190c9c9f88f626ed9bf273009e4d5abc35ebb50481cfb6833662625c8ebd7",
    ),
    (
        ".claude/agents/frontend-agent.md",
        "9860ba328f2277caf30ee9b365a3aaed37154f6b4eba097d8664fae364fe85fd",
    ),
    (
        ".claude/agents/mobile-agent.md",
        "6b6a4c3fce0c0b796e16cfb9be9d06583eaa5b9212288f7d7a98ddb1c6d0bb4c",
    ),
    (
        ".claude/agents/backend-agent.md",
        "1b4465c16894e07c836c4665988d6f1290be02395384654733baf732f3a72a9f",
    ),
    (
        ".claude/agents/qa-agent.md",
        "2a6f728dfed01f27d69705d91fe2d9660f9aeb6dd042a9e4a715a7f7ab1689ba",
    ),
];

/// `true` khi `existing` là một bản kit cũ đã biết của `relative`.
fn is_superseded_kit_file(relative: &Path, existing: &[u8]) -> bool {
    is_superseded_in(SUPERSEDED_KIT_FILES, relative, existing)
}

/// Tách khỏi `is_superseded_kit_file` để test được quyết định mà không phải
/// dựng lại nguyên nội dung một bản kit cũ chỉ để khớp băm.
fn is_superseded_in(table: &[(&str, &str)], relative: &Path, existing: &[u8]) -> bool {
    let Some(key) = relative.to_str() else {
        return false;
    };
    if !table.iter().any(|(path, _)| *path == key) {
        return false;
    }
    let digest = format!("{:x}", Sha256::digest(existing));
    table
        .iter()
        .any(|(path, hash)| *path == key && *hash == digest)
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
                        let existing = std::fs::read(&target).ok();
                        let renders_over_original = rendered != bytes
                            && existing.as_deref().is_some_and(|existing| {
                                matches_original_template(&relative, existing, bytes)
                            });
                        // Bản kit cũ còn nguyên vẹn thì nâng lên bản hiện tại.
                        // Đây là đường DUY NHẤT để sửa đổi của kit tới được
                        // project đã tạo từ trước — mọi file đã tồn tại khác
                        // đều bị bỏ qua.
                        let superseded = existing
                            .as_deref()
                            .is_some_and(|existing| is_superseded_kit_file(&relative, existing));
                        if renders_over_original || superseded {
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

    /// Thư mục cấp 1 của `.claude/` CỐ Ý không nhúng. `memory/` là nhật ký
    /// phát triển của chính kit này (feedback từ demo) — không file kit nào
    /// tham chiếu tới nó, và seed nó vào project khách là gửi kèm ghi chú
    /// nội bộ.
    const EXCLUDED_TOP_LEVEL_DIRS: &[&str] = &["memory"];

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
            let is_covered = covered.iter().any(|p| p.starts_with(&prefix));
            // Đối xứng: loại trừ phải nói thành lời ở CẢ HAI chiều, để lần
            // sau ai đó nhúng lại `memory/` thì test kêu chứ không im.
            if EXCLUDED_TOP_LEVEL_DIRS.contains(&dir.as_str()) {
                assert!(
                    !is_covered,
                    "`.claude/{dir}` bị loại trừ có chủ đích nhưng lại đang được nhúng"
                );
            } else {
                assert!(
                    is_covered,
                    "`.claude/{dir}` của kit không được nhóm nào trong GROUPS phủ"
                );
            }
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
        // `ba-agent.md` Bước 4/5 `Read` thẳng những file này; thiếu chúng
        // thì agent chạy được nhưng mọi lệnh đọc bắt buộc đều gãy.
        assert!(agents_root
            .join(".claude/ba-agent/spec-template.md")
            .is_file());
        assert!(agents_root
            .join(".claude/ba-agent/figma-outputs/output-5-mkdocs.md")
            .is_file());
        assert!(agents_root
            .join(".claude/skills/ba-figma-output/SKILL.md")
            .is_file());
        // File nhị phân cũng phải đi theo: skill bắt agent `Read` ảnh mẫu.
        assert!(agents_root
            .join(".claude/skills/ba-figma-output/examples/final_output_1.png")
            .is_file());
        assert!(
            !agents_root.join(".claude/memory").exists(),
            "nhật ký phát triển của kit không được seed vào project"
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

    fn sha256_hex(bytes: &[u8]) -> String {
        format!("{:x}", Sha256::digest(bytes))
    }

    /// Nguyên vẹn bản cũ thì nâng cấp; sửa một chữ là thành file custom và
    /// không được đụng tới nữa.
    #[test]
    fn only_an_untouched_old_kit_file_counts_as_superseded() {
        let table = [(".claude/agents/init-agent.md", "")];
        let old = b"noi dung kit cu";
        let table = [(table[0].0, sha256_hex(old).leak() as &str)];
        let path = Path::new(".claude/agents/init-agent.md");

        assert!(is_superseded_in(&table, path, old));
        assert!(!is_superseded_in(
            &table,
            path,
            b"noi dung kit cu + sua tay"
        ));
        assert!(
            !is_superseded_in(&table, Path::new(".claude/agents/ba-agent.md"), old),
            "băm chỉ có giá trị cho đúng file đã khai"
        );
    }

    /// Mỗi entry phải trỏ tới một file kit CÓ THẬT và mang băm của một bản
    /// KHÁC bản hiện tại. Entry trỏ sai path thì im lặng vô dụng; entry mang
    /// đúng băm bản hiện tại thì mọi lần materialize đều ghi đè lại file
    /// không đổi và báo `updated` mãi mãi.
    #[test]
    fn every_superseded_entry_names_a_real_kit_file_of_an_older_version() {
        let mut embedded: Vec<(PathBuf, String)> = Vec::new();
        for group in GROUPS {
            for (relative, contents) in entries_of(group) {
                if let Some(bytes) = contents {
                    embedded.push((relative, sha256_hex(bytes)));
                }
            }
        }

        for (path, hash) in SUPERSEDED_KIT_FILES {
            let current = embedded
                .iter()
                .find(|(relative, _)| relative == Path::new(path))
                .unwrap_or_else(|| panic!("{path} không có trong kit nhúng"));
            assert_ne!(
                &current.1, hash,
                "{path}: băm đã khai trùng bản hiện tại, entry này phải được gỡ"
            );
        }
    }

    /// Băm được so với template CHƯA render, nên file có render sẽ không bao
    /// giờ khớp — khai vào đây là tự đánh lừa mình.
    #[test]
    fn no_superseded_entry_is_a_rendered_template() {
        for (path, _) in SUPERSEDED_KIT_FILES {
            let relative = PathBuf::from(path);
            let rendered = render_project_name(&relative, b"x", Some("Shop"));
            assert_eq!(
                rendered, b"x",
                "{path} là template có render, không dùng được cơ chế băm"
            );
        }
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
