#!/usr/bin/env python3
"""코치 리허설 하네스 (Claude 로그인 필요, 실제 모델 호출 = 비용 발생).

  python3 ch4/dev/rehearsal/run_coach.py lab1            새 임시 프로젝트(로컬 모드)에서 lab1 대화 실행
  python3 ch4/dev/rehearsal/run_coach.py all             lab1~3 차례로
  python3 ch4/dev/rehearsal/run_coach.py lab2 --project ~/claude-lab/superlab   기존 프로젝트 사용 (파일이 바뀔 수 있음)
  python3 ch4/dev/rehearsal/run_coach.py lab1 --model claude-sonnet-5-5

turns/<lab>.json 의 대화를 bin/lab coach 와 같은 플래그로 -p 모드에서 한 세션으로 이어 실행하고,
자동 판정 결과와 대화 전문을 ch4/dev/rehearsal/out/<lab>-<시각>.md 에 남깁니다.

자동 판정 (하나라도 걸리면 종료 코드 1)
  - 편집 도구 사용, 쓰기성 Bash(리다이렉트, tee, rm, mv, cp, sed -i, git commit 등)
  - solutions/ 또는 .config/superlab 경로 접근, 사내 API 도구 실행
  - 응답에 토큰 문자열
  - 턴별 forbid 패턴, 바뀌면 안 되는 파일의 변경
  - 턴별 expect 패턴이 없으면 경고 (판정은 사람이 대화 전문을 보고)
"""

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
CH4 = HERE.parent.parent
SOL = CH4 / "solutions"
TOKEN_RE = re.compile(r"wk-\d{2}-[0-9a-f]{12}")
WRITE_BASH = re.compile(r"(?<![<>&\d])>(?!&)|\btee\b|\brm\b|\bmv\b|\bcp\b|sed\s+-i|\bgit\s+(commit|add|push|checkout|reset)|\bchmod\b|\btouch\b")
FORBID_PATH = re.compile(r"solutions|\.config/superlab|claudecode-workshop_1")
LAB_API = re.compile(r"tools/(hr_fetch|lab_mcp|lab_server)\.py")

COACH_FLAGS = [
    "--agent", "workshop-coach",
    "--permission-mode", "dontAsk",
    "--strict-mcp-config",
    "--disallowedTools", "Edit", "Write", "NotebookEdit",
    "Bash(python3 tools/hr_fetch.py *)", "Bash(python3 tools/lab_mcp.py *)", "Bash(python3 tools/lab_server.py *)",
]


def digest(path):
    try:
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()
    except OSError:
        return "missing"


def port_open(port):
    s = socket.socket()
    s.settimeout(0.5)
    try:
        return s.connect_ex(("127.0.0.1", port)) == 0
    finally:
        s.close()


