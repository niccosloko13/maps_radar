"""Strict source-specific normalization. Missing geometry remains inventory only."""
import hashlib
import json
import re
import unicodedata
from datetime import datetime, timezone, timedelta
from html.parser import HTMLParser
from .geometry import bounds


class SchemaChanged(ValueError): pass


def iso():return datetime.now(timezone.utc).isoformat()


def timestamp(value):
    if not value:return None
    try:
        dt=datetime.fromisoformat(str(value).replace('Z','+00:00'))
        return dt.replace(tzinfo=dt.tzinfo or timezone.utc).astimezone(timezone.utc).isoformat()
    except (ValueError, TypeError):return None


def flat(text):return ''.join(c for c in unicodedata.normalize('NFD',str(text or '').lower()) if unicodedata.category(c)!='Mn')


def event_type(text):
    t=flat(text)
    for keys,kind in [('interd|bloque|closure','CLOSURE'),('acident|colis|atropel','ACCIDENT'),('congestion|lentida','CONGESTION'),('alag|inund','FLOOD'),('desliz|queda de barreira','LANDSLIDE'),('eros','EROSION'),('incend|fogo','FIRE'),('animal','ANIMAL_ON_ROAD'),('objeto|carga','OBJECT_ON_ROAD'),('pane|veiculo','VEHICLE_BREAKDOWN'),('manuten','MAINTENANCE'),('sinaliza','SIGNALIZATION_WORK'),('obra|recape|paviment','ROADWORK')]:
        if re.search(keys,t):return kind
    return 'OTHER'


def make(sid,external,kind,record_class,raw,at,**fields):
    geometry=fields.pop('geometry',None);box=bounds(geometry)
    if geometry and not box:raise SchemaChanged('Invalid official geometry')
    return dict(event_id=sid+':'+str(external),source_id=sid,external_id=str(external),event_type=kind,
                record_class=record_class,subtype=None,severity='unknown',road=None,direction=None,
                municipality_ibge=None,municipality=None,km_start=None,km_end=None,
                lat=geometry['coordinates'][1] if geometry and geometry['type']=='Point' else None,
                lon=geometry['coordinates'][0] if geometry and geometry['type']=='Point' else None,
                geometry=geometry,min_lon=box[0] if box else None,min_lat=box[1] if box else None,
                max_lon=box[2] if box else None,max_lat=box[3] if box else None,
                start_at=None,updated_at=at,end_at=None,status='active',lane_impacts=[],total_closure=0,
                description=None,source_updated_at=None,retrieved_at=at,expires_at=None,confidence=.8,
                payload_json=raw,**fields)


