"""Review existing PRF/infrastructure facts against official evidence and local polygons."""
import re
import unicodedata
from .geometry import point


def canonical(value):
    return re.sub(r'[^a-z0-9]+',' ',''.join(c for c in unicodedata.normalize('NFD',str(value or '').lower()) if unicodedata.category(c)!='Mn')).strip()


def official_prf_review(row, candidates, municipality_at):
    address=(row.get('payload_json') or {}).get('address','').split('Links de compartilhamento')[0].strip()
    road=row.get('road');km=row.get('km_start')
    result=dict(event_id=row['event_id'],name=row.get('description'),road=road,km=km,
                municipality=None,lat=None,lon=None,coordinate_source=None,
                coordinate_quality='OFFICIAL_ROAD_KM' if road and km is not None else 'UNRESOLVED',
                confidence=0,status='BLOCKED',notes='Official address/road-km only; no approved coordinate',address=address)
    if row['event_type']!='PRF_OPERATIONAL_UNIT':
        result['notes']='Administrative unit: an operational-post coordinate does not establish its location'
        return result
    compatible=[]
    for candidate in candidates:
        if candidate.get('uf')!='SP' or canonical(candidate.get('situacao'))!='ativo' or candidate.get('rodovia')!=road:continue
        city=canonical(candidate.get('municipio'))
        if city not in canonical(address) and city not in canonical(row.get('description')):continue
        try:delta=abs(float(candidate['km_m'])-float(km));p=[float(candidate['longitude']),float(candidate['latitude'])]
        except (ValueError,TypeError,KeyError):continue
        compatible.append((delta,candidate,p))
    if not compatible:return result
    compatible.sort(key=lambda x:x[0]);delta,candidate,p=compatible[0]
    polygon_city=municipality_at(*p) if point(p) else None
    result.update(municipality=candidate.get('municipio'),coordinate_source='ANTT official PRF dataset; CC BY',candidate_lat=p[1],candidate_lon=p[0],official_candidate=candidate,polygon_municipality=polygon_city,km_difference=delta)
    if canonical(polygon_city)!=canonical(candidate.get('municipio')) or delta>.5:
        result.update(coordinate_quality='CONFLICT',notes='Official sources disagree in municipality polygon or road km; coordinate NOT approved')
        return result
    if len(compatible)>1 and abs(compatible[1][0]-delta)<.05:
        result.update(coordinate_quality='CONFLICT',notes='Multiple equally plausible official coordinates; requires review')
        return result
    result.update(lat=p[1],lon=p[0],coordinate_quality='OFFICIAL_COORDINATE',confidence=.97,status='APPROVED',notes='Official ANTT coordinate + PRF road/km (<=0.5km rounding) + local municipality polygon; no geocoding used')
    return result


def toll_review(row, municipality_at):
    p=[row.get('lon'),row.get('lat')];city=municipality_at(*p) if point(p) else None
    valid=bool(city and canonical(city)==canonical(row.get('municipality')) and row.get('road') and row.get('km_start') is not None and row['status']=='active')
    return dict(event_id=row['event_id'],name=row.get('description'),road=row.get('road'),km=row.get('km_start'),
                municipality=row.get('municipality'),polygon_municipality=city,lat=p[1],lon=p[0],
                coordinate_source='ANTT toll plaza dataset; CC BY',coordinate_quality='OFFICIAL_COORDINATE' if valid else 'CONFLICT',
                confidence=.95 if valid else 0,status='APPROVED' if valid else 'BLOCKED',
                notes='Official active asset; polygon municipality agrees' if valid else 'Municipality/geometry/status conflict; do not publish automatically')
