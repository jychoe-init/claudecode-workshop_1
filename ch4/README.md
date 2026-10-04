# Chapter 4 슈퍼랩 · Team Starter Kit

Part B 슈퍼랩(53분)에서 쓰는 킷입니다. 실습 순서와 설명은 워크샵 핸드북 Chapter 4를 따릅니다.

```bash
bash setup.sh            # ~/claude-lab/superlab 생성
cd ~/claude-lab/superlab
claude
```

## setup.sh가 만드는 것

| 항목 | 내용 |
|---|---|
| git 저장소 | 기본 브랜치 `main`, 오늘 날짜 커밋 2개 |
| `feature/greeting-i18n` | 개발 트랙용 변경 2개 (`main...feature/greeting-i18n` diff) |
| `.claude/settings.local.json` | `defaultMode: acceptEdits` · 개인 파일, 커밋하지 않음 |
| `.env` | 가짜 토큰 · 커밋하지 않음 |

## 킷 구성과 사용 블록

| 경로 | 블록 | 용도 |
|---|---|---|
| `presets/personal.json` `team.json` `regulated.json` | 1 울타리 ① | `claude --settings presets/<이름>.json`으로 같은 요청의 허용·승인·차단 비교 |
| `CLAUDE.md`, `.claude/rules/code-style.md` | 1 울타리 ② | `/doctor prompt-audit` 대상 |
| `.claude/skills/standup/` | 2 연결 ③ | Stop http 훅을 붙일 스킬 |
| `tools/slack_mock.py` | 2 연결 ③ | http 훅 수신기, `--forward`로 실제 Slack 전달 |
| `tools/hr_mcp.py` | 2 연결 ④ | 가짜 HR MCP 서버 (stdio), `HR_STRICT=1`로 서버 쪽 승인 강제 |
| `.claude/skills/prompt-coach/`, `samples/prompt-worksheet.md` | 3 반복작업 ⑤ | 요청문 진단 |
| `.github/pull_request_template.md` | 3 반복작업 ⑥ 개발 트랙 | `/pr-desc` 템플릿 |
| `samples/meeting_transcript.txt` `weekly_notes.md` `weekly_template.md` | 3 반복작업 ⑦ 업무 트랙 | 회의록·주간보고 입력 |
| `tools/usage_log.sh` | 4 점검·배포 ⑧ | `-p` 실행 비용·토큰을 `usage.csv`에 기록 |

## 실습 중 생기는 파일 (커밋 전에 .gitignore 대상)

`.claude/settings.local.json`, `.env`, `.slack_inbox.jsonl`, `.hr_requests.json`, `usage.csv`, `.usage/`

## 도구 단독 점검

```bash
# Slack mock: 다른 터미널에서 실행 후 아래로 확인
python3 tools/slack_mock.py
python3 -c 'import json,urllib.request as u; u.urlopen(u.Request("http://localhost:8787/", json.dumps({"hook_event_name":"Stop","last_assistant_message":"### 어제\n- 테스트"}).encode(), {"Content-Type":"application/json"}))'

# HR MCP: 초기화와 도구 목록 응답 확인
printf '%s\n' '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18"}}' \
              '{"jsonrpc":"2.0","id":2,"method":"tools/list"}' | python3 tools/hr_mcp.py
```
