# 우리 팀 Claude Code 스타터 킷

Chapter 4 슈퍼랩에서 만든 킷입니다. 이 저장소를 받으면 아래 스킬과 설정이 함께 적용됩니다.

## 이 킷으로 할 수 있는 것

1. `/meeting-notes <녹취 파일>`: 회의 녹취를 플랫폼팀 회의록 양식(결정·할 일·확인 필요)으로 정리합니다. 사람만 부릅니다.
2. `/leave-request <날짜> <사유>`: 잔여 연차와 팀 일정을 확인해 계획을 보여 주고, "진행"과 승인 창을 거쳐 휴가를 신청합니다.
3. 배포 보고 프롬프트를 Sonnet 5.5 기준으로 점검했습니다. 이 킷은 프로젝트 커밋으로 넘기며, 개인 설정은 `.claude/settings.local.json`에 둡니다.

## 시작하기

```bash
claude                    # 프로젝트 폴더에서 실행, 폴더 신뢰 확인 승인
python3 tools/hr_fetch.py me   # 사내 API 연결 확인 (토큰은 ~/.config/superlab/token)
```

## 구성

| 경로 | 내용 |
|---|---|
| `.claude/settings.json` | 팀 권한: git 조회·검사 허용, `git push` 확인, `.env`·토큰 폴더·`curl`·`wget`·`rm -rf` 차단 |
| `.claude/skills/` | 스킬 |
| `.claude/agents/workshop-coach.md` | 실습 코치 (`bin/lab coach`) |
| `tools/` | 사내 API 도구, 랩 검사, 사용량 기록 |
| `docs/` | 워크시트, 코치 진행표, 새 스킬 틀 |
