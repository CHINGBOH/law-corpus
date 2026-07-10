from __future__ import annotations

import json
import os
import subprocess


DB_ENV = {
    "PGHOST": os.environ.get("PGHOST", "127.0.0.1"),
    "PGPORT": os.environ.get("PGPORT", "5432"),
    "PGDATABASE": os.environ.get("PGDATABASE", "legal_corpus"),
    "PGUSER": os.environ.get("PGUSER", "legal_corpus"),
    "PGPASSWORD": os.environ.get("PGPASSWORD", "legal_corpus_dev"),
}


def render_sql(query: str, params: dict[str, object] | None = None) -> str:
    sql = query
    if params:
        for key, value in params.items():
            escaped = str(value).replace("'", "''")
            sql = sql.replace(f"%({key})s", f"'{escaped}'")
    return sql


def run_psql(sql: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.update(DB_ENV)
    return subprocess.run(
        ["psql", "-X", "-A", "-t", "-q", "-c", sql],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def psql_json(query: str, params: dict[str, object] | None = None) -> object:
    sql = render_sql(query, params)
    result = run_psql(sql)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "psql query failed")

    raw = result.stdout.strip()
    if not raw:
        return None
    return json.loads(raw)


def psql_exec(query: str, params: dict[str, object] | None = None) -> str:
    sql = render_sql(query, params)
    result = run_psql(sql)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "psql exec failed")
    return result.stdout.strip()


def sql_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def parse_int(value: object, default: int) -> int:
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return default


def clip(value: object, limit: int) -> str:
    text = "" if value is None else str(value)
    return text if len(text) <= limit else text[:limit] + "..."
