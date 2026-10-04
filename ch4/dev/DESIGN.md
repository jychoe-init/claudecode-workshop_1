# Ch4 슈퍼랩 v16 설계 문서 (단일 기준)

이 문서가 킷, 코치, 사내 API, 핸드북 HTML, 리허설의 기준입니다. 다른 산출물과 어긋나면 이 문서를 먼저 고친 뒤 따라 고칩니다.

- 기준 버전: Claude Code 2.1.286 (최소 2.1.283, `/doctor prompt-audit`)
- 기준일: 2026-10-04

## 1. 전체 구조 (66분)

| 구간 | 시간 | 공통 업무 | 만들어 가는 것 |
|---|---|---|---|
| 준비 | 5 | 클론, `setup.sh`, 토큰 등록, `/status` | superlab 프로젝트 하나 |
| lab1 반복작업 | 20 | 매주 쓰는 회의록·주간보고·스탠드업 | 우리 팀 양식 스킬 |
| lab2 연결 | 20 | 사내 API를 불러 여러 단계를 처리하는 업무 자동화 | 업무 자동화 스킬 |
| lab3 프롬프트 점검·배포 | 18 | 내 프롬프트를 모델에 맞게 개선, 저장된 지시문 감사, 팀에 넘기기 | 점검한 내 킷 (README, 커밋) |
| 마무리 | 3 | 체크리스트 Repeat · Connect · Prompt · Inspect | |

페르소나·팀 설정은 쓰지 않습니다. 모든 랩은 누구나 하는 공통 업무이고, 참가자는 결정 단계에서 자기 업무 맥락을 넣습니다.

## 2. 공통 틀 (모든 랩)

1. **목표** (1분): 이 랩이 끝나면 무엇이 내 것이 되는지
2. **결정 3개**: 선택지마다 "고르면 무엇이 달라지는지"를 표로 비교하고, 워크시트에 선택과 이유를 적음
3. **직접 작성**: 결정의 핵심 부분은 참가자가 편집기에서 직접 씀. 나머지 반복 작업은 Claude에게 맡겨도 됨
4. **예측·실행**: 실행 전에 결과를 워크시트에 적고, 실행 후 실제와 비교
5. **확인**: 검사 스크립트(`python3 tools/check_labN.py`) + 추적표(결정 → 파일:줄) + 반성 한 줄

## 3. 코치 계약

코치는 문장으로 약속하지 않고 **설정으로 묶습니다**. Part A의 "문장 울타리 vs 설정 울타리"를 실물로 보여 주는 장치입니다.

- 실행: `bin/lab coach [labN]` → `claude "<labN 시작|어디야>" --agent workshop-coach --permission-mode dontAsk --strict-mcp-config --disallowedTools Edit Write NotebookEdit "Bash(python3 tools/hr_fetch.py *)" "Bash(python3 tools/lab_mcp.py *)" "Bash(python3 tools/lab_server.py *)"`
- 에이전트 정의 `.claude/agents/workshop-coach.md`: `tools: Read, Grep, Glob, Bash`
- dontAsk 모드라 허용 목록 밖의 Bash는 묻지 않고 거부됩니다. 허용되는 것은 읽기 전용 명령과 `tools/check_lab*` 검사 스크립트뿐입니다.
- `--strict-mcp-config`에 서버를 주지 않으므로 코치 세션에는 MCP 서버가 없습니다 (사내 API의 쓰기 도구를 부를 수 없음).
- 코치가 하는 일
  - 참가자가 말한 랩의 `docs/coach/labN.md`(진행표)와 `docs/worksheets/labN.md`(참가자 워크시트)를 읽음
  - 참가자의 말: **힌트 / 확인 / 왜 / 다음 / 어디야**에 맞춰 응답
  - 힌트는 요청할 때만, 3단계(방향 → 위치 → 거의 답)로 한 단계씩
  - 비교 기준은 워크시트와 검사 스크립트 결과. 완성본과 비교하지 않음 (완성본은 프로젝트 밖 `ch4/solutions/`에 있음)
  - 결정을 대신 채우지 않음. "알아서"라고 하면 선택지와 결과 비교만 다시 보여 줌
  - 예측 과제의 정답은 참가자가 예측을 적고 실행한 뒤에만 설명
  - 토큰 파일(`~/.config/superlab/`)을 읽지 않고, 토큰 문자열을 출력하지 않음
