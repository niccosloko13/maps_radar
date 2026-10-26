"""Dispatch inside existing local/ASGI transport and existing Admin authorization."""
import re
from .service import Service
from .registry import BY_ID


PUBLIC={'/api/road-events','/api/road-infrastructure','/api/weather','/api/source-health'}
ADMIN={'/api/admin/road-sources','/api/admin/road-events','/api/admin/road-infrastructure','/api/admin/layer-diagnostics','/api/admin/road-source-logs'}


def handles(path):return path in PUBLIC|ADMIN or path in ('/api/road-events/route','/api/road-events/diagnostics') or path.startswith(('/api/admin/road-sources/','/api/admin/road-infrastructure/'))


def dispatch(server,h,path,q,method):
    service=Service(server.db)
    if path.startswith('/api/admin/') and not server._admin_authed_v15(h):return h.js({'error':'Admin authentication required'},401)
    one=lambda k,default=None:(q.get(k) or [default])[0]
    try:
        if method=='POST' and int(h.headers.get('Content-Length','0') or 0)>2097152:return h.js({'error':'Request too large'},413)
        if method=='GET':
            if path=='/api/source-health':return h.js({'items':service.public_health()})
            if path=='/api/admin/road-sources':return h.js({'items':service.health()})
            if path=='/api/admin/layer-diagnostics':return h.js(service.diagnostics())
            if path=='/api/admin/road-source-logs':return h.js({'items':service.logs(one('source_id'))})
            if path in ('/api/admin/road-events','/api/admin/road-infrastructure'):
                filters={k:one(k) for k in ('source_id','event_type','road','municipality','severity','status')}
                rows=service.items(record_class='infrastructure' if path.endswith('infrastructure') else None,include_inactive=True,filters=filters)
                date=one('date')
                if date:rows=[r for r in rows if str(r.get('source_updated_at') or '').startswith(date)]
                return h.js({'items':rows})
            if path in PUBLIC:
                cls={'/api/road-events':'event','/api/road-infrastructure':'infrastructure','/api/weather':'weather'}[path]
                return h.js(service.features(one('bbox'),cls,float(one('zoom',12)),set(one('types','').split(',')) if one('types') else None))
            match=re.fullmatch(r'/api/admin/road-sources/([a-z-]+)/logs',path)
            if match:return h.js({'items':service.logs(match[1])})
            match=re.fullmatch(r'/api/admin/road-sources/([a-z-]+)/catalogs',path)
            if match:return h.js(service.catalogs(match[1]))
        if method=='POST':
            data=h._body_json()
            match=re.fullmatch(r'/api/admin/road-sources/([a-z-]+)/catalogs',path)
            if match:return h.js(service.catalogs(match[1],data.get('catalog'),True))
            if path in ('/api/admin/road-infrastructure/review','/api/admin/road-infrastructure/geocode'):
                eid=data.get('event_id');proposal=None
                if not isinstance(eid,str) or len(eid)>250:raise ValueError('Invalid record id')
                if path.endswith('/geocode'):
                    rows=[r for r in service.items(record_class='infrastructure',include_inactive=True) if r['event_id']==eid]
                    if not rows:raise ValueError('Record not found')
                    address=(rows[0]['payload_json'] or {}).get('address')
                    if not address:return h.js({'error':'No authoritative address; road km alone is not a geocoding address'},409)
                    proposal=server.autocomplete_text(address,limit=3,submitted=True)
                return h.js(service.review(eid,proposal))
            if path=='/api/road-events/route':return h.js(service.route(data.get('coordinates'),float(data.get('along',0)),data.get('mode','CITY_MODE'),float(data.get('speed',0))))
            # Aggregated diagnostics write is admin-only, not a public write sink.
            if path=='/api/road-events/diagnostics':
                if not server._admin_authed_v15(h):return h.js({'error':'Admin authentication required'},401)
                return h.js(service.record_diagnostics(data))
            match=re.fullmatch(r'/api/admin/road-sources/([a-z-]+)/(sync|test|enable|disable)',path)
            if match:
                sid,action=match.groups()
                if sid not in BY_ID:raise ValueError('Unknown source')
                if action in ('sync','test'):
                    result=service.sync(sid,probe=action=='test');return h.js(result,200 if result.get('ok') else 429 if result['status']=='RATE_LIMITED' else 409)
                if not service.installed():return h.js({'error':'Road-data migration required'},409)
                with server.db() as c:c.execute('UPDATE road_data_sources SET enabled=?,status=? WHERE source_id=?',(int(action=='enable'),'NOT_CONFIGURED' if action=='enable' else 'DISABLED',sid))
                return h.js({'ok':True})
        return h.js({'error':'Endpoint or method not found'},404)
    except (ValueError,TypeError,KeyError):return h.js({'error':'Invalid road-data request'},400)
