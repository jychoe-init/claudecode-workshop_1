"""랩 검사 공용 함수 (check_lab1~3.py).

검사는 구조만 봅니다. 잘 썼는지는 참가자와 코치가 워크시트로 판단합니다.
표준 라이브러리만 씁니다 (Python 3.9+).
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BLANK = "____"
TOKEN_RE = re.compile(r"wk-\d{2}-[0-9a-f]{12}")
SKIP_DIRS = {".git", "node_modules", "__pycache__"}


# ───────────────────────────── 결과 출력 ─────────────────────────────
class Report:
    def __init__(self, title):
        self.title = title
        self.items = []

    def ok(self, msg):
        self.items.append(("ok", msg, ""))

    def warn(self, msg, where=""):
        self.items.append(("warn", msg, where))

    def fail(self, msg, where=""):
        self.items.append(("fail", msg, where))

    def check(self, cond, ok_msg, fail_msg, where="", level="fail"):
        if cond:
            self.ok(ok_msg)
        elif level == "warn":
            self.warn(fail_msg, where)
        else:
            self.fail(fail_msg, where)
        return bool(cond)

    def finish(self):
        mark = {"ok": "✔", "warn": "!", "fail": "✘"}
        print(self.title)
        for kind, msg, where in self.items:
            line = "  %s %s" % (mark[kind], msg)
            if where:
                line += "  → %s" % where
            print(line)
        n = {k: sum(1 for i in self.items if i[0] == k) for k in mark}
        print("\n결과: 통과 %d · 경고 %d · 실패 %d" % (n["ok"], n["warn"], n["fail"]))
        if n["fail"]:
            print("실패 항목부터 고치세요. 코치 터미널에서 '왜'라고 물으면 이유를 설명합니다.")
        return 1 if n["fail"] else 0


# ───────────────────────────── 파일 ─────────────────────────────
def rel(path):
    try:
        return str(Path(path).resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def read(path):
    try:
        return Path(path).read_text(encoding="utf-8")
    except OSError:
        return ""


def filled(value):
    v = (value or "").strip()
    return bool(v) and BLANK not in v


def line_of(text, needle):
    for i, line in enumerate(text.splitlines(), 1):
        if needle in line:
            return i
    return 0


# ───────────────────────────── 워크시트 ─────────────────────────────
def section(text, heading_prefix):
    """'## 2.' 처럼 시작하는 섹션의 본문 (다음 '## ' 전까지)."""
    lines = text.splitlines()
    out, inside = [], False
    for line in lines:
        if line.startswith("## "):
            if inside:
                break
            inside = line.startswith(heading_prefix)
            continue
        if inside:
            out.append(line)
    return "\n".join(out)


def table_rows(text):
    """마크다운 표의 행을 {첫 칸: [칸들]}로. 머리줄과 구분줄은 건너뜀."""
    rows = {}
    for line in text.splitlines():
        s = line.strip()
        if not s.startswith("|") or re.match(r"^\|\s*:?-{2,}", s):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if cells and re.match(r"^[A-Z]\d+$", cells[0]):
            rows[cells[0]] = cells
    return rows


def field(text, label):
    m = re.search(r"^%s\s*:\s*(.*)$" % re.escape(label), text, re.M)
    return m.group(1).strip() if m else ""


class Worksheet:
    def __init__(self, lab):
        self.path = ROOT / "docs" / "worksheets" / ("lab%d.md" % lab)
        self.text = read(self.path)
        self.where = rel(self.path)

    def exists(self):
        return bool(self.text)

    def rows(self, heading_prefix):
        return table_rows(section(self.text, heading_prefix))

    def field(self, label):
        return field(self.text, label)

    def section(self, heading_prefix):
        return section(self.text, heading_prefix)


def check_decisions(rep, ws, ids, heading="## 2."):
    rows = ws.rows(heading)
    missing = []
    for rid in ids:
        cells = rows.get(rid, [])
        choice = cells[-2] if len(cells) >= 2 else ""
        reason = cells[-1] if cells else ""
        if not (filled(choice) and filled(reason)):
            missing.append(rid)
    rep.check(not missing, "워크시트: 결정 %d개와 이유" % len(ids),
              "워크시트: 결정의 선택이나 이유가 비어 있습니다 (%s)" % ", ".join(missing),
              "%s:%d" % (ws.where, line_of(ws.text, "| %s |" % (missing[0] if missing else ids[0]))))
    return {rid: (rows.get(rid, ["", ""])[-2] if len(rows.get(rid, [])) >= 2 else "") for rid in ids}


def check_predictions(rep, ws, ids, heading="## 4.", need_actual=True):
    rows = ws.rows(heading)
    no_pred, no_actual = [], []
    for rid in ids:
        cells = rows.get(rid, [])
        pred = cells[-2] if len(cells) >= 2 else ""
        actual = cells[-1] if cells else ""
        if not filled(pred):
            no_pred.append(rid)
        elif need_actual and not filled(actual):
            no_actual.append(rid)
    rep.check(not no_pred, "워크시트: 예측 %d개" % len(ids),
              "워크시트: 실행 전 예측이 비어 있습니다 (%s)" % ", ".join(no_pred), ws.where)
    if not no_pred:
        rep.check(not no_actual, "워크시트: 예측마다 실제 결과",
                  "워크시트: 실행 후 실제 결과가 비어 있습니다 (%s)" % ", ".join(no_actual), ws.where)


def check_tracking(rep, ws, ids, heading="## 5."):
    rows = ws.rows(heading)
    missing = [rid for rid in ids if not filled(rows.get(rid, [""])[-1])]
    rep.check(not missing, "워크시트: 추적표 (결정 → 파일:줄)",
              "워크시트: 추적표가 비어 있습니다 (%s)" % ", ".join(missing), ws.where, level="warn")


def check_reflection(rep, ws, heading="## 6."):
    body = "\n".join(l for l in ws.section(heading).splitlines() if l.strip() and not l.startswith(">"))
    rep.check(filled(body), "워크시트: 반성 한 줄", "워크시트: 반성 한 줄이 비어 있습니다", ws.where, level="warn")


# ───────────────────────────── 스킬 ─────────────────────────────
def split_tools(value):
    """'Bash(a b) Read, mcp__x' → ['Bash(a b)', 'Read', 'mcp__x'] (괄호 안 공백 유지)."""
    out, buf, depth = [], "", 0
    for ch in value:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth = max(0, depth - 1)
        if depth == 0 and (ch.isspace() or ch == ","):
            if buf.strip():
                out.append(buf.strip())
            buf = ""
            continue
        buf += ch
    if buf.strip():
        out.append(buf.strip())
    return out


def frontmatter(text):
    """간단한 YAML 머리말 해석: key: value, key: 다음 줄 '- 항목' 목록, # 주석."""
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end < 0:
        return {}, text
    head, body = text[3:end], text[end + 4:]
    data, key = {}, None
    for raw in head.splitlines():
        line = raw.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        m = re.match(r"^([A-Za-z0-9_-]+)\s*:\s*(.*)$", line)
        if m:
            key, val = m.group(1), m.group(2).strip()
            if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
                val = val[1:-1]
            data[key] = val
            continue
        m = re.match(r"^\s+-\s+(.*)$", line)
        if m and key:
            item = m.group(1).strip().strip("\"'")
            prev = data.get(key)
            data[key] = (prev if isinstance(prev, list) else ([] if not prev else [prev])) + [item]
    return data, body


