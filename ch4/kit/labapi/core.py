"""슈퍼랩 사내 API 핵심 로직 (가짜 데이터).

로컬 서버(tools/lab_server.py)와 AWS Lambda(infra/lambda/handler.py)가 이 파일 하나를 함께 씁니다.
두 실행 방식의 차이는 횟수 제한과 신청 저장소 구현뿐입니다.

- 인증: Authorization: Bearer wk-<NN>-<12hex>
  <12hex> = HMAC-SHA256(secret, "wk-<NN>") 의 앞 12자. 비밀값을 바꾸면 모든 토큰이 폐기됩니다.
- 데이터: 토큰 id와 주(週)를 시드로 결정적으로 생성합니다. 같은 사람은 같은 주에 같은 데이터를 봅니다.
- 로그: 토큰 id(wk-07)만 남기고 HMAC 부분은 남기지 않습니다.

표준 라이브러리만 사용합니다 (Python 3.9+).
"""

import datetime as dt
import hashlib
import hmac
import json
import random
import re
import time
from urllib.parse import parse_qs, unquote

KST = dt.timezone(dt.timedelta(hours=9))
TOKEN_RE = re.compile(r"^wk-(\d{2})-([0-9a-f]{12})$")
DEFAULT_RATE_LIMIT = 60

NAMES = ["김지원", "박서준", "이하늘", "최유진", "정민호", "한소희", "오세훈", "윤아름", "장도윤", "임채원",
         "강예린", "조현우", "신다은", "배준서", "문가영", "서지후", "황보람", "송태경", "권나연", "유승민"]
ROLES = ["PM", "백엔드", "프론트엔드", "QA", "디자인", "데이터", "인프라"]
LEAVE_TYPES = ["연차", "연차", "연차", "반차(오전)", "반차(오후)", "병가"]
SERVICES = ["payment-api", "web-frontend", "auth-service", "notification", "search-indexer", "admin-console"]
DEPLOY_STATUS = ["success"] * 7 + ["failed", "rolled_back"]


# ───────────────────────────── 토큰 ─────────────────────────────
def token_for(seat, secret):
    tid = "wk-%02d" % int(seat)
    mac = hmac.new(secret.encode(), tid.encode(), hashlib.sha256).hexdigest()[:12]
    return "%s-%s" % (tid, mac)


def verify_token(token, secret):
    """유효하면 토큰 id(wk-07)를, 아니면 None을 돌려줍니다."""
    m = TOKEN_RE.match(token or "")
    if not m:
        return None
    tid = "wk-" + m.group(1)
    expected = hmac.new(secret.encode(), tid.encode(), hashlib.sha256).hexdigest()[:12]
    return tid if hmac.compare_digest(expected, m.group(2)) else None


