#!/usr/bin/env python3
"""사내 API 스모크 테스트 (클라우드와 로컬 서버 공용).

  python3 ch4/infra/smoke.py --base https://xxxx.lambda-url.ap-northeast-2.on.aws --secret-file ch4/infra/.secret
  python3 ch4/infra/smoke.py --base http://127.0.0.1:8787 --secret superlab-local-secret --rate-test

확인 항목: /health, /docs, 401(토큰 없음·잘못됨), /v1/me, /v1/leave, /v1/leave/ME, /v1/deploys,
POST /v1/leave/requests(201)와 조회, 422, 그리고 --rate-test면 429.
smoke 전용 좌석(기본: 81~99 중 임의)의 토큰을 써서 참가자 데이터와 섞이지 않게 합니다.
신청 날짜는 30~300일 뒤 임의의 평일이라 여러 번 실행해도 겹치지 않습니다.
"""

import argparse
import datetime as dt
import json
import random
import sys
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "kit"))
from labapi.core import token_for  # noqa: E402


def req(base, method, path, token=None, body=None):
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(base + path, data=data, method=method)
    if token:
        r.add_header("Authorization", "Bearer " + token)
    if data is not None:
        r.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(r, timeout=15) as resp:
            raw = resp.read()
            return resp.status, dict(resp.headers), raw
    except urllib.error.HTTPError as err:
        return err.code, dict(err.headers), err.read()


def random_weekday():
    d = dt.date.today() + dt.timedelta(days=random.randint(30, 300))
    while d.weekday() >= 5:
        d += dt.timedelta(days=1)
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--secret")
    ap.add_argument("--secret-file")
    ap.add_argument("--seat", type=int, default=None, help="기본: 81~99 중 임의")
    ap.add_argument("--rate-test", action="store_true", help="분당 한도를 넘겨 429를 확인 (호출이 많음)")
    ap.add_argument("--rate", type=int, default=60)
    args = ap.parse_args()
    base = args.base.rstrip("/")
    secret = args.secret or (Path(args.secret_file).read_text().strip() if args.secret_file else "")
    if not secret:
        print("--secret 또는 --secret-file이 필요합니다", file=sys.stderr)
        return 2
    seat = args.seat if args.seat is not None else random.randint(81, 99)
    tok = token_for(seat, secret)
    results = []

    def check(name, cond, detail=""):
        results.append((name, bool(cond), detail))

    s, _, b = req(base, "GET", "/health")
    check("GET /health 200", s == 200 and json.loads(b).get("ok") is True, s)
    s, h, b = req(base, "GET", "/docs")
    check("GET /docs 200 html", s == 200 and "text/html" in h.get("Content-Type", h.get("content-type", "")), s)
    s, _, _ = req(base, "GET", "/v1/me")
    check("토큰 없음 401", s == 401, s)
    s, _, _ = req(base, "GET", "/v1/me", "wk-%02d-000000000000" % seat)
    check("잘못된 토큰 401", s == 401, s)
    s, _, b = req(base, "GET", "/v1/me", tok)
    me = json.loads(b) if s == 200 else {}
    check("GET /v1/me 200, 팀 6명", s == 200 and len(me.get("team", [])) == 6, s)
    s, _, b = req(base, "GET", "/v1/leave", tok)
    check("GET /v1/leave 200", s == 200 and "leaves" in json.loads(b), s)
    s, _, b = req(base, "GET", "/v1/leave/ME", tok)
    check("GET /v1/leave/ME 200", s == 200 and "remaining" in json.loads(b), s)
    s, _, b = req(base, "GET", "/v1/deploys?days=7", tok)
    check("GET /v1/deploys 200", s == 200 and "deploys" in json.loads(b), s)
    for _ in range(5):
        day = random_weekday().isoformat()
        s, _, b = req(base, "POST", "/v1/leave/requests", tok, {"start": day, "end": day, "reason": "smoke"})
        if not (s == 422 and "겹칩니다" in b.decode("utf-8", "ignore")):
            break
    created = json.loads(b) if s == 201 else {}
    check("POST /v1/leave/requests 201", s == 201 and created.get("status") == "승인 대기", "%s %s" % (s, b[:120]))
    s, _, b = req(base, "GET", "/v1/leave/requests", tok)
    ids = [r["request_id"] for r in json.loads(b).get("requests", [])] if s == 200 else []
    check("신청 목록에 방금 신청 포함", created.get("request_id") in ids, ids[-3:])
    s, _, b = req(base, "POST", "/v1/leave/requests", tok, {"start": day, "end": day, "reason": "smoke"})
    check("같은 날짜 다시 신청 422", s == 422, s)
    s, _, b = req(base, "GET", "/v1/leave/ME", tok)
    check("잔여에 신청 반영 (available)", s == 200 and "available" in json.loads(b), s)
    s, _, _ = req(base, "POST", "/v1/leave/requests", tok, {"start": "2026-13-01"})
    check("잘못된 날짜 422", s == 422, s)
    s, _, _ = req(base, "DELETE", "/v1/me", tok)
    check("허용되지 않은 메서드 405", s == 405, s)
    if args.rate_test:
        codes = [req(base, "GET", "/health")[0]]
        got429 = False
        for _ in range(args.rate + 5):
            s, h, _ = req(base, "GET", "/v1/me", tok)
            if s == 429:
                got429 = bool(h.get("Retry-After") or h.get("retry-after"))
                break
        check("분당 한도 초과 429 + Retry-After", got429, codes)

    width = max(len(r[0]) for r in results)
    for name, ok, detail in results:
        print("%s %s  %s" % ("✔" if ok else "✘", name.ljust(width), "" if ok else detail))
    failed = [r for r in results if not r[1]]
    print("\n%d개 중 %d개 통과" % (len(results), len(results) - len(failed)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
