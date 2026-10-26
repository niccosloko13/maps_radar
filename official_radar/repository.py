"""Append-only, isolated pilot archive. No connection to the app DB or production."""
import json
import sqlite3
from pathlib import Path
from .normalize import digest


class Repository:
    def __init__(self,path):
        path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
        self.connection=sqlite3.connect(path)
        self.connection.row_factory=sqlite3.Row
        self.connection.executescript('''
        PRAGMA foreign_keys=ON;
        CREATE TABLE IF NOT EXISTS source_snapshots(id TEXT PRIMARY KEY,source_url TEXT NOT NULL,retrieved_at TEXT NOT NULL,sha256 TEXT NOT NULL,metadata_json TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS equipment(id TEXT PRIMARY KEY);
        CREATE TABLE IF NOT EXISTS equipment_versions(id TEXT PRIMARY KEY,equipment_id TEXT NOT NULL REFERENCES equipment(id),snapshot_id TEXT NOT NULL REFERENCES source_snapshots(id),municipality TEXT NOT NULL,uf TEXT NOT NULL,payload_json TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS equipment_verifications(id TEXT PRIMARY KEY,equipment_id TEXT NOT NULL REFERENCES equipment(id),verification_date TEXT,valid_until TEXT,payload_json TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS equipment_evidence(id TEXT PRIMARY KEY,equipment_id TEXT NOT NULL,claim TEXT NOT NULL,source_url TEXT NOT NULL,retrieved_at TEXT NOT NULL,payload_json TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS municipal_versions(id TEXT PRIMARY KEY,equipment_id TEXT NOT NULL,payload_json TEXT NOT NULL);
        CREATE INDEX IF NOT EXISTS idx_equipment_city ON equipment_versions(municipality,uf);
        CREATE INDEX IF NOT EXISTS idx_verification_date ON equipment_verifications(equipment_id,verification_date);
        CREATE INDEX IF NOT EXISTS idx_evidence_equipment ON equipment_evidence(equipment_id,claim);
        ''')

    def close(self):
        self.connection.close()

    def evidence(self,equipment_id):
        return [json.loads(r[0]) for r in self.connection.execute('SELECT payload_json FROM equipment_evidence WHERE equipment_id=?',(equipment_id,))]

    def record_source(self,meta):
        sid=digest([meta['source_url'],meta['sha256']])
        self.connection.execute('INSERT INTO source_snapshots VALUES(?,?,?,?,?) ON CONFLICT(id) DO NOTHING',(sid,meta['source_url'],meta['retrieved_at'],meta['sha256'],json.dumps(meta)))
        return sid

    def add_evidence(self,e):
        mandatory={'equipment_id','source_authority','source_type','claim','effective_from','effective_until','retrieved_at','source_url','raw_reference','confidence'}
        if not mandatory.issubset(e):
            raise ValueError('Incomplete evidence provenance')
        self.connection.execute('INSERT INTO equipment_evidence VALUES(?,?,?,?,?,?) ON CONFLICT(id) DO NOTHING',(digest(e),e['equipment_id'],e['claim'],e['source_url'],e['retrieved_at'],json.dumps(e,ensure_ascii=False)))

    def ingest(self,instruments,meta,municipal=()):
        c=self.connection
        with c:
            sid=self.record_source(meta)
            for r in instruments:
                eid=r['equipment_id'];c.execute('INSERT INTO equipment VALUES(?) ON CONFLICT(id) DO NOTHING',(eid,))
                c.execute('INSERT INTO equipment_versions VALUES(?,?,?,?,?,?) ON CONFLICT(id) DO NOTHING',(digest([eid,sid,r['raw_payload']]),eid,sid,r['municipality'],r['uf'],json.dumps(r,ensure_ascii=False)))
                for h in r['verifications']:
                    c.execute('INSERT INTO equipment_verifications VALUES(?,?,?,?,?) ON CONFLICT(id) DO NOTHING',(digest([eid,h['raw_payload']]),eid,h['verification_date'],h['valid_until'],json.dumps(h,ensure_ascii=False)))
                    self.add_evidence(dict(equipment_id=eid,source_authority='INMETRO_PSIE',source_type='official_open_data',claim='METROLOGY_VERIFICATION',effective_from=h['valid_from'],effective_until=h['valid_until'],retrieved_at=h['retrieved_at'],source_url=h['source_url'],raw_reference=digest(h['raw_payload']),confidence='EXACT',value=h))
                for claim,field in [('SERIAL_ID','serial_number'),('INMETRO_ID','inmetro_number')]:
                    for lane in r['lanes']:
                        if lane.get(field):
                            self.add_evidence(dict(equipment_id=eid,source_authority='INMETRO_PSIE',source_type='official_open_data',claim=claim,effective_from=None,effective_until=None,retrieved_at=r['retrieved_at'],source_url=r['source_url'],raw_reference=digest(lane['raw_payload']),confidence='EXACT',value=lane[field]))
            for r in municipal:
                c.execute('INSERT INTO municipal_versions VALUES(?,?,?) ON CONFLICT(id) DO NOTHING',(digest([r['equipment_id'],r['raw_reference']]),r['equipment_id'],json.dumps(r,ensure_ascii=False)))
                for claim,value in [('OFFICIAL_LISTING',r['address_raw']),('SPEED_LIMIT',r['speed_limit']),('DIRECTION',r['direction_raw'])]:
                    self.add_evidence(dict(equipment_id=r['equipment_id'],source_authority=r['authority'],source_type='official_municipal',claim=claim,effective_from=r['effective_from'],effective_until=None,retrieved_at=r['retrieved_at'],source_url=r['source_url'],raw_reference=r['raw_reference'],confidence='EXACT',value=value))

    def instrument(self,eid):
        rows=[json.loads(r[0]) for r in self.connection.execute('SELECT payload_json FROM equipment_versions WHERE equipment_id=?',(eid,))]
        if not rows:
            return None
        r=max(rows,key=lambda r:r['retrieved_at'])
        r['verifications']=[json.loads(h[0]) for h in self.connection.execute('SELECT payload_json FROM equipment_verifications WHERE equipment_id=? ORDER BY verification_date',(eid,))]
        return r

    def counts(self):
        tables=['source_snapshots','equipment','equipment_versions','equipment_verifications','equipment_evidence','municipal_versions']
        return {t:self.connection.execute('SELECT COUNT(*) FROM '+t).fetchone()[0] for t in tables}