# ───────────────────────────── 저장소·횟수 제한 (로컬 기본 구현) ─────────────────────────────
class MemoryLimiter:
    def __init__(self, limit=DEFAULT_RATE_LIMIT):
        self.limit = limit
        self.counts = {}

    def hit(self, tid, now=None):
        """(허용 여부, Retry-After 초)"""
        now = now or time.time()
        minute = int(now // 60)
        key = (tid, minute)
        self.counts = {k: v for k, v in self.counts.items() if k[1] >= minute - 1}
        self.counts[key] = self.counts.get(key, 0) + 1
        if self.counts[key] > self.limit:
            return False, 60 - int(now % 60)
        return True, 0


class MemoryStore:
    def __init__(self):
        self.items = {}

    def list_requests(self, tid):
        return list(self.items.get(tid, []))

    def add_request(self, tid, item):
        self.items.setdefault(tid, []).append(item)


# ───────────────────────────── 가짜 데이터 ─────────────────────────────
def _today():
    return dt.datetime.now(KST).date()


def _week_start(day):
    return day - dt.timedelta(days=day.weekday())


def _rng(tid, salt, week):
    seed = hashlib.sha256(("%s|%s|%s" % (tid, salt, week.isoformat())).encode()).hexdigest()
    return random.Random(int(seed[:16], 16))


def team_for(tid):
    rng = _rng(tid, "team", dt.date(2026, 1, 5))  # 팀 구성은 주가 바뀌어도 그대로
    names = rng.sample(NAMES, 5)
    members = [{"id": "M%02d" % (i + 1), "name": n, "role": rng.choice(ROLES)} for i, n in enumerate(names)]
    members.insert(0, {"id": "ME", "name": "나 (%s)" % tid, "role": "참가자"})
    return members


def _member(tid, member_id):
    for m in team_for(tid):
        if m["id"] == member_id:
            return m
    return None


def leaves_for(tid, start, end):
    """start~end 범위의 팀 휴가. 주 단위로 결정적으로 생성합니다."""
    team = team_for(tid)
    out = []
    week = _week_start(start - dt.timedelta(days=7))
    while week <= end:
        rng = _rng(tid, "leave", week)
        for m in team:
            if rng.random() < 0.45:
                day = week + dt.timedelta(days=rng.randrange(0, 5))
                kind = rng.choice(LEAVE_TYPES)
                length = 1 if kind != "연차" else rng.choice([1, 1, 1, 2, 3])
                for k in range(length):
                    d = day + dt.timedelta(days=k)
                    if d.weekday() >= 5:
                        continue
                    if start <= d <= end:
                        out.append({
                            "date": d.isoformat(), "member": m["id"], "name": m["name"], "type": kind,
                            "status": "승인" if d <= _today() or rng.random() < 0.7 else "승인 대기",
                        })
        week += dt.timedelta(days=7)
    out.sort(key=lambda x: (x["date"], x["member"]))
    return out


def balance_for(tid, member_id):
    m = _member(tid, member_id)
    if not m:
        return None
    rng = _rng(tid, "balance:" + member_id, dt.date(2026, 1, 5))
    total = rng.choice([15, 15, 16, 18, 20])
    used = rng.randrange(2, total - 2)
    today = _today()
    upcoming = [x for x in leaves_for(tid, today, today + dt.timedelta(days=28)) if x["member"] == member_id]
    pending = len([x for x in upcoming if x["status"] == "승인 대기"])
    return {"member": member_id, "name": m["name"], "total": total, "used": used, "pending": pending,
            "remaining": total - used, "upcoming": upcoming}


def _request_days(req):
    d, end = dt.date.fromisoformat(req["start"]), dt.date.fromisoformat(req["end"])
    while d <= end:
        if d.weekday() < 5:
            yield d
        d += dt.timedelta(days=1)


def my_request_leaves(tid, store, start, end):
    """내가 낸 신청(승인 대기)을 팀 휴가 목록 형식으로."""
    name = next(m["name"] for m in team_for(tid) if m["id"] == "ME")
    out = []
    for r in store.list_requests(tid):
        if r.get("status") != "승인 대기":
            continue
        for d in _request_days(r):
            if start <= d <= end:
                out.append({"date": d.isoformat(), "member": "ME", "name": name, "type": "연차 신청",
                            "status": "승인 대기", "request_id": r["request_id"]})
    return out


def my_balance(tid, store):
    """ME의 잔여에 내가 낸 신청을 합칩니다. available = remaining - pending_days."""
    bal = balance_for(tid, "ME")
    today = _today()
    mine = my_request_leaves(tid, store, today - dt.timedelta(days=365), today + dt.timedelta(days=365))
    seeded = [x for x in bal["upcoming"] if x["status"] == "승인 대기"]
    bal["upcoming"] = sorted(bal["upcoming"] + [x for x in mine if x["date"] <= (today + dt.timedelta(days=28)).isoformat()],
                             key=lambda x: x["date"])
    bal["pending"] = len(seeded) + len({x["request_id"] for x in mine})
    bal["pending_days"] = len(seeded) + len(mine)
    bal["available"] = bal["remaining"] - bal["pending_days"]
    return bal


def deploys_for(tid, days):
    team = [m for m in team_for(tid) if m["id"] != "ME"]
    today = _today()
    out = []
    for i in range(days):
        day = today - dt.timedelta(days=i)
        rng = _rng(tid, "deploy", day)
        if day.weekday() >= 5 and rng.random() < 0.8:
            continue
        for j in range(rng.randrange(1, 4) if day.weekday() < 5 else 1):
            svc = rng.choice(SERVICES)
            hour = rng.randrange(9, 19)
            out.append({
                "id": "D%s-%d" % (day.strftime("%m%d"), j + 1),
                "service": svc,
                "version": "v%d.%d.%d" % (rng.randrange(1, 4), rng.randrange(0, 20), rng.randrange(0, 10)),
                "env": rng.choice(["prod", "prod", "stage"]),
                "status": rng.choice(DEPLOY_STATUS),
                "author": rng.choice(team)["name"],
                "at": "%sT%02d:%02d:00+09:00" % (day.isoformat(), hour, rng.randrange(0, 60)),
            })
    out.sort(key=lambda x: x["at"], reverse=True)
    return out


# ───────────────────────────── HTTP 처리 ─────────────────────────────
DOCS_HTML = """<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>슈퍼랩 사내 API</title>
<style>body{font-family:system-ui,sans-serif;max-width:760px;margin:32px auto;padding:0 16px;line-height:1.7;color:#222}
code,pre{background:#f3f4f6;border-radius:4px;padding:1px 5px}pre{padding:12px;overflow:auto}
table{border-collapse:collapse;width:100%}td,th{border:1px solid #ddd;padding:6px 8px;text-align:left}
@media (prefers-color-scheme: dark){body{background:#111;color:#ddd}code,pre{background:#222}td,th{border-color:#444}}</style></head>
<body><h1>슈퍼랩 사내 API (가짜 데이터)</h1>
<p>Chapter 4 슈퍼랩 lab2에서 쓰는 실습용 API입니다. 실제 인사·배포 시스템과 연결되지 않습니다.
모든 <code>/v1</code> 요청에는 <code>Authorization: Bearer &lt;토큰&gt;</code> 헤더가 필요합니다.
실습에서는 직접 호출하지 말고 <code>python3 tools/hr_fetch.py</code>를 쓰세요.</p>
<table><tr><th>메서드</th><th>경로</th><th>내용</th></tr>
<tr><td>GET</td><td><code>/v1/me</code></td><td>내 id, 팀원 목록</td></tr>
<tr><td>GET</td><td><code>/v1/leave?from=YYYY-MM-DD&amp;to=YYYY-MM-DD</code></td><td>기간 내 팀 휴가 (기본: 이번 주)</td></tr>
<tr><td>GET</td><td><code>/v1/leave/{member}</code></td><td>팀원 연차 잔여와 예정 휴가</td></tr>
<tr><td>GET</td><td><code>/v1/leave/requests</code></td><td>내가 낸 휴가 신청</td></tr>
<tr><td>POST</td><td><code>/v1/leave/requests</code></td><td>휴가 신청 <code>{"start","end","reason"}</code></td></tr>
<tr><td>GET</td><td><code>/v1/deploys?days=7</code></td><td>최근 배포 이력</td></tr></table>
<p>토큰당 분당 60회까지 호출할 수 있습니다. 넘으면 429와 <code>Retry-After</code> 헤더를 돌려줍니다.</p>
</body></html>"""


def _json(status, obj, extra=None):
    headers = {"Content-Type": "application/json; charset=utf-8"}
    if extra:
        headers.update(extra)
    return status, headers, json.dumps(obj, ensure_ascii=False).encode("utf-8")


def _err(status, code, detail=None, extra=None):
    body = {"error": code}
    if detail:
        body["detail"] = detail
    return _json(status, body, extra)


def _parse_date(value, default):
    if not value:
        return default
    try:
        return dt.date.fromisoformat(value)
    except ValueError:
        raise ValueError("날짜는 YYYY-MM-DD 형식이어야 합니다: %s" % value)


def _business_days(start, end):
    n, d = 0, start
    while d <= end:
        if d.weekday() < 5:
            n += 1
        d += dt.timedelta(days=1)
    return n


def handle(method, path, query, headers, body, secret, limiter, store, log=None):
    """(status, headers, body_bytes)를 돌려줍니다. query는 원시 문자열, headers는 소문자 키 dict."""
    method = (method or "GET").upper()
    path = unquote(path or "/").rstrip("/") or "/"
    params = {k: v[-1] for k, v in parse_qs(query or "").items()}

    if path == "/health":
        return _json(200, {"ok": True})
    if path in ("/", "/docs"):
        return 200, {"Content-Type": "text/html; charset=utf-8"}, DOCS_HTML.encode("utf-8")
    if not path.startswith("/v1/"):
        return _err(404, "not_found")

    auth = headers.get("authorization", "")
    token = auth[7:].strip() if auth.lower().startswith("bearer ") else ""
    tid = verify_token(token, secret)
    if not tid:
        return _err(401, "unauthorized", "Authorization: Bearer <토큰> 헤더를 확인하세요")

    ok, retry = limiter.hit(tid)
    if not ok:
        return _err(429, "rate_limited", "분당 호출 한도를 넘었습니다", {"Retry-After": str(retry)})

    if log:
        log({"tid": tid, "method": method, "path": path})

    try:
        today = _today()
        if path == "/v1/me" and method == "GET":
            return _json(200, {"participant": tid, "display_name": "참가자 %s" % tid[3:], "team": team_for(tid)})

        if path == "/v1/leave" and method == "GET":
            start = _parse_date(params.get("from"), _week_start(today))
            end = _parse_date(params.get("to"), _week_start(today) + dt.timedelta(days=6))
            if end < start or (end - start).days > 62:
                return _err(422, "invalid_request", "기간은 시작일 이후 62일 이내여야 합니다")
            leaves = sorted(leaves_for(tid, start, end) + my_request_leaves(tid, store, start, end),
                            key=lambda x: (x["date"], x["member"]))
            return _json(200, {"from": start.isoformat(), "to": end.isoformat(), "leaves": leaves})

        if path == "/v1/leave/requests":
            if method == "GET":
                return _json(200, {"requests": store.list_requests(tid)})
            if method == "POST":
                try:
                    data = json.loads(body.decode("utf-8") if isinstance(body, bytes) else (body or "{}"))
                except (ValueError, UnicodeDecodeError):
                    return _err(422, "invalid_request", "본문은 JSON이어야 합니다")
                start = _parse_date(data.get("start"), None)
                end = _parse_date(data.get("end"), start)
                if not start or end < start:
                    return _err(422, "invalid_request", "start, end(YYYY-MM-DD)를 확인하세요")
                days = _business_days(start, end)
                if days == 0:
                    return _err(422, "invalid_request", "신청 기간에 근무일이 없습니다")
                existing = store.list_requests(tid)
                taken = {x["date"] for x in my_request_leaves(tid, store, start, end)}
                taken |= {x["date"] for x in leaves_for(tid, start, end) if x["member"] == "ME"}
                overlap = sorted(d.isoformat() for d in _request_days({"start": start.isoformat(), "end": end.isoformat()})
                                 if d.isoformat() in taken)
                if overlap:
                    return _err(422, "invalid_request", "이미 휴가이거나 신청한 날짜와 겹칩니다: %s" % ", ".join(overlap))
                available = my_balance(tid, store)["available"]
                if days > available:
                    return _err(422, "invalid_request",
                                "잔여 연차가 부족합니다: 신청 %d일, 신청 가능 %d일" % (days, available))
                item = {"request_id": "REQ-%04d" % (len(existing) + 1), "member": "ME", "start": start.isoformat(),
                        "end": end.isoformat(), "days": days, "reason": str(data.get("reason", ""))[:200],
                        "status": "승인 대기", "created_at": dt.datetime.now(KST).isoformat(timespec="seconds")}
                store.add_request(tid, item)
                return _json(201, item)
            return _err(405, "method_not_allowed")

        m = re.match(r"^/v1/leave/(ME|M\d{2})$", path)
        if m and method == "GET":
            bal = my_balance(tid, store) if m.group(1) == "ME" else balance_for(tid, m.group(1))
            return _json(200, bal) if bal else _err(404, "not_found", "팀원 id를 확인하세요 (/v1/me)")

        if path == "/v1/deploys" and method == "GET":
            try:
                days = max(1, min(30, int(params.get("days", "7"))))
            except ValueError:
                return _err(422, "invalid_request", "days는 1~30 사이 숫자여야 합니다")
            return _json(200, {"days": days, "deploys": deploys_for(tid, days)})

        if path.startswith("/v1/leave") or path in ("/v1/me", "/v1/deploys"):
            return _err(405, "method_not_allowed")
        return _err(404, "not_found")
    except ValueError as exc:
        return _err(422, "invalid_request", str(exc))
