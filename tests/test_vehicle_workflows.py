import json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from existing_o3d import import_o3d
from script_transfer import swap_scripts,compatibility,package_cfg_scripts
from test_template import mesh
from vehicle_template import render_cfg,build
from project import new_project

class WorkflowTests(unittest.TestCase):
 def test_existing_o3d_without_blender(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);source=root/'source';source.mkdir();textures=root/'images';textures.mkdir()
   raw=mesh('paint.png');(source/'porta.o3d').write_bytes(raw);(textures/'paint.png').write_bytes(b'image')
   out=import_o3d(source,root/'out',textures);project=json.loads((out/'project.json').read_text())
   self.assertEqual((out/'model'/project['parts'][0]['file']).read_bytes(),raw);self.assertTrue((out/'model'/'model.cfg').exists());self.assertEqual((out/'texture'/'paint.png').read_bytes(),b'image')
 def test_protected_o3d_rejected_without_partial_output(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);source=root/'source';source.mkdir();raw=bytearray(mesh(''));raw[4:8]=b'\x00'*4;(source/'protected.o3d').write_bytes(raw)
   with self.assertRaises(ValueError):import_o3d(source,root/'out')
   self.assertEqual(list((root/'out').iterdir()),[])
 def fixture(self,root,name,variable):
  d=root/name;(d/'Model').mkdir(parents=True);(d/'Script').mkdir()
  (d/'Script'/'vars.txt').write_text(variable+'\n');(d/'Script'/'a.osc').write_text('{init}\n{end}\n')
  (d/'Model'/'model.cfg').write_text('[mesh]\npiece.o3d\n[newanim]\norigin_from_mesh\nanim_rot\nporta\n90\n')
  (d/'Model'/'piece.o3d').write_bytes(mesh(''));(d/'vehicle.bus').write_text('[model]\nModel\\model.cfg\n[mass]\n10\n[script]\n1\nScript\\a.osc\n[varnamelist]\n1\nScript\\vars.txt\n')
  return d/'vehicle.bus'
 def test_script_only_preserves_geometry_cfg_and_physics(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);target=self.fixture(root,'target','old');donor=self.fixture(root,'donor','porta');out=swap_scripts(target,donor,root/'out')
   self.assertEqual((out/'Model'/'model.cfg').read_bytes(),(target.parent/'Model'/'model.cfg').read_bytes());self.assertEqual((out/'Model'/'piece.o3d').read_bytes(),(target.parent/'Model'/'piece.o3d').read_bytes())
   result=(out/'vehicle.bus').read_text();self.assertIn('[mass]\n10',result);self.assertIn('Script_Importado_',result);self.assertNotIn('Script_Importado_',target.read_text());self.assertTrue(compatibility(target,donor)['compatible_references'])
 def test_incompatible_scripts_blocked(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);target=self.fixture(root,'target','porta');donor=self.fixture(root,'donor','wrong')
   self.assertEqual(compatibility(target,donor)['missing_variables'],['porta'])
   with self.assertRaises(ValueError):swap_scripts(target,donor,root/'out')
 def test_cfg_with_script_bundle(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);donor=self.fixture(root,'donor','porta');folder=root/'converted';(folder/'model').mkdir(parents=True);(folder/'model'/'x.o3d').write_bytes(mesh(''))
   project=new_project({'meshes':[{'object':'X','file':'x.o3d','materials':[]}]});out=package_cfg_scripts(folder,project,donor,root/'out')
   self.assertTrue((out/'model'/'model.cfg').exists());self.assertTrue((out/'Script_Importado'/'Script'/'a.osc').exists());self.assertIn('[script]\n1',(out/'INCLUIR_NO_BUS.txt').read_text())
 def test_suggestions_require_review_and_ignore_ambiguity(self):
  from vehicle_template import suggest_mappings
  template={'pieces':[{'id':'p','mesh':'MB/Porta_0.o3d','selectors':{}}]}
  targets={'Exterior/0001_Porta_0.o3d':{'name':'Porta_0','slots_actual':[]}}
  result,count=suggest_mappings(template,targets,{})
  self.assertEqual(count,1);self.assertFalse(result['p']['confirmed'])
  targets['Interior/0002_Porta_0.o3d']={'name':'Porta_0','slots_actual':[]}
  self.assertEqual(suggest_mappings(template,targets,{})[1],0)
 def test_skin_on_kept_model_and_font_picker_output(self):
  from test_template import TemplateTests
  case=TemplateTests();case.setUp()
  try:
   skin=case.root/'skins';skin.mkdir();(skin/'Blue.cti').write_text('[item]\nBlue\npaint\nblue.png\n');(skin/'Other.cti').write_text('[item]\nOther\npaint\nother.png\n');(skin/'blue.png').write_bytes(b'blue')
   fonts=case.root/'Fonts';fonts.mkdir();(fonts/'New Font.oft').write_text('[name]\nNew Font\n');(fonts/'glyph.bmp').write_bytes(b'font')
   case.p.update(skin_targets={'paint':'old.png'},skin_file=str(skin/'Blue.cti'),skin_folder=str(skin),fonts_folder=str(fonts),font_map={'Arial':'New Font'})
   cfg,_=render_cfg(case.t,case.p);self.assertIn('[CTCTexture]\npaint\nold.png',cfg);self.assertIn('\nNew Font\n',cfg)
   out=build(case.t,case.p,case.root/'out');paint=out/'Vehicles'/'Meu_veiculo'/'Texture'/'Pinturas_Convertidas'
   self.assertTrue((paint/'Blue.cti').exists());self.assertFalse((paint/'Other.cti').exists());self.assertTrue((out/'Fonts'/'New Font.oft').exists())
  finally:case.tearDown()
if __name__=='__main__':unittest.main()
