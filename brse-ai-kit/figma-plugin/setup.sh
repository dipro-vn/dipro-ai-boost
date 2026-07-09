#!/usr/bin/env bash
#
# Figma Plugin — chạy sau khi GIẢI NÉN FILE ZIP.
# Repo: https://github.com/dungptt-creator/Figma-Plugin
#
# Script tự chạy toàn bộ: cài đặt → build → login Claude → chạy proxy.
# KHÔNG cần git, KHÔNG cần clone (source đã có sẵn trong thư mục giải nén).
#
# Cách dùng cho người nhận zip:
#   1. Giải nén file zip
#   2. Mở Terminal, cd vào thư mục vừa giải nén
#   3. Chạy:  bash setup.sh
#
#      (hoặc:  chmod +x setup.sh && ./setup.sh)
#
#   Tuỳ chọn (không bắt buộc):
#     bash setup.sh --skip-login   # bỏ qua đăng nhập Claude
#     bash setup.sh --no-start     # chỉ cài đặt + build, không chạy proxy
#

set -euo pipefail

PROXY_PORT="${PROXY_PORT:-20128}"
PROXY_HOST="${PROXY_HOST:-127.0.0.1}"
MIN_NODE_MAJOR=18

SKIP_LOGIN=0
NO_START=0

# ── Colors (dùng ANSI-C quoting để chứa ký tự ESC thật, render đúng cả trong cat) ──
if [[ -t 1 ]]; then
  C_RESET=$'\033[0m'
  C_BOLD=$'\033[1m'
  C_GREEN=$'\033[32m'
  C_YELLOW=$'\033[33m'
  C_RED=$'\033[31m'
  C_CYAN=$'\033[36m'
else
  C_RESET='' C_BOLD='' C_GREEN='' C_YELLOW='' C_RED='' C_CYAN=''
fi

info()  { printf "${C_CYAN}▸ %s${C_RESET}\n" "$*"; }
ok()    { printf "${C_GREEN}✔ %s${C_RESET}\n" "$*"; }
warn()  { printf "${C_YELLOW}⚠ %s${C_RESET}\n" "$*"; }
fail()  { printf "${C_RED}✖ %s${C_RESET}\n" "$*" >&2; exit 1; }
step()  { printf "\n${C_BOLD}══ %s ══${C_RESET}\n" "$*"; }

usage() {
  cat <<'EOF'
Figma Plugin — setup & start (chạy sau khi giải nén zip)

  bash setup.sh              Cài đặt + build + login + chạy proxy
  bash setup.sh --skip-login Bỏ qua đăng nhập Claude Code
  bash setup.sh --no-start   Chỉ cài đặt + build, không chạy proxy
  bash setup.sh -h|--help    Trợ giúp

Environment:
  PROXY_PORT   Port proxy (mặc định: 20128)
EOF
}

parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --skip-login) SKIP_LOGIN=1; shift ;;
      --no-start)   NO_START=1; shift ;;
      -h|--help)    usage; exit 0 ;;
      *) fail "Tham số không hợp lệ: $1 (dùng --help)" ;;
    esac
  done
}

