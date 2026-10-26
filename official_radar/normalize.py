"""Lossless raw references plus conservative, explicit normalization."""
import hashlib
import json
import re
import unicodedata
from datetime import date, datetime
from xml.etree import ElementTree


def text(value):
    return re.sub(r'\s+', ' ', str(value or '')).strip()


def fold(value):
    return ''.join(c for c in unicodedata.normalize('NFKD', text(value)) if not unicodedata.combining(c)).upper()


def key(value):
    return re.sub('[^A-Z0-9]', '', fold(value))


def get(row, *names):
    if not isinstance(row, dict):
        raise ValueError('Expected an object in PSIE schema')
    lookup = {key(k): v for k, v in row.items()}
    return next((lookup[key(n)] for n in names if key(n) in lookup), None)


def iso(value):
    if isinstance(value, date):
        return value.isoformat()[:10]
    for fmt in ('%d/%m/%Y', '%Y-%m-%d'):
        try:
            return datetime.strptime(text(value)[:10], fmt).date().isoformat()
        except ValueError:
            pass
    return None


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def positive_speed(value):
    try:
        speed = float(str(value).replace(',', '.'))
        return speed if 0 < speed <= 300 else None
    except (TypeError, ValueError):
        return None


def as_list(value):
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def child_rows(value, singular):
    if isinstance(value, dict):
        nested = get(value, singular)
        return as_list(nested if nested is not None else value)
    return as_list(value)


def xml_object(node):
    if not len(node):
        return node.text or ''
    out = {}
    for child in node:
        name = child.tag.split('}')[-1]
        value = xml_object(child)
        if name in out:
            if not isinstance(out[name], list):
                out[name] = [out[name]]
            out[name].append(value)
        else:
            out[name] = value
    return out


def parse_payload(raw):
    if isinstance(raw, (bytes, bytearray)):
        raw = raw.decode('utf-8-sig')
    if isinstance(raw, str):
        if raw.lstrip().startswith('<'):
            if re.search(r'<!DOCTYPE|<!ENTITY', raw, re.I):
                raise ValueError('XML declarations/entities are not allowed')
            raw = xml_object(ElementTree.fromstring(raw))
        else:
            raw = json.loads(raw)
    while isinstance(raw, dict):
        if get(raw, 'Municipio') is not None:
            return [raw]
        candidate = get(raw, 'Medidores', 'Medidor', 'items', 'records', 'data', 'ArrayOfMedidorVelocidade', 'MedidorVelocidade')
        if candidate is None:
            raise ValueError('Unrecognized PSIE schema; last valid snapshot must be retained')
        raw = candidate
    if not isinstance(raw, list) or any(not isinstance(r, dict) or get(r, 'Municipio') is None for r in raw):
        raise ValueError('Expected PSIE instrument records')
    return raw


def validate_psie_payload(raw):
    rows=parse_payload(raw)
    for row in rows:
        for field,singular in [('Faixas','Faixa'),('Historico','Verificacao')]:
            if any(not isinstance(child,dict) for child in child_rows(get(row,field),singular)):
                raise ValueError('Unexpected nested '+field+' schema')
        if get(row,'Proprietario') is not None and not isinstance(get(row,'Proprietario'),dict):
            raise ValueError('Unexpected proprietor schema')
    return rows


def normalize_psie(rows, source_url, retrieved_at):
    out = []
    for raw in rows:
        uf = text(get(raw, 'SiglaUf', 'SIGLA_UF', 'UF')).upper()
        if uf != 'SP':
            continue
        lanes = []
        for lane in child_rows(get(raw, 'Faixas'), 'Faixa'):
            lanes.append(dict(lane=text(get(lane, 'NumeroFaixa')) or None,
                              inmetro_number=text(get(lane, 'NumeroInmetro')) or None,
                              serial_number=text(get(lane, 'NumeroSerie')) or None,
                              direction=text(get(lane, 'Sentido')) or None,
                              nominal_speed=positive_speed(get(lane, 'VelocidadeNominal')),
                              raw_payload=lane))
        # Never turn a road address into a stable physical instrument ID.
        identifiers = sorted({(l['inmetro_number'] or '', l['serial_number'] or '') for l in lanes if l['inmetro_number'] or l['serial_number']})
        equipment_id = 'psie:' + digest([uf, identifiers] if identifiers else ['unidentified', raw])[:32]
        history = []
        for h in child_rows(get(raw, 'Historico'), 'Verificacao'):
            history.append(dict(equipment_id=equipment_id, certificate_number=text(get(h, 'NumeroCertificado')) or None,
                                verification_date=iso(get(h, 'DataLaudo', 'DataVerificacao')),
                                valid_from=iso(get(h, 'DataLaudo', 'DataVerificacao')),
                                valid_until=iso(get(h, 'DataValidade')), result=text(get(h, 'Resultado')) or None,
                                service_type=text(get(h, 'TipoServico')) or None,
                                source_url=source_url, retrieved_at=retrieved_at, raw_payload=h))
        owner = get(raw, 'Proprietario') or {}
        out.append(dict(equipment_id=equipment_id, identified=bool(identifiers), uf=uf,
                        instrument_type='MEDIDOR_DE_VELOCIDADE', instrument_type_basis='official dataset scope',
                        municipality=fold(get(raw, 'Municipio')), type=text(get(raw, 'TipoMedidor')) or None,
                        location=text(get(raw, 'LocalVerificacao')) or None,
                        responsible=text(get(owner, 'Nome')) or None,
                        verification_date=iso(get(raw, 'DataUltimaVerificacao')),
                        valid_until=iso(get(raw, 'DataValidade')), result=text(get(raw, 'UltimoResultado')) or None,
                        brand=get(raw, 'Marca'), model=get(raw, 'Modelo'), approval_ordinance=get(raw, 'PortariaAprovacao'),
                        lanes=lanes, verifications=history, source_url=source_url, retrieved_at=retrieved_at, raw_payload=raw))
    return out


def street_address(value):
    s = fold(value)
    s = re.sub(r'\bS\s*/\s*N[ÂºOÂ°]?\b', ' SEM NUMERO ', s)
    replacements = {'AV': 'AVENIDA', 'PRES': 'PRESIDENTE', 'DR': 'DOUTOR', 'PCA': 'PRACA'}
    s = re.sub(r'[^A-Z0-9 ]', ' ', s)
    tokens = [replacements.get(t, t) for t in s.split()]
    s = ' '.join(tokens)
    number = re.search(r'\b\d+\b', s)
    road = s[:number.start()] if number else s
    road = re.sub(r'\b(OPOS?TO|PROXIMO|ALTURA|AO|DO|DA|DE|N|NO|NUMERO|SEM|PREFEITURA|MUNICIPAL|PRAIA|GRANDE)\b', ' ', road)
    return {'street': text(road), 'number': int(number.group()) if number else None,
            'landmark': 'PREFEITURA' if 'PREFEITURA' in s else None, 'raw': value}


def direction(value):
    s = fold(value).strip('. ')
    s = re.sub(r'\bPG\b', 'PRAIA GRANDE', s)
    s = re.sub(r'\bSV\b', 'SAO VICENTE', s)
    s = re.sub(r'\bPCA\.?\b', 'PRACA', s)
    parts = re.split(r'\s*(?:/|â†’|->|\s+-\s+|(?<=[A-Z])-(?=[A-Z]))\s*', s)
    return tuple(text(re.sub('[^A-Z0-9 ]', ' ', x)) for x in parts if text(x))
