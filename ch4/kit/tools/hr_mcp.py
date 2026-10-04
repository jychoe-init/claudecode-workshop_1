#!/usr/bin/env python3
"""가짜 사내 HR 시스템 MCP 서버 (stdio, 표준 라이브러리만 사용).

실습용 가짜 데이터입니다. 실제 인사 시스템과 연결되지 않습니다.

도구
  get_leave_balance(employee_id)                       조회 · 읽기 전용
  get_holidays(month?)                                 조회 · 읽기 전용
  get_leave_requests(employee_id)                      조회 · 읽기 전용
  request_leave(employee_id, start_date, end_date, reason)   신청 · 쓰기

권한 실습
  조회 도구는 이름이 get_ 으로 시작하므로 allow 규칙 "mcp__hr__get_*" 하나로 묶을 수 있습니다.
  신청 도구는 ask 규칙 "mcp__hr__request_leave"로 승인을 받게 합니다.

서버 쪽 울타리 (선택)
  HR_STRICT=1 로 실행하면 request_leave에 _meta["anthropic/requiresUserInteraction"]=true 를 붙입니다.
  Claude Code는 이 도구를 acceptEdits·auto 모드에서도 매번 묻고, allow 규칙으로도 건너뛸 수 없습니다.

등록 예 (.mcp.json, 프로젝트 루트)
  {
    "mcpServers": {
      "hr": {
        "command": "python3",
        "args": ["${CLAUDE_PROJECT_DIR:-.}/tools/hr_mcp.py"]
      }
    }
  }
"""

import datetime as dt
import json
import os
import sys
from pathlib import Path

SERVER_INFO = {"name": "fake-hr", "version": "1.0.0"}
DEFAULT_PROTOCOL = "2025-06-18"
STRICT = os.environ.get("HR_STRICT") == "1"
PROJECT_DIR = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parent.parent)
REQUESTS_FILE = PROJECT_DIR / ".hr_requests.json"

INSTRUCTIONS = (
    "가짜 사내 HR 시스템입니다(실습용 데이터). 휴가 잔여(get_leave_balance), 공휴일(get_holidays), "
    "휴가 신청 내역(get_leave_requests) 조회와 휴가 신청(request_leave)을 제공합니다. "
    "실습 참가자의 사번은 E1001입니다. 다른 사람의 사번을 모르면 사용자에게 물어보세요."
)

EMPLOYEES = {
    "E1001": {"name": "실습 참가자", "team": "플랫폼팀", "annual_total": 15, "annual_used": 6},
    "E1002": {"name": "김지원", "team": "PM", "annual_total": 15, "annual_used": 11},
    "E1003": {"name": "박서준", "team": "백엔드", "annual_total": 18, "annual_used": 4},
    "E1004": {"name": "최유진", "team": "QA", "annual_total": 15, "annual_used": 15},
}

HOLIDAYS = [
    ("2026-10-03", "개천절"),
    ("2026-10-05", "대체공휴일(개천절)"),
    ("2026-10-09", "한글날"),
    ("2026-12-25", "성탄절"),
]


def log(msg):
    print(f"[fake-hr] {msg}", file=sys.stderr, flush=True)


