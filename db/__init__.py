"""Small DB-API compatibility boundary. Business SQL stays parameterized."""
import os
import re
import sqlite3
import threading
import contextvars
from contextlib import contextmanager
from pathlib import Path
from runtime_config import hosted

_request_connections = contextvars.ContextVar('db_request_connections', default=None)


class DatabaseConfigurationError(RuntimeError):
    """Safe configuration messages: never include connection-string values."""


@contextmanager
def request_scope():
    """Reuse idle sockets inside one request, never transactions or global pools.

    Nested repositories holding an active handle get a distinct connection.
    Every socket is closed before the request finishes, including leaked handles.
    Neon PgBouncer handles pooling across Function instances.
    """
    pool={'idle':[], 'all':[]}; token=_request_connections.set(pool)
    try: yield
    finally:
        _request_connections.reset(token)
        for raw in pool['all']: raw.close()


def backend():
    value = os.environ.get('DATABASE_BACKEND', 'postgres' if hosted() else 'sqlite')
    if value not in ('sqlite', 'postgres'):
        raise DatabaseConfigurationError('DATABASE_BACKEND must be sqlite or postgres')
    if hosted() and value != 'postgres':
        raise DatabaseConfigurationError('Vercel requires DATABASE_BACKEND=postgres')
    return value


class WriteLock:
    """Only SQLite needs the legacy process-local write lock."""
    def __init__(self):
        self.local = threading.RLock()
    def __enter__(self):
        if backend() == 'sqlite': self.local.acquire()
        return self
    def __exit__(self, *exc):
        if backend() == 'sqlite': self.local.release()


class Row(dict):
    def __getitem__(self, key):
        return tuple(self.values())[key] if isinstance(key, int) else super().__getitem__(key)


def row_factory(cursor):
    columns = [col.name for col in (cursor.description or [])]
    return lambda values: Row(zip(columns, values))


def parameters(sql):
    """Translate qmark tokens, preserving quoted values and literal percent signs.

    Schema/upsert differences are handled explicitly, never by this lexer.
    Application queries contain no comments or dollar-quoted literals.
    """
    result = []; quote = None; i = 0
    while i < len(sql):
        ch = sql[i]
        if quote:
            result.append(ch if ch != '%' else '%%')
            if ch == quote:
                if i + 1 < len(sql) and sql[i+1] == quote:
                    result.append(sql[i+1]); i += 1
                else: quote = None
        elif ch in ("'", '"'):
            quote = ch; result.append(ch)
        elif ch == '?': result.append('%s')
        else: result.append('%%' if ch == '%' else ch)
        i += 1
    return ''.join(result)


class Postgres:
    def __init__(self, url=None):
        import psycopg
        url = url or os.environ.get('DATABASE_URL')
        if not url: raise DatabaseConfigurationError('DATABASE_URL is required')
        self.pool=_request_connections.get();self.closed=False;self.url=url
        idle=self.pool['idle'] if self.pool is not None else []
        candidate=next(((key,raw) for key,raw in idle if key==url and not raw.closed),None)
        if candidate:
            idle.remove(candidate);self.raw=candidate[1]
        else:
            self.raw = psycopg.connect(url, row_factory=row_factory, connect_timeout=10,
                                      prepare_threshold=None)
            if self.pool is not None:self.pool['all'].append(self.raw)
    def execute(self, sql, params=()):
        import runtime_jobs
        runtime_jobs.check()
        if self.closed:raise RuntimeError('Connection is closed')
        from psycopg.pq import TransactionStatus
        if self.raw.info.transaction_status == TransactionStatus.IDLE:
            milliseconds=25000
            if runtime_jobs.deadline.get():milliseconds=max(1,min(milliseconds,int((runtime_jobs.deadline.get()-__import__('time').time())*1000)))
            # Neon transaction pooling rejects statement_timeout in startup
            # options. SET LOCAL is scoped to this transaction and resets safely.
            self.raw.execute("SELECT set_config('statement_timeout',%s,true),set_config('lock_timeout','10000',true)",(str(milliseconds),))
        return self.raw.execute(parameters(sql), params)
    def executemany(self, sql, rows):
        cur = self.raw.cursor(); cur.executemany(parameters(sql), rows); return cur
    def commit(self): self.raw.commit()
    def rollback(self): self.raw.rollback()
    def close(self):
        if self.closed:return
        self.closed=True
        if self.pool is None:
            try:self.raw.rollback()
            finally:self.raw.close()
        else:
            self.raw.rollback()  # Never leak a transaction into the next checkout.
            if not self.raw.closed:self.pool['idle'].append((self.url,self.raw))
    def __enter__(self): return self
    def __exit__(self, kind, value, traceback):
        try:
            if kind: self.rollback()
            else: self.commit()
        finally:self.close()


