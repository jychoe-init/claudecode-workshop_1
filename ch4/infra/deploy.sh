#!/usr/bin/env bash
# 사내 API 스택 배포 (AWS SAM CLI 필요)
#
#   bash ch4/infra/deploy.sh                 서울 리전에 배포
#   STACK=... REGION=... bash ch4/infra/deploy.sh
#
# 비밀값: LAB_TOKEN_SECRET 환경변수 → ch4/infra/.secret 파일 → 없으면 새로 만들어 .secret에 저장
# 예산 알림: BUDGET_EMAIL 환경변수 (선택)

set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STACK="${STACK:-claudecode-ch4-labapi}"
REGION="${REGION:-ap-northeast-2}"
EXPECTED_ACCOUNT="${EXPECTED_ACCOUNT:-135808921005}"

command -v sam >/dev/null 2>&1 || { echo "SAM CLI가 없습니다: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html"; exit 1; }
ACCOUNT="$(aws sts get-caller-identity --query Account --output text)"
if [ "$ACCOUNT" != "$EXPECTED_ACCOUNT" ]; then
  echo "현재 자격 증명의 계정($ACCOUNT)이 예상 계정($EXPECTED_ACCOUNT)과 다릅니다. EXPECTED_ACCOUNT로 바꾸거나 프로필을 확인하세요."
  exit 1
fi

if [ -z "${LAB_TOKEN_SECRET:-}" ]; then
  if [ -f "$HERE/.secret" ]; then
    LAB_TOKEN_SECRET="$(cat "$HERE/.secret")"
  else
    LAB_TOKEN_SECRET="$(python3 -c 'import secrets; print(secrets.token_hex(24))')"
    umask 077; printf '%s' "$LAB_TOKEN_SECRET" > "$HERE/.secret"
    echo "새 비밀값을 $HERE/.secret 에 저장했습니다 (저장소에 커밋하지 마세요)"
  fi
fi

rm -rf "$HERE/build"
mkdir -p "$HERE/build"
cp "$HERE/lambda/handler.py" "$HERE/build/"
cp -R "$HERE/../kit/labapi" "$HERE/build/labapi"
find "$HERE/build" -name '__pycache__' -prune -exec rm -rf {} +

PARAMS=("TokenSecret=$LAB_TOKEN_SECRET")
[ -n "${BUDGET_EMAIL:-}" ] && PARAMS+=("BudgetEmail=$BUDGET_EMAIL")

cd "$HERE"
sam deploy \
  --template-file template.yaml \
  --stack-name "$STACK" \
  --region "$REGION" \
  --resolve-s3 \
  --capabilities CAPABILITY_IAM \
  --no-fail-on-empty-changeset \
  --parameter-overrides "${PARAMS[@]}"

BASE="$(aws cloudformation describe-stacks --stack-name "$STACK" --region "$REGION" \
  --query "Stacks[0].Outputs[?OutputKey=='ApiBase'].OutputValue" --output text)"
BASE="${BASE%/}"
echo
echo "LAB_API_BASE=$BASE"
printf 'LAB_API_BASE=%s\n' "$BASE" > "$HERE/../lab-api.env"
echo "ch4/lab-api.env 에 기록했습니다. 커밋하면 참가자 setup.sh가 이 주소를 씁니다."
echo "확인: python3 ch4/infra/smoke.py --base $BASE --secret-file ch4/infra/.secret"
