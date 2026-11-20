from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_DIR = Path(os.environ.get("FORESIGHT_DATA_DIR", ROOT.parent / "data"))
DB_PATH = Path(os.environ.get("FORESIGHT_DB", DATA_DIR / "foresight.db"))

# Rows owned by one company ('cognition', a generated company id, or '*' for the general library).
COMPANY_SCOPED = ("signals", "sources", "job_postings", "scenarios", "archetypes", "segments", "customer_problems")

JSON_COLUMNS = {
    "queries", "evidence", "board", "gaps",
    "regions", "segment_ids", "data", "evidence_phrases", "horizon_profile", "cognition_use_cases",
    "adoption_barriers", "signal_ids", "markets", "capability_ids", "teams", "starting_titles",
    "capability_weights", "unconventional_backgrounds", "assessment", "posting_keywords", "learning_needs",
}


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def session():
    conn = connect()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript((ROOT / "schema.sql").read_text())
    for t in COMPANY_SCOPED:
        if "company_id" not in {r[1] for r in conn.execute(f"PRAGMA table_info({t})")}:
            conn.execute(f"ALTER TABLE {t} ADD COLUMN company_id TEXT NOT NULL DEFAULT 'cognition'")
    cols = {r[1] for r in conn.execute("PRAGMA table_info(candidates)")}
    if "profile_url" not in cols:
        conn.execute("ALTER TABLE candidates ADD COLUMN profile_url TEXT")
    ddl = conn.execute("SELECT sql FROM sqlite_master WHERE name='candidate_evidence'").fetchone()[0]
    if "'patent'" not in ddl:
        conn.executescript(
            "PRAGMA legacy_alter_table=ON; ALTER TABLE candidate_evidence RENAME TO candidate_evidence_old;"
            + ddl.replace("'title_only')", "'title_only','patent')") + ";"
            "INSERT INTO candidate_evidence SELECT * FROM candidate_evidence_old; DROP TABLE candidate_evidence_old;"
            "PRAGMA legacy_alter_table=OFF;")


def row(r: sqlite3.Row | None) -> dict | None:
    if r is None:
        return None
    out = dict(r)
    for k, v in out.items():
        if k in JSON_COLUMNS and isinstance(v, str):
            out[k] = json.loads(v)
    return out


def rows(rs) -> list[dict]:
    return [row(r) for r in rs]


def upsert(conn: sqlite3.Connection, table: str, record: dict) -> None:
    rec = {k: (json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else v) for k, v in record.items()}
    cols = ", ".join(rec)
    marks = ", ".join("?" for _ in rec)
    conn.execute(f"INSERT OR REPLACE INTO {table} ({cols}) VALUES ({marks})", list(rec.values()))
