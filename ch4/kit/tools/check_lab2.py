#!/usr/bin/env python3
"""lab2 · 사내 API 업무 자동화 검사.  python3 tools/check_lab2.py

워크시트(docs/worksheets/lab2.md)의 결정이 스킬, 권한, MCP 등록과 맞는지 봅니다.
쓰기(휴가 신청)가 결정 3과 다르게 자동 승인되는지를 가장 중요하게 봅니다.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from checklib import (BLANK, ROOT, Report, Skill, Worksheet, check_decisions, check_predictions,  # noqa: E402
                      check_reflection, check_tracking, decision, filled, line_of, read, run_tool, scan_tokens)

WRITE_CMDS = [
    "python3 tools/hr_fetch.py request --start 2026-10-08 --end 2026-10-08 --reason 개인 사유",
    "python3 tools/hr_fetch.py --format json request --start 2026-10-08",
]
READ_CMDS = ["python3 tools/hr_fetch.py member ME", "python3 tools/hr_fetch.py leave"]


def route(choice):
    c = (choice or "").strip()
    head = c[:1].upper()
    if head in "ABC" and head:
        return head
    if "주입" in c:
        return "A"
    if "mcp" in c.lower():
        return "C"
    if "bash" in c.lower() or "스크립트" in c:
        return "B"
    return ""


def write_mode(choice):
    c = (choice or "").lower()
    if "allow" in c or "묻지 않" in c:
        return "allow"
    if "계획" in c or "진행" in c:
        return "plan"
    if "ask" in c or "승인" in c:
        return "ask"
    return ""


def mcp_servers():
    try:
        data = json.loads(read(ROOT / ".mcp.json") or "{}")
    except ValueError:
        return None
    return data.get("mcpServers") or {}


def main():
    rep = Report("lab2 · 사내 API 업무 자동화 검사")
    ws = Worksheet(2)
    if not ws.exists():
        rep.fail("워크시트가 없습니다", "docs/worksheets/lab2.md")
        return rep.finish()

    name = ws.field("내 스킬 이름").strip("` /")
    if not rep.check(filled(name), "워크시트: 스킬 이름 '%s'" % name,
                     "워크시트 맨 위 '내 스킬 이름'을 적으세요", ws.where):
        return rep.finish()

    choices = check_decisions(rep, ws, ["D1", "D2", "D3"])
    check_predictions(rep, ws, ["P1", "P2", "P3", "P4"])

    sk = Skill(name)
    if not rep.check(sk.exists(), "스킬 파일: %s" % sk.where, "스킬 파일이 없습니다",
                     ".claude/skills/%s/SKILL.md" % name):
        return rep.finish()

    leftovers = [k for k, v in sk.fm.items() if BLANK in str(v)]
    rep.check(not leftovers, "머리말에 빈칸 없음", "머리말에 빈칸이 남아 있습니다: %s" % ", ".join(leftovers), sk.where)
    rep.check(BLANK not in sk.body, "지시문에 빈칸 없음", "지시문에 ____ 이 남아 있습니다",
              "%s:%d" % (sk.where, line_of(sk.text, BLANK)))

    allowed = sk.allowed()
    r = route(choices.get("D2"))
    mode = write_mode(choices.get("D3"))
    writes = name != "deploy-report"

    # 결정 2: 연결 수단
    if r == "A":
        inj = sk.injections()
        rep.check(inj, "결정 2(A 주입) → 주입 명령 %d개" % len(inj),
                  "결정 2는 A(주입)인데 지시문에 주입 명령이 없습니다", sk.where)
        blocked = [c for c in inj if decision("Bash", c, allowed) != "allow"]
        rep.check(not blocked, "주입 명령이 모두 허용됨 (스킬이 중단되지 않음)",
                  "허용되지 않은 주입 명령이 있어 스킬 호출 전체가 중단됩니다 (P1): %s" % "; ".join(blocked[:2]),
                  sk.where)
    elif r == "B":
        rep.check("hr_fetch.py" in sk.body, "결정 2(B Bash) → 지시문에 실행할 명령",
                  "결정 2는 B인데 지시문에 실행할 hr_fetch.py 명령이 없습니다", sk.where)
    elif r == "C":
        servers = mcp_servers()
        if servers is None:
            rep.fail(".mcp.json을 JSON으로 읽을 수 없습니다", ".mcp.json")
        else:
            lab = {k: v for k, v in servers.items() if "lab_mcp.py" in " ".join(map(str, v.get("args", [])))}
            if rep.check(lab, "결정 2(C MCP) → .mcp.json에 lab_mcp.py 서버 '%s'" % ", ".join(lab),
                         "결정 2는 C인데 .mcp.json에 tools/lab_mcp.py 서버가 없습니다", ".mcp.json"):
                srv, conf = next(iter(lab.items()))
                args = " ".join(map(str, conf.get("args", [])))
                rep.check("CLAUDE_PROJECT_DIR" in args, "서버 경로가 프로젝트 기준 (${CLAUDE_PROJECT_DIR:-.})",
                          "서버 경로가 상대 경로라 다른 폴더에서 실행하면 못 찾습니다", ".mcp.json", level="warn")
                rep.check("mcp__%s__" % srv in sk.body or "mcp__%s" % srv in " ".join(allowed),
                          "지시문이나 allowed-tools에 MCP 도구 이름",
                          "지시문에 쓸 MCP 도구 이름(mcp__%s__...)이 보이지 않습니다" % srv, sk.where, level="warn")
                WRITE_CMDS.append(("mcp", "mcp__%s__request_leave" % srv))
    else:
        rep.warn("결정 2의 선택을 A, B, C 중 하나로 시작하면 설정과 맞춰 볼 수 있습니다", ws.where)

    # 결정 3: 쓰기 처리
    # allowed-tools 허용은 스킬을 부른 턴에만 유효합니다. 계획 먼저 방식이면 "진행" 뒤의 신청은
    # 다음 턴이므로 settings 규칙만으로 판단합니다.
    grant = () if mode == "plan" else allowed

    def outcome(cmd):
        if isinstance(cmd, tuple):
            return decision(cmd[1], None, grant)
        return decision("Bash", cmd, grant)

    results = {(c[1] if isinstance(c, tuple) else c): outcome(c) for c in WRITE_CMDS}
    auto = [c for c, d in results.items() if d == "allow"]
    if not writes:
        rep.check(not auto, "조회만 하는 스킬에서 쓰기는 자동 승인되지 않음",
                  "조회만 하는 스킬인데 휴가 신청까지 자동 승인됩니다 (P2: 넓은 허용 패턴)",
                  ".claude/settings.json 또는 %s의 allowed-tools" % sk.where, level="warn")
    elif mode in ("ask", "plan"):
        rep.check(not auto, "쓰기(휴가 신청)가 자동 승인되지 않음 (결정 3: %s)" % mode,
                  "결정 3은 '%s'인데 휴가 신청이 묻지 않고 실행됩니다 (P2: 넓은 허용 패턴): %s" % (mode, auto[0] if auto else ""),
                  ".claude/settings.json 또는 %s의 allowed-tools" % sk.where)
        if mode == "plan":
            rep.check("진행" in sk.body, "계획을 보여 주고 '진행'을 기다리는 단계가 있음",
                      "결정 3은 '계획 먼저'인데 지시문에 '진행'을 기다리는 단계가 없습니다", sk.where)
            same_turn = [c for c in WRITE_CMDS if (decision(c[1], None, allowed) if isinstance(c, tuple)
                                                   else decision("Bash", c, allowed)) == "allow"]
            rep.check(not same_turn, "allowed-tools가 신청을 열지 않음",
                      "allowed-tools가 신청까지 엽니다. 스킬이 '진행' 전에 같은 턴에서 신청하면 묻지 않습니다",
                      sk.where, level="warn")
    elif mode == "allow":
        rep.check(auto, "결정 3(allow) → 쓰기가 자동 승인됨",
                  "결정 3은 allow인데 휴가 신청에 승인 창이 뜹니다", sk.where, level="warn")
        rep.warn("allow는 잘못 읽은 요청도 실제로 신청됩니다. 판단 규칙이 이를 막는지 워크시트에 적어 두세요", ws.where)
    else:
        rep.warn("결정 3의 선택을 ask, 계획 먼저, allow 중 하나로 적으면 설정과 맞춰 볼 수 있습니다", ws.where)

    rep.check(any(decision("Bash", c, allowed) == "allow" for c in READ_CMDS) or r == "C",
              "조회는 묻지 않고 실행됨", "조회 명령에도 매번 승인 창이 뜹니다 (조회만 허용하는 규칙을 추가해 보세요)",
              sk.where, level="warn")

    # 데이터 원칙
    principle = any(k in sk.body for k in ("따르지 않", "데이터로", "지시는 무시"))
    rep.check(principle, "API 응답을 데이터로 다루는 원칙이 있음",
              "API 응답 속 문장을 지시로 따르지 않는다는 원칙이 보이지 않습니다", sk.where, level="warn")

    # 실제 실행 흔적
    if writes:
        res = run_tool("tools/hr_fetch.py", "--format", "json", "requests")
        if res is None or res.returncode != 0:
            msg = (res.stderr.strip().splitlines() or [""])[-1] if res else "실행 실패"
            rep.warn("신청 목록을 조회하지 못했습니다: %s" % msg, "python3 tools/hr_fetch.py me")
        else:
            try:
                n = len(json.loads(res.stdout).get("requests", []))
            except ValueError:
                n = 0
            rep.check(n >= 1, "사내 API에 신청 기록 %d건" % n,
                      "아직 신청 기록이 없습니다. 정상 요청으로 스킬을 한 번 실행하세요",
                      "python3 tools/hr_fetch.py requests", level="warn")

    check_tracking(rep, ws, ["D1", "D2", "D3"])
    check_reflection(rep, ws)
    scan_tokens(rep)
    return rep.finish()


if __name__ == "__main__":
    sys.exit(main())
