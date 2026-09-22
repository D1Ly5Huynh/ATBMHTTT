"""HTTP client for the local CRS + xss-lab-app stack (localhost only)."""

from __future__ import annotations

import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass

APP = "http://127.0.0.1:13000"
CRS_PL1 = "http://127.0.0.1:18080"
CRS_PL2 = "http://127.0.0.1:18081"
SINKS = ("/html", "/attr", "/js")
PURIFY = ("/purify/html", "/purify/attr", "/purify/js")


@dataclass
class HttpHit:
    status: int
    body: str
    url: str
    error: str | None = None

    @property
    def blocked(self) -> bool:
        return self.status == 403

    @property
    def ok(self) -> bool:
        return 200 <= self.status < 300


def fetch(base: str, path: str, payload: str, timeout: float = 8.0) -> HttpHit:
    query = urllib.parse.urlencode({"q": payload})
    url = f"{base}{path}?{query}"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "lab-tasr/1.0", "Accept": "text/html"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", "replace")
            return HttpHit(status=int(resp.status), body=body, url=url)
    except urllib.error.HTTPError as err:
        body = err.read().decode("utf-8", "replace")
        return HttpHit(status=int(err.code), body=body, url=url, error=str(err))
    except Exception as err:
        return HttpHit(status=0, body="", url=url, error=str(err))


def stack_up() -> dict[str, bool]:
    out = {}
    for name, base in ("app", APP), ("pl1", CRS_PL1), ("pl2", CRS_PL2):
        hit = fetch(base, "/health" if name == "app" else "/html", "hello")
        out[name] = hit.ok or (name != "app" and hit.status in {200, 403})
    return out
