#!/usr/bin/env python3
"""킷 검증 (강사·개발용). Claude 로그인 없이 돌아갑니다.

  python3 ch4/dev/validate_kit.py           정적 검사 + 새 프로젝트 생성 + 완성 예시 적용 + 음성 테스트
  python3 ch4/dev/validate_kit.py --static  정적 검사만

임시 HOME에서 setup.sh --local 로 프로젝트를 만들고, 로컬 사내 API 서버(포트 8787)를 띄워 확인합니다.
"""

import argparse
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

CH4 = Path(__file__).resolve().parent.parent
KIT = CH4 / "kit"
SOL = CH4 / "solutions"
TOKEN_RE = re.compile(r"wk-\d{2}-[0-9a-f]{12}")
results = []


def check(name, cond, detail=""):
    results.append((name, bool(cond), detail))
    return bool(cond)


def frontmatter(text):
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    data = {}
    for line in text[3:end].splitlines():
        m = re.match(r"^([A-Za-z0-9_-]+)\s*:\s*(.*)$", line)
        if m and not line.lstrip().startswith("#"):
            data[m.group(1)] = m.group(2).strip().strip("\"'")
    return data


# ───────────────────────────── 정적 검사 ─────────────────────────────
def static():
    # 파이썬, 셸 문법
    for p in list(CH4.rglob("*.py")):
        if "__pycache__" in p.parts or "build" in p.parts:
            continue
        try:
            compile(p.read_text(encoding="utf-8"), str(p), "exec")
            ok = True
        except SyntaxError as e:
            ok = False
            print(e)
        check("py 문법 %s" % p.relative_to(CH4), ok)
    for p in [CH4 / "setup.sh", CH4 / "infra" / "deploy.sh", KIT / "bin" / "lab", KIT / "tools" / "usage_log.sh"]:
        r = subprocess.run(["bash", "-n", str(p)], capture_output=True, text=True)
        check("bash 문법 %s" % p.relative_to(CH4), r.returncode == 0, r.stderr)

    # JSON
    for p in list(CH4.rglob("*.json")) + list(CH4.rglob(".mcp.json")):
        try:
            json.loads(p.read_text(encoding="utf-8"))
            ok = True
        except ValueError as e:
            ok = False
            print(p, e)
        check("JSON %s" % p.relative_to(CH4), ok)

    # 스킬 머리말
    for p in sorted(list((KIT / ".claude" / "skills").glob("*/SKILL.md")) + list(SOL.rglob("SKILL.md"))):
        fm = frontmatter(p.read_text(encoding="utf-8"))
        check("스킬 name=폴더 %s" % p.relative_to(CH4), fm.get("name") == p.parent.name, fm.get("name"))
        check("스킬 description %s" % p.relative_to(CH4), len(fm.get("description", "")) >= 15)

    # 주입 명령은 의도한 스킬에만
    inj_ok = {"standup", "weekly-report"}
    for p in (KIT / ".claude" / "skills").glob("*/SKILL.md"):
        has = bool(re.search(r"!`[^`]+`", p.read_text(encoding="utf-8")))
        check("주입 명령 위치 %s" % p.parent.name, has == (p.parent.name in inj_ok))

    # lab1 표시, lab2 빈칸
    for n in ("meeting-notes", "weekly-report", "standup"):
        d = KIT / ".claude" / "skills" / n
        check("lab1 '바꿀 곳' 표시 %s" % n, all("<!-- 바꿀 곳" in (d / f).read_text() for f in ("SKILL.md", "template.md")))
    for n in ("leave-request", "deploy-report"):
        check("lab2 빈칸 %s" % n, "____" in (KIT / ".claude" / "skills" / n / "SKILL.md").read_text())

    # 코치
    agent = (KIT / ".claude" / "agents" / "workshop-coach.md").read_text(encoding="utf-8")
    fm = frontmatter(agent)
    check("코치 name", fm.get("name") == "workshop-coach")
    check("코치 tools 읽기 전용", set(t.strip() for t in fm.get("tools", "").split(",")) == {"Read", "Grep", "Glob", "Bash"})
    lab = (KIT / "bin" / "lab").read_text()
    for flag in ("--agent workshop-coach", "--permission-mode dontAsk", "--strict-mcp-config", "--disallowedTools Edit Write NotebookEdit"):
        check("bin/lab coach %s" % flag, flag in lab)
    for n in (1, 2, 3):
        check("코치 진행표 lab%d" % n, (KIT / "docs" / "coach" / ("lab%d.md" % n)).exists())
        ws = (KIT / "docs" / "worksheets" / ("lab%d.md" % n)).read_text()
        check("워크시트 lab%d 결정 D1~D3" % n, all("| D%d |" % i in ws for i in (1, 2, 3)))

    # 설정 기준선
    st = json.loads((KIT / ".claude" / "settings.json").read_text())["permissions"]
    for rule in ("Bash(curl *)", "Read(~/.config/superlab/**)", "Read(./.env)"):
        check("settings deny %s" % rule, rule in st["deny"])
    check("settings allow 검사 스크립트", "Bash(python3 tools/check_lab*)" in st["allow"])

    # CLAUDE.md 결함 3종 유지
    cm = (KIT / "CLAUDE.md").read_text()
    check("CLAUDE.md 결함: <thinking> 강제", "<thinking>" in cm)
    check("CLAUDE.md 결함: 탭 ↔ 스페이스 2칸", "탭" in cm and "스페이스 2칸" in (KIT / ".claude" / "rules" / "code-style.md").read_text())
    check("CLAUDE.md 결함: test:unit", "test:unit" in cm and "test:unit" not in (KIT / "package.json").read_text())
    check("CLAUDE.md 잔존 표기 없음 (presets, Slack)", not re.search(r"presets|Slack|slack_mock|hr_mcp", cm))

    # 킷 전체에서 사라진 것들
    stale = []
    for p in KIT.rglob("*"):
        if p.is_file() and p.suffix in (".md", ".py", ".json", ".sh", ".txt", ""):
            t = p.read_text(encoding="utf-8", errors="ignore")
            if re.search(r"slack_mock|hr_mcp|presets/|SLACK_", t):
                stale.append(str(p.relative_to(CH4)))
    check("킷에 예전 구성 언급 없음", not stale, stale[:3])

    # prompt-coach 근거 자료
    ref = KIT / ".claude" / "skills" / "prompt-coach" / "references"
    for name in ("best-practices.md", "models/opus-5-5.md", "models/sonnet-5-5.md", "models/haiku-4-5.md", "models/fable-5-1.md"):
        t = (ref / name).read_text()
        check("근거 자료 %s 기준일" % name, "기준일: 2026-10-04" in t)
        bad = re.findall(r"\]\((?!https://)[^)]+\)", t)
        check("근거 자료 %s 링크 형식" % name, not bad, bad[:2])

    # 토큰 문자열 (smoke의 고정 무효 토큰 형식 제외)
    hits = []
    for p in CH4.parent.rglob("*"):
        if ".git" in p.parts or not p.is_file() or p.name == ".secret":
            continue
        t = p.read_text(encoding="utf-8", errors="ignore")
        for m in TOKEN_RE.finditer(t):
            if not m.group(0).endswith("000000000000"):
                hits.append("%s:%s" % (p.relative_to(CH4.parent), m.group(0)[:6]))
    check("저장소에 토큰 문자열 없음", not hits, hits[:3])
    check(".gitignore에 infra/.secret", "ch4/infra/.secret" in (CH4.parent / ".gitignore").read_text())


