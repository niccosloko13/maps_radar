"""Additive, explicit migration shared by SQLite and PostgreSQL. No import DDL."""
VERSION = '003-road-data-source-readiness'
STATEMENTS = [
'''CREATE TABLE IF NOT EXISTS road_source_catalogs (
 source_id TEXT NOT NULL, catalog TEXT NOT NULL, retrieved_at TEXT NOT NULL,
 payload_json TEXT NOT NULL, PRIMARY KEY(source_id,catalog))''',
'''CREATE TABLE IF NOT EXISTS road_event_matches (
 match_id TEXT PRIMARY KEY, left_event_id TEXT NOT NULL, right_event_id TEXT NOT NULL,
 status TEXT NOT NULL, reason TEXT NOT NULL, updated_at TEXT NOT NULL)''',
'''CREATE TABLE IF NOT EXISTS road_data_sources (
 source_id TEXT PRIMARY KEY, name TEXT NOT NULL, authority TEXT NOT NULL,
 category TEXT NOT NULL, base_url TEXT NOT NULL, data_format TEXT, auth_type TEXT,
 license TEXT, terms_url TEXT, terms_version TEXT, attribution TEXT,
 commercial_restrictions TEXT, poll_interval_seconds INTEGER NOT NULL,
 rate_limit INTEGER, enabled INTEGER NOT NULL DEFAULT 1, status TEXT NOT NULL,
 last_attempt_at TEXT, last_success_at TEXT, last_source_timestamp TEXT,
 last_error TEXT, record_count INTEGER NOT NULL DEFAULT 0,
 freshness_status TEXT NOT NULL, adapter_version TEXT, contract_version TEXT,
 schema_hash TEXT, last_schema_validation TEXT, next_attempt_at REAL DEFAULT 0,
 lease_until REAL DEFAULT 0, cursor_json TEXT, response_headers_json TEXT)''',
'''CREATE TABLE IF NOT EXISTS road_source_reviews (
 source_id TEXT PRIMARY KEY REFERENCES road_data_sources(source_id),
 license TEXT, terms_url TEXT, commercial_restrictions TEXT,
 attribution_required INTEGER NOT NULL DEFAULT 0, last_terms_check TEXT,
 license_verified INTEGER NOT NULL DEFAULT 0, endpoint_verified INTEGER NOT NULL DEFAULT 0,
 blocker TEXT, next_action TEXT, evidence_json TEXT, reviewed_at TEXT NOT NULL)''',
'''CREATE TABLE IF NOT EXISTS road_event (
 event_id TEXT PRIMARY KEY, source_id TEXT NOT NULL REFERENCES road_data_sources(source_id),
 external_id TEXT NOT NULL, event_type TEXT NOT NULL, subtype TEXT, severity TEXT,
 road TEXT, direction TEXT, municipality_ibge TEXT, municipality TEXT,
 km_start REAL, km_end REAL, lat REAL, lon REAL, geometry TEXT,
 min_lon REAL, min_lat REAL, max_lon REAL, max_lat REAL,
 start_at TEXT, updated_at TEXT, end_at TEXT, status TEXT NOT NULL,
 lane_impacts TEXT, total_closure INTEGER DEFAULT 0, description TEXT,
 source_updated_at TEXT, retrieved_at TEXT NOT NULL, expires_at TEXT,
 confidence REAL, record_class TEXT NOT NULL, payload_json TEXT NOT NULL,
 UNIQUE(source_id,external_id))''',
'''CREATE TABLE IF NOT EXISTS road_location_reviews (
 event_id TEXT PRIMARY KEY REFERENCES road_event(event_id),
 lon DOUBLE PRECISION, lat DOUBLE PRECISION, coordinate_quality TEXT NOT NULL,
 confidence DOUBLE PRECISION NOT NULL DEFAULT 0, coordinate_source TEXT,
 approval_status TEXT NOT NULL, evidence_json TEXT NOT NULL, reviewed_at TEXT NOT NULL)''',
'''CREATE TABLE IF NOT EXISTS road_infrastructure_reviews (
 event_id TEXT PRIMARY KEY REFERENCES road_event(event_id), status TEXT NOT NULL,
 coordinate_quality TEXT NOT NULL, proposal_json TEXT, reviewed_at TEXT NOT NULL)''',
'''CREATE TABLE IF NOT EXISTS event_evidence (
 evidence_id TEXT PRIMARY KEY, event_id TEXT NOT NULL REFERENCES road_event(event_id),
 source_id TEXT NOT NULL, external_id TEXT NOT NULL, retrieved_at TEXT NOT NULL,
 fingerprint TEXT NOT NULL, payload_json TEXT NOT NULL)''',
'''CREATE TABLE IF NOT EXISTS road_source_logs (
 log_id TEXT PRIMARY KEY, source_id TEXT NOT NULL, started_at TEXT NOT NULL,
 finished_at TEXT, status TEXT NOT NULL, http_status INTEGER,
 records_received INTEGER DEFAULT 0, records_normalized INTEGER DEFAULT 0,
 records_created INTEGER DEFAULT 0, records_updated INTEGER DEFAULT 0,
 records_expired INTEGER DEFAULT 0, duplicates INTEGER DEFAULT 0,
 errors TEXT, duration_ms REAL, diagnostics_json TEXT)''',
'''CREATE TABLE IF NOT EXISTS road_source_history (
 history_id TEXT PRIMARY KEY, source_id TEXT NOT NULL, captured_at TEXT NOT NULL,
 snapshot_json TEXT NOT NULL)''',
'''CREATE TABLE IF NOT EXISTS road_poll_budget (
 bucket TEXT PRIMARY KEY, next_at REAL NOT NULL, window_start REAL NOT NULL,
 requests INTEGER NOT NULL, lease_until REAL NOT NULL)''',
'''CREATE TABLE IF NOT EXISTS road_layer_diagnostics (
 report_id TEXT PRIMARY KEY, captured_at TEXT NOT NULL, payload_json TEXT NOT NULL)''',
'''CREATE TABLE IF NOT EXISTS road_data_migrations (version TEXT PRIMARY KEY, applied_at TEXT NOT NULL)''',
"CREATE INDEX IF NOT EXISTS idx_road_event_viewport ON road_event(min_lon,max_lon,min_lat,max_lat)",
"CREATE INDEX IF NOT EXISTS idx_road_event_source_status ON road_event(source_id,status)",
"CREATE INDEX IF NOT EXISTS idx_road_event_type_expiry ON road_event(event_type,expires_at)",
"CREATE INDEX IF NOT EXISTS idx_road_event_city ON road_event(municipality_ibge,municipality)",
"CREATE INDEX IF NOT EXISTS idx_road_event_road ON road_event(road,direction,km_start)",
"CREATE INDEX IF NOT EXISTS idx_road_log_source ON road_source_logs(source_id,started_at)",
]


