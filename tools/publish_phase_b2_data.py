"""Explicit release operation: additive auxiliary schema + reviewed real snapshot.

No credentials in CLI arguments, no legacy writes, no auto-run on app import.
Only the reviewed project/branch's connection file under ignored B.2/private is used.
"""
import sys,os,json,re,sqlite3,hashlib
from pathlib import Path
from urllib.parse import urlsplit
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import db
from road_data.schema import apply,VERSION
A=Path('artifacts/navigation-intelligence-v3-phase-b2')
ORDER=['road_data_sources','road_source_reviews','road_event','road_location_reviews','road_infrastructure_reviews','event_evidence','road_source_logs','road_source_history','road_source_catalogs','road_event_matches','road_poll_budget']

def main():
    from psycopg import sql
    before=json.loads((A/'production-before.json').read_text())
    assert before['target_project']=='shy-art-03849128' and before['target_branch_id']=='br-old-water-b4gz2ktq'
    assert before['auxiliary_tables_existing']==[], 'Existing auxiliary state: explicit merge review required; refusing overwrite'
    url=(A/'private/release-production-url.txt').read_text(encoding='utf-8-sig').strip()
    assert hashlib.sha256(urlsplit(url).hostname.encode()).hexdigest()==before['endpoint_sha256']
    src=sqlite3.connect(A/'private/validation.sqlite');src.row_factory=sqlite3.Row
    assert src.execute("SELECT count(*) FROM road_event WHERE event_id LIKE '%TEST%' OR payload_json LIKE '%\"TEST\"%'").fetchone()[0]==0
    counts={};legacy={}
    with db.Postgres(url) as c:
        for n,v in before['counts'].items():
            assert re.fullmatch('[a-z_]+',n)
            legacy[n]=c.execute('SELECT count(*) FROM '+n).fetchone()[0]
            assert legacy[n]==v, 'Legacy count changed since audit; inspect before continuing'
        names=[r[0] for r in c.execute("SELECT tablename FROM pg_tables WHERE schemaname='public'")]
        assert not any(n in names for n in ORDER), 'Auxiliary tables appeared since audit; no overwrite allowed'
        apply(c)
        for table in ORDER:
            cols=[r[1] for r in src.execute('PRAGMA table_info('+table+')')]
            rows=[tuple(r) for r in src.execute('SELECT * FROM '+table)]
            # Client viewport captures are deliberately not imported as production diagnostics.
            if table=='road_data_sources':
                lease=cols.index('lease_until');rows=[tuple(0 if i==lease else v for i,v in enumerate(row)) for row in rows]
            statement=sql.SQL('COPY {} ({}) FROM STDIN').format(sql.Identifier(table),sql.SQL(',').join(map(sql.Identifier,cols)))
            with c.raw.cursor().copy(statement) as stream:
                for row in rows:stream.write_row(row)
            target=c.execute('SELECT count(*) FROM '+table).fetchone()[0];assert target==len(rows)
            counts[table]={'source':len(rows),'target':target}
        after={n:c.execute('SELECT count(*) FROM '+n).fetchone()[0] for n in legacy}
        assert legacy==after,'Legacy count drift: transaction rolled back'
    src.close()
    report={'schema_version':VERSION,'target_project':before['target_project'],'target_branch':'production','database':'neondb','operation':'explicit additive schema + real auxiliary snapshot COPY in one transaction','table_counts':counts,'legacy_before':legacy,'legacy_after':after,'legacy_unchanged':legacy==after,'local_sqlite_preserved':True,'client_diagnostics_imported':False,'fixture_rows':0,'existing_auxiliary_rows_overwritten':0}
    (A/'production-data-publish.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({'schema':VERSION,'real_objects':counts['road_event'],'sources':counts['road_data_sources'],'legacy_unchanged':True}))

if __name__=='__main__':
    try:main()
    except Exception as e:
        # Do not print driver messages, SQL parameters, paths with credentials or DSNs.
        print('Auxiliary publication FAILED; transaction rollback requested; error_type='+type(e).__name__,file=sys.stderr);sys.exit(1)
