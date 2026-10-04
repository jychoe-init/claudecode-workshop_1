# 완성 예시 (강사용 폴백)

참가자 프로젝트(`~/claude-lab/superlab`)에는 복사되지 않습니다. 코치도 이 폴더를 읽지 않습니다.
정답이 아니라 "이렇게도 만들 수 있다"는 한 가지 예입니다. 참가자가 시간 안에 막혔을 때만 필요한 부분을 건넵니다.

| 폴더 | 내용 | 복사할 곳 |
|---|---|---|
| `lab1/skills/meeting-notes/` | 길 A, 사람만, template 분리 | `.claude/skills/meeting-notes/` |
| `lab1/worksheets/lab1.md` | 채운 워크시트 | `docs/worksheets/lab1.md` |
| `lab2/skills/leave-request/` | B(Bash), 계획 먼저 + ask, 조회만 allowed-tools | `.claude/skills/leave-request/` |
| `lab2/skills/deploy-report/` | A(주입), 조회만 | `.claude/skills/deploy-report/` |
| `lab2/settings.json` | 기본 설정 + 신청 ask 규칙 | `.claude/settings.json` |
| `lab2/mcp-variant/` | C(MCP) 등록과 도구별 권한 | 프로젝트 루트 `.mcp.json` |
| `lab2/worksheets/lab2.md` | 채운 워크시트 | `docs/worksheets/lab2.md` |
| `lab3/files/` | 감사 결과를 반영한 `CLAUDE.md`, `.gitignore`, README 세 줄 | 프로젝트 루트 |
| `lab3/worksheets/lab3.md` | 채운 워크시트 (측정값은 예시) | `docs/worksheets/lab3.md` |

```bash
SOL=~/claude-lab/claudecode-workshop_1/ch4/solutions
cp -R $SOL/lab1/skills/meeting-notes ~/claude-lab/superlab/.claude/skills/
```

`ch4/dev/validate_kit.py`가 새 프로젝트에 이 예시를 적용해 세 검사가 모두 통과하는지 확인합니다.
