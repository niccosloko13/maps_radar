"""Explicit offline pilot: python tools/official_radar_pilot.py [--refresh] [--date YYYY-MM-DD]."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys
from datetime import date

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from official_radar.client import SourceClient, PSIE_URL
from official_radar.municipal import URL, NEWS, ALIASES, parse_municipal, decode
from official_radar.normalize import parse_payload, validate_psie_payload, normalize_psie, digest, fold, iso, street_address
from official_radar.repository import Repository
from official_radar.resolver import resolve
from official_radar.service import status_at, findEnforcementAt


def run(output,date_at,refresh=False):
    if not iso(date_at):
        raise ValueError('Invalid query date')
    output=Path(output);private=output/'private';private.mkdir(parents=True,exist_ok=True)
    client=SourceClient(private/'cache')
    raw,meta=client.fetch(PSIE_URL,validate_psie_payload,force=refresh)
    instruments=normalize_psie(parse_payload(raw),PSIE_URL,meta['retrieved_at'])
    pg=[r for r in instruments if r['municipality']=='PRAIA GRANDE']
    raw_municipal,municipal_meta=client.fetch(URL,lambda b:parse_municipal(b,'2000-01-01T00:00:00+00:00'),force=refresh)
    municipal=parse_municipal(raw_municipal,municipal_meta['retrieved_at'])
    repo=Repository(private/'official-radar-pilot.sqlite')
    try:
        before=repo.counts();repo.ingest(instruments,meta,municipal);after=repo.counts()
        repo.ingest(instruments,meta,municipal);repeated=repo.counts()
        if after!=repeated:
            raise AssertionError('Repeated snapshot import is not idempotent')
        # Historical notices remain source-level evidence, not serial-level activation proof.
        notices=[]
        for url in NEWS:
            try:
                b,nmeta=client.fetch(url,lambda b:decode(b) if len(b)>1000 else (_ for _ in ()).throw(ValueError('Incomplete notice')),force=refresh)
                notices.append(dict(source_url=url,metadata=nmeta,raw_reference=digest(decode(b)),claim='MUNICIPAL_NOTICE_REQUIRES_REVIEW'))
            except (OSError,ValueError) as error:
                notices.append(dict(source_url=url,error=type(error).__name__+': '+str(error)))
        with repo.connection:
            repo.record_source(municipal_meta)
            for notice in notices:
                if notice.get('metadata'):
                    repo.record_source(notice['metadata'])
            for point in municipal:
                for alias in ALIASES:
                    if alias['street'] in fold(point['address_raw']) and street_address(point['address_raw'])['number'] in alias['numbers']:
                        repo.add_evidence(dict(equipment_id=point['equipment_id'],source_authority='PRAIA_GRANDE_SETRAN',source_type='official_municipal',claim='ADDRESS_UPDATE',effective_from=None,effective_until=None,retrieved_at=municipal_meta['retrieved_at'],source_url=NEWS[0],raw_reference=notices[0].get('raw_reference'),confidence='LOW',value={'possible_alias':alias,'identity_confirmed':False,'basis':'current listing vs historical announcement; not a confirmed relocation'}))
        matches=[resolve(point,pg,iso(date_at)) for point in municipal]
        for m in matches:
            c=m['selected'];m['status_at_date']=status_at(c['instrument'] if c else None,m['municipal'],m['match_confidence'],date_at,repo.evidence(m['municipal']['equipment_id']))
        # Payloads and identifiers remain in the private development archive.
        (private/'psie-praia-grande.json').write_text(json.dumps(pg,ensure_ascii=False,indent=2),encoding='utf-8')
        (private/'municipal-praia-grande.json').write_text(json.dumps(municipal,ensure_ascii=False,indent=2),encoding='utf-8')
        (private/'matches.json').write_text(json.dumps(matches,ensure_ascii=False,indent=2),encoding='utf-8')
        summary=dict(query_date=iso(date_at),psie_source_records_sp=len(instruments),psie_unique_equipment_sp=len({r['equipment_id'] for r in instruments}),psie_praia_grande_records=len(pg),pg_unique_equipment=len({r['equipment_id'] for r in pg}),municipal_records=len(municipal),match_confidence=dict(Counter(m['match_confidence'] for m in matches)),points_with_candidates=sum(bool(m['selected']) for m in matches),points_resolved=sum(bool(m.get('resolved')) for m in matches),selected_with_serial=sum(bool(m['selected'] and m['selected']['serial_number']) for m in matches),selected_with_inmetro=sum(bool(m['selected'] and m['selected']['inmetro_number']) for m in matches),verified_municipal_points=sum(m['status_at_date']['status']=='OFFICIAL_VERIFIED' for m in matches),pg_instruments_with_current_approved_history=sum(status_at(r,None,'UNMATCHED',date_at)['instrument_valid_at_date'] is True for r in pg),missing_nominal_speed_pg=sum(all(l['nominal_speed'] is None for l in r['lanes']) for r in pg),source=meta,municipal_source=municipal_meta,notices=notices,archive_counts_before=before,archive_counts_after=repo.counts(),repeat_snapshot_idempotent=after==repeated)
        (output/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
        query=dict(municipality='Praia Grande',street='Av. Presidente Kennedy, 4520',date='2025-04-29')
        example=findEnforcementAt(query,municipal,pg)
        (private/'query-example.json').write_text(json.dumps(example,ensure_ascii=False,indent=2),encoding='utf-8')
        report=['# Praia Grande — associação municipal / PSIE','',f'Data consultada: {date_at}. Seleção de candidato não significa identidade comprovada. Fontes oficiais acessadas diretamente, sem captcha.','', '| municipal_location | municipal_type | speed | direction | psie_match | serial_number | inmetro_number | brand_model | last_verification | valid_until | result | match_confidence | conflicts |','| --- | --- | ---: | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |']
        for m in matches:
            point=m['municipal'];candidate=m['selected'];r=candidate['instrument'] if candidate else {}
            values=[point['address_raw'],point['type'],str(point['speed_limit']),point['direction_raw'],r.get('location') or '—',', '.join(candidate['serial_number']) if candidate else '—',', '.join(candidate['inmetro_number']) if candidate else '—',' / '.join(str(r.get(k) or 'não informado') for k in ['brand','model']),r.get('verification_date') or '—',r.get('valid_until') or '—',r.get('result') or '—',m['match_confidence'],'; '.join((candidate['conflicts']+candidate['missing']) if candidate else ['sem candidato'])+(' · concorrentes plausíveis' if m.get('ambiguous') else '')]
            report.append('| '+' | '.join(v.replace('|','/').replace('\n',' ') for v in values)+' |')
        report+=['',f'{len(municipal)} official municipal records']+[f'{summary["match_confidence"].get(k,0)} {k}' for k in ['EXACT','HIGH','MEDIUM','LOW','UNMATCHED','CONFLICT']]
        report+=['',f'Candidatos encontrados: {summary["points_with_candidates"]}; identidades resolvidas EXACT/HIGH: {summary["points_resolved"]}. Seleções com série: {summary["selected_with_serial"]}; Inmetro: {summary["selected_with_inmetro"]}. São identificadores de candidatos, não vínculos municipais aprovados.',f'Instrumentos PSIE de PG com histórico aprovado cobrindo a data: {summary["pg_instruments_with_current_approved_history"]}. Pontos municipais OFFICIAL_VERIFIED: {summary["verified_municipal_points"]}.','', 'Todos os 15 registros PSIE de PG têm VelocidadeNominal=0. Não se interpretou isso como limite 0 km/h. Fontes usam nomenclaturas diferentes para alguns sentidos. O candidato principal é classificado para revisão; alternativas permanecem no arquivo privado matches.json.','', '## Conflitos históricos de numeração','Ayrton Senna 328/382, Mallet 1180/1122, Marcos Freire 8134/8124: aliases candidatos a revisão, sem provar mudança física, correção ou identidade. A notícia /noticiaNP/id/363 está datada de 01/04/2024 e anuncia procedimentos de 02/04/2024. Não é certificado nem prova automática de ativação de cada serial.','', '## Fontes',f'- Lista municipal: {URL}',f'- PSIE SP: {PSIE_URL}',*[f'- Notícia histórica: {u}' for u in NEWS],'','Estado do mapa preservado. Não está aprovado migrar os dez pontos para somente oficiais/verificados.']
        (output/'PRAIA_GRANDE_MATCH_REPORT.md').write_text('\n'.join(report)+'\n',encoding='utf-8')
        return summary
    finally:
        repo.close()


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',default='artifacts/official-radar-finder-v1')
    parser.add_argument('--date',default=date.today().isoformat())
    parser.add_argument('--refresh',action='store_true',help='One conditional fetch per source; never polls or solves captcha')
    args=parser.parse_args()
    summary=run(args.output,args.date,args.refresh)
    print(json.dumps({k:summary[k] for k in ['query_date','psie_source_records_sp','psie_unique_equipment_sp','psie_praia_grande_records','municipal_records','match_confidence','points_resolved','verified_municipal_points','repeat_snapshot_idempotent']},ensure_ascii=False,indent=2))