def connect(path=None):
    if backend() == 'postgres': return Postgres()
    c = sqlite3.connect(path, timeout=30, factory=SQLite); c.row_factory = sqlite3.Row
    for sql in ('PRAGMA busy_timeout=30000', 'PRAGMA journal_mode=WAL',
                'PRAGMA synchronous=NORMAL', 'PRAGMA foreign_keys=ON'): c.execute(sql)
    return c


class SQLite(sqlite3.Connection):
    """Both engines close context-managed handles deterministically (Windows too)."""
    def __exit__(self, kind, value, traceback):
        try: return super().__exit__(kind, value, traceback)
        finally: self.close()


def columns(c, table):
    if not re.fullmatch(r'[a-z_]+', table): raise ValueError('Invalid table')
    if isinstance(c, Postgres):
        return {r[0] for r in c.execute('SELECT column_name FROM information_schema.columns WHERE table_schema=current_schema() AND table_name=?', (table,))}
    return {r[1] for r in c.execute('PRAGMA table_info('+table+')')}


def table_exists(c, table):
    if isinstance(c, Postgres):
        return c.execute('SELECT to_regclass(?)', (table,)).fetchone()[0] is not None
    return c.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone() is not None


def checkpoint(c):
    if not isinstance(c, Postgres):c.execute('PRAGMA wal_checkpoint(TRUNCATE)')


KEYS = {'source_syncs': ('source_id',), 'road_network_meta': ('id',),
        'signal_networks': ('id',), 'road_objects': ('id',),
        'municipality_sources': ('municipality', 'source_id'),
        'source_gaps': ('municipality',), 'assistant_update_runs': ('batch_id',)}


def upsert_statement(sql):
    """Explicit conflict targets for the audited legacy replacement writes.

    Callers pass INSERT INTO, its column list and VALUES expression. Updating only
    supplied fields preserves enrichment omitted by partial source-sync updates.
    SQLite uses this same SQL and no longer deletes/recreates conflicting rows.
    """
    match = re.match(r'INSERT INTO ([a-z_]+)\(([^)]+)\) VALUES', sql, re.I)
    if not match or match[1] not in KEYS: raise ValueError('Unaudited upsert')
    keys = KEYS[match[1]]; names = match[2].split(',')
    updates = ','.join(n+'=excluded.'+n for n in names if n not in keys)
    return sql+' ON CONFLICT('+','.join(keys)+') DO UPDATE SET '+updates


def insert_id(c, sql, params):
    if isinstance(c, Postgres): return c.execute(sql+' RETURNING id', params).fetchone()[0]
    return c.execute(sql, params).lastrowid


def status(c):
    c.execute('SELECT 1').fetchone()
    counts = {t: c.execute('SELECT count(*) FROM '+t).fetchone()[0]
              for t in ('radars', 'road_objects', 'source_registry')}
    migrations = []
    if table_exists(c, 'schema_migrations'):
        migrations = [dict(r) for r in c.execute('SELECT * FROM schema_migrations ORDER BY version DESC LIMIT 1')]
    return {'database': 'ok', 'engine': backend(), 'counts': counts,
            'schema_version': migrations[0]['version'] if migrations else 'sqlite-legacy',
            'last_migration': migrations[0] if migrations else None}
