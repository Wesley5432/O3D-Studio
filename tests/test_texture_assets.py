import sys,tempfile,subprocess,json,unittest,struct
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from engine import run

class AssetsTest(unittest.TestCase):
 def test_names_collisions_slots_missing_origin(self):
  with tempfile.TemporaryDirectory() as t:
   d=Path(t);script=d/'create.py';blend=d/'assets.blend'
   script.write_text('''import bpy,sys
from pathlib import Path
bpy.ops.wm.read_factory_settings(use_empty=True)
d=Path(sys.argv[-1]).parent
m=bpy.data.meshes.new('m');m.from_pydata([(0,0,0),(1,0,0),(0,1,0)],[],[(0,1,2)]);m.update()
o=bpy.data.objects.new('Test',m);bpy.context.collection.objects.link(o)
o.location=(2,3,4)
for folder,col in [('a',(1,0,0,1)),('b',(0,1,0,1))]:
 (d/folder).mkdir();im=bpy.data.images.new(folder,width=2,height=2);im.generated_color=col;im.filepath_raw=str(d/folder/'paint.png');im.file_format='PNG';im.save()
 # Reload as external files to exercise verbatim copy.
 im=bpy.data.images.load(str(d/folder/'paint.png'))
 mat=bpy.data.materials.new(folder);mat.use_nodes=True;n=mat.node_tree.nodes.new('ShaderNodeTexImage');n.image=im
 mat.node_tree.links.new(n.outputs['Color'],mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color']);m.materials.append(mat)
m.materials.append(m.materials[0])
# An unloaded image is deliberately missing, but its reference must survive.
im=bpy.data.images.new('missing',width=1,height=1);im.source='FILE';im.filepath=str(d/'missing.bmp')
mat=bpy.data.materials.new('missing');mat.use_nodes=True;n=mat.node_tree.nodes.new('ShaderNodeTexImage');n.image=im;mat.node_tree.links.new(n.outputs['Color'],mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color']);m.materials.append(mat)
bpy.ops.wm.save_as_mainfile(filepath=sys.argv[-1])
''')
   subprocess.run(['blender','-b','--factory-startup','--python-exit-code','1','--python',str(script),'--',str(blend)],check=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
   out=run(blend,d/'out');report=json.loads((out/'report.json').read_text());materials=report['meshes'][0]['materials']
   self.assertEqual(materials[0]['texture'],'paint.png')
   self.assertNotEqual(materials[1]['texture'],'paint.png')
   self.assertEqual(materials[2]['texture'],'paint.png');self.assertEqual(materials[2]['occurrence'],1)
   self.assertEqual(materials[3]['texture'],'missing.bmp');self.assertFalse((out/'texture'/'missing.bmp').exists())
   self.assertEqual((out/'texture'/materials[0]['texture']).read_bytes(),(d/'a'/'paint.png').read_bytes())
   self.assertEqual((out/'texture'/materials[1]['texture']).read_bytes(),(d/'b'/'paint.png').read_bytes())
   matrix=struct.unpack('<16f',next((out/'model').glob('*.o3d')).read_bytes()[-64:]);self.assertEqual(matrix[12:15],(2,4,3))
if __name__=='__main__':unittest.main()
