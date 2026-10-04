#!/usr/bin/env python3
"""사내 API 조회·신청 스크립트 (lab2).

  python3 tools/hr_fetch.py me                          내 id와 팀원
  python3 tools/hr_fetch.py leave [--from D] [--to D]   기간 내 팀 휴가 (기본: 이번 주)
  python3 tools/hr_fetch.py member <ME|M01..>           팀원 연차 잔여와 예정 휴가
  python3 tools/hr_fetch.py requests                    내가 낸 휴가 신청
  python3 tools/hr_fetch.py request --start D [--end D] [--reason 텍스트] [--dry-run]
                                                        휴가 신청 (쓰기). --dry-run은 보내지 않고 내용만 출력
  python3 tools/hr_fetch.py deploys [--days N]          최근 배포 이력

공통: --format md(기본) | json
토큰은 ~/.config/superlab/token 에서 읽고, 어떤 출력에도 쓰지 않습니다.
HTTP 오류면 종료 코드 1, 설정 오류면 2로 끝납니다.
"""

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from labapi.client import ApiError, call  # noqa: E402


def md_table(headers, rows):
    if not rows:
        return "(없음)"
    out = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    out += ["| " + " | ".join(str(c) for c in row) + " |" for row in rows]
    return "\n".join(out)


def business_days(start, end):
    n, d = 0, start
    while d <= end:
        if d.weekday() < 5:
            n += 1
        d += dt.timedelta(days=1)
    return n


def main():
    ap = argparse.ArgumentParser(description="슈퍼랩 사내 API 조회·신청")
    ap.add_argument("--format", choices=["md", "json"], default="md")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("me")
    p = sub.add_parser("leave")
    p.add_argument("--from", dest="start")
    p.add_argument("--to", dest="end")
    p = sub.add_parser("member")
    p.add_argument("member")
    sub.add_parser("requests")
    p = sub.add_parser("request")
    p.add_argument("--start", required=True)
    p.add_argument("--end")
    p.add_argument("--reason", default="")
    p.add_argument("--dry-run", action="store_true")
    p = sub.add_parser("deploys")
    p.add_argument("--days", type=int, default=7)
    args = ap.parse_args()

    try:
        if args.cmd == "me":
            data = call("GET", "/v1/me")
            text = "참가자: %s\n\n%s" % (data["participant"], md_table(
                ["id", "이름", "역할"], [[m["id"], m["name"], m["role"]] for m in data["team"]]))
        elif args.cmd == "leave":
            q = "&".join(x for x in [
                "from=" + args.start if args.start else "", "to=" + args.end if args.end else ""] if x)
            data = call("GET", "/v1/leave" + ("?" + q if q else ""))
            text = "기간: %s ~ %s\n\n%s" % (data["from"], data["to"], md_table(
                ["날짜", "id", "이름", "종류", "상태"],
                [[x["date"], x["member"], x["name"], x["type"], x["status"]] for x in data["leaves"]]))
        elif args.cmd == "member":
            data = call("GET", "/v1/leave/" + args.member)
            extra = ", 신청 가능 %d일" % data["available"] if "available" in data else ""
            text = "%s(%s) 연차: 총 %d일, 사용 %d일, 잔여 %d일, 승인 대기 %d건%s\n\n예정 휴가 (4주)\n%s" % (
                data["name"], data["member"], data["total"], data["used"], data["remaining"], data["pending"], extra,
                md_table(["날짜", "종류", "상태"], [[x["date"], x["type"], x["status"]] for x in data["upcoming"]]))
        elif args.cmd == "requests":
            data = call("GET", "/v1/leave/requests")
            text = md_table(["신청 번호", "시작", "끝", "일수", "사유", "상태"],
                            [[r["request_id"], r["start"], r["end"], r["days"], r["reason"], r["status"]]
                             for r in data["requests"]])
        elif args.cmd == "request":
            end = args.end or args.start
            body = {"start": args.start, "end": end, "reason": args.reason}
            if args.dry_run:
                try:
                    days = business_days(dt.date.fromisoformat(args.start), dt.date.fromisoformat(end))
                except ValueError:
                    print("날짜는 YYYY-MM-DD 형식이어야 합니다", file=sys.stderr)
                    return 2
                data = dict(body, business_days=days, dry_run=True)
                text = "[미리보기] %s ~ %s, 근무일 %d일, 사유: %s (아직 신청하지 않았습니다)" % (
                    args.start, end, days, args.reason or "-")
            else:
                data = call("POST", "/v1/leave/requests", body)
                text = "신청 완료: %s, %s ~ %s, %d일, 상태 %s" % (
                    data["request_id"], data["start"], data["end"], data["days"], data["status"])
        else:
            data = call("GET", "/v1/deploys?days=%d" % args.days)
            text = "최근 %d일 배포\n\n%s" % (data["days"], md_table(
                ["시각", "서비스", "버전", "환경", "결과", "배포자"],
                [[x["at"][:16].replace("T", " "), x["service"], x["version"], x["env"], x["status"], x["author"]]
                 for x in data["deploys"]]))
    except ApiError as err:
        print("API 오류 %s %s: %s" % (err.status or "-", err.code, err.detail), file=sys.stderr)
        return 2 if err.code in ("no_token",) else 1

    print(json.dumps(data, ensure_ascii=False, indent=2) if args.format == "json" else text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
