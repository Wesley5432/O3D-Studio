"""Editable model configuration, not a vehicle physics/script generator. GPL-3+."""
import json, math, re, os, uuid, copy
from pathlib import Path
from asset_paths import mesh_path

def atomic_text(path,text):
 path=Path(path);tmp=path.with_name('.'+path.name+'.'+uuid.uuid4().hex+'.tmp')
 try:
  tmp.write_text(text,encoding='utf8' if path.suffix=='.json' else 'cp1252');os.replace(tmp,path)
 finally:tmp.unlink(missing_ok=True)

def new_project(report):
 return {'version':2,'profile':None,'parts':[{'id':'part_%04d'%i,'name':m['object'],'file':m['file'],'parent':'','pivot':None,'animations':[],'mouseevent':'','visible':None,'material_rules':[],'materials':m.get('materials',[]),'origin_xyz':m.get('origin_xyz',[0,0,0])} for i,m in enumerate(report['meshes'])]}

def recipe(kind,variable='door_0',factor=-90,axle=0,side='R'):
 def a(v,f,r=(0,0,0),kind='rot'):return {'type':kind,'variable':v,'factor':f,'origin_rotation':list(r)}
 if kind=='static':return []
 if kind=='door':return [a(variable,float(factor),(0,90,0))]
 if kind=='steering':return [a('Axle_Steering_0_L',float(factor),(0,90,0))]
 if kind=='custom':return [a(variable,float(factor))]
 if kind in {'wheel_front','wheel_rear'}:
  if side not in {'L','R'} or int(axle)!=axle or not 0<=axle<=9:raise ValueError('Eixo/lado inválido')
  suffix=str(axle)+'_'+side
  result=[a('Wheel_Rotation_'+suffix,180/math.pi),a('Axle_Suspension_'+suffix,1,(0,-90,0),'trans')]
  if kind=='wheel_front':result.append(a('Axle_Steering_'+suffix,180/math.pi,(0,90,0)))
  return result
 raise ValueError('Tipo desconhecido')

def token(s,label='identificador',empty=False):
 if not isinstance(s,str) or (not s and not empty) or re.search(r'[\s\[\]{}()]',s):raise ValueError('Inválido: '+label)
 return s

def number(v):
 v=float(v)
 if not math.isfinite(v):raise ValueError('Número não finito')
 return format(v,'.16g')

def variable_ok(v,profile):
 token(v,'variável')
 return v in {'throttle','brake','clutch'} or bool(re.fullmatch(r'(?:Wheel_Rotation|Axle_Suspension|Axle_Steering)_[0-9]_[LR]',v)) or v in (profile or {}).get('variables',[])

