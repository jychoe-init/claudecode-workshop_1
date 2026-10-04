#!/usr/bin/env python3
"""참가자 토큰을 오프라인으로 만듭니다 (저장소에 넣지 마세요).

  python3 ch4/infra/issue_tokens.py --count 80 --out ~/superlab-tokens.csv
  비밀값: --secret → LAB_TOKEN_SECRET 환경변수 → ch4/infra/.secret

CSV 열: seat, token. 좌석 번호를 참가자 카드에 적어 나눠 주고, 토큰은 개인에게만 전달합니다.
"""

import argparse
import csv
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "kit"))
from labapi.core import token_for  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", type=int, default=80)
    ap.add_argument("--secret")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    secret = args.secret or os.environ.get("LAB_TOKEN_SECRET") or (
        (HERE / ".secret").read_text().strip() if (HERE / ".secret").exists() else "")
    if len(secret) < 16:
        print("비밀값이 없거나 너무 짧습니다 (--secret, LAB_TOKEN_SECRET, ch4/infra/.secret)", file=sys.stderr)
        return 2
    if not 1 <= args.count <= 99:
        print("--count는 1~99 사이여야 합니다", file=sys.stderr)
        return 2
    out = Path(os.path.expanduser(args.out))
    try:
        out.resolve().relative_to(HERE.parent.parent.resolve())
        print("경고: 저장소 안에 토큰 파일을 만들고 있습니다. 커밋하지 마세요.", file=sys.stderr)
    except ValueError:
        pass
    old = os.umask(0o077)
    try:
        with out.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["seat", "token"])
            for seat in range(1, args.count + 1):
                w.writerow(["%02d" % seat, token_for(seat, secret)])
    finally:
        os.umask(old)
    print("토큰 %d개를 %s 에 썼습니다." % (args.count, out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
