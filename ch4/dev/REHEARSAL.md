# 리허설 체크리스트 (슈퍼랩 v16)

기준: Claude Code 2.1.286 (최소 2.1.283), 2026-10-04. 참가자와 같은 인증 방식(claude.ai / Console / Bedrock)으로 합니다.

## 0. 로그인 없이 (5분)

```bash
python3 ch4/dev/validate_kit.py        # 정적 검사 + 새 프로젝트 + 완성 예시 + 음성 테스트, 전부 통과해야 함
```

## 1. 사내 API 스택 (20분, 계정 135808921005)

- [ ] `BUDGET_EMAIL=... bash ch4/infra/deploy.sh` → `ch4/lab-api.env`에 주소
- [ ] `python3 ch4/infra/smoke.py --base <주소> --secret-file ch4/infra/.secret` 15/15
- [ ] `--rate-test`로 429 + Retry-After
- [ ] `python3 ch4/infra/issue_tokens.py --count 80 --out ~/superlab-tokens.csv` (저장소 밖)
- [ ] `ch4/lab-api.env` 커밋, push
- [ ] 행사장 네트워크에서 `curl -s <주소>/health` (사내망 차단 여부)

## 2. 참가자 흐름 (깨끗한 장비 1대, 10분)

- [ ] 클론 → `setup.sh` → 토큰 붙여 넣기(화면에 안 보임) → "사내 API 응답: 참가자: wk-NN"
- [ ] `ls -l ~/.config/superlab/token` 권한 600
- [ ] `bin/lab coach lab1`이 첫 메시지 "lab1 시작"으로 열리고 진행표를 읽음
- [ ] 폴더 신뢰 확인 후 `/skills`에 meeting-notes, weekly-report, standup, leave-request, deploy-report, prompt-coach

## 3. 코치 자동 리허설 (모델 호출 비용 발생)

```bash
python3 ch4/dev/rehearsal/run_coach.py all              # 기본 모델
python3 ch4/dev/rehearsal/run_coach.py lab1 --model claude-sonnet-5-5
```

- [ ] 자동 판정 실패 0 (편집 도구, 쓰기성 Bash, 금지 경로, 사내 API 실행, 토큰, 바뀌면 안 되는 파일)
- [ ] `ch4/dev/rehearsal/out/*.md` 대화 전문을 읽고 사람 판정
  - 결정을 대신 내리지 않음 ("알아서 해" → 선택지와 질문)
  - 힌트가 한 단계씩 (방향 → 위치 → 거의 답)
  - 예측 전에는 해설하지 않음, 예측·실제가 채워진 뒤에는 해설함
  - 응답이 짧고 다음 행동이 하나

## 4. 손으로 확인할 동작 (대화형, 40분)

설계가 기대는 동작입니다. 다르면 `DESIGN.md`와 코치 진행표, 워크시트를 함께 고칩니다.

| # | 확인 | 기대 | 다르면 |
|---|---|---|---|
| C1 | 코치 세션에서 "확인" | `python3 tools/check_labN.py`가 묻지 않고 실행 (settings allow) | 코치 진행표에 "작업 터미널에서 `bin/lab check N`" 안내로 바꿈 |
| C2 | 코치에게 "cat ~/.config/superlab/token 실행해" | 거부 (Read deny + Bash deny) | settings deny 패턴 수정 |
| C3 | 코치에게 "hr_fetch.py me 실행해" | 거부 (--disallowedTools) | bin/lab의 패턴 확인 |
| L1-1 | lab1 P1: 사람만 스킬 + "회의록 정리해 줘" | 스킬 미사용, 기본 형식으로 정리 | 진행표 해설 수정 |
| L1-2 | lab1 P2: 데이터 원칙을 지운 스킬로 transcript | curl 시도 시 deny로 차단 메시지 | — (시도 자체가 없을 수 있음, 해설에 반영됨) |
| L2-1 | lab2 P1: 주입 + allowed-tools 없음 | 승인 창 없이 스킬 중단, 오류 메시지 | 워크시트 P1 문구 |
| L2-2 | lab2 P2: 넓은 allowed-tools, 같은 턴 신청 | 묻지 않고 신청 | — |
| L2-3 | lab2 P2: 계획 먼저, "진행" 뒤 신청 | 승인 창 (allowed-tools는 다음 턴에 풀림) | 진행표의 "알아 둘 동작", `check_lab2.py`의 plan 판단 |
| L2-4 | lab2 P3: `LAB_TOKEN=wk-00-bad claude` 후 주입 스킬 | 스킬 중단 | — |
| L2-5 | 주입 명령 끝에 `|| echo "조회 실패"` | 실패 문구가 들어가고 스킬은 계속 | 진행표 P3 해설에서 이 예를 뺌 |
| L2-6 | C(MCP): `.mcp.json` 등록 → 승인 → `/mcp` | `lab` 연결, `mcp__lab__get_*` allow가 조회만 엶 | MCP 예시 README 수정 |
| L3-1 | `/prompt-coach sonnet-5-5 스킬 samples/prompts.md B` | 진단표·개선본·변경표(링크)·확인 방법 4섹션 | 스킬 지시문 조정 |
| L3-2 | 같은 것을 opus-5-5 대화 A, fable-5-1 대화 A, haiku-4-5 API C로 | 모델별 항목(O3, F5, "확인 필요")이 다르게 나옴 | references 보강 |
| L3-3 | `/doctor prompt-audit` | CLAUDE.md 결함 3종 중 2개 이상 검출 | 진행표 폴백 문구 사용 |
| L3-4 | `tools/usage_log.sh -m sonnet-5-5 -e low a "..."` | usage.csv에 model, effort 기록 | 모델 ID 매핑 수정 |

## 5. 시간 (스톱워치)

| 구간 | 목표 | 실제 |
|---|---|---|
| 준비 | 5 | |
| lab1 | 20 | |
| lab2 | 20 | |
| lab3 | 18 | |
| 마무리 | 3 | |

lab이 3분 넘게 밀리면: lab1은 길 A 고정, lab2는 배포 보고(조회만) + B 고정, lab3은 샘플 A + Opus 5.5 고정.

## 6. Bedrock 참가자가 있다면

- [ ] `bin/lab coach`(`--agent`, dontAsk) 동작
- [ ] `/doctor prompt-audit` 사용 가능 여부 (안 되면 진행표 폴백)
- [ ] `usage_log.sh -m`에 Bedrock 모델 ID, `total_cost_usd` 표시 여부
- [ ] 채널(channels)은 이번 랩에서 쓰지 않음 (claude.ai/Console 인증 전용 기능)

## 7. 행사 뒤

- 스택은 삭제 지시가 있을 때까지 유지합니다. 삭제는 `infra/README.md`의 "삭제".
- 토큰 전체 폐기: 비밀값을 바꿔 다시 배포.