# Thư mục chứa chính file script này (nơi zip được giải nén).
script_dir() {
  local src="${BASH_SOURCE[0]}"
  while [[ -L "$src" ]]; do
    local dir
    dir="$(cd "$(dirname "$src")" && pwd)"
    src="$(readlink "$src")"
    [[ "$src" != /* ]] && src="$dir/$src"
  done
  cd "$(dirname "$src")" && pwd
}

is_project_root() {
  local dir="$1"
  [[ -f "$dir/manifest.json" && -f "$dir/package.json" ]]
}

require_cmd() {
  local cmd="$1"
  local hint="${2:-}"
  command -v "$cmd" >/dev/null 2>&1 && return 0
  fail "Không tìm thấy '$cmd'. ${hint}"
}

check_node_version() {
  local version major
  version="$(node -p "process.versions.node")"
  major="${version%%.*}"
  if [[ "$major" -lt "$MIN_NODE_MAJOR" ]]; then
    fail "Cần Node.js >= ${MIN_NODE_MAJOR}.x (hiện tại: v${version}). Cài từ https://nodejs.org"
  fi
  ok "Node.js v${version}"
}

check_prerequisites() {
  step "Kiểm tra môi trường"
  require_cmd node "Cài Node.js ${MIN_NODE_MAJOR}+ từ https://nodejs.org"
  require_cmd npm  "npm đi kèm Node.js — cài lại Node nếu thiếu"
  check_node_version
}

# Xác định thư mục project = nơi giải nén zip (thư mục chứa script, hoặc cwd).
resolve_project_dir() {
  step "Xác định thư mục source (đã giải nén zip)"
  local root
  root="$(script_dir)"

  if is_project_root "$root"; then
    PROJECT_DIR="$root"
  elif is_project_root "$(pwd)"; then
    PROJECT_DIR="$(pwd)"
  else
    fail "Không tìm thấy manifest.json + package.json.
   Hãy chắc chắn bạn đã GIẢI NÉN file zip và chạy script từ trong thư mục đó.
   Ví dụ:  cd Figma-Plugin && bash setup.sh"
  fi
  ok "Source: $PROJECT_DIR"
}

install_dependencies() {
  step "Cài đặt dependencies"
  cd "$PROJECT_DIR"

  if [[ -d node_modules ]] && [[ -f node_modules/.package-lock.json || -d node_modules/exceljs ]]; then
    info "node_modules đã có sẵn (đi kèm trong zip) — bỏ qua cài đặt"
  elif [[ -f package-lock.json ]]; then
    info "npm ci (theo package-lock.json)..."
    npm ci
  else
    info "npm install..."
    npm install
  fi

  ok "Dependencies sẵn sàng"
}

verify_build() {
  step "Build plugin"
  cd "$PROJECT_DIR"

  # Luôn build lại để chắc chắn dist/code.js khớp với src hiện tại.
  info "npm run build..."
  npm run build

  [[ -f dist/code.js ]] || fail "Build thất bại: thiếu dist/code.js"
  [[ -f src/ui.html ]]   || fail "Build thất bại: thiếu src/ui.html"

  local size_kb
  size_kb="$(du -k dist/code.js | awk '{print $1}')"
  ok "dist/code.js (${size_kb} KB)"
  ok "src/ui.html (ExcelJS inlined)"
}

is_claude_logged_in() {
  local claude_json="$HOME/.claude.json"
  [[ -f "$claude_json" ]] || return 1
  node -e "
    const fs = require('fs');
    try {
      const d = JSON.parse(fs.readFileSync(process.argv[1], 'utf8'));
      process.exit(d.oauthAccount && d.oauthAccount.emailAddress ? 0 : 1);
    } catch { process.exit(1); }
  " "$claude_json" 2>/dev/null
}

claude_email() {
  node -e "
    const fs = require('fs');
    try {
      const d = JSON.parse(fs.readFileSync(process.env.HOME + '/.claude.json','utf8'));
      console.log((d.oauthAccount && d.oauthAccount.emailAddress) || '');
    } catch { console.log(''); }
  " 2>/dev/null || true
}

# Trả về nguồn TTY dùng được để login interactive.
resolve_tty() {
  if [[ -t 0 ]]; then
    echo "stdin"
  elif [[ -r /dev/tty && -w /dev/tty ]]; then
    echo "/dev/tty"
  else
    echo ""
  fi
}

check_claude_login() {
  step "Đăng nhập Claude Code"
  cd "$PROJECT_DIR"

  if is_claude_logged_in; then
    local email; email="$(claude_email)"
    ok "Đã đăng nhập sẵn${email:+ ($email)} — bỏ qua bước login"
    return
  fi

  if [[ "$SKIP_LOGIN" -eq 1 ]]; then
    warn "Chưa login nhưng --skip-login được bật — bỏ qua"
    warn "AI cần login hoặc ANTHROPIC_API_KEY để chạy Auto AI / spec"
    return
  fi

  if [[ -n "${ANTHROPIC_API_KEY:-}" ]]; then
    ok "Có ANTHROPIC_API_KEY — dùng API key thay cho login OAuth"
    return
  fi

  warn "Chưa đăng nhập Claude Code — mở trình duyệt để bạn bấm Authorize..."
  info "Một trang đăng nhập Claude sẽ mở ra. Đăng nhập → bấm Authorize → quay lại đây."

  local tty; tty="$(resolve_tty)"
  if [[ -z "$tty" ]]; then
    warn "Không có terminal tương tác (TTY) để login OAuth."
    echo ""
    echo "  Mở Terminal và chạy:"
    echo "    cd \"$PROJECT_DIR\" && npm run claude:login"
    echo "  Hoặc đặt: export ANTHROPIC_API_KEY=sk-ant-..."
    echo ""
    warn "Tiếp tục — proxy vẫn chạy, nhưng AI sẽ lỗi cho tới khi login."
    return
  fi

  if [[ "$tty" == "/dev/tty" ]]; then
    npm run claude:login < /dev/tty || warn "Đăng nhập bị huỷ/lỗi"
  else
    npm run claude:login || warn "Đăng nhập bị huỷ/lỗi"
  fi

  if is_claude_logged_in; then
    local email; email="$(claude_email)"
    ok "Đăng nhập thành công${email:+ ($email)}"
  else
    warn "Login chưa hoàn tất — proxy vẫn chạy, dùng draft local hoặc ANTHROPIC_API_KEY nếu cần"
  fi
}

proxy_health_ok() {
  local code
  code="$(curl -fsS -o /dev/null -w "%{http_code}" \
    --connect-timeout 2 --max-time 3 \
    "http://${PROXY_HOST}:${PROXY_PORT}/health" 2>/dev/null || echo "000")"
  [[ "$code" == "200" ]]
}

print_figma_instructions() {
  local manifest_path="$PROJECT_DIR/manifest.json"
  step "Import plugin vào Figma Desktop"
  cat <<EOF

  1. Mở ${C_BOLD}Figma Desktop${C_RESET} (không dùng trình duyệt)
  2. Menu: ${C_BOLD}Plugins → Development → Import plugin from manifest...${C_RESET}
  3. Chọn file:
     ${C_CYAN}${manifest_path}${C_RESET}
  4. Chọn Frame trên canvas → chạy plugin "Basic Design Numbering"
  5. Sau khi sửa src/code.js: ${C_BOLD}npm run build${C_RESET} rồi Reload plugin trong Figma

EOF
}

print_proxy_urls() {
  local base="http://${PROXY_HOST}:${PROXY_PORT}"
  echo "  API:    ${base}/v1"
  echo "  Bridge: ${base}/bridge.html"
  echo "  Health: ${base}/health"
}

# Dọn instance proxy cũ/treo (đang giữ port nhưng /health không 200).
free_stale_port() {
  command -v lsof >/dev/null 2>&1 || return 0
  local pids
  pids="$(lsof -ti ":${PROXY_PORT}" -sTCP:LISTEN 2>/dev/null || true)"
  [[ -z "$pids" ]] && return 0

  if proxy_health_ok; then
    return 0   # proxy tốt đang chạy — không đụng tới
  fi

  warn "Phát hiện instance proxy cũ/treo trên port ${PROXY_PORT} (PID: ${pids//$'\n'/ }) — tự dọn..."
  # shellcheck disable=SC2086
  kill $pids 2>/dev/null || true
  sleep 1
  pids="$(lsof -ti ":${PROXY_PORT}" -sTCP:LISTEN 2>/dev/null || true)"
  if [[ -n "$pids" ]]; then
    # shellcheck disable=SC2086
    kill -9 $pids 2>/dev/null || true
    sleep 1
  fi
}

start_proxy() {
  step "Khởi động AI proxy"
  cd "$PROJECT_DIR"

  export PROXY_PORT
  local base="http://${PROXY_HOST}:${PROXY_PORT}"

  if proxy_health_ok; then
    ok "Proxy đã chạy sẵn tại ${base}"
    echo ""
    print_proxy_urls
    print_figma_instructions
    return
  fi

  free_stale_port

  if command -v lsof >/dev/null 2>&1 && lsof -i ":${PROXY_PORT}" -sTCP:LISTEN >/dev/null 2>&1; then
    fail "Port ${PROXY_PORT} vẫn bị chiếm. Kiểm tra: lsof -i :${PROXY_PORT}"
  fi

  print_figma_instructions
  info "Đang khởi động proxy (Ctrl+C để dừng)..."
  echo ""

  # Chạy thẳng node (không qua npm) để PID chính là server → kill sạch, không rò port.
  # stdin < /dev/null: proxy chạy nền không tự bật login interactive (setup.sh đã lo
  # login foreground ở trên). Chờ health rồi báo sẵn sàng; Ctrl+C sẽ dừng proxy.
  node scripts/ai-proxy-server.js < /dev/null &
  local proxy_pid=$!
  trap 'kill "$proxy_pid" 2>/dev/null || true' INT TERM

  local i
  for i in $(seq 1 30); do
    if ! kill -0 "$proxy_pid" 2>/dev/null; then
      wait "$proxy_pid"; local rc=$?
      fail "Proxy dừng bất ngờ (exit ${rc}). Xem log phía trên."
    fi
    if proxy_health_ok; then
      break
    fi
    sleep 1
  done

  if proxy_health_ok; then
    echo ""
    ok "Proxy online — sẵn sàng dùng"
    print_proxy_urls
  else
    warn "Chưa xác nhận được /health sau 30s — proxy vẫn đang chạy, kiểm tra log."
  fi

  echo ""
  info "Proxy đang chạy. Nhấn Ctrl+C để dừng."
  wait "$proxy_pid"
}

main() {
  parse_args "$@"

  printf "${C_BOLD}Figma Plugin — Setup & Start (từ zip)${C_RESET}\n"

  check_prerequisites
  resolve_project_dir
  install_dependencies
  verify_build
  check_claude_login

  if [[ "$NO_START" -eq 1 ]]; then
    step "Hoàn tất (không start proxy)"
    ok "Setup xong. Chạy proxy: cd \"$PROJECT_DIR\" && npm run proxy"
    print_figma_instructions
    exit 0
  fi

  start_proxy
}

main "$@"
