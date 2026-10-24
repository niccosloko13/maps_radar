CREATE INDEX idx_operation_logs_op ON operation_logs(operation_id,id);

CREATE INDEX idx_update_queue_status ON update_queue(status,id);

CREATE INDEX map_bbox ON map_points(longitude,latitude);

CREATE INDEX map_city_type ON map_points(municipality,kind);

CREATE INDEX map_source_trust ON map_points(source,trust);

CREATE INDEX map_updated ON map_points(updated_at);

CREATE INDEX object_viewport ON road_objects(longitude,latitude);

CREATE INDEX radar_viewport ON radars(longitude,latitude);

CREATE TABLE admin_events(id INTEGER PRIMARY KEY AUTOINCREMENT,created_at TEXT NOT NULL,kind TEXT NOT NULL,message TEXT NOT NULL,details TEXT);

CREATE TABLE assistant_update_runs(batch_id TEXT PRIMARY KEY,actor TEXT NOT NULL,started_at TEXT,finished_at TEXT,status TEXT NOT NULL,targets_json TEXT,summary_json TEXT,error TEXT);

CREATE TABLE city_scan_jobs(id INTEGER PRIMARY KEY AUTOINCREMENT,created_at TEXT NOT NULL,started_at TEXT,finished_at TEXT,status TEXT NOT NULL,municipalities_json TEXT NOT NULL,summary_json TEXT,error TEXT, include_osm INTEGER DEFAULT 1, result_json TEXT, mode TEXT DEFAULT 'all');

CREATE TABLE community_batches(batch_id TEXT PRIMARY KEY,created_at TEXT,filename TEXT,sha256 TEXT,summary_json TEXT);

CREATE TABLE manual_entries(id INTEGER PRIMARY KEY AUTOINCREMENT,entry_type TEXT NOT NULL,entity_id TEXT NOT NULL,created_at TEXT NOT NULL,created_by TEXT NOT NULL DEFAULT 'admin',notes TEXT);

CREATE TABLE map_audit(id INTEGER PRIMARY KEY,created_at TEXT,action TEXT,ids_json TEXT);

CREATE TABLE map_feedback(id INTEGER PRIMARY KEY,point_id TEXT,action TEXT,created_at TEXT);

CREATE TABLE map_points(id TEXT PRIMARY KEY,longitude REAL NOT NULL,latitude REAL NOT NULL,kind TEXT NOT NULL,speed_limit INTEGER,direction REAL,direction_type INTEGER,original_type INTEGER,source TEXT,source_type TEXT,ingested_by TEXT,imported_at TEXT,batch_id TEXT,municipality TEXT,trust TEXT DEFAULT 'community',linked_id TEXT,hidden INTEGER DEFAULT 0,updated_at TEXT,expires_at REAL,raw_json TEXT, name TEXT, report_kind TEXT);

CREATE TABLE municipalities(ibge_id TEXT PRIMARY KEY,name TEXT NOT NULL,state TEXT NOT NULL DEFAULT 'SP',last_refresh TEXT);

CREATE TABLE municipality_profiles(municipality TEXT PRIMARY KEY,radar_enabled INTEGER DEFAULT 1,signals_enabled INTEGER DEFAULT 1,objects_enabled INTEGER DEFAULT 1,last_radar_scan TEXT,last_signal_scan TEXT,last_full_scan TEXT,notes TEXT);

CREATE TABLE municipality_sources(municipality TEXT NOT NULL,source_id TEXT NOT NULL,source_name TEXT,source_url TEXT,source_type TEXT,status TEXT NOT NULL DEFAULT 'candidate',official INTEGER DEFAULT 0,first_seen TEXT NOT NULL,last_attempt TEXT,last_success TEXT,item_count INTEGER DEFAULT 0,mapped_count INTEGER DEFAULT 0,diagnostic TEXT,PRIMARY KEY(municipality,source_id));

CREATE TABLE operation_logs(id INTEGER PRIMARY KEY AUTOINCREMENT,operation_id TEXT NOT NULL,created_at TEXT NOT NULL,level TEXT NOT NULL DEFAULT 'info',stage TEXT,municipality TEXT,source_id TEXT,message TEXT NOT NULL,details TEXT);

CREATE TABLE radar_history(history_id INTEGER PRIMARY KEY AUTOINCREMENT,radar_id TEXT NOT NULL,source TEXT NOT NULL,version_hash TEXT NOT NULL,captured_at TEXT NOT NULL,valid_to TEXT,raw_json TEXT NOT NULL);

