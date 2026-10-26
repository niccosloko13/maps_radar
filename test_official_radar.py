"""Offline regression tests. No government or production calls in this suite."""
import copy
from datetime import datetime,timezone
import json
from pathlib import Path
import tempfile
import unittest
import urllib.error
from official_radar.client import SourceClient
from official_radar.municipal import parse_municipal,URL
from official_radar.normalize import parse_payload,normalize_psie,street_address,direction,iso,digest
from official_radar.repository import Repository
from official_radar.resolver import resolve
from official_radar.service import status_at,findEnforcementAt,getEquipmentStatusAt,OfficialRadarFinder

TIME='2026-10-25T03:00:00+00:00'


def raw_record():
    return dict(SiglaUf='SP',Municipio='PRAIA GRANDE',LocalVerificacao='Av. Presidente Kennedy, 4520',TipoMedidor='Fixo',Faixas=[dict(NumeroFaixa='1',NumeroInmetro='TEST-I',NumeroSerie='TEST-S',Sentido='AVIAÇÃO-TUPI',VelocidadeNominal='40')],Historico=[dict(NumeroCertificado='TEST-C',DataLaudo='01/01/2025',DataValidade='31/12/2025',Resultado='Aprovado',TipoServico='Periódica')],Proprietario={'Nome':'Fixture only'})


def instrument():
    return normalize_psie([raw_record()],'https://servicos.rbmlq.gov.br/dados-abertos/SP/medidores.json',TIME)[0]


def listing():
    return dict(equipment_id='fixture-listing',municipality='Praia Grande',address_raw='Av. Pres. Kennedy, próximo ao nº 4520',direction_raw='Aviação/Tupi',speed_limit=40,type='electronic_speed_reducer',effective_from='2024-01-01',metrology_required=True)


class ParserTests(unittest.TestCase):
    def test_real_municipal_parser(self):
        records=parse_municipal(Path('tests/fixtures/official-radar/praia-grande-service-249.html').read_bytes(),TIME)
        self.assertEqual(len(records),10);self.assertEqual(sum(r['type']=='speed_camera' for r in records),2)
        self.assertEqual([r['speed_limit'] for r in records],[60,60]+[40]*8)
        self.assertTrue(all(r['latitude'] is None and r['coordinate_confidence'] is None for r in records))

    def test_municipal_schema_change_is_rejected(self):
        with self.assertRaises(ValueError):parse_municipal(b'<html>unavailable</html>',TIME)

    def test_json_xml_and_schema_variation(self):
        r=raw_record();self.assertEqual(parse_payload(json.dumps([r])),[r])
        self.assertEqual(parse_payload({'Medidores':{'Medidor':[r]}}),[r])
        x='<Medidores><Medidor><SIGLA_UF>SP</SIGLA_UF><MUNICIPIO>PRAIA GRANDE</MUNICIPIO><Faixas><Faixa><NumeroSerie>001</NumeroSerie></Faixa></Faixas></Medidor></Medidores>'
        n=normalize_psie(parse_payload(x),'fixture',TIME);self.assertEqual(n[0]['lanes'][0]['serial_number'],'001')
        self.assertEqual(normalize_psie([dict(r,SiglaUf='SC')],'fixture',TIME),[])
        with self.assertRaises(ValueError):parse_payload({'error':'unavailable'})
        with self.assertRaises(ValueError):parse_payload('<!DOCTYPE x><Medidores/>')

    def test_raw_payload_and_zero_speed_preserved(self):
        r=raw_record();r['Faixas'][0]['VelocidadeNominal']='0';n=normalize_psie([r],'fixture',TIME)[0]
        self.assertIsNone(n['lanes'][0]['nominal_speed']);self.assertEqual(n['raw_payload'],r)
        self.assertEqual(n['lanes'][0]['raw_payload']['VelocidadeNominal'],'0');self.assertIsNone(n['brand'])

    def test_streets_and_direction_normalization(self):
        a=street_address('AV. PRES. KENNEDY, altura do Nº 4520');b=street_address('Avenida Presidente Kennedy, n. 4520')
        self.assertEqual(a['street'],b['street']);self.assertEqual(a['number'],4520)
        self.assertEqual(street_address('Av. Pres. Kennedy, s/nº, próximo à Prefeitura')['landmark'],'PREFEITURA')
        self.assertEqual(direction('PG/SV.'),direction('PRAIA GRANDE - SÃO VICENTE'))
        self.assertNotEqual(direction('PG/SV'),direction('SV/PG'))
        self.assertEqual(iso('31/02/2026'),None)


