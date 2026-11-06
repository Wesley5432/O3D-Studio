"""Build a read-only geometry preview from a reference CFG and current associations."""
import copy
from pathlib import Path
from vehicle_template import commands,arg,index,resolve,variable_patch,pivot_patch
from skin_cfg import bindings

def preview_project(template,plan,targets):
 plan=copy.deepcopy(plan)
 for p in template['pieces']:
  if plan['mapping'].get(p['id'],{}).get('mode','pending')=='pending':plan['mapping'][p['id']]={'mode':'keep'}
 root=Path(template['root']);files=index(root);parent=Path(template['cfg']).parent.relative_to(root).as_posix();parts=[];identities={}
 for piece in template['pieces']:
  m=plan['mapping'][piece['id']]
  if m['mode']=='remove':continue
  if m['mode']=='replace':
   if m.get('target') not in targets:raise ValueError('Selecione o O3D de destino')
   source=Path(plan['converted'])/'model'/m['target']
  else:source=resolve(None,files,piece['mesh'],parent)
  if not source:raise ValueError('Malha da prévia ausente: '+piece['mesh'])
  block=variable_patch(piece['block'],m.get('variables',{}))
  if m['mode']=='replace':block=pivot_patch(block,m.get('pivot'))
  part={'id':piece['id'],'name':piece['mesh'],'file':piece['mesh'],'preview_source':str(source),'parent':'','pivot':None,'animations':[],'skin_bindings':{},'preview_notices':[]}
  for c in commands(block):
   if c['tag']=='[mesh_ident]':identities[arg(c)]=part['id']
   elif c['tag']=='[animparent]':part['parent']=arg(c)
   elif c['tag']=='[newanim]':
    lines=c['args'];i=0;steps=[]
    while i<len(lines):
     command=lines[i].strip()
     if command=='origin_from_mesh':steps.append((command,None))
     elif command=='origin_trans':steps.append((command,[float(x) for x in lines[i+1:i+4]]));i+=3
     elif command in {'origin_rot_x','origin_rot_y','origin_rot_z'}:steps.append((command,float(lines[i+1])));i+=1
     elif command in {'anim_rot','anim_trans'}:
      part['animations'].append({'type':command[5:],'variable':lines[i+1].strip(),'factor':float(lines[i+2]),'origin_steps':copy.deepcopy(steps)});i+=2
     elif command in {'offset','delay','maxspeed'}:part['preview_notices'].append(command+' não é simulado nesta prévia')
     i+=1
  values=bindings(template,plan,piece,targets)
  part['skin_bindings']={bone:target for bone,target in values.items() if isinstance(target,str)};parts.append(part)
 for p in parts:
  if p['parent']:
   if p['parent'] not in identities:raise ValueError('Parent não encontrado na prévia: '+p['parent'])
   p['parent']=identities[p['parent']]
 return {'version':2,'parts':parts,'lights':[]}
