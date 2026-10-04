"""사내 API 클라이언트 (hr_fetch.py, lab_mcp.py 공용).

설정을 찾는 순서
  주소: LAB_API_BASE 환경변수 → ~/.config/superlab/api_base → http://127.0.0.1:8787
  토큰: LAB_TOKEN 환경변수 → ~/.config/superlab/token
  (SUPERLAB_CONFIG_DIR로 설정 폴더를 바꿀 수 있음)

토큰 값은 어떤 출력에도 쓰지 않습니다.
"""

import json
import os
import urllib.error
import urllib.request
from pathlib import Path

DEFAULT_BASE = "http://127.0.0.1:8787"


class ApiError(Exception):
    def __init__(self, status, code, detail=""):
        super().__init__("%s %s %s" % (status, code, detail))
        self.status, self.code, self.detail = status, code, detail


def config_dir():
    return Path(os.environ.get("SUPERLAB_CONFIG_DIR") or Path.home() / ".config" / "superlab")


def _read(path):
    try:
        return Path(path).read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def api_base():
    return (os.environ.get("LAB_API_BASE") or _read(config_dir() / "api_base") or DEFAULT_BASE).rstrip("/")


def token():
    return os.environ.get("LAB_TOKEN") or _read(config_dir() / "token")


def call(method, path, body=None, timeout=10):
    tok = token()
    if not tok:
        raise ApiError(0, "no_token", "토큰이 없습니다. ch4/setup.sh로 토큰을 등록하세요")
    data = json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None
    req = urllib.request.Request(api_base() + path, data=data, method=method)
    req.add_header("Authorization", "Bearer " + tok)
    req.add_header("Accept", "application/json")
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as err:
        try:
            payload = json.loads(err.read().decode("utf-8") or "{}")
        except ValueError:
            payload = {}
        detail = payload.get("detail", "")
        if err.code == 429:
            detail = "%s (%s초 뒤 다시 시도)" % (detail, err.headers.get("Retry-After", "?"))
        raise ApiError(err.code, payload.get("error", "http_error"), detail)
    except (urllib.error.URLError, TimeoutError) as err:
        raise ApiError(0, "unreachable", "%s 에 연결할 수 없습니다 (%s)" % (api_base(), err))