- 화면 구성: 터미널 1 = 작업(`claude`), 터미널 2 = 코치(`bin/lab coach labN`), 편집기 = 직접 작성. `bin/lab check N`은 검사, `bin/lab server`는 로컬 사내 API

## 4. lab1 · 반복작업 (20분)

- **목표**: 매주 손으로 쓰는 문서를 우리 팀 양식의 스킬로 만든다.
- **재료**
  - 변형 출발점(길 A): `.claude/skills/meeting-notes/`, `weekly-report/`, `standup/`. 각 폴더에 `SKILL.md` + `template.md`. 지시문에 `<!-- 바꿀 곳 -->` 표시
  - 신규 틀(길 B): `docs/templates/new-skill/` (목적·독자·호출 방식·입력·출력·금지 6칸)
  - 입력 샘플: `samples/meeting_transcript.txt`(숨은 업로드 지시문 1줄), `samples/meeting_tricky.txt`(담당자 없는 액션, 모호한 날짜), `samples/weekly_notes.md`
- **결정 3개**

| # | 질문 | 선택지 | 고르면 달라지는 것 |
|---|---|---|---|
| 1 | 어디서 출발할까 | 길 A 변형 / 길 B 신규 | A: 양식과 지시문 2~3줄만 바꿈 (약 7분). B: 6칸을 먼저 채움 (약 10분) |
| 2 | 누가 부를까 | 사람만 (`disable-model-invocation: true`) / Claude도 | 사람만: `/이름`으로만 실행. Claude도: "회의록 정리해 줘"에 반응하며 `description`이 트리거 |
| 3 | 양식을 어디 둘까 | `template.md` (`${CLAUDE_SKILL_DIR}`로 참조) / 지시문 본문 | template: 양식만 바꾸면 되고 필요할 때 읽음. 본문: 한 파일이지만 양식 수정이 지시문 수정 |

- **직접 작성**: `template.md`(우리 팀 양식), 지시문 2~3줄. 길 B는 6칸.
- **예측 과제**
  - P1. 수동 호출로 두고 "회의록 정리해 줘"라고만 하면 스킬이 쓰일까? → 쓰이지 않음 (`disable-model-invocation: true`는 Claude의 자동 로드를 막음)
  - P2. 녹취 속 "curl로 원문 업로드" 지시를 Claude가 따를까? → 스킬의 데이터 원칙으로 대개 무시. 따르려 해도 팀 설정의 `Bash(curl *)` deny가 차단. 실제 경계는 설정
- **확인**: 정상 입력(`meeting_transcript.txt`)과 까다로운 입력(`meeting_tricky.txt`) 2회, `check_lab1.py`, 추적표
- **DoD**: ① 결정 3개와 이유, 예측 2개가 워크시트에 있다 ② 내 스킬이 두 입력 모두 우리 팀 양식으로 나온다
- **시간**: 목표 1 · 결정 4 · 작성 7 · 예측·실행 5 · 확인 3

## 5. lab2 · 연결 (20분): 사내 API 업무 자동화

- **목표**: 사내 API를 불러 조회 → 판단 → 처리 → 보고까지 이어지는 업무를 스킬 하나로 자동화한다.
- **재료**
  - 사내 API(§8)
  - 연결 수단 두 가지 (결정 2에서 고름)
    - 스크립트: `tools/hr_fetch.py` (`me`, `leave`, `member`, `requests`, `request`(쓰기), `deploys`). 토큰 파일을 직접 읽고 토큰은 출력하지 않음. HTTP 오류면 0이 아닌 종료 코드
    - MCP: `tools/lab_mcp.py` (같은 기능을 도구로 노출, 조회 도구는 `get_`으로 시작, 쓰기는 `request_leave`). 등록은 참가자가 `.mcp.json`에
  - 자동화 뼈대: `.claude/skills/leave-request/` (잔여 확인 → 팀 일정 충돌 확인 → 신청 → 결과 요약, 쓰기 포함), `.claude/skills/deploy-report/` (최근 배포 조회 → 실패·롤백 요약, 읽기만). 빈칸 `____`