def artesp(payload,sid,at=None):
    at=at or iso()
    if not isinstance(payload,dict) or not isinstance(payload.get('results'),list) or not isinstance(payload.get('meta'),dict):raise SchemaChanged('ARTESP envelope changed')
    if str(payload['meta'].get('versao','')).split('.')[0]!='1':raise SchemaChanged('ARTESP contract version changed')
    rows=[]
    for r in payload['results']:
        if not isinstance(r,dict) or not r.get('slug') or 'status' not in r:raise SchemaChanged('ARTESP required fields changed')
        road=r.get('rodovia') or {};cities=r.get('municipios') or []
        if not isinstance(road,dict) or not isinstance(cities,list):raise SchemaChanged('ARTESP road/municipality changed')
        kind=event_type(' '.join(str(r.get(k) or '') for k in ['classe','subclasse_oc','subclasse_ac','tipo_ac','categoria','tipo_obra']))
        if sid=='artesp-interventions' and kind=='OTHER':kind='ROADWORK'
        geom=r.get('geometry')
        if not geom and r.get('lat') is not None and r.get('lng') is not None:
            try:geom={'type':'Point','coordinates':[float(r['lng']),float(r['lat'])]}
            except (ValueError,TypeError):raise SchemaChanged('ARTESP coordinates changed')
        row=make(sid,r['slug'],kind,'event',r,at,geometry=geom)
        update=timestamp(r.get('atualizado_em') or payload['meta'].get('timestamp'))
        if flat(r['status']) not in ('ativa','ativo','active','em andamento','finalizada','finalizado','encerrada','encerrado','ended'):raise SchemaChanged('ARTESP operational status changed')
        closed=flat(r['status']) not in ('ativa','ativo','active','em andamento')
        total=bool(r.get('interdicao_total') is True or flat(r.get('bloqueio')) in ('total','interdicao total'))
        severe=any(flat(v.get('tipo')) in ('fatal','grave') and float(v.get('qtd') or 0)>0 for v in r.get('fim',[]) if isinstance(v,dict))
        row.update(road=road.get('nome') or road.get('slug'),direction=r.get('sentido'),
                   municipality=(cities[0].get('nome') if cities else None),municipality_ibge=(str(cities[0].get('cod_ibge') or '') if cities else None),
                   km_start=r.get('km_inicial'),km_end=r.get('km_final'),start_at=timestamp(r.get('dt_hr_inicio') or r.get('dt_hr_oc')),
                   end_at=timestamp(r.get('dt_hr_termino')),status='ended' if closed else 'active',total_closure=int(total),
                   severity='critical' if total or severe else 'unknown',source_updated_at=update,updated_at=update or at,
                   expires_at=(datetime.fromisoformat(at)+timedelta(minutes=30)).isoformat(),
                   lane_impacts=r.get('interdicoes') or [],subtype=r.get('tipo_obra') or r.get('tipo_ac'),
                   description=r.get('observacoes_cci') or r.get('complemento') or r.get('tipo_obra') or r.get('classe'))
        rows.append(row)
        for i,traffic in enumerate(r.get('congestionamentos') or []):
            if not isinstance(traffic,dict):raise SchemaChanged('ARTESP congestion changed')
            # Only supplied geometry is used. Never draw a guessed road segment from km.
            child=make(sid,str(r['slug'])+':traffic:'+str(i),'CONGESTION','event',traffic,at,geometry=traffic.get('geometry'))
            child.update({k:row[k] for k in ['road','direction','municipality','municipality_ibge','status','expires_at','source_updated_at']})
            child.update(km_start=traffic.get('km_inicial'),km_end=traffic.get('km_final'),description=traffic.get('descricao') or 'Congestionamento informado pela ARTESP')
            rows.append(child)
    return rows


class Page(HTMLParser):
    def __init__(self):super().__init__();self.text=[];self.links=[];self.skip=0
    def handle_data(self,t):
        if not self.skip:self.text.append(t.strip())
    def handle_starttag(self,tag,attrs):
        if tag in ('script','style'):self.skip+=1
        if tag=='a':self.links += [v for k,v in attrs if k=='href']
    def handle_endtag(self,tag):
        if tag in ('script','style'):self.skip=max(0,self.skip-1)


def prf(html,url,at=None):
    p=Page();p.feed(html);t=' '.join(p.text);at=at or iso()
    # The authoritative page distinguishes administrative and operational units.
    title=re.search(r'(?:Unidade Operacional|Superintendência|Delegacia)([^|]{0,120})',t,re.I)
    if not title or 'Endereço:' not in t:raise SchemaChanged('PRF address/title not found')
    h1=re.search(r'<h1\b[^>]*>(.*?)</h1>',html,re.S|re.I)
    unit_page=Page();unit_page.feed(h1[1] if h1 else title[0].split('Publicado')[0])
    unit=' '.join(unit_page.text).strip();kind='PRF_OPERATIONAL_UNIT' if flat(unit).startswith('unidade operacional') else 'PRF_SUPERINTENDENCY' if flat(unit).startswith('superintendencia') else 'PRF_DELEGACY'
    address=t.split('Endereço:',1)[1].split('Telefone',1)[0].split('Links de compartilhamento',1)[0].strip()
    km=re.search(r'Km\s*([\d,.]+)',address,re.I);road=re.search(r'BR\s*[- ]?\s*(\d{3})',address)
    date=re.search(r'Modificado em\s*(\d{2})/(\d{2})/(\d{4})',t)
    row=make('prf-sp',hashlib.sha256(url.encode()).hexdigest()[:20],kind,'infrastructure',{'name':unit,'address':address,'url':url,'coordinate_quality':'unmapped'},at)
    row.update(description=unit,road='BR-'+road[1] if road else None,km_start=float(km[1].replace(',','.')) if km else None,
               source_updated_at=f'{date[3]}-{date[2]}-{date[1]}T00:00:00-03:00' if date else None)
    # No geocoded coordinate is passed off as official. Address-only records stay in Admin.
    return [row]


