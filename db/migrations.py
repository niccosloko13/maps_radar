"""Explicit schema migration; never run automatically on Function import."""
from datetime import datetime, timezone
from pathlib import Path

VERSION = '001-vercel-neon'


def apply(connection):
    raw = connection.raw
    raw.execute("SELECT pg_advisory_xact_lock(hashtext('relas-schema-migrations'))")
    raw.execute(Path(__file__).with_name('schema.sql').read_text(encoding='utf8'))
    raw.execute('INSERT INTO schema_migrations(version,applied_at,description) VALUES(%s,%s,%s) ON CONFLICT(version) DO NOTHING',
                (VERSION, datetime.now(timezone.utc).isoformat(), 'SQLite inventory, distributed runtime state and jobs'))