class ResolverTests(unittest.TestCase):
    def test_high_requires_speed_direction_type_and_unique_candidate(self):
        self.assertEqual(resolve(listing(),[instrument()])['match_confidence'],'HIGH')
        r=instrument();r['lanes'][0]['nominal_speed']=None
        self.assertEqual(resolve(listing(),[r])['match_confidence'],'MEDIUM')

    def test_exact_requires_official_id_and_location(self):
        l=dict(listing(),serial_number='TEST-S')
        self.assertEqual(resolve(l,[instrument()])['match_confidence'],'EXACT')
        r=instrument();r['location']='Outra rua 4520'
        self.assertEqual(resolve(l,[r])['match_confidence'],'CONFLICT')

    def test_ambiguity_downgrades_high(self):
        r=instrument();other=copy.deepcopy(r);other['equipment_id']='other-physical-device'
        m=resolve(listing(),[r,other]);self.assertEqual(m['match_confidence'],'MEDIUM');self.assertFalse(m['resolved'])

    def test_speed_and_direction_conflicts(self):
        for field,value in [('direction','TUPI - AVIAÇÃO'),('nominal_speed',60)]:
            r=instrument();r['lanes'][0][field]=value
            self.assertEqual(resolve(listing(),[r])['match_confidence'],'CONFLICT')

    def test_historical_alias_is_not_identity(self):
        r=instrument();r['location']='Av Ayrton Senna da Silva, 328'
        l=dict(listing(),address_raw='Av. Ayrton Senna da Silva oposto 382')
        m=resolve(l,[r]);self.assertEqual(m['match_confidence'],'CONFLICT');self.assertFalse(m['resolved'])

    def test_no_match_and_weak_text(self):
        r=instrument();r['municipality']='SANTOS';self.assertEqual(resolve(listing(),[r])['match_confidence'],'UNMATCHED')
        r=instrument();r['location']='Av Presidente Kennedy'
        self.assertEqual(resolve(listing(),[r])['match_confidence'],'LOW')


class TemporalTests(unittest.TestCase):
    def test_boundaries_and_expired(self):
        for d,want in [('2024-12-31',None),('2025-01-01',True),('2025-12-31',True),('2026-01-01',False)]:
            self.assertEqual(status_at(instrument(),listing(),'HIGH',d)['valid_at_date'],want)

    def test_missing_identity_or_historical_listing_is_unknown(self):
        self.assertIsNone(status_at(instrument(),listing(),'LOW','2025-05-01')['valid_at_date'])
        l=dict(listing(),effective_from='2026-10-25')
        s=status_at(instrument(),l,'HIGH','2025-05-01');self.assertIsNone(s['official_listing']);self.assertIsNone(s['valid_at_date']);self.assertTrue(s['instrument_valid_at_date'])
        l=dict(listing(),effective_from='2025-01-01',retrieved_at='2025-06-01T00:00:00Z')
        self.assertIsNone(status_at(instrument(),l,'HIGH','2025-07-01')['official_listing'])

    def test_new_rejection_supersedes_old_certificate_and_repair_recovers(self):
        r=instrument();r['verifications']+= [dict(verification_date='2025-04-29',valid_from='2025-04-29',valid_until='2025-04-29',result='Reprovado'),dict(verification_date='2025-09-12',valid_from='2025-09-12',valid_until='2026-09-11',result='Aprovado')]
        self.assertFalse(status_at(r,listing(),'HIGH','2025-04-29')['valid_at_date'])
        self.assertFalse(status_at(r,listing(),'HIGH','2025-06-01')['valid_at_date'])
        self.assertTrue(status_at(r,listing(),'HIGH','2025-09-12')['valid_at_date'])

    def test_same_day_incompatible_verifications_conflict(self):
        r=instrument();r['verifications'].append(dict(r['verifications'][0],result='Reprovado'))
        self.assertEqual(status_at(r,listing(),'HIGH','2025-01-01')['status'],'OFFICIAL_CONFLICT')

    def test_notices_are_scoped_and_deactivation_does_not_mean_illegal(self):
        r=instrument();l=listing();notice=dict(equipment_id='different-equipment',claim='DEACTIVATION_NOTICE',confidence='HIGH',effective_from='2025-01-01')
        self.assertTrue(status_at(r,l,'HIGH','2025-05-01',[notice])['valid_at_date'])
        notice['equipment_id']=l['equipment_id'];s=status_at(r,l,'HIGH','2025-05-01',[notice]);self.assertEqual(s['status'],'DEACTIVATED');self.assertFalse(s['valid_at_date'])

    def test_find_enforcement_uses_ids_and_does_not_invent_historical_listing(self):
        result=findEnforcementAt(dict(municipality='Praia Grande',street='Av Presidente Kennedy 4520',date='2025-05-01',serial_number='TEST-S'),[listing()],[instrument()])
        self.assertEqual(len(result['candidates']),1);self.assertTrue(result['candidates'][0]['valid_at_date'])
        bad=findEnforcementAt(dict(municipality='Praia Grande',date='2025-05-01',serial_number='wrong'),[listing()],[instrument()]);self.assertEqual(bad['candidates'],[])

    def test_two_argument_finder_api_resolves_municipal_identity(self):
        finder=OfficialRadarFinder([listing()],[instrument()])
        status=finder.getEquipmentStatusAt('fixture-listing','2025-05-01')
        self.assertEqual(status['status'],'OFFICIAL_VERIFIED');self.assertTrue(status['valid_at_date'])
        self.assertIsNone(finder.getEquipmentStatusAt('unknown','2025-05-01')['valid_at_date'])


