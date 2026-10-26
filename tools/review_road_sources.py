"""B.1 evidence review. Writes ONLY the explicitly isolated validation database.

No production URL, geocoder, inferred station coordinates or fixture import.
"""
import sys
import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
ROOT=Path(__file__).resolve().parents[1]
ART=ROOT/'artifacts/navigation-intelligence-v3-phase-b1'


def run():
    import os
    os.environ.update(DATABASE_BACKEND='sqlite',RELAS_ENV='development',VERCEL='0')
    import db
    from community import Municipalities
    from road_data import Service
    from road_data.coordinate_review import official_prf_review,toll_review
    from road_data.adapters import iso
    from road_data.registry import SOURCES
    database=ART/'private/validation.sqlite'
    service=Service(lambda:db.connect(database));service.initialize()
    municipalities=Municipalities(ROOT)
    package=json.loads((ART/'private/antt-prf-package.json').read_text(encoding='utf-8'))['result']
    assert package.get('license_id')=='cc-by'
    resource=next(r for r in package['resources'] if str(r.get('format')).upper()=='JSON')
    candidates=json.loads((ART/'private/antt-prf.json').read_text(encoding='utf-8'))['PRF']
    old=service.items(include_inactive=True,limit=10000)
    reviews=[official_prf_review(r,candidates,municipalities.city) for r in old if r['source_id']=='prf-sp']
    tolls=[toll_review(r,municipalities.city) for r in old if r['source_id']=='antt-tolls']
    for review in reviews:
        review.update(evidence_url=resource['url'],coordinate_source_updated_at=resource.get('last_modified'),license='CC BY (ANTT coordinate record)')
    with service.connect() as c:
        for row in reviews+tolls:
            evidence=dict(row)
            if row.get('official_candidate'):evidence['published_name']=row['official_candidate'].get('nome_do_prf')
            c.execute('INSERT INTO road_location_reviews(event_id,lon,lat,coordinate_quality,confidence,coordinate_source,approval_status,evidence_json,reviewed_at) VALUES(?,?,?,?,?,?,?,?,?) ON CONFLICT(event_id) DO UPDATE SET lon=excluded.lon,lat=excluded.lat,coordinate_quality=excluded.coordinate_quality,confidence=excluded.confidence,coordinate_source=excluded.coordinate_source,approval_status=excluded.approval_status,evidence_json=excluded.evidence_json,reviewed_at=excluded.reviewed_at',
                      (row['event_id'],row['lon'],row['lat'],row['coordinate_quality'],row['confidence'],row['coordinate_source'],row['status'],json.dumps(evidence,ensure_ascii=False),iso()))
    checks={
        'artesp-occurrences':('CC BY-NC 4.0','https://ccm.artesp.sp.gov.br/rodovias/api/docs/',True,True,'Non-commercial; attribution; portal terms acceptance required','Configure backend occurrence API credential'),
        'artesp-interventions':('CC BY-NC 4.0','https://ccm.artesp.sp.gov.br/rodovias/api/docs/',True,True,'Non-commercial; attribution; portal terms acceptance required','Configure backend intervention API credential'),
        'antt-tolls':('CC BY (catalog does not specify version)','https://dados.antt.gov.br/dataset/praca-de-pedagio',True,True,'Attribution required; current catalog snapshot is not a real-time operation guarantee','Review conflicting coordinates; collect within daily cache interval'),
        'prf-sp':('CC BY (ANTT coordinates); CC BY-ND 3.0 (original PRF directory)','https://dados.antt.gov.br/dataset/prf',True,True,'Map uses ANTT coordinate facts and label; original PRF text retained unchanged in inventory; attribution required','Resolve coordinate conflicts; do not geocode-promote administrative units'),
        'sp-aguas':('UNVERIFIED','https://apps.spaguas.sp.gov.br/sibh/',False,True,'Public endpoint; footer reserves rights; no source-specific redistribution grant confirmed','Obtain source-specific data license; configure scheduled backend collection'),
        'defesa-civil-sp':('UNVERIFIED','https://admin.defesacivil.sp.gov.br/previsaodotempo/sp/alertas',False,False,'No explicit reusable data license or machine-readable alert contract confirmed','Validate licensed machine-readable alert endpoint; HTML empty state is not a feed'),
        'pmrv-sp':('UNVERIFIED','https://www4.policiamilitar.sp.gov.br/unidades/cprv/',False,False,'Current source and data license not confirmed','Obtain current official dataset/endpoint and redistribution terms'),
        'artesp-tolls':('ARTESP portal data terms (June 2025)','https://dadosabertos.artesp.sp.gov.br/terms',True,False,'Attribution, integrity, no endorsement; dataset-specific restrictions prevail','Locate current geographic plaza inventory, not traffic statistics'),
        'official-support':('UNVERIFIED','https://www.der.sp.gov.br/',False,False,'No source-specific data license/feed confirmed','Validate official support inventory, coordinates and license'),
    }
    with service.connect() as c:
        for source in SOURCES:
            sid=source['source_id'];license,terms,verified,endpoint,restrictions,action=checks[sid]
            evidence={'checked_at':iso(),'terms_url':terms,'license_basis':'explicit publisher catalog/docs' if verified else 'no explicit source-specific grant confirmed','coordinate_dataset_url':resource['url'] if sid=='prf-sp' else None}
            c.execute('INSERT INTO road_source_reviews(source_id,license,terms_url,commercial_restrictions,attribution_required,last_terms_check,license_verified,endpoint_verified,blocker,next_action,evidence_json,reviewed_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(source_id) DO UPDATE SET license=excluded.license,terms_url=excluded.terms_url,commercial_restrictions=excluded.commercial_restrictions,attribution_required=excluded.attribution_required,last_terms_check=excluded.last_terms_check,license_verified=excluded.license_verified,endpoint_verified=excluded.endpoint_verified,next_action=excluded.next_action,evidence_json=excluded.evidence_json,reviewed_at=excluded.reviewed_at',
                      (sid,license,terms,restrictions,int(verified),iso(),int(verified),int(endpoint),None,action,json.dumps(evidence,ensure_ascii=False),iso()))
    for name,values in [('prf-coordinate-review.json',reviews),('antt-coordinate-review.json',tolls)]:
        (ART/name).write_text(json.dumps(values,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    summary={'prf_records':len(reviews),'prf_approved':sum(r['status']=='APPROVED' for r in reviews),'prf_conflicts':sum(r['coordinate_quality']=='CONFLICT' for r in reviews),'tolls':len(tolls),'tolls_approved':sum(r['status']=='APPROVED' for r in tolls),'toll_conflicts':sum(r['coordinate_quality']=='CONFLICT' for r in tolls),'no_geocoding_used':True,'local_calibrated_BR_network_available':False,'production_modified':False}
    (ART/'COORDINATE_SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8');print(json.dumps(summary))


if __name__=='__main__':run()
