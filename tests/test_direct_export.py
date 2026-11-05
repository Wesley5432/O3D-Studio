import sys,unittest,tempfile
from pathlib import Path
from zipfile import ZipFile
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from output_files import publish,export_meshes
from test_template import mesh
import test_vehicle_workflows as workflows
from project import new_project,load_profile
from script_transfer import package_cfg_scripts

class DirectExportTests(unittest.TestCase):
 def test_selected_and_all_direct_with_textures(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);source=root/'source';(source/'model').mkdir(parents=True);(source/'texture').mkdir()
   parts=[]
   for name in ('a','b'):
    (source/'model'/(name+'.o3d')).write_bytes(mesh(name+'.png'));(source/'texture'/(name+'.png')).write_bytes(name.encode());parts.append({'id':name,'file':name+'.o3d'})
   dest=root/'out';self.assertEqual(export_meshes(source,{'parts':parts},dest,['b']),dest)
   self.assertTrue((dest/'model/b.o3d').exists());self.assertFalse((dest/'model/a.o3d').exists());self.assertFalse((dest/'texture/a.png').exists())
   export_meshes(source,{'parts':parts},dest);self.assertTrue((dest/'model/a.o3d').exists())
   self.assertEqual(sorted(p.name for p in dest.iterdir() if p.is_dir()),['model','texture'])
 def test_backup_unrelated_and_rollback(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);stage=root/'stage';stage.mkdir();dest=root/'out';dest.mkdir()
   (stage/'a').write_text('new');(stage/'b').write_text('new');(dest/'a').write_text('old');(dest/'unrelated').write_text('keep')
   import shutil
   real=shutil.copy2
   def fail(source,target):
    if Path(source).name=='b':raise OSError('disk failure')
    return real(source,target)
   with patch('output_files.shutil.copy2',side_effect=fail):
    with self.assertRaises(OSError):publish(stage,dest)
   self.assertEqual((dest/'a').read_text(),'old');self.assertFalse((dest/'b').exists());self.assertEqual((dest/'unrelated').read_text(),'keep')
   publish(stage,dest)
   with ZipFile(next(dest.glob('backup_exportacao_*.zip'))) as z:self.assertEqual(z.read('a'),b'old')
 def test_donor_bus_included_and_relinked(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);donor=workflows.WorkflowTests().fixture(root,'donor','porta');source=root/'source';(source/'model').mkdir(parents=True);(source/'model/x.o3d').write_bytes(mesh(''))
   (donor.parent/'sound.cfg').write_text('sound dependency')
   project=new_project({'meshes':[{'object':'X','file':'x.o3d','materials':[]}]})
   dest=root/'out';self.assertEqual(package_cfg_scripts(source,project,donor,dest),dest)
   bus=(dest/donor.name).read_text();self.assertIn('[model]\nmodel\\model.cfg',bus);self.assertIn('[mass]\n10',bus);self.assertTrue((dest/'sound.cfg').exists());self.assertEqual(load_profile(dest/donor.name)['missing'],[])
   self.assertEqual(donor.read_text().count('Script_Importado'),0)
