"""Lossless, transactional, explicitly invoked migration. No SQLite writes.

Usage: python tools/migrate_sqlite_to_neon.py --sqlite PATH --target-env NEON_MIGRATION_URL
Default is a read-only plan. Pass --apply after checking the target inventory.
Existing equal primary-key rows are skipped; differing rows abort the entire
transaction, never overwrite a better destination record. No automatic deletes.
"""
import argparse
import hashlib
import json
import os
import sqlite3
import sys
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from runtime_config import load_environment
from db import Postgres
from db.migrations import apply


def quote(name):
    return '"'+name.replace('"','""')+'"'


def digest(rows):
    h = hashlib.sha256()
    # Stable across engines, independent of row/order/collation. Includes NULLs,
    # all columns, JSON bytes, timestamps and every historical row.
    for encoded in sorted(json.dumps(list(r),ensure_ascii=False,separators=(',',':')) for r in rows):
        h.update(encoded.encode()); h.update(b'\n')
    return h.hexdigest()


def migrate(source, url, output, execute=False):
    source=Path(source).resolve(); output=Path(output); output.mkdir(parents=True,exist_ok=True)
    if not source.is_file(): raise ValueError('Source SQLite does not exist')
    src=sqlite3.connect(source.as_uri()+'?mode=ro',uri=True)
    try:
        tables=[r[0] for r in src.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
        definitions={t:src.execute('PRAGMA table_info('+quote(t)+')').fetchall() for t in tables}
        report={'started_at':datetime.now(timezone.utc).isoformat(),'mode':'apply' if execute else 'plan','tables':{},'verified':False}
        with Postgres(url) as pg:
            existing=pg.execute("SELECT table_name FROM information_schema.tables WHERE table_schema=current_schema() ORDER BY table_name").fetchall()
            report['destination_tables_before']=[r[0] for r in existing]
            for t in tables:
                rows=src.execute('SELECT * FROM '+quote(t)).fetchall()
                report['tables'][t]={'source':len(rows),'source_sha256':digest(rows)}
            if not execute:
                (output/'migration-plan.json').write_text(json.dumps(report,indent=2),encoding='utf8');src.close();return report
            # Backup API includes committed WAL pages and is a consistent snapshot.
            backups=output/'backups';backups.mkdir(exist_ok=True)
            backup=(backups/('radar-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')+'.sqlite')).resolve()
            with closing(sqlite3.connect(backup)) as dst:src.backup(dst)
            src.close()
            src=sqlite3.connect(backup.as_uri()+'?mode=ro',uri=True)
            snapshot_tables=[r[0] for r in src.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
            if snapshot_tables!=tables:raise ValueError('SQLite schema changed while taking backup; retry with local writers stopped')
            report['backup_created']=True
            apply(pg)
            pg.raw.execute("SELECT pg_advisory_xact_lock(hashtext('relas-sqlite-import'))")
            report['caches']={}
            for name in ('der_road_network.json','geocode_cache.json','bumps_cache.json'):
                cache=source.parent/name
                if not cache.is_file():continue
                contents=cache.read_text(encoding='utf-8-sig')
                json.loads(contents)  # Refuse a corrupt cache instead of silently losing it.
                inserted=pg.raw.execute('INSERT INTO runtime_state(key,value_json,updated_at) VALUES(%s,%s,%s) ON CONFLICT(key) DO NOTHING',(name,contents,report['started_at'])).rowcount
                report['caches'][name]={'inserted':inserted,'bytes':cache.stat().st_size}
            for t in tables:
                definitions[t]=src.execute('PRAGMA table_info('+quote(t)+')').fetchall()
                columns=[r[1] for r in definitions[t]];keys=[r[1] for r in sorted(definitions[t],key=lambda r:r[5]) if r[5]]
                if not keys: raise ValueError('No stable primary key: '+t)
                target_columns={r[0] for r in pg.raw.execute('SELECT column_name FROM information_schema.columns WHERE table_schema=current_schema() AND table_name=%s',(t,))}
                if not set(columns)<=target_columns: raise ValueError('Unmapped columns in '+t)
                sql_columns=','.join(map(quote,columns))
                target_rows=[tuple(r.values()) for r in pg.raw.execute('SELECT '+sql_columns+' FROM '+quote(t))]
                key_indexes=[columns.index(k) for k in keys]
                target={tuple(r[i] for i in key_indexes):r for r in target_rows}
                rows=src.execute('SELECT '+sql_columns+' FROM '+quote(t)).fetchall()
                additions=[]
                for row in rows:
                    old=target.get(tuple(row[i] for i in key_indexes))
                    if old is not None:
                        if old!=row: raise ValueError('Destination conflict in '+t+'; transaction rolled back')
                    else: additions.append(row)
                # COPY only missing rows inside the same transaction. No lossy upsert.
                with pg.raw.cursor() as cursor:
                    with cursor.copy('COPY '+quote(t)+' ('+sql_columns+') FROM STDIN') as copy:
                        for row in additions: copy.write_row(row)
                after=[tuple(r.values()) for r in pg.raw.execute('SELECT '+sql_columns+' FROM '+quote(t))]
                source_keys={tuple(r[i] for i in key_indexes) for r in rows}
                subset=[r for r in after if tuple(r[i] for i in key_indexes) in source_keys]
                before_hash=digest(rows);after_hash=digest(subset)
                if len(subset)!=len(rows) or before_hash!=after_hash: raise ValueError('Verification failed in '+t)
                report['tables'][t]={'source':len(rows),'destination':len(after),'inserted':len(additions),'matched':len(subset),'source_sha256':before_hash,'destination_sha256':after_hash}
                # Repair identities after importing explicit IDs, including empty tables.
                identities=pg.raw.execute("SELECT column_name FROM information_schema.columns WHERE table_schema=current_schema() AND table_name=%s AND is_identity='YES'",(t,)).fetchall()
                for identity in identities:
                    name=identity[0]
                    maximum=pg.raw.execute('SELECT max('+quote(name)+') FROM '+quote(t)).fetchone()[0]
                    pg.raw.execute('SELECT setval(pg_get_serial_sequence(%s,%s),%s,%s)',(t,name,maximum or 1,maximum is not None))
            total_hash=hashlib.sha256(json.dumps({t:r['source_sha256'] for t,r in report['tables'].items()},sort_keys=True).encode()).hexdigest()
            pg.raw.execute('INSERT INTO migration_imports(snapshot_sha256,imported_at,counts_json) VALUES(%s,%s,%s) ON CONFLICT DO NOTHING',(total_hash,report['started_at'],json.dumps(report['tables'])))
            report['verified']=True
        src.close()
        report['finished_at']=datetime.now(timezone.utc).isoformat()
        (output/'migration-result.json').write_text(json.dumps(report,indent=2),encoding='utf8')
        return report

    finally:src.close()


def main():
    load_environment();parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sqlite',required=True);parser.add_argument('--target-env',default='NEON_MIGRATION_URL')
    parser.add_argument('--output',default=str(ROOT/'artifacts/vercel-neon'))
    parser.add_argument('--apply',action='store_true');args=parser.parse_args()
    url=os.environ.get(args.target_env)
    if not url: parser.error('Missing target environment variable')
    if '-pooler.' in url: parser.error('Migration requires a direct connection')
    try:
        result=migrate(args.sqlite,url,args.output,args.apply)
        print(json.dumps({'mode':result['mode'],'tables':len(result['tables']),'records':sum(t['source'] for t in result['tables'].values()),'verified':result['verified']}))
    except Exception as error:
        # Driver errors may include a connection URI; don't echo them.
        print('Migration failed: '+(str(error) if isinstance(error,ValueError) else type(error).__name__),file=sys.stderr)
        raise SystemExit(1)


if __name__=='__main__':main()
