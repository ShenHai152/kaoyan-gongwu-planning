"""Export the FastAPI OpenAPI document to a committed JSON file.

The frontend generates its types from this file, so the build never depends on
a running backend, and CI can detect contract drift.

Usage:
    python -m export_openapi            # writes backend/openapi.json
    python -m export_openapi --check    # fails if the file is stale
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from app.main import app

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "backend" / "openapi.json"


def render() -> str:
    return json.dumps(app.openapi(), ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    rendered = render()
    if args.check:
        if not TARGET.exists() or TARGET.read_text(encoding="utf-8") != rendered:
            print("openapi.json is stale; run python -m export_openapi", file=sys.stderr)
            return 1
        print("openapi.json up to date.")
        return 0

    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_text(rendered, encoding="utf-8")
    paths = len(app.openapi()["paths"])
    print(f"wrote {TARGET.relative_to(ROOT)} ({paths} paths)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