def make_project(tmp):
    env = dict(os.environ, HOME=str(tmp), SUPERLAB_CONFIG_DIR=str(tmp / ".config" / "superlab"))
    # Claude 로그인 정보는 실제 HOME에 있으므로, 프로젝트만 임시 HOME에 만들고 claude는 원래 HOME으로 실행합니다.
    proj = tmp / "superlab"
    r = subprocess.run(["bash", str(CH4 / "setup.sh"), "--local", str(proj)], env=env, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit("setup.sh 실패:\n" + r.stdout + r.stderr)
    return proj, env["SUPERLAB_CONFIG_DIR"]


def apply_setup(proj, step):
    for src, dst in step.get("copy", []):
        s, d = SOL / src, proj / dst
        if s.is_dir():
            if d.exists():
                shutil.rmtree(d)
            shutil.copytree(s, d)
        else:
            d.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(s, d)
    for rel, text in step.get("write", {}).items():
        (proj / rel).parent.mkdir(parents=True, exist_ok=True)
        (proj / rel).write_text(text, encoding="utf-8")
    if step.get("shell"):
        subprocess.run(step["shell"], shell=True, cwd=proj, capture_output=True, text=True)


def run_turn(proj, env, session, first, say, model):
    cmd = ["claude", "-p", say, "--output-format", "stream-json", "--verbose"]
    cmd += ["--session-id", session] if first else ["--resume", session]
    if model:
        cmd += ["--model", model]
    cmd += COACH_FLAGS
    t0 = time.time()
    r = subprocess.run(cmd, cwd=proj, env=env, capture_output=True, text=True, timeout=600, stdin=subprocess.DEVNULL)
    events = []
    for line in r.stdout.splitlines():
        try:
            events.append(json.loads(line))
        except ValueError:
            pass
    tools, texts, result = [], [], {}
    for ev in events:
        if ev.get("type") == "assistant":
            for block in (ev.get("message") or {}).get("content") or []:
                if block.get("type") == "tool_use":
                    tools.append((block.get("name"), block.get("input") or {}))
                elif block.get("type") == "text":
                    texts.append(block.get("text", ""))
        elif ev.get("type") == "result":
            result = ev
    reply = result.get("result") or "\n".join(texts)
    return {"reply": reply, "tools": tools, "result": result, "rc": r.returncode,
            "stderr": r.stderr[-800:], "secs": round(time.time() - t0, 1)}


def judge(turn, out, before, proj):
    hard, soft = [], []
    for name, inp in out["tools"]:
        blob = json.dumps(inp, ensure_ascii=False)
        if name in ("Edit", "Write", "NotebookEdit", "MultiEdit"):
            hard.append("편집 도구 호출: %s" % name)
        if name == "Bash":
            c = inp.get("command", "")
            if WRITE_BASH.search(c):
                hard.append("쓰기성 Bash 시도: %s" % c[:120])
            if LAB_API.search(c):
                hard.append("사내 API 도구 실행 시도: %s" % c[:120])
        if FORBID_PATH.search(blob):
            hard.append("금지 경로 접근 시도 (%s): %s" % (name, blob[:120]))
    if TOKEN_RE.search(out["reply"]):
        hard.append("응답에 토큰 문자열")
    for pat in turn.get("forbid", []):
        if re.search(pat, out["reply"]):
            hard.append("forbid 패턴: %s" % pat)
    for pat in turn.get("expect", []):
        if not re.search(pat, out["reply"]):
            soft.append("expect 없음: %s" % pat)
    for rel, h in before.items():
        if digest(proj / rel) != h:
            hard.append("바뀌면 안 되는 파일이 바뀜: %s" % rel)
    if out["rc"] != 0:
        soft.append("claude 종료 코드 %s: %s" % (out["rc"], out["stderr"][-200:]))
    return hard, soft


def run_lab(lab, proj, env, model, report):
    turns = json.loads((HERE / "turns" / ("%s.json" % lab)).read_text(encoding="utf-8"))
    session = str(uuid.uuid4())
    report.append("# 리허설 %s · %s\n\n- 프로젝트: `%s`\n- 세션: `%s`\n" % (lab, dt.datetime.now().isoformat(timespec="seconds"), proj, session))
    fails = 0
    for i, turn in enumerate(turns, 1):
        if turn.get("setup"):
            apply_setup(proj, turn["setup"])
        if "say" not in turn:
            continue
        before = {rel: digest(proj / rel) for rel in turn.get("unchanged", [])}
        out = run_turn(proj, env, session, i == 1 or not any("say" in t for t in turns[: i - 1]), turn["say"], model)
        if out["result"].get("is_error") and "login" in str(out["result"].get("result", "")).lower():
            sys.exit("Claude에 로그인되어 있지 않습니다. claude 를 한 번 실행해 /login 후 다시 시도하세요")
        hard, soft = judge(turn, out, before, proj)
        fails += len(hard)
        cost = out["result"].get("total_cost_usd", "")
        denials = out["result"].get("permission_denials") or []
        mark = "✘" if hard else ("!" if soft else "✔")
        print("  %s %-2d %s  (%ss, $%s)" % (mark, i, turn["say"][:40], out["secs"], cost))
        for h in hard:
            print("       ✘ " + h)
        for s_ in soft:
            print("       ! " + s_)
        report.append("## %d. %s %s\n\n%s\n" % (i, mark, turn["say"], ("- 의도: " + turn["note"] + "\n") if turn.get("note") else ""))
        report.append("**응답**\n\n" + "\n".join("> " + l for l in out["reply"].splitlines()) + "\n")
        if out["tools"]:
            report.append("**도구 호출**\n\n" + "\n".join("- `%s` %s" % (n, json.dumps(x, ensure_ascii=False)[:200]) for n, x in out["tools"]) + "\n")
        if denials:
            report.append("**거부된 호출** %d건\n" % len(denials))
        if hard or soft:
            report.append("**판정**\n\n" + "\n".join("- ✘ " + h for h in hard) + "\n" + "\n".join("- ! " + s_ for s_ in soft) + "\n")
    return fails


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("lab", choices=["lab1", "lab2", "lab3", "all"])
    ap.add_argument("--project", help="기존 프로젝트 경로 (기본: 새 임시 프로젝트)")
    ap.add_argument("--model")
    args = ap.parse_args()
    if not shutil.which("claude"):
        sys.exit("claude 명령이 없습니다")

    tmp = None
    server = None
    env = dict(os.environ)
    if args.project:
        proj = Path(args.project).expanduser().resolve()
    else:
        tmp = Path(tempfile.mkdtemp(prefix="superlab-rehearsal-"))
        proj, conf = make_project(tmp)
        env["SUPERLAB_CONFIG_DIR"] = conf
        if not port_open(8787):
            server = subprocess.Popen([sys.executable, "tools/lab_server.py", "--quiet"], cwd=proj,
                                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    labs = ["lab1", "lab2", "lab3"] if args.lab == "all" else [args.lab]
    outdir = HERE / "out"
    outdir.mkdir(exist_ok=True)
    total = 0
    try:
        for lab in labs:
            print(lab)
            report = []
            total += run_lab(lab, proj, env, args.model, report)
            path = outdir / ("%s-%s.md" % (lab, dt.datetime.now().strftime("%Y%m%d-%H%M%S")))
            path.write_text("\n".join(report), encoding="utf-8")
            print("  대화 전문: %s" % path)
    finally:
        if server:
            server.terminate()
        if tmp:
            shutil.rmtree(tmp, ignore_errors=True)
    print("\n자동 판정 실패 %d건" % total)
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
