import sys, unittest, tempfile, json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from project import new_project, render_cfg, recipe, validate_project

class ProjectTests(unittest.TestCase):
 def setUp(self):
  self.project=new_project({'meshes':[{'object':'Door','file':'door.o3d','materials':[{'texture':'paint.png','occurrence':0},{'texture':'paint.png','occurrence':1}]}]})
  self.project['profile']={'variables':['door_0'],'triggers':['horn'],'missing':[]}
 def test_door(self):
  part=self.project['parts'][0];part['animations']=recipe('door',variable='door_0',factor=-90)
  cfg=render_cfg(self.project)
  self.assertIn('origin_from_mesh\norigin_rot_y\n90\nanim_rot\ndoor_0\n-90',cfg)
 def test_material_occurrence(self):
  p=self.project['parts'][0];p['material_rules']=[{'slot':1,'alpha':2}]
  self.assertIn('[matl]\npaint.png\n1\n\n[matl_alpha]\n2',render_cfg(self.project))
 def test_invalid_variable(self):
  self.project['parts'][0]['animations']=recipe('door',variable='wrong')
  with self.assertRaises(ValueError): render_cfg(self.project)
 def test_parent_cycle(self):
  self.project['parts'][0]['parent']=self.project['parts'][0]['id']
  with self.assertRaises(ValueError):render_cfg(self.project)
 def test_cfg_injection(self):
  self.project['parts'][0]['file']='x.o3d\n[mesh]\nx.o3d'
  with self.assertRaises(ValueError):render_cfg(self.project)
 def test_wheel(self):
  a=recipe('wheel_front',axle=0,side='R');self.assertEqual([x['variable'] for x in a],['Wheel_Rotation_0_R','Axle_Suspension_0_R','Axle_Steering_0_R'])
  self.project['parts'][0]['animations']=a
  self.assertIn('57.29577951308232',render_cfg(self.project))
if __name__=='__main__':unittest.main()

class MoreProjectTests(unittest.TestCase):
 def test_profile_files_and_event_family(self):
  from project import load_profile
  with tempfile.TemporaryDirectory() as t:
   d=Path(t);(d/'Script').mkdir();(d/'Script'/'vars.txt').write_text('door_0\n')
   (d/'Script'/'a.osc').write_text("' {trigger:comment_only}\n{trigger:handle_drag}\n{end}\n")
   (d/'bus.bus').write_text('[script]\n1\nscript\\a.osc\n[varnamelist]\n1\nscript\\vars.txt\n[constfile]\n1\nScript\\missing.txt\n')
   p=load_profile(d/'bus.bus');self.assertEqual(p['triggers'],['handle_drag']);self.assertEqual(p['variables'],['door_0']);self.assertEqual(len(p['missing']),1)
   project=new_project({'meshes':[{'object':'D','file':'d.o3d'}]});project['profile']=p
   with self.assertRaises(ValueError):render_cfg(project)
   (d/'Script'/'missing.txt').write_text('[const]\nx\n1\n');project['profile']=load_profile(d/'bus.bus')
   project['parts'][0]['mouseevent']='handle';self.assertIn('[mouseevent]\nhandle',render_cfg(project))
 def test_parent_before_child_and_manual_pivot(self):
  p=new_project({'meshes':[{'object':'child','file':'c.o3d'},{'object':'parent','file':'p.o3d'}]})
  p['parts'][0]['parent']='part_0001';p['parts'][0]['pivot']=[1,2,3];p['parts'][0]['animations']=recipe('custom',variable='brake',factor=20)
  cfg=render_cfg(p);self.assertLess(cfg.index('p.o3d'),cfg.index('c.o3d'));self.assertIn('origin_trans\n1\n2\n3',cfg)
