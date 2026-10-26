"""Explicit Phase-B migration/sync. Never runs on app import or deployment."""
import argparse
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from runtime_config import load_environment
load_environment()
import db
from road_data import Service


def main():
    import json
    p=argparse.ArgumentParser();p.add_argument('action',choices=['migrate','sync','health','diagnostics'])
    p.add_argument('--sqlite',help='Explicit SQLite target; production SQLite is never inferred')
    p.add_argument('--source');args=p.parse_args()
    if db.backend()=='sqlite' and not args.sqlite:p.error('--sqlite is required in SQLite mode')
    if args.sqlite:
        import os
        os.environ['DATABASE_BACKEND']='sqlite'
        Path(args.sqlite).parent.mkdir(parents=True,exist_ok=True)
    s=Service(lambda:db.connect(args.sqlite))
    if args.action=='migrate':
        if args.sqlite and Path(args.sqlite).exists():
            import sqlite3,datetime
            target=Path(args.sqlite+'.phase-b-'+datetime.datetime.now().strftime('%Y%m%d%H%M%S')+'.backup')
            with sqlite3.connect(args.sqlite) as old,sqlite3.connect(target) as backup:old.backup(backup)
        s.initialize();from road_data.schema import VERSION;result={'ok':True,'schema':VERSION}
    elif args.action=='sync':result=s.sync(args.source)
    elif args.action=='health':result=s.health()
    else:result=s.diagnostics()
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
