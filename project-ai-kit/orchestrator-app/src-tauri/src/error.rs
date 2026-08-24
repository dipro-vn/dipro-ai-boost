use serde::Serialize;

/// App-wide error type. Every Tauri command returns `Result<T, AppError>` so the
/// frontend always receives a structured `{ code, message, details? }` payload —
/// never a bare string or a generic "Error" (see orchestrator SPEC E1/E3: mọi
/// lỗi phải rõ ràng, không hiện thông báo chung chung).
#[derive(Debug, thiserror::Error)]
pub enum AppError {
    #[error("io error: {0}")]
    Io(#[from] std::io::Error),

    #[error("json error: {0}")]
    Json(#[from] serde_json::Error),

    #[error("store error: {0}")]
    Store(#[from] tauri_plugin_store::Error),

    #[error("git error: {0}")]
    Git(#[from] git2::Error),

    #[error("path is outside the allowed root: {path}")]
    PathOutsideRoot { path: String },

    #[error("no project is currently open")]
    NoProjectOpen,

    #[error("{message}")]
    Invalid { message: String },

    #[error("{path}: {reason}")]
    RestrictedPath { path: String, reason: String },
}

impl AppError {
    fn code(&self) -> &'static str {
        match self {
            AppError::Io(_) => "io_error",
            AppError::Json(_) => "json_error",
            AppError::Store(_) => "store_error",
            AppError::Git(_) => "git_error",
            AppError::PathOutsideRoot { .. } => "path_outside_root",
            AppError::NoProjectOpen => "no_project_open",
            AppError::Invalid { .. } => "invalid",
            AppError::RestrictedPath { .. } => "restricted_path",
        }
    }
}

/// Tauri serializes command errors via `Serialize`, so we hand-roll the shape
/// instead of deriving it, to guarantee the `{ code, message }` contract stays
/// stable regardless of how the enum evolves.
impl Serialize for AppError {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: serde::Serializer,
    {
        use serde::ser::SerializeStruct;
        let mut state = serializer.serialize_struct("AppError", 2)?;
        state.serialize_field("code", self.code())?;
        state.serialize_field("message", &self.to_string())?;
        state.end()
    }
}

pub type AppResult<T> = Result<T, AppError>;