class StorageTests(unittest.TestCase):
    def test_append_only_history_and_idempotent_import(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo=Repository(Path(tmp)/'pilot.sqlite');r=instrument();meta=dict(source_url='fixture',retrieved_at=TIME,sha256=digest(r))
            repo.ingest([r],meta);a=repo.counts();repo.ingest([r],meta);self.assertEqual(a,repo.counts())
            changed=copy.deepcopy(r);changed['raw_payload']['NewField']='new snapshot';changed['verifications'].append(dict(changed['verifications'][0],verification_date='2026-01-01',raw_payload={'new':'history'}))
            repo.ingest([changed],dict(meta,sha256='new'));self.assertEqual(repo.counts()['equipment_verifications'],2)
            self.assertEqual(len(repo.instrument(r['equipment_id'])['verifications']),2)
            self.assertIsNone(getEquipmentStatusAt('missing','2025-01-01',repo)['valid_at_date']);repo.close()

    def test_unavailable_and_invalid_source_retain_last_good_cache(self):
        class Response:
            url=URL;headers={'ETag':'fixture','Last-Modified':'fixture'}
            def read(self,n):return b'[1]'
            def __enter__(self):return self
            def __exit__(self,*args):pass
        with tempfile.TemporaryDirectory() as tmp:
            client=SourceClient(tmp,ttl=0,opener=lambda *a,**k:Response())
            b,first=client.fetch(URL,json.loads)
            client.opener=lambda *a,**k:(_ for _ in ()).throw(urllib.error.URLError('temporary outage'))
            cached,meta=client.fetch(URL,json.loads);self.assertEqual(b,cached);self.assertTrue(meta['stale']);self.assertEqual(first['retrieved_at'],meta['retrieved_at'])
            client.opener=lambda *a,**k:Response()
            cached,meta=client.fetch(URL,lambda b:json.loads(b) if b==b'[1]' else None);self.assertFalse(meta['stale'])

    def test_invalid_new_payload_does_not_replace_valid_blob(self):
        class Response:
            url=URL;headers={}
            body=b'[1]'
            def read(self,n):return self.body
            def __enter__(self):return self
            def __exit__(self,*args):pass
        with tempfile.TemporaryDirectory() as tmp:
            response=Response();client=SourceClient(tmp,ttl=0,opener=lambda *a,**k:response)
            _,first=client.fetch(URL,json.loads);response.body=b'<html>temporarily unavailable</html>'
            raw,last=client.fetch(URL,json.loads);self.assertEqual(raw,b'[1]');self.assertTrue(last['stale']);self.assertEqual(first['sha256'],last['sha256'])


if __name__=='__main__':unittest.main()
