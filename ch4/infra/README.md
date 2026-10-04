# 사내 API 스택 (강사용)

lab2에서 참가자가 부르는 가짜 사내 API(휴가·배포 데이터)입니다. 코드(`ch4/kit/labapi/core.py`)는 참가자 로컬 서버와 같고, 횟수 제한과 신청 저장만 DynamoDB를 씁니다.

| 리소스 | 설정 |
|---|---|
| Lambda | Python 3.12, arm64, 256MB, 10초 |
| Function URL | AuthType NONE. 인증은 코드에서 HMAC 토큰으로 |
| 권한 | `lambda:InvokeFunctionUrl`(FunctionUrlAuthType NONE) + `lambda:InvokeFunction`(InvokedViaFunctionUrl) |
| DynamoDB | 온디맨드, TTL(`expires_at`). 횟수 카운터 3분, 신청 14일 보관 |
| 로그 | 7일 보관, 토큰 id만 기록 |
| 예산 알림 | `BUDGET_EMAIL`을 주면 월 20달러의 80%에서 메일 |

CloudFront는 쓰지 않습니다. OAC로 Function URL을 보호하면 POST마다 클라이언트가 본문의 SHA256을 `x-amz-content-sha256` 헤더로 보내야 해서, 참가자 스크립트가 복잡해집니다.

## 배포

필요: AWS CLI, SAM CLI, 계정 135808921005 자격 증명

```bash
BUDGET_EMAIL=you@example.com bash ch4/infra/deploy.sh
```

- 비밀값이 없으면 새로 만들어 `ch4/infra/.secret`에 저장합니다 (커밋하지 않음, `.gitignore`에 있음).
- 끝나면 주소를 `ch4/lab-api.env`에 씁니다. 이 파일을 커밋해야 참가자 `setup.sh`가 클라우드 주소를 씁니다.
- 동시 실행을 묶어 두려면 `sam deploy`에 `ReservedConcurrency=20`을 더하세요. 새 계정은 전체 한도가 10이라 기본값은 0(묶지 않음)입니다.

## 확인

```bash
python3 ch4/infra/smoke.py --base "$(grep LAB_API_BASE ch4/lab-api.env | cut -d= -f2)" --secret-file ch4/infra/.secret
python3 ch4/infra/smoke.py --base ... --secret-file ch4/infra/.secret --rate-test   # 429까지 확인 (호출 60회 이상)
```

smoke는 좌석 99번 토큰을 써서 참가자 데이터와 섞이지 않습니다.

## 토큰 발급

```bash
python3 ch4/infra/issue_tokens.py --count 80 --out ~/superlab-tokens.csv
```

- 형식 `wk-<좌석>-<12자리>`. 저장소 밖에 두고, 참가자에게 각자 한 줄씩 전달합니다.
- 전부 폐기하려면 비밀값을 바꿔 다시 배포합니다 (`LAB_TOKEN_SECRET=... bash ch4/infra/deploy.sh`).

## 삭제

```bash
aws cloudformation delete-stack --stack-name claudecode-ch4-labapi --region ap-northeast-2
aws cloudformation wait stack-delete-complete --stack-name claudecode-ch4-labapi --region ap-northeast-2
```

SAM이 만든 패키지 버킷(`aws-sam-cli-managed-default`)은 다른 SAM 배포와 공유되므로 따로 지우지 않습니다. 삭제 후에는 `ch4/lab-api.env`를 비워 참가자가 로컬 서버로 돌아가게 합니다.

## 문제가 생기면

| 증상 | 확인 |
|---|---|
| 모든 요청이 403 | Function URL 권한 두 개가 붙었는지: `aws lambda get-policy --function-name <함수>` |
| 401 | 참가자 토큰과 배포 비밀값이 같은 값으로 만들어졌는지 |
| 429가 자주 남 | `RateLimitPerMinute` 파라미터를 올려 다시 배포 |
| 사내망에서 연결 안 됨 | `*.lambda-url.ap-northeast-2.on.aws` 접근 허용 여부. 안 되면 참가자를 로컬 서버(`bin/lab server`)로 전환 |