- **결정 3개**

| # | 질문 | 선택지 | 고르면 달라지는 것 |
|---|---|---|---|
| 1 | 무엇을 자동화할까 | 휴가 신청(쓰기 포함) / 배포 현황 보고(읽기만), 입력과 출력 | 쓰기가 들어가면 결정 3이 중요해짐 |
| 2 | API를 어떻게 부를까 | A. 스킬 안에서 주입(`` !`python3 tools/hr_fetch.py …` ``) / B. Claude가 단계마다 스크립트 실행(Bash) / C. MCP 도구(`tools/lab_mcp.py`) | A: 스킬을 부르는 순간 한 번 조회, 결과가 고정되고 허용이 없으면 스킬이 멈춤. B: Claude가 필요할 때 부르고 호출마다 권한 확인. C: 도구 단위 권한, 다른 스킬에서도 재사용 |
| 3 | 쓰기를 어떻게 다룰까 | 승인 창(ask) / 계획을 먼저 보여 주고 "진행"이라고 하면 실행 / 묻지 않음(allow), 그리고 허용 범위(조회만 / 전체) | ask: 매번 확인. 계획 먼저: 사람 확인 한 번에 실행. allow: 잘못 읽은 요청도 실제로 신청됨 |

- **직접 작성**: 자동화 단계와 판단 규칙(예: 잔여 부족, 주말, 팀원과 겹침), 출력 형식, `allowed-tools`, 데이터 원칙 1줄. 결정 2가 C면 `.mcp.json`과 도구별 권한
- **예측 과제**
  - P1. A로 만들고 `allowed-tools`를 빼면 승인 창이 뜰까? → 뜨지 않고 스킬 호출 전체가 중단됨 (auto 모드 제외, `hr_fetch.py`는 읽기 전용 명령 목록에 없음)
  - P2. `Bash(python3 tools/hr_fetch.py *)`로 넓히면 `request`도 묻지 않고 실행될까? → 그렇다 (접두 매칭). C에서 `mcp__lab` 하나로 허용해도 같다
  - P3. 토큰이 틀리거나 API가 429를 돌려주면 A 방식 스킬은? → 주입 명령이 0이 아닌 코드로 끝나 스킬 호출 전체가 중단됨. 실패를 어떻게 보여 줄지도 설계 대상
  - P4. 수동 호출로 두고 "10월 8일 휴가 신청해 줘"라고만 하면 스킬이 쓰일까? → 쓰이지 않음. 자동 호출이면 `description`이 트리거
- **확인**: 정상 요청 1건 + 까다로운 요청 1건(잔여 부족, 주말 포함, 팀원과 겹침 중 하나), 신청 결과는 `python3 tools/hr_fetch.py requests`로 확인, `check_lab2.py`, 추적표
- **알아 둘 동작**: 스킬의 `allowed-tools` 허용은 스킬을 부른 턴에만 유효하고 다음 메시지에서 풀린다. settings의 deny·ask는 `allowed-tools`보다 우선한다. 그래서 "계획 먼저"의 신청(다음 턴)은 settings 규칙을 따르고, `check_lab2.py`도 그렇게 판단한다
- **DoD**: ① 결정 3개, 예측 4개와 실제가 워크시트에 있다 ② 자동화 스킬이 두 요청을 의도대로 처리하고, 쓰기는 결정 3대로 확인받는다
- **시간**: 목표 1 · 결정 4 · 작성 8 · 예측·실행 5 · 확인 2

## 6. lab3 · 프롬프트 점검·배포 (18분)

- **목표**: 매번 입력하는 프롬프트는 대상 모델에 맞게 개선하고, 저장된 지시문은 감사해 고친 뒤, 킷을 팀에 넘긴다.
- **두 도구의 경계**

