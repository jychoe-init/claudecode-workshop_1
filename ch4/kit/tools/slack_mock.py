#!/usr/bin/env python3
"""Slack 수신기 mock (중계기).

Claude Code의 http 훅은 이벤트 JSON을 그대로 POST합니다. 실제 Slack Incoming Webhook은
{"text": "..."} 형식만 받으므로 바로 보낼 수 없습니다. 이 스크립트가 중간에서 받아
Stop 훅의 last_assistant_message를 Slack 메시지처럼 보여 주고, 원하면 실제 Slack으로 변환해 전달합니다.

사용법
  python3 tools/slack_mock.py                      # 수신만 (기본 127.0.0.1:8787)
  python3 tools/slack_mock.py --port 8790          # 포트 변경 (또는 SLACK_MOCK_PORT)
  SLACK_WEBHOOK_URL=https://hooks.slack.com/services/... \
    python3 tools/slack_mock.py --forward          # 실제 Slack으로 {"text"} 변환 전달

응답 규칙
  http 훅은 "2xx + 빈 본문"을 성공으로 처리합니다. 2xx라도 평문 본문(예: Slack의 "ok")은
  오류로 취급되므로, 이 수신기는 항상 빈 본문으로 200을 돌려줍니다.

표준 라이브러리만 사용합니다.
"""

import argparse
import datetime as dt
import json
import os
import sys
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INBOX = ROOT / ".slack_inbox.jsonl"
CHANNEL = os.environ.get("SLACK_MOCK_CHANNEL", "#team-standup")


def forward_to_slack(url: str, text: str) -> str:
    body = json.dumps({"text": text}).encode("utf-8")
    req = urllib.request.Request(
        url, data=body, headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return f"Slack 전달 {resp.status}"
    except urllib.error.HTTPError as err:
        return f"Slack 전달 실패 {err.code}: {err.read().decode('utf-8', 'replace')[:200]}"
    except (urllib.error.URLError, TimeoutError) as err:
        return f"Slack 전달 실패: {err}"


class Handler(BaseHTTPRequestHandler):
    server_version = "SlackMock/1.0"

    def do_GET(self):
        body = "slack mock is running. Claude Code http 훅을 POST로 보내세요.\n".encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b""
        try:
            event = json.loads(raw.decode("utf-8") or "{}")
        except (UnicodeDecodeError, json.JSONDecodeError):
            event = {"_unparsed": raw[:500].decode("utf-8", "replace")}

        text = event.get("last_assistant_message") or ""
        now = dt.datetime.now().strftime("%H:%M:%S")
        record = {
            "received_at": dt.datetime.now().isoformat(timespec="seconds"),
            "path": self.path,
            "hook_event_name": event.get("hook_event_name"),
            "session_id": event.get("session_id"),
            "text": text,
        }
        with INBOX.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

        line = "─" * 60
        print(f"\n{line}\n{CHANNEL}  ←  Claude Code ({event.get('hook_event_name') or '?'} 훅)  {now}\n{line}")
        if text:
            print(text)
        else:
            keys = ", ".join(sorted(event.keys())) or "(빈 본문)"
            print(f"[last_assistant_message 없음] 받은 필드: {keys}")
        if self.server.forward_url and text:
            print(f"[{forward_to_slack(self.server.forward_url, text)}]")
        print(line, flush=True)

        # http 훅 성공 조건: 2xx + 빈 본문
        self.send_response(200)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def log_message(self, fmt, *args):  # 기본 접속 로그는 숨김
        pass


def main() -> int:
    parser = argparse.ArgumentParser(description="Claude Code http 훅용 Slack mock 수신기")
    parser.add_argument("--port", type=int, default=int(os.environ.get("SLACK_MOCK_PORT", "8787")))
    parser.add_argument("--forward", action="store_true", help="SLACK_WEBHOOK_URL로 {text} 변환 전달")
    args = parser.parse_args()

    forward_url = None
    if args.forward:
        forward_url = os.environ.get("SLACK_WEBHOOK_URL")
        if not forward_url:
            print("--forward에는 SLACK_WEBHOOK_URL 환경변수가 필요합니다.", file=sys.stderr)
            return 2

    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    server.forward_url = forward_url
    mode = "수신 + Slack 전달" if forward_url else "수신만"
    print(f"slack mock 대기 중: http://localhost:{args.port}/  ({mode}, 기록: {INBOX.name})", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n종료합니다.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
