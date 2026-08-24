//! Kết thúc cả **nhóm** tiến trình của một run, không chỉ tiến trình con
//! trực tiếp.
//!
//! Claude CLI sinh MCP server làm tiến trình con của nó. Chúng thừa kế pipe
//! stdout của run, nên chừng nào còn sống thì pipe không bao giờ EOF —
//! chính là thứ từng làm console run agent treo vĩnh viễn. Giết mỗi tiến
//! trình CLI không đủ: MCP server là "cháu", nằm ngoài tầm với của
//! `Child::kill()`.
//!
//! `spawn::build_command` đặt mỗi run vào một process group riêng
//! (`process_group(0)` → PGID = PID của CLI), nên ở đây chỉ cần bắn tín
//! hiệu tới nhóm mang id đó.

/// Tín hiệu gửi tới nhóm. Cố ý chỉ có 2 mức: xin nghỉ tử tế, rồi ép.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Signal {
    /// Cho tiến trình cơ hội tự dọn dẹp.
    Terminate,
    /// Dùng khi `Terminate` bị phớt lờ.
    Kill,
}

#[cfg(unix)]
impl Signal {
    fn as_raw(self) -> libc::c_int {
        match self {
            Signal::Terminate => libc::SIGTERM,
            Signal::Kill => libc::SIGKILL,
        }
    }
}

/// Gửi `signal` tới mọi tiến trình trong nhóm có PGID bằng `pid`.
///
/// Best-effort — nhóm đã chết hết thì đây là no-op (`ESRCH`). Cũng no-op
/// khi tiến trình được spawn ngoài `build_command` (không có nhóm riêng):
/// lúc đó không tồn tại nhóm nào mang id `pid`.
#[cfg(unix)]
pub fn signal_group(pid: u32, signal: Signal) {
    if pid == 0 {
        return;
    }
    let pgid = pid as libc::pid_t;
    // Chốt chặn cuối: không đời nào bắn vào nhóm của chính app. Trên thực
    // tế không xảy ra (PID con không thể bằng PGID của app), nhưng hậu quả
    // nếu sai là app tự sát nên vẫn kiểm.
    if pgid == unsafe { libc::getpgrp() } {
        return;
    }
    unsafe {
        libc::killpg(pgid, signal.as_raw());
    }
}

/// Windows không có khái niệm process group kiểu POSIX; kết thúc cả cây
/// tiến trình ở đó cần Job Object, là việc riêng. App chạy chủ yếu trên
/// macOS nên để no-op có chủ đích, thay vì giả vờ đã xử lý.
#[cfg(not(unix))]
pub fn signal_group(_pid: u32, _signal: Signal) {}