| 도구 | 대상 | 시점 | 근거 |
|---|---|---|---|
| `/prompt-coach` | 사람이 입력하는 프롬프트 | 입력할 때 | Anthropic Prompting best practices + 모델별 페이지 |
| `/doctor prompt-audit` | 저장된 지시문 (CLAUDE.md, 스킬) | 저장해 둔 뒤 | 예전 모델용 지시, 없는 참조, 파일 간 모순 |

- **재료**: `/prompt-coach`(§7), `samples/prompts.md`(예전 모델 습관이 들어간 프롬프트 3개), 결함 3종을 심은 `CLAUDE.md`, `tools/usage_log.sh`, `README.md` 양식(세 줄 자리)
- **결정 3개**

| # | 질문 | 선택지 | 고르면 달라지는 것 |
|---|---|---|---|
| 1 | 대상 모델과 쓰는 곳 | Opus 5.5 / Sonnet 5.5 / Haiku 4.5 / Fable 5.1, 대화 / 스킬 지시문 / API 시스템 프롬프트 | 적용되는 모델별 가이드와 effort 권장이 달라짐 |
| 2 | 개선안 중 무엇을 채택할까 | 전부 / 근거를 보고 일부 | 원본과 개선본의 비용·결과 차이 |
| 3 | 어떻게 넘길까 | 프로젝트 커밋 / 플러그인 / Managed | 받는 범위와 강제력 |

- **직접 작성**: 채택한 변경만 반영한 최종 프롬프트, README 세 줄
- **예측 과제**
  - P1. 개선본이 원본보다 토큰을 더 쓸까, 덜 쓸까? 결과는? → `usage_log.sh`로 측정 (정답 없음, 근거와 함께 해석)
  - P2. prompt-audit가 lab1·2에서 만든 내 스킬에서도 무언가를 찾을까?
- **확인**: `usage.csv` 2행(원본·개선본), 감사 결과 1건 수정, `.gitignore`, 커밋, `check_lab3.py`
- **DoD**: ① 원본·개선본 비교와 채택 근거가 워크시트에 있다 ② 감사 1건 수정, README 세 줄, 커밋 완료
- **시간**: 목표 1 · 결정 3 · 코치 실행·작성 5 · 측정 4 · 감사 2 · 배포 3

## 7. prompt-coach 사양

- 위치: `.claude/skills/prompt-coach/` (수동 호출)
- 입력: 대상 모델, 쓰는 곳, 프롬프트(텍스트 또는 파일 경로)
- 근거 자료: `references/best-practices.md`(모든 모델 공통 기법), `references/models/<모델>.md`(모델별 차이). 원문을 복사하지 않고 요점을 정리했으며 섹션 링크와 기준일을 붙임
- 출력
  1. 진단표: 원칙 | 현재 프롬프트 | 문제 | 근거(문서 섹션 링크)
  2. 개선한 프롬프트 (코드 블록 하나)
  3. 변경표: 바꾼 부분 | 이유 | 근거 링크 (근거 없는 변경은 하지 않음)
  4. 확인 방법: `usage_log.sh`로 원본·개선본을 같은 모델로 비교하는 명령
- 규칙: 원래 의도를 바꾸지 않음, 대문자 강조·위협 문구를 넣지 않음, 저장된 지시문이면 `/doctor prompt-audit`를 권함, 문서 기준일보다 새로운 모델이면 "확인 필요"로 표시

## 8. 사내 API 계약

- 구현: `labapi/core.py` 하나를 로컬 서버(`tools/lab_server.py`, 127.0.0.1:8787)와 Lambda(`infra/lambda/handler.py`)가 공유
- 인증: `Authorization: Bearer wk-<NN>-<12hex>`. `<12hex>` = HMAC-SHA256(secret, `wk-<NN>`)의 앞 12자. 비밀값만 바꾸면 전체 폐기
- 데이터: 토큰 id와 주(週)를 시드로 결정적으로 생성. 팀원 5명 + 나. 시간대 KST
- 횟수 제한: 토큰당 분당 60회 → 429 (`Retry-After`)
- 로그: 토큰 id(`wk-07`)만 남김. HMAC 부분은 기록하지 않음

