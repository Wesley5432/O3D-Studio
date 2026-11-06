"""Bind O3D vertex groups to CFG controller meshes and recompute mesh indices."""
from vehicle_template import commands,arg,set_arg

def bindings(template,plan,piece,targets):
 mapping=plan['mapping'].get(piece['id'],{});result={};first=[p for p in template['pieces'] if p.get('lod',0)==0]
 for c in commands(piece['block']):
  if c['tag']=='[setbone]':
   index=int(arg(c,1))
   if index<0:result[arg(c)]=index
   elif index>=len(first):raise ValueError('Índice [setbone] fora da lista: '+piece['mesh'])
   else:result[arg(c)]=first[index]['id']
 if mapping.get('mode')=='replace':
  target=targets.get(mapping.get('target'),{});bones=target.get('bones_actual',[])
  if result and not bones:raise ValueError('A peça substituta precisa de pesos: '+piece['mesh'])
  result={name:result.get(name,'') for name in bones}
  for bone in bones:
   controller=target.get('skin_bindings',{}).get(bone)
   file=next((f for f,p in targets.items() if p.get('id')==controller),None)
   matches=[id for id,m in plan['mapping'].items() if file and m.get('mode')=='replace' and m.get('target')==file]
   if len(matches)==1:result[bone]=matches[0]
  if set(mapping.get('bones',{}))-set(bones):raise ValueError('Grupo de deformação não existe no O3D de destino')
  result.update(mapping.get('bones',{}))
 for bone,target in result.items():
  if isinstance(target,int) and target<0:continue
  if target not in {p['id'] for p in first} or target==piece['id'] or plan['mapping'].get(target,{}).get('mode')=='remove':raise ValueError('Associe um controlador válido para '+piece['mesh']+' / '+bone)
 return result

def validate_bindings(template,plan,targets):
 edges={};ids={arg(c):p['id'] for p in template['pieces'] for c in commands(p['block']) if c['tag']=='[mesh_ident]'}
 for p in template['pieces']:
  if plan['mapping'].get(p['id'],{}).get('mode') not in {'keep','replace'}:continue
  b=bindings(template,plan,p,targets);edges[p['id']]=[v for v in b.values() if isinstance(v,str)]
  edges[p['id']].extend(ids.get(arg(c),'') for c in commands(p['block']) if c['tag']=='[animparent]')
 done=set();active=set()
 def visit(id):
  if id in active:raise ValueError('Ciclo entre controladores de deformação e hierarquia')
  if id in done:return
  active.add(id)
  for target in edges.get(id,[]):visit(target)
  active.remove(id);done.add(id)
 for id in edges:visit(id)

def patch_skin(block,template,plan,piece,targets):
 values=bindings(template,plan,piece,targets)
 if not values:return block
 first=[p for p in template['pieces'] if p.get('lod',0)==0 and plan['mapping'].get(p['id'],{}).get('mode')!='remove'];indices={p['id']:i for i,p in enumerate(first)}
 if plan['mapping'][piece['id']]['mode']=='keep':
  for c in reversed(commands(block)):
   if c['tag']=='[setbone]':
    target=values[arg(c)];index=target if isinstance(target,int) else indices[target]
    block=block[:c['start']]+set_arg(block[c['start']:c['end']],c['tag'],1,str(index))+block[c['end']:]
  return block
 for c in reversed(commands(block)):
  if c['tag'] in {'[setbone]','[smoothskin]'}:
   lines=block[c['start']:c['end']].splitlines(keepends=True);count=3 if c['tag']=='[setbone]' else 1
   block=block[:c['start']]+''.join(lines[count:])+block[c['end']:]
 lines=block.splitlines(keepends=True);insert='\n[smoothskin]\n\n'
 for bone,target in values.items():insert+='[setbone]\n'+bone+'\n'+str(target if isinstance(target,int) else indices[target])+'\n\n'
 return ''.join(lines[:2])+insert+''.join(lines[2:])