def prf_administrative(html,url,at=None):
    rows=[]
    modified=re.search(r'Modificado em\s*</?[^>]*>?\s*(\d{2}/\d{2}/\d{4})',html)
    plain=Page();plain.feed(html);date=re.search(r'Modificado em\s*(\d{2}/\d{2}/\d{4})',' '.join(plain.text))
    for heading,body in re.findall(r'<h2\b[^>]*>(.*?)</h2>(.*?)(?=<h2\b|$)',html,re.I|re.S):
        title=Page();title.feed(heading);name=' '.join(title.text)
        if not re.match(r'(Superintendência|Delegacia)',name,re.I):continue
        snippet='<h1>'+heading+'</h1> Modificado em '+(date[1] if date else '')+' '+body
        try:rows+=prf(snippet,url+'#'+hashlib.sha256(name.encode()).hexdigest()[:12],at)
        except SchemaChanged:continue
    return rows


STATIC={'PMRV_COMPANY','PMRV_OPERATIONAL_BASE','PMRV_POST','TOLL_PLAZA','SAU','OPERATIONAL_BASE','TOW_BASE','MECHANICAL_SUPPORT','DER_BASE','CONCESSIONAIRE_BASE','PRF_SUPERINTENDENCY','PRF_DELEGACY','PRF_OPERATIONAL_UNIT'}


def official_geojson(payload,sid,at=None):
    """Configured, officially reviewed GeoJSON; public URL is validated separately."""
    if not isinstance(payload,dict) or payload.get('type')!='FeatureCollection' or not isinstance(payload.get('features'),list):raise SchemaChanged('Expected official GeoJSON FeatureCollection')
    rows=[];at=at or iso()
    for f in payload['features']:
        p=f.get('properties') or {};kind=p.get('event_type') or p.get('type');external=p.get('id') or f.get('id')
        if not external or not kind:raise SchemaChanged('Official feature identity/type missing')
        cls='infrastructure' if kind in STATIC else 'weather' if kind in ('RAIN_STATION','HEAVY_RAIN','STORM','GALE','FLOOD_ALERT','OTHER_WEATHER_ALERT') else 'event'
        if sid=='pmrv-sp' and kind not in ('PMRV_COMPANY','PMRV_OPERATIONAL_BASE','PMRV_POST'):raise SchemaChanged('Not a PMRv unit')
        if sid=='artesp-tolls' and kind!='TOLL_PLAZA':raise SchemaChanged('Not a toll plaza')
        if sid=='official-support' and kind not in ('SAU','OPERATIONAL_BASE','TOW_BASE','MECHANICAL_SUPPORT','DER_BASE','CONCESSIONAIRE_BASE'):raise SchemaChanged('Not an official support category')
        if sid=='defesa-civil-sp' and kind not in ('HEAVY_RAIN','STORM','GALE','FLOOD_ALERT','OTHER_WEATHER_ALERT'):raise SchemaChanged('Not a Civil Defense weather alert')
        if sid=='sp-aguas' and kind!='RAIN_STATION':raise SchemaChanged('Rain stations cannot establish regional weather alerts')
        if cls!='infrastructure' and not timestamp(p.get('valid_until') or p.get('expires_at')):raise SchemaChanged('Temporary official feature needs explicit validity')
        row=make(sid,external,kind,cls,p,at,geometry=f.get('geometry'))
        for k in ('severity','road','direction','municipality_ibge','municipality','km_start','km_end','description','start_at','end_at','source_updated_at'):
            if k in p:row[k]=p[k]
        row['expires_at']=timestamp(p.get('valid_until') or p.get('expires_at')) if cls!='infrastructure' else None
        row['source_updated_at']=timestamp(row['source_updated_at'])
        row['status']=p.get('status','active');rows.append(row)
    return rows


