#!/usr/bin/env bash
# Chapter 4 슈퍼랩 실습 프로젝트 생성
#
#   bash ch4/setup.sh [대상 폴더]          기본값: ~/claude-lab/superlab
#   SUPERLAB_FORCE=1 bash ch4/setup.sh     기존 폴더를 .bak-<시각>으로 옮기고 새로 생성
#   bash ch4/setup.sh --token [대상 폴더]  토큰만 다시 등록 (프로젝트는 그대로)
#   bash ch4/setup.sh --local [대상 폴더]  클라우드 대신 로컬 사내 API 서버 사용
#   SUPERLAB_TOKEN=<토큰> bash ch4/setup.sh   토큰을 묻지 않고 등록
#
# 하는 일
#   1. 필요한 도구와 Claude Code 버전 점검
#   2. kit/ 를 대상 폴더로 복사하고 독립 git 저장소로 초기화 (커밋 2개, 태그 superlab-start)
#   3. 커밋하지 않는 개인 파일 생성: .claude/settings.local.json(acceptEdits), .env(가짜 값)
#   4. 사내 API 연결: 주소와 토큰을 ~/.config/superlab/ 에 저장 (권한 600, 저장소 밖)
#   5. 연결 확인: python3 tools/hr_fetch.py me

set -euo pipefail

MIN_CC_VERSION="2.1.283"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KIT_DIR="$SCRIPT_DIR/kit"
CONF_DIR="${SUPERLAB_CONFIG_DIR:-$HOME/.config/superlab}"
LOCAL_BASE="http://127.0.0.1:8787"

MODE="full"
LOCAL=0
TARGET=""
for arg in "$@"; do
  case "$arg" in
    --token) MODE="token" ;;
    --local) LOCAL=1 ;;
    -h|--help) sed -n '2,16p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) TARGET="$arg" ;;
  esac
done
TARGET="${TARGET:-$HOME/claude-lab/superlab}"

ok()   { printf '  \033[32m✔\033[0m %s\n' "$1"; }
warn() { printf '  \033[33m!\033[0m %s\n' "$1"; WARNINGS=$((WARNINGS + 1)); }
fail() { printf '  \033[31m✘\033[0m %s\n' "$1"; exit 1; }
WARNINGS=0

