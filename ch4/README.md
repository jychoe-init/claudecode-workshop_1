# Chapter 4 슈퍼랩

Part B 슈퍼랩(66분)에서 쓰는 자료입니다. 진행 순서와 설명은 워크샵 핸드북 Chapter 4를 따릅니다.

| 구간 | 시간 | 만드는 것 |
|---|---|---|
| 준비 | 5 | 실습 프로젝트, 토큰 등록 |
| lab1 반복작업 | 20 | 우리 팀 양식의 문서 스킬 |
| lab2 연결 | 20 | 사내 API를 부르는 업무 자동화 스킬 |
| lab3 프롬프트 점검·배포 | 18 | 모델에 맞게 고친 프롬프트, 감사한 지시문, 커밋한 킷 |
| 마무리 | 3 | 체크리스트 |

## 참가자

```bash
git clone https://github.com/jychoe-init/claudecode-workshop_1.git ~/claude-lab/claudecode-workshop_1
bash ~/claude-lab/claudecode-workshop_1/ch4/setup.sh     # 토큰을 물으면 강사에게 받은 값을 붙여 넣기
cd ~/claude-lab/superlab
```

화면은 셋으로 씁니다.

| 화면 | 명령 | 용도 |
|---|---|---|
| 터미널 1 | `claude` | 작업 |
| 터미널 2 | `bin/lab coach lab1` | 코치 (읽기 전용, 힌트·확인·왜·다음·어디야) |
| 편집기 | `docs/worksheets/lab1.md` | 결정, 예측, 직접 작성 |

토큰만 다시 등록: `bash ~/claude-lab/claudecode-workshop_1/ch4/setup.sh --token`
클라우드에 연결되지 않으면: `bash .../setup.sh --token --local` 후 터미널 하나 더 열어 `bin/lab server`

## 폴더

| 경로 | 내용 | 참가자 프로젝트에 복사 |
|---|---|---|
| `setup.sh` | 프로젝트 생성, 토큰 등록, 연결 확인 | — |
| `kit/` | 참가자 프로젝트 원본 | ○ |
| `lab-api.env` | 클라우드 사내 API 주소 (`infra/deploy.sh`가 채움) | — |
| `solutions/` | 완성 예시 (강사 폴백) | ✕ |
| `infra/` | 사내 API 스택 (Lambda, DynamoDB) | ✕ |
| `dev/` | 설계 문서, 킷 검증, 리허설 스크립트 | ✕ |

## 킷 구성

| 경로 | 랩 | 용도 |
|---|---|---|
| `.claude/skills/meeting-notes`, `weekly-report`, `standup` | lab1 | 변형 출발점 (`<!-- 바꿀 곳 -->` 표시) |
| `docs/templates/new-skill/` | lab1 | 새 스킬 틀 (6칸) |
| `samples/meeting_transcript.txt`, `meeting_tricky.txt`, `weekly_notes.md` | lab1 | 입력 샘플 (섞인 지시문 포함) |
| `.claude/skills/leave-request`, `deploy-report` | lab2 | 자동화 뼈대 (`____` 빈칸) |
| `tools/hr_fetch.py`, `tools/lab_mcp.py`, `tools/lab_server.py`, `labapi/` | lab2 | 사내 API 스크립트, MCP 서버, 로컬 서버 |
| `.claude/skills/prompt-coach/` | lab3 | 모델별 프롬프트 점검 (공식 문서 근거) |
| `samples/prompts.md`, `CLAUDE.md`(결함 3종), `tools/usage_log.sh` | lab3 | 점검·감사·측정 대상 |
| `.claude/agents/workshop-coach.md`, `bin/lab`, `docs/coach/`, `docs/worksheets/` | 전체 | 코치와 워크시트 |
| `tools/check_lab1.py` ~ `check_lab3.py` | 전체 | 구조 검사 |

## 강사

- 사내 API 배포·토큰·삭제: [`infra/README.md`](infra/README.md)
- 설계 기준: [`dev/DESIGN.md`](dev/DESIGN.md)
- 킷 검증 (로그인 불필요): `python3 ch4/dev/validate_kit.py`
- 리허설: [`dev/REHEARSAL.md`](dev/REHEARSAL.md)
