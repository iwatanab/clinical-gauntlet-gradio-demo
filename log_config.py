import io
import json
import logging
import re
import sys


def short(s: str, n: int = 80) -> str:
    """Truncate a string for log output."""
    return s if len(s) <= n else s[:n] + "..."


_FENCE_RE = re.compile(r"^```(?:json)?\s*\n?(.*?)\n?```\s*$", re.DOTALL)


def parse_json(raw: str) -> dict:
    """Parse a JSON string, stripping markdown code fences if present."""
    text = raw.strip()
    m = _FENCE_RE.match(text)
    if m:
        text = m.group(1).strip()
    return json.loads(text)


def configure():
    root = logging.getLogger()
    if root.handlers:
        return  # idempotent — guard against double-init on hot-reload

    root.setLevel(logging.DEBUG)
    fmt = "%(asctime)s %(levelname)-8s %(name)-35s %(message)s"
    datefmt = "%H:%M:%S"
    formatter = logging.Formatter(fmt, datefmt)

    ch = logging.StreamHandler(io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace"))
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)

    fh = logging.FileHandler("gauntlet.log", mode="w", encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)

    root.addHandler(ch)
    root.addHandler(fh)
