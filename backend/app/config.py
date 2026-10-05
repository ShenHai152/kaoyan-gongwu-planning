"""Configuration boundary: load `.env` into the process environment, once.

Explicit by design (this project's engineering rules): configuration is read at a
named boundary, never guessed inside a domain. Existing environment variables
always win, so a shell export or a CI secret is never shadowed by a file.

Secrets live only here and in the environment. They never enter commits, logs,
or test fixtures (this project's engineering rules).
"""

from __future__ import annotations

import os
from functools import cache
from pathlib import Path

from dotenv import load_dotenv

# backend/app/config.py -> backend/app -> backend -> project root
_PROJECT_ROOT = Path(__file__).resolve().parents[2]


def env_file() -> Path | None:
    """The env file to load, or None when the project has none.

    `EXAM_ENV_FILE` overrides the location, which keeps tests and deployments
    from depending on a file in the working tree.
    """
    override = os.environ.get("EXAM_ENV_FILE")
    if override:
        return Path(override)
    candidate = _PROJECT_ROOT / ".env"
    return candidate if candidate.exists() else None


@cache
def load_env() -> Path | None:
    """Load the env file once; return the path used, or None.

    Cached so repeated calls (app startup, ETL entrypoints) are cheap and the
    file is never re-read mid-process. `override=False` keeps real environment
    variables authoritative.
    """
    path = env_file()
    if path is None:
        return None
    load_dotenv(path, override=False)
    return path
