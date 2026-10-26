"""Isolated policy tests only; synthetic rows are never source coverage evidence."""
import unittest,io,zipfile
from road_data.artesp_assets import normalize,records
from road_data.adapters import SchemaChanged
from road_data.geometry import corridor

class ArtespAssetTests(unittest.TestCase):
 def row(self,**changes):
  r={'ID':'TEST-ASSET','Desc_Componente':'Pedágio','Rodovia':'SP160','Localizacao':'km 032+381','Sentido':'Sul','Latitude':'-23.820826','Longitude':'-46.582601','Municipio':'São Bernardo do Campo','Cod_Status':'Ativo','Nome_Concessionaria':'TEST ONLY'};r.update(changes);return r
 def test_strict_scoped_types_excludes_radar_equipment(self):
  rows=normalize([self.row(),self.row(ID='TEST-RADAR',Desc_Componente='Medidor de Velocidade (Radar Fixo)')],'artesp-tolls',None,municipality_at=lambda *p:'São Bernardo do Campo')
  self.assertEqual(len(rows),1);self.assertEqual(rows[0]['event_type'],'TOLL_PLAZA');self.assertEqual(rows[0]['km_start'],32.381)
 def test_only_sau_support_not_moving_vehicles(self):
  rows=normalize([self.row(Desc_Componente='Posto de Atendimento - SAU'),self.row(ID='TEST-CAR',Desc_Componente='Veículo Operacional')],'official-support',None,municipality_at=lambda *p:'São Bernardo do Campo')
  self.assertEqual(len(rows),1);self.assertEqual(rows[0]['event_type'],'SAU')
 def test_polygon_conflict_remains_inventory_not_map_geometry(self):
  row=normalize([self.row()],'artesp-tolls',None,municipality_at=lambda *p:'Different city')[0]
  self.assertIsNone(row['geometry']);self.assertFalse(row['payload_json']['coordinate_verified']);self.assertIn('Latitude',row['payload_json'])
 def test_direction_not_relaxed(self):
  row=normalize([self.row()],'artesp-tolls',None,municipality_at=lambda *p:'São Bernardo do Campo')[0]
  p=row['geometry']['coordinates'];route=[[p[0],p[1]-.001],[p[0],p[1]+.001]]
  self.assertEqual(corridor([row],route,0,'ROAD_MODE',20),[])
  self.assertEqual(len(corridor([row],route[::-1],0,'ROAD_MODE',20)),1)
 def test_schema_or_empty_preserves_snapshot_via_failure(self):
  for rows in ([],[self.row(Cod_Status='Mystery')],[self.row(),self.row()]):
   with self.assertRaises(SchemaChanged):normalize(rows,'artesp-tolls',None,municipality_at=lambda *p:'São Bernardo do Campo')
 def test_disabled_not_silently_active(self):
  row=normalize([self.row(Cod_Status='Desativado')],'artesp-tolls',None,municipality_at=lambda *p:'São Bernardo do Campo')[0]
  self.assertEqual(row['status'],'ended')
 def test_bad_xlsx_rejected(self):
  with self.assertRaises(SchemaChanged):list(records(b'not an xlsx'))
if __name__=='__main__':unittest.main()
