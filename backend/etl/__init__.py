"""ETL adapters: raw files -> kaoyan records.

Loading the env file here means every `python -m etl.*` entrypoint sees the same
configuration as the API (e.g. `EXAM_DATABASE_URL`), without each loader
repeating it.
"""

from app.config import load_env

load_env()
