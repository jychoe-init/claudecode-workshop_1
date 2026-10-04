#!/usr/bin/env bash
# 같은 프롬프트를 새 세션(-p)으로 실행하고 비용·토큰을 usage.csv에 한 줄씩 기록합니다.
# 훅 입력에는 토큰·비용 필드가 없으므로, -p --output-format json 의 결과를 사용합니다.
#
# 사용법
#   tools/usage_log.sh <라벨> "<프롬프트>" ['<--settings 로 넘길 JSON 또는 파일 경로>']
#
# 예: 스킬을 켠 상태와 끈 상태 비교 (skillOverrides)
#   tools/usage_log.sh notes-on  "samples/meeting_transcript.txt 를 회의록으로 정리해 줘"
#   tools/usage_log.sh notes-off "samples/meeting_transcript.txt 를 회의록으로 정리해 줘" \
#     '{"skillOverrides":{"meeting-notes":"off"}}'
#
# 결과
#   usage.csv           실행마다 1줄 (비용, 토큰, 턴 수, 소요 시간, 권한 거부 수)
#   .usage/<라벨>.md    응답 본문 (품질 비교용)
#
# 주의
#   -p 실행에서는 승인 요청(ask)이 모두 거부됩니다. 읽기 위주의 프롬프트로 비교하세요.
#   total_cost_usd 는 목록가 기준 추정치입니다. 구독 플랜에서는 청구액과 다릅니다.

set -euo pipefail

if [ $# -lt 2 ]; then
  sed -n '2,20p' "$0" | sed 's/^# \{0,1\}//'
  exit 2
fi

label="$1"
prompt="$2"
settings="${3:-}"

command -v claude >/dev/null 2>&1 || { echo "claude 명령을 찾을 수 없습니다" >&2; exit 1; }

root="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
mkdir -p "$root/.usage"
raw="$(mktemp)"
trap 'rm -f "$raw"' EXIT

args=(-p "$prompt" --output-format json)
if [ -n "$settings" ]; then
  args+=(--settings "$settings")
fi

echo "실행 중: [$label] ${settings:+(--settings $settings)}" >&2
status=0
(cd "$root" && claude "${args[@]}") > "$raw" || status=$?

python3 - "$raw" "$root/usage.csv" "$root/.usage/$label.md" "$label" "$status" <<'PY'
import csv, datetime, json, os, sys

raw_path, csv_path, md_path, label, status = sys.argv[1:6]
text = open(raw_path, encoding="utf-8", errors="replace").read().strip()

data = {}
for candidate in (text, text.splitlines()[-1] if text else ""):
    try:
        data = json.loads(candidate)
        break
    except (json.JSONDecodeError, IndexError):
        continue
if isinstance(data, list):  # 혹시 메시지 배열로 온 경우 마지막 result 메시지 사용
    data = next((m for m in reversed(data) if isinstance(m, dict) and m.get("type") == "result"), {})

usage = data.get("usage") or {}
row = {
    "timestamp": datetime.datetime.now().isoformat(timespec="seconds"),
    "label": label,
    "total_cost_usd": data.get("total_cost_usd", ""),
    "input_tokens": usage.get("input_tokens", ""),
    "output_tokens": usage.get("output_tokens", ""),
    "cache_read_tokens": usage.get("cache_read_input_tokens", ""),
    "cache_write_tokens": usage.get("cache_creation_input_tokens", ""),
    "num_turns": data.get("num_turns", ""),
    "duration_ms": data.get("duration_ms", ""),
    "permission_denials": len(data.get("permission_denials") or []),
    "is_error": data.get("is_error", status != "0"),
}

new_file = not os.path.exists(csv_path)
with open(csv_path, "a", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(row))
    if new_file:
        writer.writeheader()
    writer.writerow(row)

with open(md_path, "w", encoding="utf-8") as f:
    f.write(str(data.get("result", text)) + "\n")

print("  ".join(f"{k}={v}" for k, v in row.items() if k != "timestamp"))
print(f"기록: {os.path.relpath(csv_path)}  응답: {os.path.relpath(md_path)}")
if not data:
    print("경고: JSON 결과를 읽지 못했습니다. 응답 원문을 확인하세요.", file=sys.stderr)
PY
