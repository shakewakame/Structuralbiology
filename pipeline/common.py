"""Shared helpers: paths, dates, and HTTP with retries and a small disk cache."""

from __future__ import annotations

import datetime as dt
import gzip
import hashlib
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ISSUES_DIR = ROOT / "data" / "issues"
CACHE_DIR = ROOT / ".cache"

USER_AGENT = "structbio-daily/0.1 (+https://github.com/shakewakame/Structuralbiology)"
JST = dt.timezone(dt.timedelta(hours=9))


def today_jst() -> dt.date:
    return dt.datetime.now(JST).date()


def default_index_date() -> dt.date:
    """The last full UTC day. Europe PMC's first-index date for it is complete by now."""
    return dt.datetime.now(dt.timezone.utc).date() - dt.timedelta(days=1)


def issue_dir(issue_date: str) -> Path:
    return ISSUES_DIR / issue_date


def _request(url: str, data: bytes | None, headers: dict, timeout: int) -> bytes:
    req = urllib.request.Request(url, data=data, headers={"User-Agent": USER_AGENT, **headers})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        body = r.read()
        if r.headers.get("Content-Encoding") == "gzip":
            body = gzip.decompress(body)
        return body


def fetch(url: str, *, params: dict | None = None, data: bytes | None = None,
          headers: dict | None = None, timeout: int = 90, retries: int = 4,
          ok_404: bool = False) -> bytes | None:
    """GET (or POST when data is given) with exponential backoff on 429/5xx/network errors.

    Returns None for a 404 when ok_404 is set.
    """
    if params:
        url = url + ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
    delay = 2.0
    for attempt in range(retries + 1):
        try:
            return _request(url, data, headers or {}, timeout)
        except urllib.error.HTTPError as e:
            if e.code == 404 and ok_404:
                return None
            if e.code not in (408, 429, 500, 502, 503, 504) or attempt == retries:
                raise
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            if attempt == retries:
                raise
        time.sleep(delay)
        delay *= 2
    raise RuntimeError("unreachable")


def fetch_json(url: str, **kw):
    body = fetch(url, **kw)
    return None if body is None else json.loads(body)


def cached(kind: str, key: str, suffix: str = "") -> Path:
    safe = key if key.replace("_", "").replace("-", "").isalnum() else hashlib.sha1(key.encode()).hexdigest()
    path = CACHE_DIR / kind / f"{safe}{suffix}"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))
