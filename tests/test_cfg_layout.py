import sys,unittest,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from vehicle_template import *
from test_template import mesh

class LayoutTests(unittest.TestCase):
 def test_preserve_parameter_whitespace(self):
  source='### PORTA\n[mesh]\n  old.o3d  \n\n[newanim]\norigin_from_mesh\nanim_rot\nbrake\n-90\n'
  self.assertEqual(set_arg(source,'[mesh]',0,'new.o3d'),source.replace('old.o3d','new.o3d'))
 def test_external_cfg_preserves_real_template(self):
  original=Path(__file__).resolve().parents[1]/'examples'/'TorinoS_MB.cfg'
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp)/'bus';(root/'Model').mkdir(parents=True)
   (root/'test.osc').write_text('{init}\n{end}\n')
   bus=root/'test.bus';bus.write_text('[script]\n1\ntest.osc\n[model]\nModel\\default.cfg\n')
   (root/'Model'/'default.cfg').write_text('OLD CFG\n')
   for c in commands(txt(original)):
    if c['tag']=='[mesh]':
     p=root/'Model'/arg(c).replace('\\','/');p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(mesh('fixture.png'))
   t=load_template(bus,original);plan=new_plan(t,'');plan['mapping']={p['id']:{'mode':'keep'} for p in t['pieces']}
   result,_=render_cfg(t,plan);self.assertEqual(result,txt(original));self.assertEqual(len(t['pieces']),306)
   out=build(t,plan,Path(tmp)/'output');self.assertEqual((out/'Vehicles'/'Meu_veiculo'/'Model'/'default.cfg').read_bytes(),original.read_bytes())
   self.assertEqual((root/'Model'/'default.cfg').read_text(),'OLD CFG\n')
   plan['font_map']={'CorpoS_byZane':'MinhaFonte'}
   result,_=render_cfg(t,plan);self.assertEqual(result,txt(original).replace('\nCorpoS_byZane\n','\nMinhaFonte\n'))
if __name__=='__main__':unittest.main()