def sibh(payload,at=None):
    if not isinstance(payload,dict) or not isinstance(payload.get('measurements'),list):raise SchemaChanged('SIBH measurements envelope changed')
    rows=[];at=at or iso()
    for p in payload['measurements']:
        if not isinstance(p,dict) or not p.get('station_prefix_id') or 'value' not in p:raise SchemaChanged('SIBH station contract changed')
        if not str(p.get('cod_ibge','')).startswith('35'):continue
        if p.get('value') is None or not p.get('max_date'):continue
        try:lon,lat=float(p['longitude']),float(p['latitude']);value=float(p['value'])
        except (KeyError,ValueError,TypeError):raise SchemaChanged('SIBH coordinates/value changed')
        if value<0:continue
        reading=timestamp(p['max_date'])
        if not reading:raise SchemaChanged('SIBH reading timestamp changed')
        row=make('sp-aguas',p['station_prefix_id'],'RAIN_STATION','weather',p,at,geometry={'type':'Point','coordinates':[lon,lat]})
        from .readiness import station_freshness
        observation=station_freshness(p,datetime.fromisoformat(at).timestamp(),at)
        expiry=observation.get('expires_at_seconds')
        row.update(description=p.get('station_name'),municipality=p.get('city'),municipality_ibge=str(p['cod_ibge']),
                   source_updated_at=reading,updated_at=reading,expires_at=datetime.fromtimestamp(expiry,timezone.utc).isoformat() if expiry else at,
                   severity='attention' if value>0 else 'unknown')
        # Station accumulation is NOT a polygon of rainfall or a claim of heavy rain on a road.
        rows.append(row)
    return rows


def antt_tolls(payload,source_date,at=None):
    if not isinstance(payload,dict) or not isinstance(payload.get('praca-de-pedagio'),list):raise SchemaChanged('ANTT toll envelope changed')
    rows=[];at=at or iso()
    for p in payload['praca-de-pedagio']:
        if p.get('uf')!='SP':continue
        if not all(k in p for k in ('concessionaria','praca_de_pedagio','rodovia','km_m','situacao','latitude','longitude')):raise SchemaChanged('ANTT toll fields changed')
        try:lon=float(str(p['longitude']).replace(',','.'));lat=float(str(p['latitude']).replace(',','.'));km=float(str(p['km_m']).replace(',','.'))
        except (ValueError,TypeError):raise SchemaChanged('ANTT toll coordinates/km changed')
        identity=[p[k] for k in ('concessionaria','praca_de_pedagio','rodovia','km_m','sentido')]
        eid=hashlib.sha256(json.dumps(identity,ensure_ascii=False).encode()).hexdigest()[:24]
        row=make('antt-tolls',eid,'TOLL_PLAZA','infrastructure',p,at,geometry={'type':'Point','coordinates':[lon,lat]})
        row.update(description=p['praca_de_pedagio'],road=p['rodovia'],km_start=km,direction=p.get('sentido'),municipality=p.get('municipio'),
                   status='active' if flat(p['situacao']) in ('ativo','ativa','em operacao') else 'ended',source_updated_at=timestamp(source_date),updated_at=timestamp(source_date) or at)
        rows.append(row)
    return rows
