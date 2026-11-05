import json,struct,tempfile,unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from engine import run
from asset_paths import clean_name,mesh_path,GROUPS
from project import export_cfg
from o3d_binary import read
from check_conversion import chunk,read as read_geometry
from PIL import Image

class ThreeDSTests(unittest.TestCase):
 def test_real_3ds_mix_texture_recovery_and_grouped_cfg(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);model=root/'input';model.mkdir();textures=root/'images';textures.mkdir()
   Image.new('RGB',(2,2),(10,120,220)).save(textures/'Paint.PNG')
   material=chunk(0xAFFF,chunk(0xA000,b'paint\0')+chunk(0xA020,chunk(0x0011,bytes([255,255,255])))+chunk(0xA200,chunk(0x0030,struct.pack('<H',100))+chunk(0xA300,b'paint.png\0')+chunk(0xA354,struct.pack('<f',2.0))+chunk(0xA35A,struct.pack('<f',0.25))))
   vertices=chunk(0x4110,struct.pack('<H9f',3,0,0,0,2,0,0,0,3,0))
   faces=chunk(0x4120,struct.pack('<H4H',1,0,1,2,0)+chunk(0x4130,b'paint\0'+struct.pack('<HH',1,0)))
   uv=chunk(0x4140,struct.pack('<H6f',3,0,0,1,0,0,1))
   src=model/'fixture.3ds';src.write_bytes(chunk(0x4d4d,chunk(0x3d3d,material+chunk(0x4000,b'Painel frente\0'+chunk(0x4100,vertices+faces+uv)))))
   out=run(src,root/'out',organize=True,texture_directory=textures)
   report=json.loads((out/'report.json').read_text());self.assertEqual(len(report['textures']),1)
   tex=report['meshes'][0]['materials'][0]['texture'];self.assertTrue(tex)
   self.assertEqual((out/'texture'/tex).read_bytes(),(textures/'Paint.PNG').read_bytes())
   self.assertTrue(report['textures'][0]['available']);self.assertTrue(report['meshes'][0]['file'].startswith('Painel/'))
   self.assertEqual(read(out/'model'/report['meshes'][0]['file'])['textures'],[tex])
   vertices,_,_=read_geometry(out/'model'/report['meshes'][0]['file'])
   self.assertEqual({(round(v[6],4),round(v[7],4)) for v in vertices},{(0,1.25),(0.5,1.25),(0,0.25)},report['warnings'])
   self.assertTrue(all((out/'model'/g).is_dir() for g in GROUPS))
   project=json.loads((out/'project.json').read_text());cfg=export_cfg(out,project)
   self.assertIn('[mesh]\nPainel\\',cfg.read_text(encoding='cp1252'))
   self.assertFalse(any('procedural' in w or 'aproximação' in w for w in report['warnings']))
   (textures/'duplicate').mkdir();Image.new('RGB',(2,2),(255,0,0)).save(textures/'duplicate'/'paint.png')
   ambiguous=run(src,root/'ambiguous',texture_directory=textures);r=json.loads((ambiguous/'report.json').read_text())
   self.assertTrue(any('ambígua' in w for w in r['warnings']));self.assertFalse(r['textures'][0]['available'])
   (textures/'Paint.PNG').unlink();(textures/'duplicate'/'paint.png').unlink()
   missing=run(src,root/'missing',texture_directory=textures);r=json.loads((missing/'report.json').read_text())
   self.assertFalse(r['textures'][0]['available']);self.assertTrue(r['meshes'][0]['materials'][0]['texture'])

 def test_names_and_traversal(self):
  self.assertEqual(clean_name('Suspensão: dianteira?'),'Suspensao_dianteira');self.assertEqual(clean_name('CON'),'_CON')
  self.assertEqual(mesh_path('Interior/porta.o3d'),'Interior/porta.o3d')
  for invalid in ['../x.o3d','/x.o3d','Interior/../../x.o3d','foo/x.o3d','Interior\\x.o3d']:
   with self.assertRaises(ValueError):mesh_path(invalid)
if __name__=='__main__':unittest.main()