def tools_of(fm):
    v = fm.get("allowed-tools", "")
    if isinstance(v, list):
        out = []
        for item in v:
            out.extend(split_tools(item))
        return out
    return split_tools(v)


class Skill:
    def __init__(self, name):
        self.name = name
        self.dir = ROOT / ".claude" / "skills" / name
        self.path = self.dir / "SKILL.md"
        self.text = read(self.path)
        self.fm, self.body = frontmatter(self.text)
        self.where = rel(self.path)

    def exists(self):
        return bool(self.text)

    def manual(self):
        return str(self.fm.get("disable-model-invocation", "")).lower() == "true"

    def allowed(self):
        return [t for t in tools_of(self.fm) if BLANK not in t]

    def injections(self):
        cmds = re.findall(r"!`([^`\n]+)`", self.body)
        for block in re.findall(r"^```!\s*\n(.*?)^```", self.body, re.M | re.S):
            cmds.extend(l.strip() for l in block.splitlines() if l.strip())
        return cmds


# ───────────────────────────── 권한 규칙 ─────────────────────────────
def _rule_regex(pattern):
    if pattern.endswith(":*"):
        pattern = pattern[:-2] + " *"
    parts = [re.escape(p) for p in pattern.split("*")]
    rx = ".*".join(parts)
    if pattern.endswith(" *") and pattern.count("*") == 1:
        rx = re.escape(pattern[:-2]) + "(?: .*)?"
    return re.compile("^" + rx + "$", re.S)


def rule_matches(rule, tool, command=None):
    """rule 예: 'Bash(git log *)', 'mcp__lab', 'mcp__lab__get_*', 'Read'."""
    rule = rule.strip()
    if tool.startswith("mcp__"):
        if "(" in rule:
            return False
        if rule == tool:
            return True
        parts = tool.split("__")
        if len(parts) >= 3 and rule in ("mcp__%s" % parts[1], "mcp__%s__*" % parts[1]):
            return True
        if "*" in rule:
            return bool(_rule_regex(rule).match(tool))
        return False
    m = re.match(r"^([A-Za-z]+)(?:\((.*)\))?$", rule, re.S)
    if not m or m.group(1) != tool:
        return False
    if m.group(2) is None or m.group(2) in ("", "*"):
        return True
    return command is not None and bool(_rule_regex(m.group(2)).match(command))


def settings_rules():
    rules = {"allow": [], "ask": [], "deny": []}
    for name in ("settings.json", "settings.local.json"):
        try:
            data = json.loads(read(ROOT / ".claude" / name) or "{}")
        except ValueError:
            continue
        perms = data.get("permissions") or {}
        for k in rules:
            rules[k].extend(perms.get(k) or [])
    return rules


def decision(tool, command=None, extra_allow=()):
    """deny → ask → allow 순서. 반환: 'deny' | 'ask' | 'allow' | 'prompt'(규칙 없음)."""
    rules = settings_rules()
    if any(rule_matches(r, tool, command) for r in rules["deny"]):
        return "deny"
    if any(rule_matches(r, tool, command) for r in rules["ask"]):
        return "ask"
    if any(rule_matches(r, tool, command) for r in list(rules["allow"]) + list(extra_allow)):
        return "allow"
    return "prompt"


# ───────────────────────────── 기타 ─────────────────────────────
def scan_tokens(rep):
    hits = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            p = Path(dirpath) / fn
            try:
                if p.stat().st_size > 2_000_000:
                    continue
                text = p.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            for m in TOKEN_RE.finditer(text):
                hits.append("%s (%s-************)" % (rel(p), m.group(0)[:5]))
    rep.check(not hits, "토큰 문자열이 프로젝트 파일에 없음",
              "토큰 문자열이 파일에 들어 있습니다. 지우고 토큰을 다시 발급받으세요", ", ".join(hits[:3]))


def git(*args):
    try:
        return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        return None


def run_tool(*args, timeout=20):
    try:
        return subprocess.run([sys.executable, *args], cwd=ROOT, capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired):
        return None