def validate_project(project):
 if project.get('version')!=2:raise ValueError('Versão de projeto incompatível')
 parts=project.get('parts',[])
 if not parts:raise ValueError('Projeto sem peças')
 ids=[token(p['id']) for p in parts]
 if len(set(ids))!=len(ids):raise ValueError('IDs duplicados')
 profile=copy.deepcopy(project.get('profile') or {})
 manual=project.get('custom_variables',[])
 if not isinstance(manual,list) or any(not isinstance(v,str) or not re.fullmatch(r'[A-Za-z_][A-Za-z_0-9]*',v) for v in manual):raise ValueError('Variável manual inválida')
 profile['variables']=sorted(set(profile.get('variables',[]))|set(manual))
 for p in parts:
  f=p['file']
  mesh_path(f)
  if p.get('parent') and p['parent'] not in ids:raise ValueError('Parent não encontrado')
  if p.get('pivot') is not None:
   if len(p['pivot'])!=3:raise ValueError('Pivô requer XYZ')
   for v in p['pivot']:number(v)
  for a in p['animations']:
   if a['type'] not in {'rot','trans'}:raise ValueError('Tipo de animação inválido')
   if not variable_ok(a['variable'],profile):raise ValueError('Variável não reconhecida no perfil: '+a['variable'])
   number(a['factor'])
   if len(a['origin_rotation'])!=3:raise ValueError('Rotação requer XYZ')
   for v in a['origin_rotation']:number(v)
  if p.get('visible'):
   if not variable_ok(p['visible']['variable'],profile):raise ValueError('Variável de visibilidade não reconhecida')
   number(p['visible']['value'])
  if p.get('mouseevent'):
   e=token(p['mouseevent']);available=(profile or {}).get('triggers',[])
   if not any(x in available for x in [e,e+'_off',e+'_drag']):raise ValueError('Evento ausente no perfil: '+e)
  for mat in p.get('materials',[]):
   tex=mat['texture']
   if not isinstance(tex,str) or re.search(r'[\\/\r\n\[\]:]',tex):raise ValueError('Nome de textura inválido')
   tex.encode('cp1252')
   if len(tex.encode('cp1252'))>255 or not isinstance(mat['occurrence'],int) or mat['occurrence']<0:raise ValueError('Ocorrência/material inválido')
  used=set()
  for rule in p['material_rules']:
   slot=rule['slot']
   if not isinstance(slot,int) or not 0<=slot<len(p['materials']) or slot in used:raise ValueError('Slot de material inválido/duplicado')
   used.add(slot);mat=p['materials'][slot]
   if not mat['texture']:raise ValueError('Slot sem textura identificável')
   if rule.get('alpha') not in {None,0,1,2}:raise ValueError('Modo alpha inválido')
   if rule.get('nightmap'):
    if Path(rule['nightmap']).name!=rule['nightmap'] or re.search(r'[\\/\r\n\[\]:]',rule['nightmap']):raise ValueError('Nightmap inválido')
    if not variable_ok(rule.get('variable',''),profile):raise ValueError('Variável de luz não reconhecida')
 if profile and profile.get('missing'):raise ValueError('O perfil possui arquivos de script/variáveis/constantes ausentes. Selecione uma base completa.')
 byid={p['id']:p for p in parts};order=[];visiting=set();done=set()
 def visit(p):
  if p['id'] in visiting:raise ValueError('Ciclo na hierarquia')
  if p['id'] in done:return
  visiting.add(p['id'])
  if p.get('parent'):visit(byid[p['parent']])
  visiting.remove(p['id']);done.add(p['id']);order.append(p)
 for p in parts:visit(p)
 return order

def render_cfg(project):
 parts=validate_project(project);out=['########################################','MODELO UNIVERSAL - O3D Auto Converter 0.6','Configuracao visual; requer integracao ao .bus e scripts.','########################################','']
 def emit(tag,*args):out.extend([tag,*map(str,args),''])
 for p in parts:
  label=str(p.get('name',p['id'])).replace('\n',' ').replace('\r',' ').encode('cp1252','replace').decode('cp1252')
  out.extend(['########################################','PECA: '+label,'########################################',''])
  emit('[mesh]',p['file'].replace('/','\\'));emit('[mesh_ident]',p['id'])
  if p.get('parent'):emit('[animparent]',p['parent'])
  if p.get('mouseevent'):emit('[mouseevent]',p['mouseevent'])
  if p.get('visible'):emit('[visible]',p['visible']['variable'],number(p['visible']['value']))
  for a in p['animations']:
   out.append('[newanim]')
   if p.get('pivot') is None:out.append('origin_from_mesh')
   else:out.extend(['origin_trans',*[number(x) for x in p['pivot']]])
   for axis,v in zip('xyz',a['origin_rotation']):
    if float(v):out.extend(['origin_rot_'+axis,number(v)])
   out.extend(['anim_'+a['type'],a['variable'],number(a['factor']),''])
  for rule in p['material_rules']:
   mat=p['materials'][rule['slot']]
   emit('[matl]',mat['texture'],mat['occurrence'])
   if rule.get('alpha') is not None:emit('[matl_alpha]',rule['alpha'])
   if rule.get('nightmap'):
    emit('[matl_change]',mat['texture'],mat['occurrence'],rule['variable']);emit('[matl_item]');emit('[matl_nightmap]',rule['nightmap'])
 result='\n'.join(out);result.encode('cp1252');return result

def save_project(path,project):
 # Save unfinished drafts, but require a valid model to export CFG.
 atomic_text(path,json.dumps(project,ensure_ascii=False,indent=2))

