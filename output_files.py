"""Publish staged files directly, preserving unrelated output and backing up replacements."""
import shutil,tempfile,uuid
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED

def publish(stage,destination):
 stage=Path(stage).resolve();dest=Path(destination).resolve();dest.mkdir(parents=True,exist_ok=True)
 entries=list(stage.rglob('*'))
 if any(p.is_symlink() for p in entries):raise ValueError('Link simbólico na saída')
 files=[p for p in entries if p.is_file()]
 directories=[dest/p.relative_to(stage) for p in entries if p.is_dir()]
 for directory in directories:
  for parent in [directory,*directory.parents]:
   if parent==dest.parent:break
   if parent.is_symlink():raise ValueError('Link simbólico no destino')
   if parent.exists() and not parent.is_dir():raise ValueError('Arquivo ocupa nome de pasta: '+str(parent))
 targets=[]
 for source in files:
  if source.is_symlink():raise ValueError('Link simbólico na saída')
  target=dest/source.relative_to(stage)
  for parent in [target,*target.parents]:
   if parent==dest.parent:break
   if parent.is_symlink():raise ValueError('Link simbólico no destino')
  if target.exists() and not target.is_file():raise ValueError('Pasta ocupa nome de arquivo: '+str(target))
  targets.append((source,target))
 existing=[t for _,t in targets if t.exists()]
 backup=dest/('backup_exportacao_'+uuid.uuid4().hex[:8]+'.zip') if existing else None
 if backup:
  with ZipFile(backup,'w',ZIP_DEFLATED) as z:
   for target in existing:z.write(target,target.relative_to(dest).as_posix())
 written=[]
 try:
  for directory in directories:directory.mkdir(parents=True,exist_ok=True)
  for source,target in targets:
   target.parent.mkdir(parents=True,exist_ok=True);written.append(target);shutil.copy2(source,target)
 except Exception:
  for target in written:
   if target.exists():target.unlink()
  if backup:
   with ZipFile(backup) as z:z.extractall(dest)
  raise
 return dest

def export_meshes(folder,project,destination,selected=None):
 from asset_paths import mesh_path
 from o3d_binary import read,slots
 from vehicle_template import index,resolve
 folder=Path(folder).resolve();dest=Path(destination).resolve()
 if dest==folder or dest.is_relative_to(folder):raise ValueError('Escolha saída fora do projeto de origem')
 parts=project['parts'] if selected is None else [p for p in project['parts'] if p['id'] in selected]
 if not parts or (selected is not None and len(parts)!=len(set(selected))):raise ValueError('Selecione uma peça válida')
 textures=index(folder/'texture');missing=[]
 with tempfile.TemporaryDirectory() as tmp:
  stage=Path(tmp)
  for part in parts:
   mesh_path(part['file']);source=folder/'model'/part['file'];target=stage/'model'/part['file'];target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
   for slot in slots(read(source)):
    name=slot['texture']
    if not name:continue
    texture=resolve(None,textures,name)
    if not texture:missing.append(name);continue
    target=stage/'texture'/texture.relative_to(folder/'texture');target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(texture,target)
  if missing:raise ValueError('Texturas ausentes: '+', '.join(sorted(set(missing))))
  return publish(stage,dest)
