import unittest,tempfile,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import project as p

class UniversalTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);(self.root/'model').mkdir();(self.root/'model'/'door.o3d').write_bytes(b'fixture')
  self.project=p.new_project({'meshes':[{'object':'Porta','file':'door.o3d','materials':[]}]})
 def tearDown(self):self.tmp.cleanup()
 def test_empty_cfg_generated_and_backup(self):
  target=self.root/'model'/'modelo.cfg';target.write_bytes(b'')
  p.export_cfg(self.root,self.project,target)
  self.assertIn('[mesh]\ndoor.o3d',target.read_text(encoding='cp1252'))
  old=target.read_bytes();p.export_cfg(self.root,self.project,target)
  self.assertIn(old,[x.read_bytes() for x in target.parent.glob('modelo.backup_*.cfg')])
 def test_external_cfg_relative_mesh(self):
  target=self.root/'modelo.cfg';p.export_cfg(self.root,self.project,target)
  self.assertIn('[mesh]\nmodel\\door.o3d',target.read_text(encoding='cp1252'))
 def test_manual_variable(self):
  self.project['custom_variables']=['porta_motor'];self.project['parts'][0]['animations']=p.recipe('door',variable='porta_motor')
  self.assertIn('porta_motor',p.render_cfg(self.project))
  self.project['custom_variables']=['bad\n[mesh]']
  with self.assertRaises(ValueError):p.render_cfg(self.project)
 def test_script_catalog(self):
  script=self.root/'door.osc';script.write_text("' (L.L.fake) {trigger:fake}\n{trigger:door_toggle}\n(L.L.door_open) 1 (S.L.door_open)\n(L.$.destination)\n{end}\n")
  profile=p.load_scripts([script]);self.assertEqual(profile['variables'],['door_open']);self.assertEqual(profile['triggers'],['door_toggle']);self.assertEqual(profile['string_variables'],['destination'])
  self.project['profile']=profile;self.project['parts'][0]['animations']=p.recipe('door',variable='door_open');p.render_cfg(self.project)
 def test_empty_cfg_ui_route_without_bus(self):
  from studio import Studio
  import editor
  class Value:
   def __init__(self,value):self.value=value
   def get(self):return self.value
  target=self.root/'empty.cfg';target.write_bytes(b'  \r\n')
  obj=Studio.__new__(Studio);obj.fields={'cfg':Value(str(target))};seen=[];obj.universal=seen.append
  obj.load();self.assertEqual(seen,[str(target)])
 def test_bus_string_variables(self):
  (self.root/'v.txt').write_text('door_open\n');(self.root/'s.txt').write_text('destination\n');(self.root/'a.osc').write_text('{init}\n{end}\n')
  bus=self.root/'a.bus';bus.write_text('[script]\n1\na.osc\n[varnamelist]\n1\nv.txt\n[stringvarnamelist]\n1\ns.txt\n')
  profile=p.load_profile(bus);self.assertEqual(profile['variables'],['door_open']);self.assertEqual(profile['string_variables'],['destination'])
 def test_bad_target_does_not_overwrite(self):
  target=self.root/'model'/'door.o3d';old=target.read_bytes()
  with self.assertRaises(ValueError):p.export_cfg(self.root,self.project,target)
  self.assertEqual(target.read_bytes(),old)
if __name__=='__main__':unittest.main()