def apply(c):
    from datetime import datetime, timezone
    import db
    if isinstance(c, db.Postgres):
        c.execute("SELECT pg_advisory_xact_lock(hashtext('relas-road-data-schema'))")
    for statement in STATEMENTS:
        c.execute(statement.replace(' REAL',' DOUBLE PRECISION'))
    if isinstance(c, db.Postgres):
        # Explicit upgrade of an early validation schema; epoch seconds must not
        # use float4, which loses minute-scale precision at present dates.
        for table, cols in {'road_event':['lat','lon','min_lon','min_lat','max_lon','max_lat','km_start','km_end','confidence'],
                            'road_data_sources':['next_attempt_at','lease_until'],
                            'road_poll_budget':['next_at','window_start','lease_until'],
                            'road_source_logs':['duration_ms']}.items():
            for col in cols:
                r=c.execute('SELECT data_type FROM information_schema.columns WHERE table_schema=current_schema() AND table_name=? AND column_name=?',(table,col)).fetchone()
                if r and r[0]=='real':c.execute('ALTER TABLE '+table+' ALTER COLUMN '+col+' TYPE DOUBLE PRECISION')
    c.execute('INSERT INTO road_data_migrations(version,applied_at) VALUES(?,?) ON CONFLICT(version) DO NOTHING',
              (VERSION, datetime.now(timezone.utc).isoformat()))
