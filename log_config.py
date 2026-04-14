import io
import logging
import sys


def short(s: str, n: int = 80) -> str:
    """Truncate a string for log output."""
    return s if len(s) <= n else s[:n] + "..."


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