CREATE TABLE radar_validations(id INTEGER PRIMARY KEY AUTOINCREMENT,radar_id TEXT NOT NULL,checked_at TEXT NOT NULL,status TEXT NOT NULL,valid_from TEXT,valid_until TEXT,source TEXT,certificate TEXT,notes TEXT);

CREATE TABLE radars(id TEXT PRIMARY KEY,physical_radar_id TEXT,source TEXT NOT NULL,external_id TEXT,name TEXT NOT NULL,latitude REAL,longitude REAL,speed_limit INTEGER,speed_text TEXT,direction TEXT,status TEXT NOT NULL DEFAULT 'active',confidence INTEGER NOT NULL DEFAULT 90,municipality TEXT,state TEXT DEFAULT 'SP',road TEXT,km TEXT,radar_type TEXT,der_number TEXT,serial_number TEXT,schedule TEXT,study_url TEXT,source_url TEXT,source_date TEXT,position_quality TEXT,inmetro_registration TEXT,lanes INTEGER,local_code TEXT,quality_grade TEXT,first_seen TEXT NOT NULL,last_seen TEXT NOT NULL,current_hash TEXT NOT NULL,raw_json TEXT NOT NULL, ingested_by TEXT, ingestion_batch TEXT, provenance_note TEXT);

CREATE TABLE road_network_meta(id INTEGER PRIMARY KEY CHECK(id=1), source_url TEXT, fetched_at TEXT, segments INTEGER DEFAULT 0, usable_segments INTEGER DEFAULT 0, sha256 TEXT, error TEXT);

CREATE TABLE road_object_history(history_id INTEGER PRIMARY KEY AUTOINCREMENT,object_id TEXT NOT NULL,source TEXT NOT NULL,captured_at TEXT NOT NULL,raw_json TEXT NOT NULL);

CREATE TABLE road_objects(id TEXT PRIMARY KEY,source TEXT NOT NULL,external_id TEXT,object_type TEXT NOT NULL,name TEXT,latitude REAL,longitude REAL,municipality TEXT,state TEXT DEFAULT 'SP',status TEXT DEFAULT 'active',confidence INTEGER DEFAULT 70,official INTEGER DEFAULT 0,speed_limit INTEGER,direction TEXT,timing_mode TEXT DEFAULT 'unknown',cycle_seconds REAL,green_seconds REAL,red_seconds REAL,adaptive INTEGER DEFAULT 0,timing_source TEXT,source_url TEXT,source_date TEXT,first_seen TEXT NOT NULL,last_seen TEXT NOT NULL,raw_json TEXT NOT NULL, ingested_by TEXT, ingestion_batch TEXT, provenance_note TEXT);

CREATE TABLE signal_networks(id TEXT PRIMARY KEY,municipality TEXT NOT NULL,name TEXT NOT NULL,mode TEXT NOT NULL,count_known INTEGER,live_timing INTEGER DEFAULT 0,description TEXT,source_url TEXT,source_date TEXT,last_seen TEXT NOT NULL);

CREATE TABLE source_attempts(id INTEGER PRIMARY KEY AUTOINCREMENT,municipality TEXT NOT NULL,source_id TEXT,attempted_at TEXT NOT NULL,status TEXT NOT NULL,item_count INTEGER DEFAULT 0,mapped_count INTEGER DEFAULT 0,diagnostic TEXT,url TEXT);

CREATE TABLE source_gaps(municipality TEXT PRIMARY KEY,status TEXT NOT NULL DEFAULT 'needs_source',reason TEXT,attempts INTEGER DEFAULT 0,last_checked TEXT,next_retry TEXT,notes TEXT);

CREATE TABLE source_registry(source_id TEXT PRIMARY KEY,name TEXT NOT NULL,scope TEXT,coverage TEXT,mode TEXT,priority INTEGER DEFAULT 50,url TEXT,official INTEGER DEFAULT 1,enabled INTEGER DEFAULT 1,last_seen TEXT,notes TEXT);

CREATE TABLE source_syncs(source_id TEXT PRIMARY KEY,status TEXT NOT NULL,started_at TEXT,finished_at TEXT,http_status INTEGER,imported INTEGER DEFAULT 0,updated INTEGER DEFAULT 0,unchanged INTEGER DEFAULT 0,skipped INTEGER DEFAULT 0,mapped INTEGER DEFAULT 0,roads INTEGER DEFAULT 0,source_url TEXT,error TEXT,diagnostic TEXT);

CREATE TABLE update_queue(id INTEGER PRIMARY KEY AUTOINCREMENT,municipality TEXT,category TEXT NOT NULL,source_id TEXT NOT NULL,label TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'pending',discovered_at TEXT NOT NULL,applied_at TEXT,details TEXT);