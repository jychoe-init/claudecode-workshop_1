# lab2 결정 2 = C (MCP) 예시

1. `.mcp.json`을 프로젝트 루트에 복사합니다.
2. `.claude/settings.json`의 permissions에 아래를 더합니다.

```json
{
  "allow": ["mcp__lab__get_*"],
  "ask": ["mcp__lab__request_leave"]
}
```

3. `claude`를 다시 열고 프로젝트 MCP 서버 `lab` 사용을 승인합니다. `/mcp`에서 연결 상태를 봅니다.
4. 스킬 지시문의 조회·신청 단계에 도구 이름을 씁니다.
   - 잔여: `mcp__lab__get_leave_balance` (member: `ME`)
   - 팀 휴가: `mcp__lab__get_leave` (from, to)
   - 신청: `mcp__lab__request_leave` (start, end, reason)

`mcp__lab`이나 `mcp__lab__*`를 allow에 넣으면 `request_leave`까지 묻지 않습니다 (P2).
