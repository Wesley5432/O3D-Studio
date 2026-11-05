import unittest
import test_template
from vehicle_template import render_cfg,scan_plan,preview_piece

class PieceBlockTests(unittest.TestCase):
 setUp=test_template.TemplateTests.setUp
 tearDown=test_template.TemplateTests.tearDown
 replace=test_template.TemplateTests.replace
 def volante(self):
  self.replace()
  self.t['pieces'][0]['block']='[mesh]\ndoor.o3d\n---\n[matl_change]\nold.png\n0\nlights_stand\n\n[matl_item]\n\n[matl_nightmap]\nInterior_LM.png\n\n[animparent]\najuste_volante\n\n[mesh_ident]\nvolante_rot\n\n[mouseevent]\ncp_whe_pos\n\n[visible]\ncp_lenkrad_visible\n1\n\n[newanim]\norigin_from_mesh\norigin_rot_y\n90\nanim_rot\nAxle_Steering_0_L\n1200\n'
  parent=dict(self.t['pieces'][0],id='mesh_parent',block='[mesh]\ndoor.o3d\n[mesh_ident]\najuste_volante\n',selectors={},variables=[])
  self.t['pieces'].insert(0,parent);self.p['mapping']['mesh_parent']={'mode':'keep'}
 def test_complete_steering_block_and_preview(self):
  self.volante();cfg,names=render_cfg(self.t,self.p)
  expected=self.t['pieces'][1]['block'].replace('door.o3d','Convertidos\\new.o3d').replace('old.png',names['new.png'])
  self.assertTrue(cfg.endswith(expected));self.assertEqual(preview_piece(self.t['pieces'][1],self.p['mapping']['mesh_0000'],scan_plan(self.t,self.p)['targets']),expected)
 def test_duplicate_identity_blocked(self):
  self.volante();self.t['pieces'][0]['block']+='[mesh_ident]\nvolante_rot\n'
  self.assertTrue(any('duplicado' in e for e in scan_plan(self.t,self.p)['errors']))
 def test_parent_cycle_blocked(self):
  self.volante();self.t['pieces'][0]['block']+='[animparent]\nvolante_rot\n'
  self.assertTrue(any('Ciclo' in e for e in scan_plan(self.t,self.p)['errors']))
