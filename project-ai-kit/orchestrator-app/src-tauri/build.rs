fn main() {
    // `tauri::generate_context!` nhúng icon vào binary bằng proc macro, mà proc
    // macro không phát được `cargo:rerun-if-changed`. Thiếu dòng này thì đổi file
    // trong `icons/` cargo vẫn coi crate là fresh, không biên dịch lại, và
    // `tauri dev` tiếp tục hiện icon cũ đã nhúng từ lần build trước.
    println!("cargo:rerun-if-changed=icons");
    tauri_build::build()
}
