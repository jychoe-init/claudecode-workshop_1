# 우리 팀 Claude Code 스타터 킷

Chapter 4 슈퍼랩에서 만든 킷입니다. 이 저장소를 받으면 아래 스킬과 설정이 함께 적용됩니다.

## 이 킷으로 할 수 있는 것

1. ____ <!-- lab1: 어떤 반복 문서를, 어떻게 부르면 나오는지 -->
2. ____ <!-- lab2: 무엇을 자동화했고, 쓰기는 어떻게 확인받는지 -->
3. ____ <!-- lab3: 어떤 프롬프트를 어느 모델에 맞게 점검했고, 이 킷을 어떻게 넘기는지 -->

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
