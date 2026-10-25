"""Historical SQLite migrations, retained intact for local/offline databases."""

def initialize(s):
    s.ensure_user_data(); c=s.db(); c.executescript('''
    CREATE TABLE IF NOT EXISTS radars(id TEXT PRIMARY KEY,physical_radar_id TEXT,source TEXT NOT NULL,external_id TEXT,name TEXT NOT NULL,latitude REAL,longitude REAL,speed_limit INTEGER,speed_text TEXT,direction TEXT,status TEXT NOT NULL DEFAULT 'active',confidence INTEGER NOT NULL DEFAULT 90,municipality TEXT,state TEXT DEFAULT 'SP',road TEXT,km TEXT,radar_type TEXT,der_number TEXT,serial_number TEXT,schedule TEXT,study_url TEXT,source_url TEXT,source_date TEXT,position_quality TEXT,inmetro_registration TEXT,lanes INTEGER,local_code TEXT,quality_grade TEXT,first_seen TEXT NOT NULL,last_seen TEXT NOT NULL,current_hash TEXT NOT NULL,raw_json TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS radar_history(history_id INTEGER PRIMARY KEY AUTOINCREMENT,radar_id TEXT NOT NULL,source TEXT NOT NULL,version_hash TEXT NOT NULL,captured_at TEXT NOT NULL,valid_to TEXT,raw_json TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS source_syncs(source_id TEXT PRIMARY KEY,status TEXT NOT NULL,started_at TEXT,finished_at TEXT,http_status INTEGER,imported INTEGER DEFAULT 0,updated INTEGER DEFAULT 0,unchanged INTEGER DEFAULT 0,skipped INTEGER DEFAULT 0,mapped INTEGER DEFAULT 0,roads INTEGER DEFAULT 0,source_url TEXT,error TEXT,diagnostic TEXT);
    CREATE TABLE IF NOT EXISTS road_network_meta(id INTEGER PRIMARY KEY CHECK(id=1), source_url TEXT, fetched_at TEXT, segments INTEGER DEFAULT 0, usable_segments INTEGER DEFAULT 0, sha256 TEXT, error TEXT);
    CREATE TABLE IF NOT EXISTS municipalities(ibge_id TEXT PRIMARY KEY,name TEXT NOT NULL,state TEXT NOT NULL DEFAULT 'SP',last_refresh TEXT);
    CREATE TABLE IF NOT EXISTS source_registry(source_id TEXT PRIMARY KEY,name TEXT NOT NULL,scope TEXT,coverage TEXT,mode TEXT,priority INTEGER DEFAULT 50,url TEXT,official INTEGER DEFAULT 1,enabled INTEGER DEFAULT 1,last_seen TEXT,notes TEXT);
    CREATE TABLE IF NOT EXISTS admin_events(id INTEGER PRIMARY KEY AUTOINCREMENT,created_at TEXT NOT NULL,kind TEXT NOT NULL,message TEXT NOT NULL,details TEXT);
    CREATE TABLE IF NOT EXISTS road_objects(id TEXT PRIMARY KEY,source TEXT NOT NULL,external_id TEXT,object_type TEXT NOT NULL,name TEXT,latitude REAL,longitude REAL,municipality TEXT,state TEXT DEFAULT 'SP',status TEXT DEFAULT 'active',confidence INTEGER DEFAULT 70,official INTEGER DEFAULT 0,speed_limit INTEGER,direction TEXT,timing_mode TEXT DEFAULT 'unknown',cycle_seconds REAL,green_seconds REAL,red_seconds REAL,adaptive INTEGER DEFAULT 0,timing_source TEXT,source_url TEXT,source_date TEXT,first_seen TEXT NOT NULL,last_seen TEXT NOT NULL,raw_json TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS road_object_history(history_id INTEGER PRIMARY KEY AUTOINCREMENT,object_id TEXT NOT NULL,source TEXT NOT NULL,captured_at TEXT NOT NULL,raw_json TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS signal_networks(id TEXT PRIMARY KEY,municipality TEXT NOT NULL,name TEXT NOT NULL,mode TEXT NOT NULL,count_known INTEGER,live_timing INTEGER DEFAULT 0,description TEXT,source_url TEXT,source_date TEXT,last_seen TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS municipality_sources(municipality TEXT NOT NULL,source_id TEXT NOT NULL,source_name TEXT,source_url TEXT,source_type TEXT,status TEXT NOT NULL DEFAULT 'candidate',official INTEGER DEFAULT 0,first_seen TEXT NOT NULL,last_attempt TEXT,last_success TEXT,item_count INTEGER DEFAULT 0,mapped_count INTEGER DEFAULT 0,diagnostic TEXT,PRIMARY KEY(municipality,source_id));
    CREATE TABLE IF NOT EXISTS source_gaps(municipality TEXT PRIMARY KEY,status TEXT NOT NULL DEFAULT 'needs_source',reason TEXT,attempts INTEGER DEFAULT 0,last_checked TEXT,next_retry TEXT,notes TEXT);
    CREATE TABLE IF NOT EXISTS city_scan_jobs(id INTEGER PRIMARY KEY AUTOINCREMENT,created_at TEXT NOT NULL,started_at TEXT,finished_at TEXT,status TEXT NOT NULL,municipalities_json TEXT NOT NULL,summary_json TEXT,error TEXT);
    CREATE TABLE IF NOT EXISTS source_attempts(id INTEGER PRIMARY KEY AUTOINCREMENT,municipality TEXT NOT NULL,source_id TEXT,attempted_at TEXT NOT NULL,status TEXT NOT NULL,item_count INTEGER DEFAULT 0,mapped_count INTEGER DEFAULT 0,diagnostic TEXT,url TEXT);
    CREATE TABLE IF NOT EXISTS municipality_profiles(municipality TEXT PRIMARY KEY,radar_enabled INTEGER DEFAULT 1,signals_enabled INTEGER DEFAULT 1,objects_enabled INTEGER DEFAULT 1,last_radar_scan TEXT,last_signal_scan TEXT,last_full_scan TEXT,notes TEXT);
    CREATE TABLE IF NOT EXISTS radar_validations(id INTEGER PRIMARY KEY AUTOINCREMENT,radar_id TEXT NOT NULL,checked_at TEXT NOT NULL,status TEXT NOT NULL,valid_from TEXT,valid_until TEXT,source TEXT,certificate TEXT,notes TEXT);
    CREATE TABLE IF NOT EXISTS manual_entries(id INTEGER PRIMARY KEY AUTOINCREMENT,entry_type TEXT NOT NULL,entity_id TEXT NOT NULL,created_at TEXT NOT NULL,created_by TEXT NOT NULL DEFAULT 'admin',notes TEXT);
    ''')
    # lightweight migrations for older local databases
    existing={r[1] for r in c.execute('PRAGMA table_info(radars)').fetchall()}
    for col,typ in [('inmetro_registration','TEXT'),('lanes','INTEGER'),('local_code','TEXT'),('quality_grade','TEXT'),('physical_radar_id','TEXT')]:
     if col not in existing:c.execute(f'ALTER TABLE radars ADD COLUMN {col} {typ}')
    c.execute('PRAGMA journal_mode=WAL'); c.execute('PRAGMA busy_timeout=30000')
    # Jobs are process-local workers. If the app was closed mid-scan, never leave them stuck forever.
    c.execute("UPDATE city_scan_jobs SET status='interrupted',finished_at=?,error=COALESCE(error,'Aplicativo encerrado antes da conclusão') WHERE status IN ('queued','running')",(s.now(),))
    for src in s.SOURCE_REGISTRY:
     c.execute('INSERT INTO source_registry(source_id,name,scope,coverage,mode,priority,url,official,enabled,last_seen) VALUES(?,?,?,?,?,?,?,?,1,?) ON CONFLICT(source_id) DO UPDATE SET name=excluded.name,scope=excluded.scope,coverage=excluded.coverage,mode=excluded.mode,priority=excluded.priority,url=excluded.url,official=excluded.official', (src['id'],src['name'],src.get('scope'),src.get('coverage'),src.get('mode'),src.get('priority',50),src.get('url'),1 if src.get('official') else 0,s.now()))
    c.commit(); c.close()


