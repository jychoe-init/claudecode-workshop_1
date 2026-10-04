#!/usr/bin/env python3
"""lab3 · 프롬프트 점검·배포 검사.  python3 tools/check_lab3.py

워크시트, 사용량 기록, 지시문 감사 결과 반영, .gitignore, README, 커밋을 봅니다.
"""

import csv
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from checklib import (BLANK, ROOT, Report, Worksheet, check_decisions, check_predictions,  # noqa: E402
                      check_reflection, filled, git, read, scan_tokens)

IGNORE_NEEDED = {
    "usage.csv": ["usage.csv"],
    ".usage/": [".usage", ".usage/", ".usage/*"],
    ".claude/settings.local.json": [".claude/settings.local.json", "settings.local.json", "*.local.json"],
    ".env": [".env", ".env*", "*.env"],
}
NEVER_TRACKED = [".env", ".claude/settings.local.json", "usage.csv"]


def audit_findings():
    """CLAUDE.md에 심어 둔 결함 3종이 남아 있는지."""
    claude = read(ROOT / "CLAUDE.md")
    style = read(ROOT / ".claude" / "rules" / "code-style.md")
    try:
        scripts = (json.loads(read(ROOT / "package.json") or "{}").get("scripts") or {})
    except ValueError:
        scripts = {}
    return {
        "예전 모델용 지시 (<thinking> 강제, IMPORTANT/CRITICAL)":
            "<thinking>" in claude or ("IMPORTANT" in claude and "CRITICAL" in claude),
        "파일 간 모순 (CLAUDE.md 탭 ↔ rules 스페이스 2칸)":
            bool(re.search(r"탭|Tab", claude)) and bool(re.search(r"스페이스\s*2|2\s*칸", style)),
        "없는 참조 (npm run test:unit)":
            "test:unit" in claude and "test:unit" not in scripts,
    }


def main():
    rep = Report("lab3 · 프롬프트 점검·배포 검사")
    ws = Worksheet(3)
    if not ws.exists():
        rep.fail("워크시트가 없습니다", "docs/worksheets/lab3.md")
        return rep.finish()

    check_decisions(rep, ws, ["D1", "D2", "D3"])
    check_predictions(rep, ws, ["P1", "P2"])

    final = ws.section("## 3.")
    code = re.findall(r"```[a-z]*\n(.*?)```", final, re.S)
    rep.check(code and filled(code[0]) and len(code[0].strip()) > 20, "워크시트: 채택한 변경만 반영한 최종 프롬프트",
              "워크시트 3번에 최종 프롬프트를 코드 블록으로 붙이세요", ws.where)

    # 사용량 비교
    rows = []
    try:
        with open(ROOT / "usage.csv", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
    except OSError:
        pass
    labels = {r.get("label") for r in rows}
    rep.check(len(rows) >= 2 and len(labels) >= 2, "usage.csv: 원본·개선본 %d행" % len(rows),
              "usage.csv에 서로 다른 라벨로 2행 이상이 필요합니다 (원본, 개선본)",
              "tools/usage_log.sh -m <모델> original \"...\"")
    models = {r.get("model") for r in rows if r.get("model")}
    if len(rows) >= 2:
        rep.check(len(models) <= 1, "같은 모델로 비교함",
                  "원본과 개선본을 서로 다른 모델로 실행했습니다 (%s)" % ", ".join(sorted(models)), "usage.csv",
                  level="warn")

    # 지시문 감사 반영
    found = audit_findings()
    fixed = [k for k, remains in found.items() if not remains]
    rep.check(fixed, "감사 결과 반영: %s" % (", ".join(fixed) or "-"),
              "CLAUDE.md의 감사 결과를 아직 하나도 고치지 않았습니다 (/doctor prompt-audit)", "CLAUDE.md")
    for k, remains in found.items():
        if remains and fixed:
            rep.warn("남은 감사 항목: %s" % k, "CLAUDE.md")

    # .gitignore
    gi = [l.strip() for l in read(ROOT / ".gitignore").splitlines() if l.strip() and not l.startswith("#")]
    missing = [k for k, pats in IGNORE_NEEDED.items() if not any(p in gi for p in pats)]
    rep.check(not missing, ".gitignore: 개인 파일과 실행 기록 제외",
              ".gitignore에 빠진 항목: %s" % ", ".join(missing), ".gitignore")

    # README
    readme = read(ROOT / "README.md")
    rep.check(readme and BLANK not in readme, "README: 세 줄 채움", "README.md에 ____ 이 남아 있습니다", "README.md")

    # git
    res = git("rev-list", "--count", "superlab-start..HEAD")
    if res is None or res.returncode != 0:
        rep.warn("시작 지점(superlab-start 태그)을 찾지 못해 커밋 수를 셀 수 없습니다", "git log --oneline")
    else:
        n = int(res.stdout.strip() or 0)
        rep.check(n >= 1, "실습 후 커밋 %d개" % n, "아직 커밋하지 않았습니다", "git status")
    res = git("ls-files")
    tracked = set(res.stdout.split()) if res and res.returncode == 0 else set()
    leaked = [p for p in NEVER_TRACKED if p in tracked]
    rep.check(not leaked, "개인 파일이 커밋에 들어가지 않음",
              "커밋에 들어가면 안 되는 파일이 있습니다: %s (git rm --cached 로 빼세요)" % ", ".join(leaked), "git ls-files")
    res = git("status", "--porcelain")
    if res and res.returncode == 0:
        rep.check(not res.stdout.strip(), "작업 트리 깨끗함 (모두 커밋)",
                  "커밋하지 않은 변경이 있습니다", "git status", level="warn")

    check_reflection(rep, ws, heading="## 5.")
    scan_tokens(rep)
    return rep.finish()


if __name__ == "__main__":
    sys.exit(main())
