import json
import sqlite3
from contextlib import closing, contextmanager
from pathlib import Path

from app.config import settings


@contextmanager
def database():
    if settings.HISTORY_DATABASE_URL:
        import psycopg

        connection = psycopg.connect(settings.HISTORY_DATABASE_URL, connect_timeout=10)
        identity, placeholder = "BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY", "%s"
    else:
        path = Path(settings.HISTORY_DB_PATH)
        path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(path, timeout=10)
        identity, placeholder = "INTEGER PRIMARY KEY", "?"

    with closing(connection), connection:
        if settings.HISTORY_DATABASE_URL:
            connection.execute("SELECT pg_advisory_xact_lock(328798481)")
        connection.execute(f"""
            CREATE TABLE IF NOT EXISTS query_history (
                id {identity},
                latency_seconds DOUBLE PRECISION NOT NULL,
                eval_score DOUBLE PRECISION,
                record TEXT NOT NULL
            )
        """)
        if settings.HISTORY_DATABASE_URL:
            connection.commit()
        yield connection, placeholder


def save(record):
    with database() as (connection, placeholder):
        values = ", ".join([placeholder] * 3)
        connection.execute(
            f"INSERT INTO query_history (latency_seconds, eval_score, record) VALUES ({values})",
            (record["latency_seconds"], record["eval_score"], json.dumps(record)),
        )


def stats():
    with database() as (connection, _):
        total, latency, score = connection.execute(
            "SELECT COUNT(*), AVG(latency_seconds), AVG(eval_score) FROM query_history"
        ).fetchone()
        recent = connection.execute("SELECT record FROM query_history ORDER BY id DESC LIMIT 20").fetchall()
    return {
        "last_ingested_at": None,
        "total_queries": total,
        "avg_latency_seconds": round(latency or 0, 3),
        "avg_eval_score": round(score, 3) if score is not None else None,
        "recent_queries": [json.loads(row[0]) for row in recent],
    }
