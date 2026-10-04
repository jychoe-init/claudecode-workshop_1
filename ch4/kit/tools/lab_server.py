#!/usr/bin/env python3
"""사내 API 로컬 대체 서버 (클라우드 API와 같은 labapi/core.py를 씁니다).

  python3 tools/lab_server.py                 127.0.0.1:8787 에서 실행
  python3 tools/lab_server.py --issue 3       로컬 비밀값으로 토큰 3개 출력하고 종료
  python3 tools/lab_server.py --port 8790 --rate 60

클라우드 API가 막힌 환경에서는 이 서버를 켜 두고, ~/.config/superlab/api_base 를
http://127.0.0.1:8787 로 두면(setup.sh 로컬 모드) 실습이 그대로 진행됩니다.
"""

import argparse
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from labapi import core  # noqa: E402

LOCAL_SECRET = "superlab-local-secret"


class Handler(BaseHTTPRequestHandler):
    server_version = "SuperlabLocalAPI/1.0"

    def _serve(self):
        path, _, query = self.path.partition("?")
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length) if length else b""
        headers = {k.lower(): v for k, v in self.headers.items()}
        status, out_headers, out = core.handle(self.command, path, query, headers, body,
                                               self.server.secret, self.server.limiter, self.server.store,
                                               log=self.server.log)
        self.send_response(status)
        for k, v in out_headers.items():
            self.send_header(k, v)
        self.send_header("Content-Length", str(len(out)))
        self.end_headers()
        self.wfile.write(out)

    do_GET = do_POST = do_PUT = do_DELETE = do_PATCH = _serve

    def log_message(self, fmt, *args):
        pass


def main():
    ap = argparse.ArgumentParser(description="슈퍼랩 사내 API 로컬 서버")
    ap.add_argument("--port", type=int, default=int(os.environ.get("LAB_SERVER_PORT", "8787")))
    ap.add_argument("--secret", default=os.environ.get("LAB_TOKEN_SECRET", LOCAL_SECRET))
    ap.add_argument("--rate", type=int, default=core.DEFAULT_RATE_LIMIT, help="토큰당 분당 호출 한도")
    ap.add_argument("--issue", type=int, metavar="N", help="토큰 N개를 출력하고 종료")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    if args.issue:
        for seat in range(1, args.issue + 1):
            print(core.token_for(seat, args.secret))
        return 0

    srv = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    srv.secret = args.secret
    srv.limiter = core.MemoryLimiter(args.rate)
    srv.store = core.MemoryStore()
    srv.log = None if args.quiet else (lambda e: print(json.dumps(e, ensure_ascii=False), flush=True))
    print("사내 API 로컬 서버: http://127.0.0.1:%d/  (문서 /docs, 분당 %d회)" % (args.port, args.rate), flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\n종료합니다.")
    finally:
        srv.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
