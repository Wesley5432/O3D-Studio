import sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from cfg_adaptation import lights,move_light,adapt_references
from script_transfer import compatibility,swap_scripts
import test_vehicle_workflows as fixtures

class AdaptationTests(unittest.TestCase):
 def test_light_coordinates_preserve_other_arguments(self):
  text='[spotlight]\n1\n2\n3\n0\n1\n0\n255\n255\n255\n[interiorlight]\nlight_on\n2\n240\n240\n250\n4\n5\n6\n'
  result=move_light(text,1,[7,8,9]);self.assertEqual(result,text.replace('4\n5\n6','7\n8\n9'));self.assertEqual(lights(result)[1]['xyz'],[7,8,9])
  with self.assertRaises(ValueError):move_light(text,0,[float('nan'),0,0])
 def test_mapping_contexts_only(self):
  text='[mesh]\nold.o3d\n[visible]\nold\n1\n[matl_change]\nold.png\n0\nold\n[mouseevent]\nclick\n[newanim]\norigin_from_mesh\nanim_rot\nold\n1200\n[texttexture]\nroute\nFont\n'
  out=adapt_references(text,{'numeric':{'old':'new'},'events':{'click':'press'},'strings':{'route':'line'}})
  self.assertIn('old.o3d',out);self.assertIn('old.png',out);self.assertIn('anim_rot\nnew\n1200',out);self.assertIn('[mouseevent]\npress',out);self.assertIn('[texttexture]\nline\nFont',out)
 def test_mapped_script_swap(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);f=fixtures.WorkflowTests();target=f.fixture(root,'target','porta');donor=f.fixture(root,'donor','door_new');mapping={'numeric':{'porta':'door_new'}}
   self.assertFalse(compatibility(target,donor)['compatible_references']);self.assertTrue(compatibility(target,donor,mapping)['compatible_references'])
   out=swap_scripts(target,donor,root/'out',mapping);self.assertIn('anim_rot\ndoor_new\n90',(out/'Model/model.cfg').read_text());self.assertIn('anim_rot\nporta\n90',(target.parent/'Model/model.cfg').read_text())
 def test_bad_mapping_rejected(self):
  with self.assertRaises(ValueError):adapt_references('',{'numeric':{'x':'bad\nname'}})
