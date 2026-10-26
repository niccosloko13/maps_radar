"""Persistent auxiliary store and request-bound polling. No poll on map requests."""
import hashlib
import json
import os
import time
import uuid
import urllib.request
import urllib.error
import ssl
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import urlparse, urlencode, urljoin
import db
from . import adapters as A
from .registry import SOURCES, BY_ID, KEYS, credential
from .geometry import finite, corridor


def dump(value):return json.dumps(value,ensure_ascii=False,separators=(',',':'),sort_keys=True)
def at(seconds=None):return datetime.fromtimestamp(seconds or time.time(),timezone.utc).isoformat()
def epoch(value):
    try:return datetime.fromisoformat(value.replace('Z','+00:00')).timestamp()
    except (ValueError,TypeError,AttributeError):return 0


def http(url,headers):
    # Verified system TLS, no verify=False; secrets never enter error messages.
    ctx=ssl.create_default_context()
    bundle=Path(__file__).resolve().parents[1]/'certs'/'cacert.pem'
    if bundle.exists():ctx.load_verify_locations(str(bundle))
    try:
        import certifi
        ctx.load_verify_locations(certifi.where())
    except ImportError:pass
    class OfficialRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self,req,fp,code,msg,hdrs,newurl):
            host=urlparse(newurl).hostname or ''
            allowed=host.endswith('.sp.gov.br') or host=='www.gov.br' or host=='dados.antt.gov.br'
            if urlparse(newurl).scheme!='https' or not allowed or headers.get('Authorization') and host!=urlparse(url).hostname:raise ValueError('Unsafe official source redirect')
            return super().redirect_request(req,fp,code,msg,hdrs,newurl)
    try:
        opener=urllib.request.build_opener(urllib.request.HTTPSHandler(context=ctx),OfficialRedirect())
        with opener.open(urllib.request.Request(url,headers={'User-Agent':'Relas/PhaseB (public road safety)',**headers}),timeout=15) as r:
            body=r.read(8_000_001)
            if len(body)>8_000_000:raise A.SchemaChanged('Source payload exceeds 8MB')
            return r.status,dict(r.headers),body
    except urllib.error.HTTPError as e:return e.code,dict(e.headers),b''


