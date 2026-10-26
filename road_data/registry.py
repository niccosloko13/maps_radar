"""Source contracts: URLs are fixed official origins, credentials never serialized."""
ARTESP = 'https://ccm.artesp.sp.gov.br/rodovias/api/'


def definition(sid, name, authority, category, url, **extras):
    return dict(source_id=sid, name=name, authority=authority, category=category,
                base_url=url, data_format='JSON', auth_type='none', license='Not yet verified',
                terms_url=url, terms_version=None, attribution=authority,
                commercial_restrictions='Review source terms before redistribution',
                poll_interval_seconds=86400, rate_limit=None, enabled=1,
                status='NOT_CONFIGURED', record_count=0, freshness_status='BROKEN',
                adapter_version='1.0.0', contract_version='1', **extras)


SOURCES = [
    definition('artesp-occurrences', 'ARTESP · Ocorrências', 'ARTESP', 'events', ARTESP+'ocorrencias/'),
    definition('artesp-interventions', 'ARTESP · Intervenções', 'ARTESP', 'events', ARTESP+'intervencoes/'),
    definition('sp-aguas', 'SP Águas · SIBH', 'SP Águas', 'weather', 'https://apps.spaguas.sp.gov.br/sibh/'),
    definition('defesa-civil-sp', 'Defesa Civil SP', 'Defesa Civil SP', 'weather', 'https://admin.defesacivil.sp.gov.br/previsaodotempo/sp/alertas'),
    definition('prf-sp', 'PRF · Unidades SP', 'PRF', 'infrastructure', 'https://www.gov.br/prf/pt-br/canais-de-atendimento/unidades-prf/sao-paulo'),
    definition('pmrv-sp', 'PM Rodoviária SP', 'PMESP/CPRv', 'infrastructure', 'https://www4.policiamilitar.sp.gov.br/unidades/cprv/'),
    definition('artesp-tolls', 'ARTESP · Pedágios', 'ARTESP', 'infrastructure', 'https://dadosabertos.artesp.sp.gov.br/'),
    definition('antt-tolls', 'ANTT · Praças de pedágio SP', 'ANTT', 'infrastructure', 'https://dados.antt.gov.br/api/3/action/package_show?id=praca-de-pedagio'),
    definition('official-support', 'Bases e apoio oficiais', 'DER/Concessionárias', 'infrastructure', 'https://www.der.sp.gov.br/'),
]
for s in SOURCES:
    if s['source_id'].startswith('artesp-') and s['category']=='events':
        s.update(auth_type='api-key', license='CC BY-NC 4.0',
                 terms_url=ARTESP+'docs/', commercial_restrictions='Non-commercial; attribution required',
                 poll_interval_seconds=300, rate_limit=12, status='AUTH_REQUIRED')
KEYS = {'artesp-occurrences':'ARTESP_OCCURRENCES_API_KEY',
        'artesp-interventions':'ARTESP_INTERVENTIONS_API_KEY'}
BY_ID = {s['source_id']: s for s in SOURCES}
SIBH_URL='https://cth.daee.sp.gov.br/sibh/api/v2/measurements/now?station_type_id=2&show_all=false&serializer=complete&public=true&hours=1'
BY_ID['sp-aguas'].update(base_url=SIBH_URL,poll_interval_seconds=600)
BY_ID['antt-tolls'].update(license='CC BY',terms_url='https://dados.antt.gov.br/dataset/praca-de-pedagio',commercial_restrictions='Attribution required',poll_interval_seconds=86400)
for sid in ('artesp-tolls','official-support'):
    BY_ID[sid].update(base_url='https://dadosabertos.artesp.sp.gov.br/api/3/action/package_show?id=cadastro-de-ativos',authority='ARTESP',license='CC BY (catalog version unspecified)',terms_url='https://dadosabertos.artesp.sp.gov.br/dataset/cadastro-de-ativos',attribution='ARTESP - Cadastro de Ativos',poll_interval_seconds=86400)


def credential(sid):
    import os
    return os.environ.get(KEYS.get(sid, ''), '') or (os.environ.get('ARTESP_API_KEY', '') if sid in KEYS else '')
