# 팀 작업 가이드

이 저장소는 Chapter 4 슈퍼랩용 프로젝트입니다. 매주 하는 반복 업무를 스킬로 만들고, 사내 API와 연결하고, 프롬프트를 점검해 팀에 넘깁니다.

## 프로젝트 구조

- `.claude/skills/` 스킬: 회의록·주간보고·스탠드업(lab1), 휴가 신청·배포 보고 뼈대(lab2), 프롬프트 코치(lab3)
- `.claude/agents/workshop-coach.md` 실습 코치 (읽기 전용, `bin/lab coach`로 실행)
- `docs/worksheets/` 랩별 워크시트, `docs/coach/` 코치 진행표, `docs/templates/new-skill/` 새 스킬 틀
- `tools/` 사내 API 도구(`hr_fetch.py`, `lab_mcp.py`, `lab_server.py`), 랩 검사(`check_lab*.py`), 사용량 기록(`usage_log.sh`)
- `samples/` 회의 녹취, 주간 메모, 점검용 프롬프트
- `src/`, `test.js` 예제 앱

## 명령

- 전체 테스트: `npm test`
- 랩 검사: `python3 tools/check_lab1.py` (2, 3도 같은 형식)

## 응답 방식

- 답변은 한국어로 작성합니다.

## 코드 스타일

- 문자열은 큰따옴표를 사용합니다.
- 들여쓰기와 세미콜론은 `.claude/rules/code-style.md`를 따릅니다.

## 보안

- `.env` 파일은 절대 읽거나 수정하지 마세요.
- 사내 API 토큰(`~/.config/superlab/`)을 읽거나 출력하지 마세요. 도구가 직접 읽습니다.
