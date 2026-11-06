"""Static O3D -> Wavefront OBJ/MTL. No Blender dependency; no script execution."""
import hashlib,json,os,shutil,tempfile
from pathlib import Path
from asset_paths import clean_name,mesh_path
from o3d_binary import scan
from output_files import publish
from vehicle_template import index,resolve

def export_obj(sources,destination,textures=None):
 """sources = [(O3D path, relative OBJ path)]. Coordinates: X right, Y forward, Z up."""
 dest=Path(destination).resolve();sources=[(Path(p).resolve(),Path(n)) for p,n in sources]
 if not sources:raise ValueError('Selecione pelo menos um O3D')
 roots=[]
 for root in textures or []:
  root=Path(root).resolve()
  if root not in roots:roots.append(root)
 lookups=[(root,index(root)) for root in roots];names=set();warnings=[];report=[]
 for source,name in sources:
  mesh_path(name.with_suffix('.o3d').as_posix())
  if source.suffix.casefold()!='.o3d' or name.suffix.casefold()!='.obj':raise ValueError('Entrada O3D e saída OBJ obrigatórias')
  if name.as_posix().casefold() in names:raise ValueError('Nomes de saída repetidos: '+str(name))
  names.add(name.as_posix().casefold())
  if dest==source.parent or dest.is_relative_to(source.parent):raise ValueError('Escolha uma saída fora da pasta dos O3D originais')
 if any(dest==r or dest.is_relative_to(r) for r in roots):raise ValueError('Escolha uma saída fora da pasta de texturas de origem')
 with tempfile.TemporaryDirectory() as tmp:
  stage=Path(tmp)
  for source,name in sources:
   info=scan(source.read_bytes(),geometry=True);target=stage/name;target.parent.mkdir(parents=True,exist_ok=True)
   mtl=target.with_suffix('.mtl');materials=info['material_data'] or [{'texture':'','values':(1,1,1,1,0,0,0,0,0,0,0)}]
   with mtl.open('w',encoding='utf8',newline='\n') as f:
    for i,m in enumerate(materials):
     v=m['values'];f.write(f'newmtl material_{i}\nKd {v[0]:.9g} {v[1]:.9g} {v[2]:.9g}\nd {v[3]:.9g}\nKs {v[4]:.9g} {v[5]:.9g} {v[6]:.9g}\nKe {v[7]:.9g} {v[8]:.9g} {v[9]:.9g}\nNs {max(0,min(1000,v[10])):.9g}\nillum 2\n')
     texture=m['texture']
     if texture:
      found=next((p for _,files in lookups if (p:=resolve(None,files,texture))),None)
      if found:
       digest=hashlib.sha256(found.read_bytes()).hexdigest()[:16];copied=stage/'texturas_obj'/(digest+found.suffix.lower())
       copied.parent.mkdir(exist_ok=True)
       if not copied.exists():shutil.copy2(found,copied)
       f.write('map_Kd '+Path(os.path.relpath(copied,mtl.parent)).as_posix()+'\n')
      else:warnings.append(f'{source.name}: textura não localizada: {texture}')
     f.write('\n')
   with target.open('w',encoding='utf8',newline='\n') as f:
    f.write('# O3D Studio: geometria estática; X direita, Y frente, Z cima.\n# A matriz O3D é o pivô, não uma transformação adicional.\nmtllib '+mtl.name+'\no '+clean_name(source.stem)+'\n')
    for x,y,z,*_ in info['vertex_data']:f.write(f'v {x:.9g} {z:.9g} {y:.9g}\n')
    for *_,u,v in info['vertex_data']:f.write(f'vt {u:.9g} {1-v:.9g}\n')
    for row in info['vertex_data']:f.write(f'vn {row[3]:.9g} {row[5]:.9g} {row[4]:.9g}\n')
    last=None
    for a,b,c,mat in info['triangle_data']:
     if mat!=last:f.write(f'usemtl material_{mat}\n');last=mat
     # Swap Y/Z changes handedness; reverse winding to keep the normals consistent.
     f.write('f '+' '.join(f'{i+1}/{i+1}/{i+1}' for i in (c,b,a))+'\n')
   if info['bones']:warnings.append(source.name+': ossos/pesos não fazem parte do OBJ; exportada a pose estática')
   report.append({'source':str(source),'obj':name.as_posix(),'vertices':info['vertices'],'triangles':info['triangles'],'pivot_o3d':info['matrix']})
  result={'files':report,'warnings':sorted(set(warnings)),'note':'OBJ estático com UV e materiais. Animações, eventos, física e efeitos do CFG não são transferidos.'}
  (stage/'relatorio_obj.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
  publish(stage,dest)
 return result

def export_project_obj(folder,project,destination,selected=None):
 folder=Path(folder).resolve();dest=Path(destination).resolve()
 if dest==folder or dest.is_relative_to(folder):raise ValueError('Escolha saída fora do projeto')
 parts=project['parts'] if selected is None else [p for p in project['parts'] if p['id'] in selected]
 if not parts or (selected is not None and len(parts)!=len(set(selected))):raise ValueError('Selecione uma peça válida')
 sources=[]
 for p in parts:
  mesh_path(p['file']);sources.append((folder/'model'/p['file'],Path(p['file']).with_suffix('.obj')))
 return export_obj(sources,dest,[folder/'texture'])