def load_requests():
    if REQUESTS_FILE.exists():
        try:
            return json.loads(REQUESTS_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            log(f"{REQUESTS_FILE.name}를 읽지 못해 빈 목록으로 시작합니다")
    return []


def save_requests(items):
    REQUESTS_FILE.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")


def business_days(start, end):
    holiday_dates = {h[0] for h in HOLIDAYS}
    days, cur = 0, start
    while cur <= end:
        if cur.weekday() < 5 and cur.isoformat() not in holiday_dates:
            days += 1
        cur += dt.timedelta(days=1)
    return days


def pending_days(employee_id):
    return sum(r["days"] for r in load_requests() if r["employee_id"] == employee_id and r["status"] == "승인 대기")


class ToolError(Exception):
    pass


def employee(employee_id):
    emp = EMPLOYEES.get(employee_id)
    if not emp:
        raise ToolError(f"사번 {employee_id}를 찾을 수 없습니다. 사용 가능한 사번: {', '.join(EMPLOYEES)}")
    return emp


def tool_get_leave_balance(args):
    eid = args.get("employee_id", "")
    emp = employee(eid)
    pending = pending_days(eid)
    remaining = emp["annual_total"] - emp["annual_used"]
    return {
        "employee_id": eid,
        "name": emp["name"],
        "team": emp["team"],
        "annual_total": emp["annual_total"],
        "annual_used": emp["annual_used"],
        "pending_requests_days": pending,
        "remaining": remaining,
        "available_to_request": remaining - pending,
    }


def tool_get_holidays(args):
    month = args.get("month")
    items = [{"date": d, "name": n} for d, n in HOLIDAYS if not month or d.startswith(month)]
    return {"month": month or "전체", "holidays": items, "note": "실습용 데이터"}


def tool_get_leave_requests(args):
    eid = args.get("employee_id", "")
    employee(eid)
    return {"employee_id": eid, "requests": [r for r in load_requests() if r["employee_id"] == eid]}


def tool_request_leave(args):
    eid = args.get("employee_id", "")
    emp = employee(eid)
    try:
        start = dt.date.fromisoformat(args.get("start_date", ""))
        end = dt.date.fromisoformat(args.get("end_date", ""))
    except ValueError:
        raise ToolError("start_date, end_date는 YYYY-MM-DD 형식이어야 합니다")
    if end < start:
        raise ToolError("end_date가 start_date보다 빠릅니다")
    days = business_days(start, end)
    if days == 0:
        raise ToolError("신청 기간에 근무일이 없습니다 (주말·공휴일만 포함)")
    available = emp["annual_total"] - emp["annual_used"] - pending_days(eid)
    if days > available:
        raise ToolError(f"잔여 연차가 부족합니다: 신청 {days}일, 신청 가능 {available}일")
    items = load_requests()
    req = {
        "request_id": f"REQ-{len(items) + 1:04d}",
        "employee_id": eid,
        "name": emp["name"],
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "days": days,
        "reason": args.get("reason", ""),
        "status": "승인 대기",
        "created_at": dt.datetime.now().isoformat(timespec="seconds"),
    }
    items.append(req)
    save_requests(items)
    return req


EMPLOYEE_ID = {"type": "string", "description": "사번 (예: E1001)"}

TOOLS = [
    {
        "name": "get_leave_balance",
        "title": "휴가 잔여 조회",
        "description": "직원의 연차 총일수, 사용일수, 승인 대기 일수, 신청 가능 일수를 조회합니다.",
        "inputSchema": {
            "type": "object",
            "properties": {"employee_id": EMPLOYEE_ID},
            "required": ["employee_id"],
        },
        "annotations": {"readOnlyHint": True},
        "handler": tool_get_leave_balance,
    },
    {
        "name": "get_holidays",
        "title": "공휴일 조회",
        "description": "회사 공휴일 목록을 조회합니다. month(YYYY-MM)를 주면 해당 월만 돌려줍니다.",
        "inputSchema": {
            "type": "object",
            "properties": {"month": {"type": "string", "description": "YYYY-MM (선택)"}},
        },
        "annotations": {"readOnlyHint": True},
        "handler": tool_get_holidays,
    },
    {
        "name": "get_leave_requests",
        "title": "휴가 신청 내역 조회",
        "description": "직원의 휴가 신청 내역과 상태를 조회합니다.",
        "inputSchema": {
            "type": "object",
            "properties": {"employee_id": EMPLOYEE_ID},
            "required": ["employee_id"],
        },
        "annotations": {"readOnlyHint": True},
        "handler": tool_get_leave_requests,
    },
    {
        "name": "request_leave",
        "title": "휴가 신청",
        "description": "휴가를 신청합니다. 주말·공휴일을 제외한 근무일 수만큼 연차를 차감 예정으로 잡고 승인 대기 상태로 등록합니다.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "employee_id": EMPLOYEE_ID,
                "start_date": {"type": "string", "description": "시작일 YYYY-MM-DD"},
                "end_date": {"type": "string", "description": "종료일 YYYY-MM-DD"},
                "reason": {"type": "string", "description": "사유"},
            },
            "required": ["employee_id", "start_date", "end_date"],
        },
        "annotations": {"readOnlyHint": False, "destructiveHint": False},
        "handler": tool_request_leave,
    },
]

if STRICT:
    for t in TOOLS:
        if t["name"] == "request_leave":
            t["_meta"] = {"anthropic/requiresUserInteraction": True}

HANDLERS = {t["name"]: t["handler"] for t in TOOLS}


def public_tool(t):
    return {k: v for k, v in t.items() if k != "handler"}


def result(msg_id, payload):
    return {"jsonrpc": "2.0", "id": msg_id, "result": payload}


def error(msg_id, code, message):
    return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": code, "message": message}}


def handle(msg):
    if not isinstance(msg, dict):
        return error(None, -32600, "Invalid Request")
    method = msg.get("method")
    msg_id = msg.get("id")
    is_notification = "id" not in msg

    if method == "initialize":
        requested = (msg.get("params") or {}).get("protocolVersion") or DEFAULT_PROTOCOL
        log(f"initialize (protocol {requested}, strict={STRICT})")
        return result(msg_id, {
            "protocolVersion": requested,
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": SERVER_INFO,
            "instructions": INSTRUCTIONS,
        })
    if method == "ping":
        return result(msg_id, {})
    if method == "tools/list":
        return result(msg_id, {"tools": [public_tool(t) for t in TOOLS]})
    if method == "tools/call":
        params = msg.get("params") or {}
        name = params.get("name")
        args = params.get("arguments") or {}
        handler = HANDLERS.get(name)
        if not handler:
            return error(msg_id, -32602, f"Unknown tool: {name}")
        log(f"tools/call {name} {json.dumps(args, ensure_ascii=False)}")
        try:
            data = handler(args)
            text = json.dumps(data, ensure_ascii=False, indent=2)
            return result(msg_id, {"content": [{"type": "text", "text": text}], "isError": False})
        except ToolError as exc:
            return result(msg_id, {"content": [{"type": "text", "text": str(exc)}], "isError": True})
    if is_notification:
        return None  # notifications/initialized 등은 응답하지 않음
    return error(msg_id, -32601, f"Method not found: {method}")


def main():
    log(f"started (project: {PROJECT_DIR})")
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            reply = error(None, -32700, "Parse error")
        else:
            if isinstance(msg, list):
                replies = [r for r in (handle(m) for m in msg) if r is not None]
                reply = replies or None
            else:
                reply = handle(msg)
        if reply is not None:
            sys.stdout.write(json.dumps(reply, ensure_ascii=False) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