def export_cfg(folder,project,target=None):
 folder=Path(folder);cfg=render_cfg(project)
 for p in project['parts']:
  if not (folder/'model'/p['file']).is_file():raise ValueError('O3D ausente: '+p['file'])
  for r in p['material_rules']:
   if r.get('nightmap') and not (folder/'texture'/r['nightmap']).is_file():raise ValueError('Nightmap ausente: '+r['nightmap'])
 target=Path(target) if target else folder/'model'/'Model_gerado.cfg'
 if target.suffix.lower()!='.cfg':raise ValueError('Escolha um arquivo .cfg de saída')
 if not target.parent.is_dir():raise ValueError('A pasta de saída não existe')
 lines=cfg.splitlines()
 for i,line in enumerate(lines[:-1]):
  if line=='[mesh]':
   relative=os.path.relpath((folder/'model'/lines[i+1].replace('\\','/')).resolve(),target.parent.resolve()).replace(os.sep,'\\')
   if any(c in relative for c in '\r\n[]'):raise ValueError('Caminho de malha inválido')
   lines[i+1]=relative
 cfg='\n'.join(lines)+'\n';cfg.encode('cp1252')
 if target.exists():
  backup=target.with_name(target.stem+'.backup_'+uuid.uuid4().hex[:8]+'.cfg');backup.write_bytes(target.read_bytes())
 atomic_text(target,cfg);return target

def load_profile(busfile):
 busfile=Path(busfile);root=busfile.parent;lookup={p.relative_to(root).as_posix().casefold():p for p in root.rglob('*') if p.is_file()}
 lines=busfile.read_text(encoding='cp1252').splitlines();selected={};missing=[];variables=set();triggers=set();strings=set()
 for i,l in enumerate(lines):
  if l.strip() in {'[script]','[varnamelist]','[constfile]','[stringvarnamelist]'}:
   count=int(lines[i+1]);refs=[x.strip() for x in lines[i+2:i+2+count]]
   if count<0 or len(refs)!=count:raise ValueError('Lista truncada no .bus')
   selected[l.strip()]=refs
   for ref in refs:
    p=lookup.get(ref.replace('\\','/').casefold())
    if p is None:missing.append(ref);continue
    text=p.read_text(encoding='cp1252')
    if l.strip()=='[varnamelist]':variables.update(x.strip() for x in text.splitlines() if re.fullmatch(r'[A-Za-z_][A-Za-z_0-9]*',x.strip()))
    if l.strip()=='[stringvarnamelist]':strings.update(x.strip() for x in text.splitlines() if re.fullmatch(r'[A-Za-z_][A-Za-z_0-9]*',x.strip()))
    if l.strip()=='[script]':
     clean='\n'.join(x.split("'",1)[0] for x in text.splitlines());triggers.update(re.findall(r'\{trigger:([^}]+)\}',clean))
 if not selected.get('[script]'):raise ValueError('O .bus não declara scripts')
 return {'name':busfile.name,'source':str(busfile.resolve()),'string_variables':sorted(strings),'variables':sorted(variables),'triggers':sorted(triggers),'selected':selected,'missing':missing}


def load_scripts(paths):
 """Read numeric/string references and trigger definitions; never execute OSC."""
 variables=set();strings=set();triggers=set();sources=[]
 for value in paths:
  path=Path(value).resolve()
  if path.suffix.lower()!='.osc':raise ValueError('Selecione scripts .osc')
  clean='\n'.join(line.split("'",1)[0] for line in path.read_text(encoding='cp1252').splitlines())
  variables.update(re.findall(r'\((?:L|S)\.L\.([A-Za-z_][A-Za-z_0-9]*)\)',clean))
  strings.update(re.findall(r'\((?:L|S)\.\$\.([A-Za-z_][A-Za-z_0-9]*)\)',clean))
  triggers.update(re.findall(r'\{trigger:([A-Za-z_][A-Za-z_0-9]*)\}',clean));sources.append(str(path))
 if not sources:raise ValueError('Nenhum script selecionado')
 return {'name':'Scripts selecionados','variables':sorted(variables),'string_variables':sorted(strings),'triggers':sorted(triggers),'missing':[],'selected':{'[script]':sources},'references_only':True}
