"""Create an editable project from unencrypted O3D without using Blender."""
from output_files import publish
import hashlib,json,shutil,tempfile,uuid
from pathlib import Path
from asset_paths import GROUPS,clean_name,suggest_group,source_mesh_name
from o3d_binary import scan,slots,patch_textures
from project import new_project,save_project,export_cfg
from vehicle_template import index,resolve

def import_o3d(source,destination,textures=None):
 source=Path(source).resolve();dest=Path(destination).resolve()
 if not source.is_dir():raise ValueError('Escolha a pasta com os arquivos O3D')
 if dest==source or dest.is_relative_to(source):raise ValueError('Saída deve ficar fora da pasta de entrada')
 files=index(source);meshes=sorted((p for p in files.values() if p.suffix.lower()=='.o3d'),key=lambda p:p.as_posix())
 if not meshes:raise ValueError('Nenhum O3D encontrado')
 texture_root=Path(textures).resolve() if textures else None;texture_index=index(texture_root) if texture_root else {}
 if texture_root and not texture_root.is_dir():raise ValueError('Pasta de texturas inexistente')
 dest.mkdir(parents=True,exist_ok=True);stage=Path(tempfile.mkdtemp(prefix='.o3d-import-',dir=dest));final=dest
 try:
  for group in GROUPS:(stage/'model'/group).mkdir(parents=True)
  (stage/'texture').mkdir();entries=[];records={};warnings=[];used_mesh_names=set()
  for i,path in enumerate(meshes):
   raw=path.read_bytes();info=scan(raw);names={}
   for texture in info['textures']:
    if not texture:continue
    normalized=texture.replace('\\','/');basename=normalized.rsplit('/',1)[-1]
    if Path(basename).suffix.lower() not in {'.bmp','.png','.tga','.dds','.jpg','.jpeg'}:raise ValueError('Formato de textura não suportado no O3D: '+texture)
    safe=bool(basename==texture and clean_name(Path(basename).stem)==Path(basename).stem)
    name=basename if safe else clean_name(Path(basename).stem)+'_'+hashlib.sha256(texture.encode('cp1252')).hexdigest()[:8]+Path(basename).suffix.lower()
    names[texture]=name
    if texture in records:continue
    found=resolve(texture_root,texture_index,texture)
    if not found:
     candidates=[p for p in texture_index.values() if p.name.casefold()==basename.casefold()]
     if len(candidates)==1:found=candidates[0]
     elif len(candidates)>1:warnings.append('Textura ambígua: '+texture)
    if found:
     output=stage/'texture'/name
     if output.exists() and output.read_bytes()!=found.read_bytes():raise ValueError('Texturas com mesmo nome e conteúdo diferente: '+name)
     shutil.copy2(found,output)
    else:warnings.append('Textura não localizada: '+texture)
    records[texture]={'texture':name,'source_texture':texture,'available':bool(found)}
   group=suggest_group(path.stem);name=group+'/'+source_mesh_name(path.stem,used_mesh_names)
   result=patch_textures(raw,names);(stage/'model'/name).write_bytes(result);matrix=info['matrix']
   if not matrix:warnings.append('O3D sem matriz de origem; configure o pivô antes de animar: '+path.name)
   entries.append({'object':path.stem,'bones':info['bone_names'],'source_o3d':str(path),'file':name,'vertices':info['vertices'],'triangles':info['triangles'],'materials':[{'name':'Material '+str(s['slot']),**s} for s in slots(scan(result))],'origin_xyz':[matrix[12],matrix[14],matrix[13]] if matrix else [0,0,0]})
  report={'format_version':2,'source':str(source),'imported_o3d':True,'meshes':entries,'textures':list(records.values()),'warnings':warnings}
  project=new_project(report);save_project(stage/'project.json',project);(stage/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');
  if any(p.get('bones') for p in project['parts']):
   warnings.append('O3D com pesos: confira os vínculos na aba Deformação antes de gerar o CFG.')
   (stage/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
  else:export_cfg(stage,project,stage/'model'/'model.cfg')
  publish(stage,final);shutil.rmtree(stage);return final
 except Exception:shutil.rmtree(stage,ignore_errors=True);raise