# ───────────────────────────── 동적 검사 ─────────────────────────────
def run(cmd, cwd, env, timeout=60):
    return subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True, timeout=timeout, shell=isinstance(cmd, str))


def port_open(port):
    s = socket.socket()
    s.settimeout(0.5)
    try:
        return s.connect_ex(("127.0.0.1", port)) == 0
    finally:
        s.close()


def dynamic():
    tmp = Path(tempfile.mkdtemp(prefix="superlab-validate-"))
    env = dict(os.environ, HOME=str(tmp), SUPERLAB_CONFIG_DIR=str(tmp / ".config" / "superlab"),
               GIT_AUTHOR_NAME="v", GIT_AUTHOR_EMAIL="v@example.com",
               GIT_COMMITTER_NAME="v", GIT_COMMITTER_EMAIL="v@example.com")
    env.pop("LAB_TOKEN", None)
    env.pop("LAB_API_BASE", None)
    proj = tmp / "claude-lab" / "superlab"
    server = None
    try:
        r = run(["bash", str(CH4 / "setup.sh"), "--local", str(proj)], tmp, env, timeout=120)
        check("setup.sh --local 성공", r.returncode == 0, r.stdout[-400:] + r.stderr[-400:])
        check("setup 연결 확인 통과", "사내 API 응답" in r.stdout, r.stdout[-300:])
        conf = tmp / ".config" / "superlab"
        check("토큰 파일 권한 600", (conf / "token").exists() and oct((conf / "token").stat().st_mode)[-3:] == "600")
        check("프로젝트에 solutions·infra·dev 없음", not any((proj / d).exists() for d in ("solutions", "infra", "dev")))
        r = run(["git", "tag", "--list", "superlab-start"], proj, env)
        check("시작 태그 superlab-start", r.stdout.strip() == "superlab-start")
        r = run(["git", "status", "--porcelain"], proj, env)
        check("setup 직후 추적 안 되는 파일은 settings.local.json뿐", r.stdout.strip() == "?? .claude/settings.local.json", r.stdout)

        if port_open(8787):
            check("8787 포트 비어 있음 (다른 서버가 떠 있으면 검증 불가)", False)
            return
        server = subprocess.Popen([sys.executable, "tools/lab_server.py", "--quiet"], cwd=proj, env=env,
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(30):
            if port_open(8787):
                break
            time.sleep(0.1)

        # 빈 상태: 세 검사 모두 실패해야 함
        for n in (1, 2, 3):
            r = run([sys.executable, "tools/check_lab%d.py" % n], proj, env)
            check("빈 상태 check_lab%d 실패" % n, r.returncode == 1)

        # 완성 예시 적용
        sk = proj / ".claude" / "skills"
        shutil.rmtree(sk / "meeting-notes")
        shutil.copytree(SOL / "lab1" / "skills" / "meeting-notes", sk / "meeting-notes")
        for n in ("leave-request", "deploy-report"):
            shutil.rmtree(sk / n)
            shutil.copytree(SOL / "lab2" / "skills" / n, sk / n)
        shutil.copy(SOL / "lab2" / "settings.json", proj / ".claude" / "settings.json")
        for n in (1, 2, 3):
            shutil.copy(SOL / ("lab%d" % n) / "worksheets" / ("lab%d.md" % n), proj / "docs" / "worksheets")

        r = run([sys.executable, "tools/check_lab1.py"], proj, env)
        check("완성 예시 check_lab1 통과", r.returncode == 0, r.stdout[-600:])

        r = run([sys.executable, "tools/hr_fetch.py", "request", "--start", "2026-10-14", "--reason", "검증"], proj, env)
        check("hr_fetch request 201", r.returncode == 0, r.stderr)
        r = run([sys.executable, "tools/check_lab2.py"], proj, env)
        check("완성 예시 check_lab2 통과", r.returncode == 0, r.stdout[-800:])
        check("check_lab2 출력에 토큰 없음", not TOKEN_RE.search(r.stdout + r.stderr))

        # lab3: 사용량 2행(가짜), 파일, 커밋
        (proj / "usage.csv").write_text("timestamp,label,model,total_cost_usd\n2026-10-04T10:00:00,original,claude-sonnet-5-5,0.02\n"
                                        "2026-10-04T10:01:00,improved,claude-sonnet-5-5,0.01\n", encoding="utf-8")
        for f in ("CLAUDE.md", ".gitignore", "README.md"):
            shutil.copy(SOL / "lab3" / "files" / f, proj / f)
        run("git add -A && git commit -q -m 'feat: superlab kit'", proj, env)
        r = run([sys.executable, "tools/check_lab3.py"], proj, env)
        check("완성 예시 check_lab3 통과", r.returncode == 0, r.stdout[-800:])
        r = run(["git", "ls-files"], proj, env)
        check("커밋에 개인 파일 없음", not re.search(r"^(\.env|usage\.csv|\.claude/settings\.local\.json)$", r.stdout, re.M))

        # 음성 테스트
        settings = proj / ".claude" / "settings.json"
        base = settings.read_text()
        data = json.loads(base)
        data["permissions"]["allow"].append("Bash(python3 tools/hr_fetch.py *)")
        data["permissions"]["ask"] = [a for a in data["permissions"]["ask"] if "hr_fetch" not in a]
        settings.write_text(json.dumps(data))
        r = run([sys.executable, "tools/check_lab2.py"], proj, env)
        check("음성: settings에 넓은 allow → check_lab2 실패", r.returncode == 1 and "묻지 않고 실행" in r.stdout, r.stdout[-400:])
        settings.write_text(base)

        dr = sk / "deploy-report" / "SKILL.md"
        dr_text = dr.read_text()
        ws2 = proj / "docs" / "worksheets" / "lab2.md"
        ws2_text = ws2.read_text()
        ws2.write_text(ws2_text.replace("내 스킬 이름: leave-request", "내 스킬 이름: deploy-report")
                       .replace("| B Bash |", "| A 주입 |"))
        dr.write_text(re.sub(r"^allowed-tools:.*\n", "", dr_text, flags=re.M))
        r = run([sys.executable, "tools/check_lab2.py"], proj, env)
        check("음성: 주입 명령 허용 없음 → check_lab2 실패 (P1)", r.returncode == 1 and "중단" in r.stdout, r.stdout[-400:])
        dr.write_text(dr_text)
        r = run([sys.executable, "tools/check_lab2.py"], proj, env)
        check("주입 + allowed-tools → check_lab2 통과", r.returncode == 0, r.stdout[-600:])
        ws2.write_text(ws2_text)

        tpl = sk / "meeting-notes" / "template.md"
        tpl_text = tpl.read_text()
        tpl.write_text("<!-- 바꿀 곳: 남김 -->\n" + tpl_text)
        r = run([sys.executable, "tools/check_lab1.py"], proj, env)
        check("음성: '바꿀 곳' 표시 남김 → check_lab1 실패", r.returncode == 1)
        tpl.write_text(tpl_text)

        tok = (conf / "token").read_text().strip()
        leak = proj / "docs" / "notes.md"
        leak.write_text("메모 " + tok + "\n")
        r = run([sys.executable, "tools/check_lab1.py"], proj, env)
        check("음성: 토큰 유출 → check_lab1 실패", r.returncode == 1 and "토큰 문자열" in r.stdout)
        check("음성: 검사 출력은 토큰을 가림", tok not in r.stdout)
        leak.unlink()

        r = run(["bash", "-c", "LAB_TOKEN=wk-00-bad python3 tools/hr_fetch.py me"], proj, env)
        check("잘못된 토큰 → hr_fetch 종료 코드 1, 401", r.returncode == 1 and "401" in r.stderr, r.stderr)

        r = run(["bash", "bin/lab"], proj, env)
        check("bin/lab 도움말", r.returncode == 0 and "coach" in r.stdout)
    finally:
        if server:
            server.terminate()
            server.wait(timeout=5)
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--static", action="store_true")
    args = ap.parse_args()
    static()
    if not args.static:
        dynamic()
    failed = [r for r in results if not r[1]]
    for name, ok, detail in results:
        if not ok:
            print("✘ %s  %s" % (name, str(detail)[:600]))
    print("\n%d개 중 %d개 통과" % (len(results), len(results) - len(failed)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
