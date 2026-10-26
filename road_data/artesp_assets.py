"""Licensed ARTESP assets: only existing toll and SAU layers, never radar import."""
import io,re,zipfile,xml.etree.ElementTree as E
from functools import lru_cache
from pathlib import Path
from .adapters import SchemaChanged,make,flat,iso
from .coordinate_review import canonical
from .geometry import point

RESOURCE='8b3212ff-1647-42ad-8a45-39e9934c92e1'
CATALOG='https://dadosabertos.artesp.sp.gov.br/api/3/action/package_show?id=cadastro-de-ativos'
NS='{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'

@lru_cache(maxsize=1)
def municipalities():
    from community import Municipalities
    return Municipalities(Path(__file__).resolve().parents[1])

def records(body):
    try:z=zipfile.ZipFile(io.BytesIO(body))
    except zipfile.BadZipFile:raise SchemaChanged('ARTESP assets workbook changed')
    if sum(i.file_size for i in z.infolist())>50_000_000:raise SchemaChanged('ARTESP workbook expansion limit')
    strings=[]
    if 'xl/sharedStrings.xml' in z.namelist():
        strings=[''.join(x.itertext()) for x in E.fromstring(z.read('xl/sharedStrings.xml')).findall(NS+'si')]
    if 'xl/worksheets/sheet1.xml' not in z.namelist():raise SchemaChanged('ARTESP asset sheet missing')
    headers=None;count=0
    with z.open('xl/worksheets/sheet1.xml') as stream:
        for _,row in E.iterparse(stream,events=('end',)):
            if row.tag!=NS+'row':continue
            values={}
            for c in row.findall(NS+'c'):
                ref=re.match('[A-Z]+',c.get('r',''))
                if not ref:raise SchemaChanged('Asset cell reference missing')
                index=0
                for letter in ref[0]:index=index*26+ord(letter)-64
                v=c.find(NS+'v');value=v.text if v is not None else ''
                if c.get('t')=='s':value=strings[int(value)]
                elif c.find(NS+'is') is not None:value=''.join(c.find(NS+'is').itertext())
                values[index-1]=value or ''
            if headers is None:
                headers=[values.get(i,'') for i in range(max(values)+1)]
                if not {'ID','Desc_Componente','Rodovia','Localizacao','Sentido','Latitude','Longitude','Cod_Status','Municipio','Nome_Concessionaria'}<=set(headers):raise SchemaChanged('ARTESP asset required headers changed')
            else:
                count+=1
                if count>50000:raise SchemaChanged('ARTESP asset row limit')
                yield {h:values.get(i,'') for i,h in enumerate(headers)}
            row.clear()

def normalize(rows,sid,updated_at,at=None,municipality_at=None):
    at=at or iso();municipality_at=municipality_at or municipalities().city;result=[];seen=set()
    allowed={'pedagio'} if sid=='artesp-tolls' else {'posto de atendimento - sau','base operacional - sau'}
    for raw in rows:
        if flat(raw.get('Desc_Componente')) not in allowed:continue
        if not raw.get('ID') or raw['ID'] in seen:raise SchemaChanged('ARTESP duplicate/missing stable asset ID')
        seen.add(raw['ID']);r=dict(raw);road=re.fullmatch(r'SP\s*-?\s*(\d{3})',r.get('Rodovia',''));km=re.fullmatch(r'km\s*(\d+)\+(\d{3})',r.get('Localizacao',''),re.I)
        try:p=[float(r['Longitude'].replace(',','.')),float(r['Latitude'].replace(',','.'))]
        except (ValueError,TypeError,KeyError):p=None
        city=municipality_at(*p) if point(p) else None
        valid=bool(city and canonical(city)==canonical(r.get('Municipio')) and road and km)
        r.update(coordinate_verified=valid,polygon_municipality=city,coordinate_quality='OFFICIAL_COORDINATE' if valid else 'CONFLICT',asset_review='ARTESP_ASSET_B2',concessionaria=r.get('Nome_Concessionaria'))
        row=make(sid,r['ID'],'TOLL_PLAZA' if sid=='artesp-tolls' else 'SAU','infrastructure',r,at,geometry={'type':'Point','coordinates':p} if valid else None)
        state=flat(r.get('Cod_Status'))
        if state not in ('ativo','desativado'):raise SchemaChanged('Unknown ARTESP asset operation status')
        row.update(road='SP-'+road[1] if road else r.get('Rodovia'),km_start=int(km[1])+int(km[2])/1000 if km else None,direction=r.get('Sentido'),municipality=r.get('Municipio'),description=r.get('Nome') or r.get('Desc_Componente'),source_updated_at=updated_at,updated_at=updated_at or at,status='active' if state=='ativo' else 'ended')
        result.append(row)
    if not result:raise SchemaChanged('ARTESP expected asset subset empty; previous snapshot retained')
    return result
