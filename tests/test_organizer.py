import json,tempfile,unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from organizer import organize_copy
from project import new_project,export_cfg
from vehicle_template import target_parts
from test_template import mesh
class OrganizerTests(unittest.TestCase):
 def test_new_copy_updates_paths_and_cfg(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t)/'original';(root/'model').mkdir(parents=True)
   (root/'model'/'a.o3d').write_bytes(mesh(''))
   report={'meshes':[{'object':'Motor estranho','file':'a.o3d','materials':[]}],'textures':[]}
   (root/'report.json').write_text(json.dumps(report));project=new_project(report)
   export_cfg(root,project);project['cfg_output']=str(root/'model'/'Model_gerado.cfg')
   out=organize_copy(root,project,{'part_0000':{'group':'Interior','name':'Banco: 1?'}})
   result=json.loads((out/'project.json').read_text());self.assertEqual(result['parts'][0]['file'],'Interior/0000_Banco_1.o3d')
   self.assertTrue((root/'model'/'a.o3d').exists());self.assertFalse((out/'model'/'a.o3d').exists())
   self.assertEqual((out/'model'/'Interior'/'0000_Banco_1.o3d').read_bytes(),(root/'model'/'a.o3d').read_bytes())
   self.assertIn('[mesh]\nInterior\\0000_Banco_1.o3d',(out/'model'/'Model_gerado.cfg').read_text())
   self.assertEqual(json.loads((out/'report.json').read_text())['meshes'][0]['file'],result['parts'][0]['file'])
   self.assertEqual(len(target_parts(out)),1);export_cfg(out,result)
 def test_grouped_template_export(self):
  from test_template import TemplateTests
  from vehicle_template import build
  case=TemplateTests();case.setUp()
  try:
   case.replace();folder=Path(case.p['converted']);(folder/'model'/'Exterior').mkdir();(folder/'model'/'new.o3d').rename(folder/'model'/'Exterior'/'new.o3d')
   (folder/'project.json').write_text(json.dumps({'parts':[{'file':'Exterior/new.o3d'}]}));case.p['mapping']['mesh_0000']['target']='Exterior/new.o3d'
   out=build(case.t,case.p,case.root/'out');self.assertTrue((out/'Vehicles'/'Meu_veiculo'/'Model'/'Convertidos'/'Exterior'/'new.o3d').exists())
  finally:case.tearDown()
if __name__=='__main__':unittest.main()