def upgrade(s):
    c=s.db()
    sql=(
      "CREATE TABLE IF NOT EXISTS operation_logs(id INTEGER PRIMARY KEY AUTOINCREMENT,operation_id TEXT NOT NULL,created_at TEXT NOT NULL,level TEXT NOT NULL DEFAULT 'info',stage TEXT,municipality TEXT,source_id TEXT,message TEXT NOT NULL,details TEXT);"
      "CREATE INDEX IF NOT EXISTS idx_operation_logs_op ON operation_logs(operation_id,id);"
      "CREATE TABLE IF NOT EXISTS update_queue(id INTEGER PRIMARY KEY AUTOINCREMENT,municipality TEXT,category TEXT NOT NULL,source_id TEXT NOT NULL,label TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'pending',discovered_at TEXT NOT NULL,applied_at TEXT,details TEXT);"
      "CREATE INDEX IF NOT EXISTS idx_update_queue_status ON update_queue(status,id);"
      "CREATE TABLE IF NOT EXISTS assistant_update_runs(batch_id TEXT PRIMARY KEY,actor TEXT NOT NULL,started_at TEXT,finished_at TEXT,status TEXT NOT NULL,targets_json TEXT,summary_json TEXT,error TEXT);"
    )
    with s.DB_WRITE_LOCK:
        c.executescript(sql)
        cols={r[1] for r in c.execute('PRAGMA table_info(city_scan_jobs)').fetchall()}
        for col,typ in [('include_osm','INTEGER DEFAULT 1'),('result_json','TEXT'),('mode','TEXT DEFAULT \'all\'')]:
            if col not in cols:c.execute(f'ALTER TABLE city_scan_jobs ADD COLUMN {col} {typ}')
        rocols={r[1] for r in c.execute('PRAGMA table_info(road_objects)').fetchall()}
        for col,typ in [('ingested_by','TEXT'),('ingestion_batch','TEXT'),('provenance_note','TEXT')]:
            if col not in rocols:c.execute(f'ALTER TABLE road_objects ADD COLUMN {col} {typ}')
        rcols={r[1] for r in c.execute('PRAGMA table_info(radars)').fetchall()}
        for col,typ in [('ingested_by','TEXT'),('ingestion_batch','TEXT'),('provenance_note','TEXT')]:
            if col not in rcols:c.execute(f'ALTER TABLE radars ADD COLUMN {col} {typ}')
        c.commit()
    c.close()


