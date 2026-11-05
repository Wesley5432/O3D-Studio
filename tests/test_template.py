import sys,unittest,tempfile,json,struct
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from vehicle_template import *
from o3d_binary import scan

def mesh(texture):
 raw=texture.encode('cp1252')
 return b'\x84\x19\x07\x00'+struct.pack('<I',0xffffffff)+b'\x17'+struct.pack('<I',3)+struct.pack('<24f',*([0.0]*24))+b'\x49'+struct.pack('<I3HH',1,0,1,2,0)+b'\x26'+struct.pack('<H',1)+struct.pack('<11f',*([1.0]*11))+bytes([len(raw)])+raw+b'\x79'+struct.pack('<16f',*([1.0]*16))

class TemplateTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.base=self.root/'base';self.base.mkdir();(self.base/'Model').mkdir();(self.base/'Texture').mkdir()
  (self.base/'Model'/'door.o3d').write_bytes(mesh('old.png'));(self.base/'Texture'/'old.png').write_bytes(b'old image')
  (self.base/'a.osc').write_text('{init}\n{end}\n')
  (self.base/'a.bus').write_text('[script]\n1\na.osc\n[friendlyname]\nMaker\nBus\nVariant\n[model]\nModel\\model.cfg\n')
  self.cfg='[CTC]\nColorscheme\nTexture\\Paint\n0\n[CTCTexture]\npaint\nold.png\n[texttexture]\nline\nArial\n100\n50\n0\n255\n255\n255\n[mesh]\ndoor.o3d\n[mesh_ident]\ndoor\n[newanim]\norigin_from_mesh\norigin_rot_y\n90\nanim_rot\nbrake\n-90\n[matl]\nold.png\n0\n[matl_alpha]\n2\n'
  (self.base/'Model'/'model.cfg').write_text(self.cfg)
  self.t=load_template(self.base/'a.bus');self.p=new_plan(self.t,'');self.p['mapping']={'mesh_0000':{'mode':'keep'}}
 def tearDown(self):self.temp.cleanup()
 def replace(self):
  c=self.root/'converted';(c/'model').mkdir(parents=True);(c/'texture').mkdir();(c/'model'/'new.o3d').write_bytes(mesh('new.png'));(c/'texture'/'new.png').write_bytes(b'new image');(c/'project.json').write_text(json.dumps({'parts':[{'file':'new.o3d'}]}));self.p['converted']=str(c)
  self.p['mapping']['mesh_0000']={'mode':'replace','target':'new.o3d','materials':{'old.png|0':0},'confirmed':True};self.p['skin_targets']={'paint':'new.png'}
 def test_noop_preserves_exact_structure(self):self.assertEqual(render_cfg(self.t,self.p)[0],self.cfg)
 def test_pending_blocks_export(self):
  self.p['mapping']={}
  with self.assertRaises(ValueError):render_cfg(self.t,self.p)
 def test_build_replacement_keeps_geometry_and_animation(self):
  self.replace();out=build(self.t,self.p,self.root/'out');v=out/'Vehicles'/'Meu_veiculo';cfg=txt(v/'Model'/'model.cfg');name=render_cfg(self.t,self.p)[1]['new.png']
  self.assertIn('[matl]\n'+name+'\n0',cfg);self.assertIn('origin_rot_y\n90\nanim_rot\nbrake\n-90',cfg);self.assertIn('[CTCTexture]\npaint\n'+name,cfg)
  data=(v/'Model'/'Convertidos'/'new.o3d').read_bytes();self.assertEqual(patch_textures(data,{name:'new.png'}),mesh('new.png'));self.assertEqual((v/'Texture'/name).read_bytes(),b'new image');self.assertEqual(txt(self.base/'Model'/'model.cfg'),self.cfg)
 def test_required_material_and_texture(self):
  self.replace();self.p['mapping']['mesh_0000']['materials']={};self.assertTrue(scan_plan(self.t,self.p)['errors']);self.p['mapping']['mesh_0000']['materials']={'old.png|0':0};(Path(self.p['converted'])/'texture'/'new.png').unlink();self.assertTrue(scan_plan(self.t,self.p)['errors'])
 def test_skin_requires_explicit_binding(self):
  self.replace();self.p['skin_targets']={}
  with self.assertRaises(ValueError):render_cfg(self.t,self.p)
 def test_reference_change_blocks(self):
  (self.base/'Model'/'model.cfg').write_text(self.cfg+'\n')
  with self.assertRaises(ValueError):build(self.t,self.p,self.root/'out')
 def test_source_output_rejected(self):
  with self.assertRaises(ValueError):build(self.t,self.p,self.base/'output')
 def test_missing_parent_rejected(self):
  self.t['pieces'][0]['block']+='[animparent]\nmissing\n';self.assertTrue(scan_plan(self.t,self.p)['errors'])
 def test_fonts_and_pivot_and_variable(self):
  self.replace();self.p['font_map']={'Arial':'My Font'};self.p['mapping']['mesh_0000'].update(pivot=[1,2,3],variables={'brake':'throttle'});cfg,_=render_cfg(self.t,self.p);self.assertIn('origin_trans\n1\n2\n3',cfg);self.assertIn('anim_rot\nthrottle\n-90',cfg);self.assertIn('line\nMy Font',cfg)
if __name__=='__main__':unittest.main()
