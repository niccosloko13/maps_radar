"""Praia Grande service 249 adapter. Never geocodes or modifies map points."""
import html
import json
import re
from .normalize import digest, fold, text

URL = 'https://www.praiagrande.sp.gov.br/cartaservicos/Servicos/consultaCS.asp'
NEWS = [
    'https://www2.praiagrande.sp.gov.br/noticiaNP/id/363',
    'https://www2.praiagrande.sp.gov.br/noticia/setran-e-ipem-realizam-afericoes-de-lombadas--eletronicas-e-radares-nesta-quintafeira-18',
    'https://www2.praiagrande.sp.gov.br/noticia/ipem-realiza-afericao-de-lombadas-eletronicas-e-radares-em-pg-',
]
ALIASES = [dict(street='AYRTON SENNA', numbers=[328,382]),
           dict(street='MARECHAL MALLET', numbers=[1180,1122]),
           dict(street='MARCOS FREIRE', numbers=[8134,8124])]


def decode(raw):
    if isinstance(raw, str):
        return raw
    try:
        return raw.decode('utf-8-sig')
    except UnicodeDecodeError:
        return raw.decode('cp1252')


def parse_municipal(raw, retrieved_at, source_url=URL):
    document = decode(raw)
    match = re.search(r'\{\s*"id"\s*:\s*249\s*,', document)
    if not match:
        raise ValueError('Official municipal service 249 not found')
    service, _ = json.JSONDecoder().raw_decode(document[match.start():])
    description = service.get('descricao', '')
    lines = html.unescape(re.sub('<[^>]*>', '\n', description))
    lines = [text(s) for s in lines.splitlines() if text(s)]
    records, typ = [], None
    for i, line in enumerate(lines):
        f = fold(line)
        if 'CONTROLADOR ELETRONICO' in f:
            typ = 'speed_camera'
        elif 'REDUTOR ELETRONICO' in f:
            typ = 'electronic_speed_reducer'
        if not re.match(r'^AV(?:ENIDA)?\.', line, re.I):
            continue
        if typ is None or i+2 >= len(lines):
            raise ValueError('Municipal point without type/direction/speed')
        d = re.match(r'Sentido:\s*(.*)', lines[i+1], re.I)
        speed = re.search(r'Velocidade Regulamentada:\s*(\d+)\s*Km/h', lines[i+2], re.I)
        if not d or not speed:
            raise ValueError('Municipal schema variation: incomplete point')
        address = re.split(r'\s+[-–]\s+', line, maxsplit=1)[0].strip()
        records.append(dict(equipment_id='pg-listing:'+digest([address, d.group(1)])[:24],
                            authority='PRAIA_GRANDE_SETRAN',municipality='PRAIA GRANDE',uf='SP',type=typ,
                            address_raw=address,direction_raw=d.group(1).rstrip('. '),speed_limit=int(speed.group(1)),
                            official_status='listed',metrology_required=True,source_url=source_url,retrieved_at=retrieved_at,
                            effective_from=retrieved_at[:10],effective_until=None,coordinate_source=None,
                            coordinate_confidence=None,latitude=None,longitude=None,raw_reference=digest(description),
                            raw_payload={'address':line,'direction':lines[i+1],'speed':lines[i+2]}))
    if len(records) != 10 or len({r['equipment_id'] for r in records}) != 10:
        raise ValueError(f'Expected ten distinct municipal points; observed {len(records)}. Review before accepting.')
    return records