def initialize_community(s):
    from community import transaction
    with transaction(s) as c:
        c.executescript("CREATE TABLE IF NOT EXISTS map_points(id TEXT PRIMARY KEY,longitude REAL NOT NULL,latitude REAL NOT NULL,kind TEXT NOT NULL,speed_limit INTEGER,direction REAL,direction_type INTEGER,original_type INTEGER,source TEXT,source_type TEXT,ingested_by TEXT,imported_at TEXT,batch_id TEXT,municipality TEXT,trust TEXT DEFAULT 'community',linked_id TEXT,hidden INTEGER DEFAULT 0,updated_at TEXT,expires_at REAL,raw_json TEXT);\nCREATE INDEX IF NOT EXISTS radar_viewport ON radars(longitude,latitude);\nCREATE INDEX IF NOT EXISTS object_viewport ON road_objects(longitude,latitude);\nCREATE INDEX IF NOT EXISTS map_bbox ON map_points(longitude,latitude);\nCREATE INDEX IF NOT EXISTS map_city_type ON map_points(municipality,kind);\nCREATE INDEX IF NOT EXISTS map_source_trust ON map_points(source,trust);\nCREATE INDEX IF NOT EXISTS map_updated ON map_points(updated_at);\nCREATE TABLE IF NOT EXISTS community_batches(batch_id TEXT PRIMARY KEY,created_at TEXT,filename TEXT,sha256 TEXT,summary_json TEXT);\nCREATE TABLE IF NOT EXISTS map_feedback(id INTEGER PRIMARY KEY,point_id TEXT,action TEXT,created_at TEXT);\nCREATE TABLE IF NOT EXISTS map_audit(id INTEGER PRIMARY KEY,created_at TEXT,action TEXT,ids_json TEXT);\n")
        columns = {r[1] for r in c.execute('PRAGMA table_info(map_points)')}
        for col in ['name', 'report_kind']:
            if col not in columns:
                c.execute('ALTER TABLE map_points ADD COLUMN ' + col + ' TEXT')
