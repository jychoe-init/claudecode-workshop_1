#!/usr/bin/env python3
"""사내 API를 도구로 노출하는 MCP 서버 (stdio, lab2 결정 2의 C 경로).

등록 예 (.mcp.json, 프로젝트 루트)
  {
    "mcpServers": {
      "lab": {
        "command": "python3",
        "args": ["${CLAUDE_PROJECT_DIR:-.}/tools/lab_mcp.py"]
      }
    }
  }

도구
  get_me, get_leave, get_leave_balance, get_leave_requests, get_deploys   조회 (이름이 get_으로 시작)
  request_leave                                                           휴가 신청 (쓰기)

권한 예: allow "mcp__lab__get_*", ask "mcp__lab__request_leave"
토큰은 ~/.config/superlab/token 에서 읽고, 도구 결과에 쓰지 않습니다. 표준 라이브러리만 사용합니다.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from labapi.client import ApiError, call  # noqa: E402

DEFAULT_PROTOCOL = "2025-06-18"
DATE = {"type": "string", "description": "YYYY-MM-DD"}

TOOLS = [
    {"name": "get_me", "description": "내 참가자 id와 팀원 목록을 조회합니다.",
     "inputSchema": {"type": "object", "properties": {}}, "annotations": {"readOnlyHint": True}},
    {"name": "get_leave", "description": "기간 내 팀 휴가를 조회합니다. 생략하면 이번 주(월~일)입니다.",
     "inputSchema": {"type": "object", "properties": {"from": DATE, "to": DATE}}, "annotations": {"readOnlyHint": True}},
    {"name": "get_leave_balance", "description": "팀원의 연차 총일수·사용·잔여·승인 대기와 예정 휴가를 조회합니다. 나는 ME.",
     "inputSchema": {"type": "object", "properties": {"member": {"type": "string", "description": "ME 또는 M01~M05"}},
                     "required": ["member"]}, "annotations": {"readOnlyHint": True}},
    {"name": "get_leave_requests", "description": "내가 낸 휴가 신청 목록과 상태를 조회합니다.",
     "inputSchema": {"type": "object", "properties": {}}, "annotations": {"readOnlyHint": True}},
    {"name": "get_deploys", "description": "최근 배포 이력을 조회합니다.",
     "inputSchema": {"type": "object", "properties": {"days": {"type": "integer", "minimum": 1, "maximum": 30}}},
     "annotations": {"readOnlyHint": True}},
    {"name": "request_leave", "description": "휴가를 신청합니다(쓰기). 근무일만큼 승인 대기로 등록됩니다.",
     "inputSchema": {"type": "object", "properties": {"start": DATE, "end": DATE, "reason": {"type": "string"}},
                     "required": ["start"]}, "annotations": {"readOnlyHint": False, "destructiveHint": False}},
]


def run_tool(name, args):
    if name == "get_me":
        return call("GET", "/v1/me")
    if name == "get_leave":
        q = "&".join("%s=%s" % (k, args[k]) for k in ("from", "to") if args.get(k))
        return call("GET", "/v1/leave" + ("?" + q if q else ""))
    if name == "get_leave_balance":
        return call("GET", "/v1/leave/" + str(args.get("member", "ME")))
    if name == "get_leave_requests":
        return call("GET", "/v1/leave/requests")
    if name == "get_deploys":
        return call("GET", "/v1/deploys?days=%d" % int(args.get("days", 7)))
    if name == "request_leave":
        start = args.get("start")
        return call("POST", "/v1/leave/requests",
                    {"start": start, "end": args.get("end") or start, "reason": args.get("reason", "")})
    raise KeyError(name)


def reply(msg_id, result=None, error=None):
    msg = {"jsonrpc": "2.0", "id": msg_id}
    msg["error" if error else "result"] = error or result
    sys.stdout.write(json.dumps(msg, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def handle(msg):
    method, msg_id = msg.get("method"), msg.get("id")
    if method == "initialize":
        proto = (msg.get("params") or {}).get("protocolVersion") or DEFAULT_PROTOCOL
        return reply(msg_id, {"protocolVersion": proto, "capabilities": {"tools": {"listChanged": False}},
                              "serverInfo": {"name": "superlab-lab-api", "version": "1.0.0"},
                              "instructions": "슈퍼랩 사내 API(가짜 데이터). 조회 도구는 get_으로 시작하고, request_leave는 쓰기입니다."})
    if method == "ping":
        return reply(msg_id, {})
    if method == "tools/list":
        return reply(msg_id, {"tools": TOOLS})
    if method == "tools/call":
        params = msg.get("params") or {}
        name = params.get("name")
        if name not in {t["name"] for t in TOOLS}:
            return reply(msg_id, error={"code": -32602, "message": "Unknown tool: %s" % name})
        try:
            data = run_tool(name, params.get("arguments") or {})
            return reply(msg_id, {"content": [{"type": "text", "text": json.dumps(data, ensure_ascii=False, indent=2)}],
                                  "isError": False})
        except ApiError as err:
            return reply(msg_id, {"content": [{"type": "text", "text": "API 오류 %s %s: %s" % (
                err.status or "-", err.code, err.detail)}], "isError": True})
    if "id" in msg:
        return reply(msg_id, error={"code": -32601, "message": "Method not found: %s" % method})
    return None


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except ValueError:
            reply(None, error={"code": -32700, "message": "Parse error"})
            continue
        for m in (msg if isinstance(msg, list) else [msg]):
            if isinstance(m, dict):
                handle(m)


if __name__ == "__main__":
    main()