class Service:
    def __init__(self,connect,transport=http,clock=time.time):self.connect=connect;self.http=transport;self.clock=clock

    def installed(self):
        with self.connect() as c:return db.table_exists(c,'road_data_sources')

    def initialize(self):
        from .schema import apply
        with self.connect() as c:
            apply(c)
            for s in SOURCES:
                names=list(s)
                c.execute('INSERT INTO road_data_sources('+','.join(names)+') VALUES('+','.join('?' for _ in names)+') ON CONFLICT(source_id) DO NOTHING',tuple(s.values()))

    def health(self):
        if not self.installed():return [dict(s,installed=False,status='AUTH_REQUIRED' if s['source_id'] in KEYS and not credential(s['source_id']) else 'BLOCKED_LICENSE',freshness_status='UNKNOWN',blocker='SOURCE_SCHEMA_NOT_INSTALLED; LICENSE_REVIEW_REQUIRED',next_action='Apply the explicit additive source migration and reviewed policies',credential_configured=bool(credential(s['source_id']))) for s in SOURCES]
        with self.connect() as c:rows=[dict(r) for r in c.execute('SELECT * FROM road_data_sources ORDER BY category,source_id')]
        with self.connect() as c:
            reviews={r['source_id']:dict(r) for r in c.execute('SELECT * FROM road_source_reviews')} if db.table_exists(c,'road_source_reviews') else {}
            locations=[dict(r) for r in c.execute('SELECT e.source_id,l.approval_status FROM road_location_reviews l JOIN road_event e ON e.event_id=l.event_id')] if db.table_exists(c,'road_location_reviews') else []
        from .readiness import source_readiness
        for s in rows:
            age=self.clock()-epoch(s['last_success_at']);interval=s['poll_interval_seconds']
            s['credential_configured']=bool(credential(s['source_id'])) if s['source_id'] in KEYS else None
            if not s['enabled']:s['status']='DISABLED'
            elif s['source_id'] in KEYS and not s['credential_configured']:s['status']='AUTH_REQUIRED'
            s['freshness_status']='BROKEN' if not s['last_success_at'] else 'FRESH' if age<=interval*2 else 'AGING' if age<=interval*4 else 'STALE'
            if s['last_success_at'] and s['last_error']:s['freshness_status']='STALE'
            source_age=self.clock()-epoch(s['last_source_timestamp'])
            if s['last_source_timestamp'] and s['category']=='infrastructure' and s['freshness_status'] in ('FRESH','AGING'):
                if source_age>180*86400:s['freshness_status']='STALE'
                elif source_age>30*86400:s['freshness_status']='AGING'
            if s['freshness_status']=='STALE' and s['status']=='HEALTHY':s['status']='STALE'
            approved=sum(r['source_id']==s['source_id'] and r['approval_status']=='APPROVED' for r in locations)
            blocked=sum(r['source_id']==s['source_id'] and r['approval_status']!='APPROVED' for r in locations)
            s.update(source_readiness(s,reviews.get(s['source_id']),self.clock(),s['credential_configured'],approved,blocked))
            s['installed']=True;s.pop('cursor_json',None)
            s['response_headers']=json.loads(s.pop('response_headers_json') or '{}')
        return rows

    def reserve(self,sid):
        """Atomic SQL gate: survives Function instances, source leases and shared keys."""
        now=self.clock();key=credential(sid)
        bucket='artesp:'+hashlib.sha256(key.encode()).hexdigest() if sid in KEYS else sid
        interval=max(300,int(os.getenv('ARTESP_POLL_INTERVAL_SECONDS','300'))) if sid in KEYS else BY_ID[sid]['poll_interval_seconds']
        with self.connect() as c:
            c.execute('INSERT INTO road_poll_budget(bucket,next_at,window_start,requests,lease_until) VALUES(?,0,0,0,0) ON CONFLICT(bucket) DO NOTHING',(bucket,))
            # SQLite serializes this write; PostgreSQL locks only this bucket's row.
            result=c.execute('UPDATE road_poll_budget SET next_at=?,requests=CASE WHEN window_start<=? THEN 1 ELSE requests+1 END,window_start=CASE WHEN window_start<=? THEN ? ELSE window_start END,lease_until=? WHERE bucket=? AND next_at<=? AND lease_until<=? AND (window_start<=? OR requests<?)',
                (now+interval,now-3600,now-3600,now,now+45,bucket,now,now,now-3600,12 if sid in KEYS else 1000))
            if not result.rowcount:return None
            result=c.execute('UPDATE road_data_sources SET lease_until=?,last_attempt_at=?,next_attempt_at=? WHERE source_id=? AND enabled=1 AND lease_until<=? AND next_attempt_at<=?',(now+45,at(now),now+interval,sid,now,now))
            if not result.rowcount:c.rollback();return None
        return bucket

    def sync(self,sid,probe=False):
        if sid not in BY_ID:raise ValueError('Unknown official source')
        if not self.installed():return {'ok':False,'status':'NOT_CONFIGURED','error':'Apply tools/road_data.py migrate first'}
        if sid in KEYS and not credential(sid):
            with self.connect() as c:c.execute("UPDATE road_data_sources SET status='AUTH_REQUIRED',last_error='API credential required' WHERE source_id=?",(sid,))
            return {'ok':False,'status':'AUTH_REQUIRED'}
        url=BY_ID[sid]['base_url'];override=os.getenv('RELAS_'+sid.upper().replace('-','_')+'_URL')
        if override:
            # No arbitrary URL from Admin: configuration must point to an official HTTPS host.
            host=urlparse(override).hostname or ''
            if urlparse(override).scheme!='https' or not (host.endswith('.sp.gov.br') or host in ('www.gov.br','dados.antt.gov.br')):raise ValueError('Configured source must use an official HTTPS origin')
            if 'waze' in override.lower():raise ValueError('Waze is not an official road-data feed')
            url=override
        if sid in ('pmrv-sp','defesa-civil-sp') and not override:
            return {'ok':False,'status':'NOT_CONFIGURED','error':'No reviewed machine-readable source configured; portal is not an adapter'}
        bucket=self.reserve(sid)
        if bucket is None:return {'ok':False,'status':'RATE_LIMITED','error':'Polling interval, hourly quota or active lease'}
        start=self.clock();status=None;received=0;headers={};rows=[];complete=True
        log_id=uuid.uuid4().hex;contract_shape=[]
        try:
            params={};previous=None
            with self.connect() as c:
                state=dict(c.execute('SELECT * FROM road_data_sources WHERE source_id=?',(sid,)).fetchone())
                previous=json.loads(state['cursor_json']) if state['cursor_json'] else None
            if sid in KEYS:
                params={'limit':100,'offset':previous.get('offset',0) if previous else 0,'filtro_finalizada':1,
                        'include':'interdicoes,atualizacoes' if sid=='artesp-interventions' else 'fim,interdicoes,congestionamentos,atualizacoes'}
                url+='?'+urlencode(params)
            auth={'Authorization':'Api-Key '+credential(sid)} if sid in KEYS else {}
            status,headers,body=self.http(url,auth)
            headers={k.lower():v for k,v in headers.items()}
            if status!=200:raise RuntimeError('HTTP_'+str(status))
            if sid in ('artesp-tolls','official-support') and not override:
                from .artesp_assets import RESOURCE,records,normalize
                package=json.loads(body).get('result')
                if not isinstance(package,dict) or package.get('license_id')!='cc-by':raise A.SchemaChanged('ARTESP asset catalog/license changed')
                resource=next((r for r in package.get('resources',[]) if r.get('id')==RESOURCE),None)
                if not resource or urlparse(resource['url']).hostname!='dadosabertos.artesp.sp.gov.br':raise A.SchemaChanged('ARTESP reviewed resource missing/origin changed')
                code,_,download=self.http(resource['url'],{})
                if code!=200:raise RuntimeError('HTTP_'+str(code))
                inventory=list(records(download));received=len(inventory)
                rows=normalize(inventory,sid,A.timestamp(resource.get('last_modified')),at(start))
                cursor=None;complete=True;contract_shape=['CKAN cc-by',RESOURCE,sorted(inventory[0]) if inventory else []]
            elif sid=='antt-tolls':
                package=json.loads(body).get('result')
                if not isinstance(package,dict) or package.get('license_id')!='cc-by':raise A.SchemaChanged('ANTT catalog/license changed')
                resources=[r for r in package.get('resources',[]) if str(r.get('format','')).upper()=='JSON']
                if not resources:raise A.SchemaChanged('ANTT JSON resource missing')
                resource=max(resources,key=lambda r:r.get('last_modified') or '')
                if urlparse(resource['url']).hostname!='dados.antt.gov.br':raise A.SchemaChanged('ANTT resource origin changed')
                code,_,download=self.http(resource['url'],{})
                if code!=200:raise RuntimeError('HTTP_'+str(code))
                payload=json.loads(download);received=len(payload.get('praca-de-pedagio',[]));rows=A.antt_tolls(payload,resource.get('last_modified') or package.get('metadata_modified'),at(start))
                cursor=None;complete=True;contract_shape=['CKAN cc-by','praca-de-pedagio',sorted(payload['praca-de-pedagio'][0]) if received else []]
            elif sid=='prf-sp':
                text=body.decode('utf-8');page=A.Page();page.feed(text)
                links=sorted(set(urljoin(url,x) for x in page.links if urljoin(url,x).startswith(BY_ID[sid]['base_url']+'/') and not x.endswith('/view')))
                # Bounded official directory snapshot, one page per second, once/day.
                if not links:raise A.SchemaChanged('PRF index has no operational page links')
                if len(links)>30:raise A.SchemaChanged('PRF directory unexpectedly exceeds bounded contract')
                rows=A.prf_administrative(text,url,at(start))
                for index,target in enumerate(links):
                    if self.clock()-start>90:raise TimeoutError('Bounded PRF collection window exceeded')
                    if index:time.sleep(1)
                    status,_,unit=self.http(target,{})
                    if status!=200:raise RuntimeError('HTTP_'+str(status))
                    rows+=A.prf(unit.decode('utf-8'),target,at(start));received+=1
                contract_shape=['html','h1','address','publication_date']
                cursor=None;complete=True
            else:
                payload=json.loads(body);received=len(payload.get('results',payload.get('measurements',payload.get('features',[]))))
                sample=payload.get('results',payload.get('measurements',payload.get('features',[])))
                contract_shape=[sorted(payload),sorted(sample[0]) if sample and isinstance(sample[0],dict) else []]
                rows=A.artesp(payload,sid,at(start)) if sid in KEYS else A.sibh(payload,at(start)) if sid=='sp-aguas' and not override else A.official_geojson(payload,sid,at(start))
                cursor=None
                if sid in KEYS:
                    next_offset=payload['meta'].get('next_offset')
                    if next_offset is not None:
                        if not isinstance(next_offset,int) or next_offset<=params['offset']:raise A.SchemaChanged('ARTESP non-advancing pagination')
                        cursor={'offset':next_offset,'rows':(previous.get('rows',[]) if previous else [])+rows};complete=False
                    elif previous:rows=previous.get('rows',[])+rows
            safe_headers={k:headers[k][:300] for k in ('x-ratelimit-limit','x-ratelimit-remaining','retry-after','x-data-license','x-api-terms-version','x-api-terms-accept-by') if k in headers}
            write_counts=self.persist(sid,rows,at(start)) if complete and not probe else {}
            with self.connect() as c:
                schema_hash=hashlib.sha256(dump(contract_shape).encode()).hexdigest()
                c.execute('UPDATE road_data_sources SET status=?,freshness_status=?,last_error=NULL,last_success_at=CASE WHEN ?=1 THEN ? ELSE last_success_at END,last_source_timestamp=?,schema_hash=?,last_schema_validation=?,cursor_json=?,response_headers_json=?,terms_version=?,lease_until=0 WHERE source_id=?',
                    ('HEALTHY' if complete else 'DEGRADED','FRESH' if complete else 'AGING',int(complete and not probe),at(start),max((r['source_updated_at'] or '' for r in rows),default='') or None,schema_hash,at(start),dump(cursor) if cursor else None,dump(safe_headers),headers.get('x-api-terms-version'),sid))
            result={'ok':True,'status':'HEALTHY' if complete else 'PAGINATING','received':received,'normalized':len(rows),'snapshot_published':complete and not probe,'probe':probe,**write_counts}
            if headers.get('x-ratelimit-remaining')=='0':
                with self.connect() as c:c.execute('UPDATE road_poll_budget SET next_at=window_start+3600 WHERE bucket=?',(bucket,))
        except Exception as e:
            # Error class/status only: response bodies, URLs and credentials never logged.
            error='PARSER_DEGRADED' if isinstance(e,(A.SchemaChanged,ValueError,KeyError,TypeError)) else 'HTTP_'+str(status) if status else type(e).__name__
            result={'ok':False,'status':'AUTH_REQUIRED' if status==401 else 'DEGRADED' if error=='PARSER_DEGRADED' else 'ERROR','error':error}
            retry=max(300,int(headers.get('retry-after','0'))) if str(headers.get('retry-after','0')).isdigit() else 3600
            with self.connect() as c:
                c.execute('UPDATE road_data_sources SET status=?,freshness_status=CASE WHEN last_success_at IS NULL THEN ? ELSE ? END,last_error=?,lease_until=0,next_attempt_at=? WHERE source_id=?',(result['status'],'BROKEN','STALE',error,self.clock()+retry,sid))
                if status==429:c.execute('UPDATE road_poll_budget SET next_at=? WHERE bucket=?',(self.clock()+max(retry,3600),bucket))
        finally:
            with self.connect() as c:c.execute('UPDATE road_poll_budget SET lease_until=0 WHERE bucket=?',(bucket,))
        with self.connect() as c:
            c.execute('INSERT INTO road_source_logs(log_id,source_id,started_at,finished_at,status,http_status,records_received,records_normalized,records_created,records_updated,records_expired,duplicates,errors,duration_ms,diagnostics_json) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                (log_id,sid,at(start),at(self.clock()),result['status'],status,received,len(rows),result.get('created',0),result.get('updated',0),result.get('expired',0),result.get('duplicates',0),result.get('error'),(self.clock()-start)*1000,dump(result)))
        return result

    def persist(self,sid,rows,captured,replace=True):
        with self.connect() as c:
            old=[dict(r) for r in c.execute('SELECT * FROM road_event WHERE source_id=?',(sid,))]
            old_ids={r['event_id'] for r in old};new_ids={r['event_id'] for r in rows}
            c.execute('INSERT INTO road_source_history(history_id,source_id,captured_at,snapshot_json) VALUES(?,?,?,?)',(uuid.uuid4().hex,sid,captured,dump(old)))
            if replace:c.execute("UPDATE road_event SET status='ended' WHERE source_id=?",(sid,))
            for r in rows:
                names=list(r);values=[dump(r[k]) if k in ('geometry','lane_impacts','payload_json') and r[k] is not None else r[k] for k in names]
                c.execute('INSERT INTO road_event('+','.join(names)+') VALUES('+','.join('?' for _ in names)+') ON CONFLICT(event_id) DO UPDATE SET '+','.join(k+'=excluded.'+k for k in names if k!='event_id'),values)
                fingerprint=hashlib.sha256(dump(r['payload_json']).encode()).hexdigest();eid=r['event_id']+':'+fingerprint
                c.execute('INSERT INTO event_evidence(evidence_id,event_id,source_id,external_id,retrieved_at,fingerprint,payload_json) VALUES(?,?,?,?,?,?,?) ON CONFLICT(evidence_id) DO NOTHING',(eid,r['event_id'],sid,r['external_id'],captured,fingerprint,dump(r['payload_json'])))
                if r['payload_json'].get('asset_review')=='ARTESP_ASSET_B2':
                    valid=r['payload_json']['coordinate_verified']
                    c.execute('INSERT INTO road_location_reviews(event_id,lon,lat,coordinate_quality,confidence,coordinate_source,approval_status,evidence_json,reviewed_at) VALUES(?,?,?,?,?,?,?,?,?) ON CONFLICT(event_id) DO UPDATE SET lon=excluded.lon,lat=excluded.lat,coordinate_quality=excluded.coordinate_quality,confidence=excluded.confidence,coordinate_source=excluded.coordinate_source,approval_status=excluded.approval_status,evidence_json=excluded.evidence_json,reviewed_at=excluded.reviewed_at',(r['event_id'],r['lon'],r['lat'],'OFFICIAL_COORDINATE' if valid else 'CONFLICT',.95 if valid else 0,'ARTESP Cadastro de Ativos; official coordinate + municipality polygon','APPROVED' if valid else 'BLOCKED',dump({'polygon_municipality':r['payload_json']['polygon_municipality'],'original_coordinate_retained_in_payload':True}),captured))
            count=c.execute('SELECT count(*) FROM road_event WHERE source_id=?',(sid,)).fetchone()[0]
            c.execute('UPDATE road_data_sources SET record_count=? WHERE source_id=?',(count,sid))
        self.match_candidates(sid,captured)
        return {'created':len(new_ids-old_ids),'updated':len(new_ids&old_ids),'expired':sum(r['status']=='active' and r['event_id'] not in new_ids for r in old) if replace else 0,'duplicates':len(rows)-len(new_ids)}

    def match_candidates(self,sid,captured):
        """Conservative review candidates; no destructive cross-source merge."""
        from .geometry import distance
        with self.connect() as c:
            rows=[dict(r) for r in c.execute("SELECT event_id,source_id,event_type,road,direction,lat,lon,start_at,km_start FROM road_event WHERE status='active' AND lon IS NOT NULL")]
            mine=[r for r in rows if r['source_id']==sid];others=[r for r in rows if r['source_id']!=sid]
            for a in mine:
                for b in others:
                    if not a['road'] or a['road']!=b['road'] or not a['direction'] or a['direction']!=b['direction'] or a['event_type']!=b['event_type']:continue
                    if abs(epoch(a['start_at'])-epoch(b['start_at']))>900 or distance([a['lon'],a['lat']],[b['lon'],b['lat']])>20:continue
                    ids=sorted([a['event_id'],b['event_id']]);mid=hashlib.sha256('|'.join(ids).encode()).hexdigest()
                    c.execute('INSERT INTO road_event_matches(match_id,left_event_id,right_event_id,status,reason,updated_at) VALUES(?,?,?,?,?,?) ON CONFLICT(match_id) DO UPDATE SET updated_at=excluded.updated_at',(mid,*ids,'REVIEW','same type/road/direction; <=20m; <=15min',captured))

    def items(self,bbox=None,record_class=None,include_inactive=False,filters=None,limit=1500):
        if not self.installed():return []
        where=['1=1'];args=[]
        if not include_inactive:where+= ["status='active'","(expires_at IS NULL OR expires_at>?)"];args.append(at(self.clock()))
        if record_class:where.append('record_class=?');args.append(record_class)
        with self.connect() as c:has_locations=db.table_exists(c,'road_location_reviews')
        if bbox:
            if isinstance(bbox,str):bbox=[float(n) for n in bbox.split(',')]
            if len(bbox)!=4 or not all(finite(n) for n in bbox) or not -180<=bbox[0]<bbox[2]<=180 or not -90<=bbox[1]<bbox[3]<=90:raise ValueError('Invalid bbox')
            where+=(["COALESCE(l.lon,e.max_lon)>=?","COALESCE(l.lon,e.min_lon)<=?","COALESCE(l.lat,e.max_lat)>=?","COALESCE(l.lat,e.min_lat)<=?"] if has_locations else ['max_lon>=?','min_lon<=?','max_lat>=?','min_lat<=?']);args += [bbox[0],bbox[2],bbox[1],bbox[3]]
        for key in ('source_id','event_type','road','municipality','severity','status'):
            if filters and filters.get(key):where.append(key+'=?');args.append(filters[key])
        if include_inactive and filters and filters.get('status')=='active':where.append('(expires_at IS NULL OR expires_at>?)');args.append(at(self.clock()))
        select='SELECT e.*,l.lon AS approved_lon,l.lat AS approved_lat,l.coordinate_quality AS approved_quality,l.confidence AS approved_confidence,l.coordinate_source AS approved_source,l.approval_status,l.evidence_json AS location_evidence FROM road_event e LEFT JOIN road_location_reviews l ON l.event_id=e.event_id' if has_locations else 'SELECT e.* FROM road_event e'
        with self.connect() as c:rows=[dict(r) for r in c.execute(select+' WHERE '+' AND '.join(where)+' ORDER BY CASE severity WHEN \'critical\' THEN 0 ELSE 1 END,updated_at DESC LIMIT ?',args+[limit])]
        health={s['source_id']:s for s in self.health()}
        with self.connect() as c:reviews={r['event_id']:dict(r) for r in c.execute('SELECT event_id,status,coordinate_quality FROM road_infrastructure_reviews')}
        for r in rows:
            for k in ('geometry','lane_impacts','payload_json'):r[k]=json.loads(r[k]) if r[k] else None
            source=health[r['source_id']];r.update(source_type='official',source=source['authority'],freshness=source['freshness_status'],source_status=source['status'],license=source['license'],attribution=source['attribution'])
            r['effective_status']='expired' if r['expires_at'] and epoch(r['expires_at'])<=self.clock() else r['status']
            # Do not expose tariffs without explicit validity and amount.
            p=r['payload_json'] or {};r['tariff']=p.get('tariff') if p.get('tariff_valid_until') and epoch(p['tariff_valid_until'])>self.clock() and finite(p.get('tariff')) else None
            r['concessionaire']=p.get('concessionaria')
            if r['event_type']=='RAIN_STATION':r.update(rainfall_mm=p.get('value'),measurement_window_hours=1,observation_type='station_accumulation')
            if r['record_class']=='infrastructure':r['coordinate_quality']=p.get('coordinate_quality') or ('official_geometry' if r['geometry'] else 'unmapped')
            r['review_status']=reviews.get(r['event_id'],{}).get('status')
            from .readiness import APPROVED_QUALITIES,station_freshness
            if r.get('approval_status')=='APPROVED' and r.get('approved_quality') in APPROVED_QUALITIES and finite(r.get('approved_lon')) and finite(r.get('approved_lat')):
                r.update(lon=r['approved_lon'],lat=r['approved_lat'],min_lon=r['approved_lon'],max_lon=r['approved_lon'],min_lat=r['approved_lat'],max_lat=r['approved_lat'],geometry={'type':'Point','coordinates':[r['approved_lon'],r['approved_lat']]},coordinate_quality=r['approved_quality'],coordinate_source=r['approved_source'],location_confidence=r['approved_confidence'])
                if r['source_id']=='prf-sp':
                    evidence=json.loads(r.get('location_evidence') or '{}')
                    r.update(description=evidence.get('published_name') or r['description'],municipality=evidence.get('municipality') or r['municipality'],source='ANTT / PRF',license='CC BY (ANTT coordinate record)',attribution='ANTT (coordinates); PRF (directory evidence)',coordinate_source_updated_at=evidence.get('coordinate_source_updated_at'))
                    if evidence.get('published_km') is not None:r['km_start']=evidence['published_km']
                    if evidence.get('published_direction'):r['direction']=evidence['published_direction']
            elif r.get('approved_quality'):r['coordinate_quality']=r['approved_quality']
            if r['event_type']=='RAIN_STATION':
                observation=station_freshness(p,self.clock(),source['last_success_at'],observed=epoch(r['retrieved_at'])>=epoch(source['last_success_at'])-1);r.update(observation_freshness=observation,freshness=observation['state'])
            coordinate_ok=r['source_id'] not in ('prf-sp','antt-tolls') or r.get('approval_status')=='APPROVED'
            observation_ok=r['event_type']!='RAIN_STATION' or r['observation_freshness']['current']
            r.update(freshness_kind=source['freshness_kind'],source_blocker=source['blocker'],next_action=source['next_action'],license_verified=source['license_verified'])
            r['map_eligible']=bool(r['effective_status']=='active' and r['geometry'] and source['enabled'] and source['license_verified'] and source['endpoint_verified'] and coordinate_ok and observation_ok)
            r['navigation_eligible']=bool(r['map_eligible'] and r['freshness'] in ('FRESH','AGING') and not source['last_error'] and r['event_type']!='RAIN_STATION')
            for key in ('approved_lon','approved_lat','approved_quality','approved_confidence','approved_source','location_evidence'):r.pop(key,None)
        return rows

    def review(self,event_id,proposal=None):
        if not self.installed():raise ValueError('Migration required')
        with self.connect() as c:
            row=c.execute("SELECT event_id FROM road_event WHERE event_id=? AND record_class='infrastructure'",(event_id,)).fetchone()
            if not row:raise ValueError('Infrastructure record not found')
            c.execute('INSERT INTO road_infrastructure_reviews(event_id,status,coordinate_quality,proposal_json,reviewed_at) VALUES(?,?,?,?,?) ON CONFLICT(event_id) DO UPDATE SET status=excluded.status,coordinate_quality=excluded.coordinate_quality,proposal_json=excluded.proposal_json,reviewed_at=excluded.reviewed_at',(event_id,'REVIEW','geocoded_proposal' if proposal else 'requires_review',dump(proposal) if proposal else None,at(self.clock())))
        return {'ok':True,'status':'REVIEW','published_to_map':False}

    def features(self,bbox,record_class=None,zoom=12,types=None):
        if not bbox:raise ValueError('bbox is required')
        rows=self.items(bbox,record_class);features=[]
        for r in rows:
            if not r['map_eligible'] or types and r['event_type'] not in types:continue
            p=dict(r);geom=p.pop('geometry');p.pop('payload_json',None);features.append({'type':'Feature','id':r['event_id'],'geometry':geom,'properties':p})
        return {'type':'FeatureCollection','features':features,'returned':len(features),'limit':1500,'possibly_truncated':len(rows)==1500,'source_health':self.public_health()}

    def public_health(self):return [{k:s.get(k) for k in ('source_id','name','status','freshness_status','freshness_kind','last_success_at','license','attribution','blocker','next_action')} for s in self.health()]

    def route(self,coords,along=0,mode='CITY_MODE',speed=0):
        from .geometry import point
        if not isinstance(coords,list) or not 2<=len(coords)<=5000 or not all(point(p) for p in coords):raise ValueError('Invalid route')
        bbox=[min(p[0] for p in coords)-.002,min(p[1] for p in coords)-.002,max(p[0] for p in coords)+.002,max(p[1] for p in coords)+.002]
        rows=corridor([r for r in self.items(bbox,limit=3000) if r['map_eligible']],coords,along,mode,speed)
        # Dry/stale rain stations are not a weather alert. A measurement never establishes a regional storm.
        for r in rows:r.pop('payload_json',None)
        return {'items':rows,'counts':{k:sum(r['record_class']==k for r in rows) for k in ('event','weather','infrastructure')},'source_health':self.public_health()}

    def logs(self,sid=None):
        if not self.installed():return []
        with self.connect() as c:return [dict(r) for r in c.execute('SELECT * FROM road_source_logs'+(' WHERE source_id=?' if sid else '')+' ORDER BY started_at DESC LIMIT 100',(sid,) if sid else ())]

    def catalogs(self,sid,catalog=None,sync=False):
        allowed={'concessionarias','rodovias','municipios','categorias' if sid=='artesp-interventions' else 'subclasses'}
        if sid not in KEYS or catalog and catalog not in allowed or sync and catalog not in allowed:raise ValueError('Invalid official catalog')
        if not self.installed():return {'items':[],'status':'NOT_CONFIGURED'}
        if sync:
            if not credential(sid):return {'ok':False,'status':'AUTH_REQUIRED'}
            bucket=self.reserve(sid)
            if not bucket:return {'ok':False,'status':'RATE_LIMITED'}
            started=self.clock();code=None
            try:
                code,headers,body=self.http(BY_ID[sid]['base_url']+'filtros/'+catalog+'/?limit=100',{'Authorization':'Api-Key '+credential(sid)})
                if code!=200:raise RuntimeError('HTTP_'+str(code))
                payload=json.loads(body)
                if not isinstance(payload.get('results'),list):raise A.SchemaChanged('Catalog envelope changed')
                # Store pagination metadata; never pretend this is the whole catalog.
                with self.connect() as c:c.execute('INSERT INTO road_source_catalogs(source_id,catalog,retrieved_at,payload_json) VALUES(?,?,?,?) ON CONFLICT(source_id,catalog) DO UPDATE SET retrieved_at=excluded.retrieved_at,payload_json=excluded.payload_json',(sid,catalog,at(self.clock()),dump(payload)))
                return {'ok':True,'count':len(payload['results']),'partial':bool(payload.get('meta',{}).get('next_offset'))}
            except Exception as e:
                if code==429:
                    with self.connect() as c:c.execute('UPDATE road_poll_budget SET next_at=? WHERE bucket=?',(self.clock()+3600,bucket))
                return {'ok':False,'status':'AUTH_REQUIRED' if code==401 else 'ERROR','error':'PARSER_DEGRADED' if isinstance(e,(A.SchemaChanged,ValueError)) else 'HTTP_'+str(code) if code else type(e).__name__}
            finally:
                with self.connect() as c:
                    c.execute('UPDATE road_poll_budget SET lease_until=0 WHERE bucket=?',(bucket,));c.execute('UPDATE road_data_sources SET lease_until=0 WHERE source_id=?',(sid,))
                    c.execute('INSERT INTO road_source_logs(log_id,source_id,started_at,finished_at,status,http_status,duration_ms,diagnostics_json) VALUES(?,?,?,?,?,?,?,?)',(uuid.uuid4().hex,sid,at(started),at(self.clock()),'CATALOG_OK' if code==200 else 'CATALOG_ERROR',code,(self.clock()-started)*1000,dump({'catalog':catalog})))
        with self.connect() as c:return {'items':[dict(r) for r in c.execute('SELECT * FROM road_source_catalogs WHERE source_id=?',(sid,))]}

    def diagnostics(self):
        if not self.installed():return {'sources':self.health(),'counts':[],'clients':[]}
        with self.connect() as c:
            rows=[dict(r) for r in c.execute("SELECT source_id,event_type,record_class,count(*) AS normalized,sum(CASE WHEN status='active' AND (expires_at IS NULL OR expires_at>?) THEN 1 ELSE 0 END) AS active,sum(CASE WHEN status='active' AND geometry IS NOT NULL AND (expires_at IS NULL OR expires_at>?) THEN 1 ELSE 0 END) AS eligible_map FROM road_event GROUP BY source_id,event_type,record_class",(at(self.clock()),at(self.clock())))]
            clients=[dict(r) for r in c.execute('SELECT * FROM road_layer_diagnostics ORDER BY captured_at DESC LIMIT 20')]
            matches=[dict(r) for r in c.execute('SELECT * FROM road_event_matches ORDER BY updated_at DESC LIMIT 100')]
        sources=self.health();disabled={s['source_id'] for s in sources if not s['enabled']}
        inventory=self.items(include_inactive=True,limit=10000)
        for row in rows:
            row['eligible_map']=sum(bool(r['map_eligible']) for r in inventory if r['source_id']==row['source_id'] and r['event_type']==row['event_type'])
            row['blocked_map']=row['active']-row['eligible_map']
        return {'sources':sources,'counts':rows,'clients':clients,'possible_duplicates':matches,'rendered_semantics':'Client-reported rendered features; never inferred from API count','logs':self.logs()}

    def record_diagnostics(self,data):
        # No coordinates/route/user identifier, bounded aggregate counters only.
        permitted=('received','normalized','active','eligible_map','eligible_route','rendered','alerted')
        payload={k:max(0,min(100000,int(data[k]))) for k in permitted if k in data}
        if isinstance(data.get('sources'),dict):
            payload['sources']={sid:{k:max(0,min(100000,int(counters[k]))) for k in permitted if k in counters}
                for sid,counters in data['sources'].items() if sid in BY_ID and isinstance(counters,dict)}
        if not self.installed():return {'ok':False,'status':'NOT_CONFIGURED'}
        with self.connect() as c:
            c.execute('DELETE FROM road_layer_diagnostics WHERE captured_at<?',(at(self.clock()-86400),))
            c.execute('INSERT INTO road_layer_diagnostics(report_id,captured_at,payload_json) VALUES(?,?,?)',(uuid.uuid4().hex,at(self.clock()),dump(payload)))
        return {'ok':True}