version_ge() {  # $1 >= $2 ? (macOS 기본 bash 3.2에서도 동작)
  local IFS=.
  local -a a=($1) b=($2)
  local i x y
  for i in 0 1 2; do
    x=${a[i]:-0}; y=${b[i]:-0}
    if ((10#$x > 10#$y)); then return 0; fi
    if ((10#$x < 10#$y)); then return 1; fi
  done
  return 0
}

mask() { printf '%s' "${1:0:6}************"; }

# ───────────────────────────── 1) 도구 점검 ─────────────────────────────
check_tools() {
  echo "1) 도구 점검"
  command -v git >/dev/null 2>&1 || fail "git이 없습니다"
  ok "git $(git --version | awk '{print $3}')"

  if command -v python3 >/dev/null 2>&1; then
    PY_VER="$(python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])')"
    version_ge "$PY_VER" "3.9" || fail "python3 $PY_VER — 3.9 이상이 필요합니다"
    ok "python3 $PY_VER"
  else
    fail "python3가 없습니다 (3.9 이상 필요)"
  fi

  if command -v node >/dev/null 2>&1; then
    ok "node $(node --version)"
  else
    warn "node가 없습니다. 예제 앱 테스트(npm test)만 못 돌리고 랩은 진행됩니다"
  fi

  if command -v claude >/dev/null 2>&1; then
    CC_VER="$(claude --version 2>/dev/null | grep -Eo '[0-9]+\.[0-9]+\.[0-9]+' | head -n1 || true)"
    if [ -z "$CC_VER" ]; then
      warn "claude 버전을 읽지 못했습니다. 'claude --version'을 직접 확인하세요 (v$MIN_CC_VERSION 이상)"
    elif version_ge "$CC_VER" "$MIN_CC_VERSION"; then
      ok "Claude Code $CC_VER"
    else
      warn "Claude Code $CC_VER — v$MIN_CC_VERSION 이상이 필요합니다 ('claude update' 후 다시 확인)"
    fi
  else
    warn "claude 명령이 없습니다. 설치 후 실습을 시작하세요 (v$MIN_CC_VERSION 이상)"
  fi
}

# ───────────────────────────── 2·3) 프로젝트 생성 ─────────────────────────────
create_project() {
  echo
  echo "2) 실습 프로젝트 생성: $TARGET"
  [ -d "$KIT_DIR" ] || fail "kit 폴더를 찾지 못했습니다: $KIT_DIR"

  if [ -e "$TARGET" ]; then
    if [ "${SUPERLAB_FORCE:-0}" = "1" ]; then
      BACKUP="$TARGET.bak-$(date +%Y%m%d-%H%M%S)"
      mv "$TARGET" "$BACKUP"
      ok "기존 폴더를 옮겼습니다: $BACKUP"
    else
      fail "이미 있습니다: $TARGET  (새로 만들려면 SUPERLAB_FORCE=1, 토큰만 다시 등록하려면 --token)"
    fi
  fi

  mkdir -p "$TARGET"
  cp -R "$KIT_DIR/." "$TARGET/"
  find "$TARGET" -name '__pycache__' -type d -prune -exec rm -rf {} + 2>/dev/null || true
  chmod +x "$TARGET"/tools/*.py "$TARGET"/tools/*.sh "$TARGET"/bin/lab
  ok "킷 파일 복사"

  cd "$TARGET"
  git init -q
  git symbolic-ref HEAD refs/heads/main
  git config user.name  >/dev/null 2>&1 || git config user.name  "superlab"
  git config user.email >/dev/null 2>&1 || git config user.email "superlab@example.com"

  git add -A
  git commit -q -m "chore: superlab starter kit"

  cat > src/greet.js <<'EOF'
export function greet(name) {
  return `Hello, ${name}!`;
}

export function farewell(name) {
  return `Goodbye, ${name}!`;
}
EOF
  cat > test.js <<'EOF'
import assert from "node:assert/strict";
import { greet, farewell } from "./src/greet.js";

assert.equal(greet("Claude"), "Hello, Claude!");
assert.equal(farewell("Claude"), "Goodbye, Claude!");
console.log("PASS");
EOF
  git commit -q -am "feat: add farewell message"
  git tag -f superlab-start >/dev/null
  ok "커밋 2개, 시작 지점 태그 superlab-start (/standup이 읽을 오늘 커밋)"

  mkdir -p .claude
  cat > .claude/settings.local.json <<'EOF'
{
  "permissions": {
    "defaultMode": "acceptEdits"
  }
}
EOF
  printf '# 실습용 가짜 값입니다\nAPI_TOKEN=lab-fake-token\n' > .env
  ok "개인 파일 생성 (커밋 안 함): .claude/settings.local.json, .env"

  if command -v node >/dev/null 2>&1 && npm test --silent >/dev/null 2>&1; then
    ok "npm test 통과"
  fi
}

# ───────────────────────────── 4) 사내 API 연결 ─────────────────────────────
cloud_base() {
  local f="$SCRIPT_DIR/lab-api.env" v=""
  if [ -f "$f" ]; then
    v="$(grep -E '^LAB_API_BASE=' "$f" | tail -n1 | cut -d= -f2- | tr -d '[:space:]"' || true)"
  fi
  printf '%s' "${v%/}"
}

save_conf() {  # $1=파일 이름, $2=값
  ( umask 077; mkdir -p "$CONF_DIR"; printf '%s\n' "$2" > "$CONF_DIR/$1" )
  chmod 600 "$CONF_DIR/$1"
}

register_api() {
  echo
  echo "4) 사내 API 연결"
  local base token
  base="$(cloud_base)"
  if [ "$LOCAL" = "1" ] || [ -z "$base" ]; then
    base="$LOCAL_BASE"
    [ "$LOCAL" = "1" ] || ok "클라우드 주소가 아직 없어 로컬 서버 모드로 설정합니다"
    token="${SUPERLAB_TOKEN:-$(python3 "$KIT_DIR/tools/lab_server.py" --issue 1)}"
    save_conf api_base "$base"
    save_conf token "$token"
    ok "로컬 모드: $base (실습 중 다른 터미널에서 'bin/lab server'를 켜 둡니다)"
    ok "로컬 토큰 저장: $CONF_DIR/token ($(mask "$token"))"
    return
  fi

  token="${SUPERLAB_TOKEN:-}"
  if [ -z "$token" ]; then
    if [ -t 0 ]; then
      printf '  강사에게 받은 토큰을 붙여 넣고 Enter (화면에 표시되지 않음): '
      IFS= read -rs token
      echo
    else
      warn "토큰 입력을 받을 수 없습니다. 나중에 'bash $SCRIPT_DIR/setup.sh --token'으로 등록하세요"
      save_conf api_base "$base"
      return
    fi
  fi
  token="$(printf '%s' "$token" | tr -d '[:space:]')"
  if ! printf '%s' "$token" | grep -Eq '^wk-[0-9]{2}-[0-9a-f]{12}$'; then
    fail "토큰 형식이 아닙니다 (wk-<좌석 2자리>-<12자리>). 다시 실행하세요: bash $SCRIPT_DIR/setup.sh --token"
  fi
  save_conf api_base "$base"
  save_conf token "$token"
  ok "클라우드 모드: $base"
  ok "토큰 저장: $CONF_DIR/token ($(mask "$token"), 권한 600, 저장소 밖)"
}

# ───────────────────────────── 5) 연결 확인 ─────────────────────────────
verify_api() {
  echo
  echo "5) 연결 확인"
  local dir="$TARGET" server_pid="" out
  [ -f "$dir/tools/hr_fetch.py" ] || dir="$KIT_DIR"
  if [ "$(cat "$CONF_DIR/api_base" 2>/dev/null)" = "$LOCAL_BASE" ]; then
    if ! python3 - <<'PY' 2>/dev/null
import socket, sys
s = socket.socket(); s.settimeout(1)
sys.exit(0 if s.connect_ex(("127.0.0.1", 8787)) == 0 else 1)
PY
    then
      python3 "$dir/tools/lab_server.py" --quiet >/dev/null 2>&1 &
      server_pid=$!
      sleep 1
    fi
  fi
  if out="$(cd "$dir" && python3 tools/hr_fetch.py me 2>&1)"; then
    ok "사내 API 응답: $(printf '%s\n' "$out" | grep -m1 -E '참가자|wk-[0-9]{2}' | sed 's/^[#[:space:]]*//' || echo 'OK')"
  else
    warn "사내 API 연결 실패: $(printf '%s\n' "$out" | tail -n1)"
  fi
  if [ -n "$server_pid" ]; then kill "$server_pid" 2>/dev/null || true; fi
}

# ───────────────────────────── 실행 ─────────────────────────────
if [ "$MODE" = "token" ]; then
  register_api
  verify_api
  exit 0
fi

check_tools
create_project
register_api
verify_api

echo
if [ "$WARNINGS" -gt 0 ]; then
  echo "경고 $WARNINGS건을 확인한 뒤 실습을 시작하세요."
else
  echo "준비 완료."
fi
cat <<EOF

다음 단계
  cd $TARGET
  claude                 # 터미널 1: 작업. 첫 실행 시 폴더 신뢰 확인을 승인
  bin/lab coach lab1     # 터미널 2: 코치 (읽기 전용)

워크시트: docs/worksheets/lab1.md (편집기로 열어 두세요)
EOF
