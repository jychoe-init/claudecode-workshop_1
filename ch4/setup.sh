#!/usr/bin/env bash
# Chapter 4 슈퍼랩 실습 프로젝트 생성
#
#   bash ch4/setup.sh [대상 폴더]          기본값: ~/claude-lab/superlab
#   SUPERLAB_FORCE=1 bash ch4/setup.sh     기존 폴더를 .bak-<시각>으로 옮기고 새로 생성
#
# 하는 일
#   1. 필요한 도구와 Claude Code 버전 점검
#   2. kit/ 내용을 대상 폴더로 복사하고 독립 git 저장소로 초기화 (기본 브랜치 main)
#   3. 오늘 날짜 커밋 2개 생성 (/standup 이 "어제 이후 커밋"을 읽을 수 있도록)
#   4. feature/greeting-i18n 브랜치에 커밋 2개 생성 (개발 트랙 /pr-desc 용 diff)
#   5. 커밋하지 않는 개인 파일 생성: .claude/settings.local.json(acceptEdits), .env(가짜 값)

set -euo pipefail

MIN_CC_VERSION="2.1.283"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KIT_DIR="$SCRIPT_DIR/kit"
TARGET="${1:-$HOME/claude-lab/superlab}"

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

echo "1) 도구 점검"
command -v git >/dev/null 2>&1 || fail "git이 없습니다"
ok "git $(git --version | awk '{print $3}')"

if command -v node >/dev/null 2>&1; then
  ok "node $(node --version)"
else
  fail "node가 없습니다 (Node.js 18 이상 필요)"
fi

if command -v python3 >/dev/null 2>&1; then
  PY_VER="$(python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])')"
  version_ge "$PY_VER" "3.9" || fail "python3 $PY_VER — 3.9 이상이 필요합니다"
  ok "python3 $PY_VER"
else
  fail "python3가 없습니다 (3.9 이상 필요)"
fi

if command -v jq >/dev/null 2>&1; then
  ok "jq $(jq --version 2>/dev/null | sed 's/^jq-//')"
else
  ok "jq 없음 (선택 사항, 없어도 진행됩니다)"
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

if python3 - <<'PY' 2>/dev/null
import socket, sys
s = socket.socket()
try:
    s.bind(("127.0.0.1", 8787))
except OSError:
    sys.exit(1)
finally:
    s.close()
PY
then
  ok "8787 포트 사용 가능 (Slack mock 수신기)"
else
  warn "8787 포트를 다른 프로그램이 쓰고 있습니다. 실습 때 SLACK_MOCK_PORT로 다른 포트를 지정하세요"
fi

echo
echo "2) 실습 프로젝트 생성: $TARGET"
[ -d "$KIT_DIR" ] || fail "kit 폴더를 찾지 못했습니다: $KIT_DIR"

if [ -e "$TARGET" ]; then
  if [ "${SUPERLAB_FORCE:-0}" = "1" ]; then
    BACKUP="$TARGET.bak-$(date +%Y%m%d-%H%M%S)"
    mv "$TARGET" "$BACKUP"
    ok "기존 폴더를 옮겼습니다: $BACKUP"
  else
    fail "이미 있습니다: $TARGET  (새로 만들려면 SUPERLAB_FORCE=1 을 붙여 다시 실행)"
  fi
fi

mkdir -p "$TARGET"
cp -R "$KIT_DIR/." "$TARGET/"
find "$TARGET" -name '__pycache__' -type d -prune -exec rm -rf {} + 2>/dev/null || true
chmod +x "$TARGET"/tools/*.py "$TARGET"/tools/*.sh
ok "킷 파일 복사"

cd "$TARGET"
git init -q
git symbolic-ref HEAD refs/heads/main
git config user.name  >/dev/null 2>&1 || git config user.name  "superlab"
git config user.email >/dev/null 2>&1 || git config user.email "superlab@example.com"

git add -A
git commit -q -m "chore: superlab starter kit scaffold"

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
ok "main 커밋 2개"

git checkout -q -b feature/greeting-i18n
cat > src/i18n.js <<'EOF'
const MESSAGES = {
  en: (name) => `Hello, ${name}!`,
  ko: (name) => `안녕하세요, ${name}님!`,
};

export function localize(locale, name) {
  const render = MESSAGES[locale] ?? MESSAGES.en;
  return render(name);
}
EOF
cat > src/greet.js <<'EOF'
import { localize } from "./i18n.js";

export function greet(name, locale = "en") {
  return localize(locale, name);
}

export function farewell(name) {
  return `Goodbye, ${name}!`;
}
EOF
git add -A
git commit -q -m "feat: add locale-aware greeting"

cat > test.js <<'EOF'
import assert from "node:assert/strict";
import { greet, farewell } from "./src/greet.js";

assert.equal(greet("Claude"), "Hello, Claude!");
assert.equal(greet("클로드", "ko"), "안녕하세요, 클로드님!");
assert.equal(farewell("Claude"), "Goodbye, Claude!");
console.log("PASS");
EOF
git commit -q -am "test: cover korean greeting"
git checkout -q main
ok "feature/greeting-i18n 브랜치 커밋 2개 (현재 브랜치: main)"

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

if npm test --silent >/dev/null 2>&1; then
  ok "npm test 통과"
else
  warn "npm test 실패 — node 설치를 확인하세요"
fi

echo
if [ "$WARNINGS" -gt 0 ]; then
  echo "경고 $WARNINGS건을 확인한 뒤 실습을 시작하세요."
else
  echo "준비 완료."
fi
cat <<EOF

다음 단계
  cd $TARGET
  claude            # 첫 실행 시 폴더 신뢰 확인 화면이 나오면 승인

브랜치
  main                    오늘 날짜 커밋 2개
  feature/greeting-i18n   개발 트랙(/pr-desc)용 변경 2개
EOF