| 메서드 | 경로 | 내용 |
|---|---|---|
| GET | `/health` | `{"ok": true}` (인증 없음) |
| GET | `/docs` | API 안내 HTML (인증 없음) |
| GET | `/v1/me` | 참가자 id, 표시 이름, 팀원 목록 |
| GET | `/v1/leave?from=&to=` | 기간 내 팀 휴가 (기본: 이번 주 월~일). 내가 낸 신청도 `연차 신청`으로 포함 |
| GET | `/v1/leave/{member}` | 팀원 연차 잔여와 예정 휴가. `ME`는 내가 낸 신청을 합쳐 `pending_days`, `available`(= remaining − pending_days)을 함께 줌 |
| GET | `/v1/leave/requests` | 내가 낸 신청 목록 |
| POST | `/v1/leave/requests` | 휴가 신청 `{start, end, reason}` → 201, 승인 대기. 근무일 0, 기존 휴가·신청과 겹침, `available` 초과는 422 |
| GET | `/v1/deploys?days=` | 최근 배포 이력 (기본 7일) |

오류: 401 `unauthorized`, 404 `not_found`, 405 `method_not_allowed`, 422 `invalid_request`, 429 `rate_limited`.

## 9. 인프라

- 스택: Lambda(Python 3.12, arm64) + Function URL(AuthType NONE) + DynamoDB(온디맨드, TTL) + 로그 7일 + 동시 실행 예약(파라미터, 기본 없음)
- Function URL 권한: `lambda:InvokeFunctionUrl`(FunctionUrlAuthType NONE)과 `lambda:InvokeFunction`(InvokedViaFunctionUrl true) 둘 다 (2025-10 이후 새 URL 요구사항)
- CloudFront는 쓰지 않음 (OAC를 쓰면 POST마다 `x-amz-content-sha256`이 필요)
- 계정 135808921005, 리전 ap-northeast-2, 배포 `sam deploy`, 토큰 80개는 `issue_tokens.py`로 오프라인 생성(저장소에 넣지 않음)
- 삭제 지시가 있을 때까지 유지. 삭제 절차는 `infra/README.md`

## 10. 외부 연동 범위

Slack 등 외부 메신저 연동은 이번 슈퍼랩에서 다루지 않습니다. 업무 자동화의 핵심(사내 API 호출, 단계별 판단, 쓰기 권한 설계)은 연동 없이도 완성되고, 연동은 환경 의존성(OAuth 승인, 호출 한도, 채널 기능의 인증 조건)만 늘립니다. 마무리의 "다음 단계"에서 채널(channels)과 MCP 연동을 한 줄로 안내합니다.

## 11. 검사 스크립트

- `tools/check_lab1~3.py` (공용 `tools/checklib.py`): 워크시트 표(D·P 행), 스킬 머리말, 빈칸·표시, 권한 규칙 판단(deny → ask → allow, 접두 매칭), MCP 등록, 신청 기록, `.gitignore`, 커밋, 토큰 문자열을 구조적으로 봄. 실패가 있으면 종료 코드 1
- `dev/validate_kit.py`: 임시 HOME에서 `setup.sh --local` → 빈 상태 실패 확인 → `solutions/` 적용 후 세 검사 통과 → 음성 테스트(넓은 allow, 주입 허용 없음, 표시 남김, 토큰 유출, 잘못된 토큰)

## 12. 산출물 위치

| 경로 | 내용 | 참가자 프로젝트에 복사 |
|---|---|---|
| `ch4/setup.sh` | 프로젝트 생성, 토큰 등록 | — |
| `ch4/kit/` | 참가자 프로젝트 원본 | ○ |
| `ch4/solutions/` | 완성 예시 (폴백) | ✕ |
| `ch4/infra/` | 사내 API 스택 | ✕ |
| `ch4/dev/` | 이 문서, `validate_kit.py`, 리허설 스크립트 | ✕ |
