"""Explain references from their CFG/script context, without guessing script semantics."""
import re
from pathlib import Path
from cfg_reader import active_commands
from vehicle_template import arg,txt,index,resolve

IDENT=re.compile(r'[A-Za-z_][A-Za-z_0-9]*\Z')

def cfg_usages(text,source='CFG',section=''):
 result=[];mesh='(global)';material='';lod=''
 def add(name,kind,role,description,c,offset=1):
  if not IDENT.fullmatch(name):return
  result.append({'name':name,'kind':kind,'role':role,'description':description,'source':str(source),'line':c['line']+offset,'section':section,'mesh':mesh,'material':material,'lod':lod,'command':c['tag'],'excerpt':text[c['start']:c['end']].strip()})
 for c in active_commands(text):
  tag=c['tag']
  if tag=='[LOD]':lod=arg(c);mesh='(global)';material=''
  elif tag=='[mesh]':mesh=arg(c);material=''
  elif tag in {'[matl]','[matl_change]'}:
   material=arg(c)+' #'+arg(c,1)
   if tag=='[matl_change]':add(arg(c,2),'numeric','Material','Seleciona a variante [matl_item] do material '+material+'.',c,3)
  elif tag=='[visible]':add(arg(c),'numeric','Visibilidade','Exibe esta peça quando a variável corresponde ao valor '+arg(c,1)+'.',c)
  elif tag=='[mouseevent]':add(arg(c),'events','Evento do mouse','Evento da peça clicada; o script define a ação. Variantes _drag e _off tratam arrasto e soltura.',c)
  elif tag=='[newanim]':
   for i,line in enumerate(c['args']):
    command=line.strip()
    if command in {'anim_rot','anim_trans'} and i+2<len(c['args']):
     name=c['args'][i+1].strip();factor=c['args'][i+2].strip();role='Rotação' if command=='anim_rot' else 'Translação'
     origins=[]
     for n,item in enumerate(c['args']):
      if item.strip()=='origin_from_mesh':origins.append('pivô do O3D')
      elif item.strip() in {'origin_rot_x','origin_rot_y','origin_rot_z'} and n+1<len(c['args']):origins.append(item.strip()+' = '+c['args'][n+1].strip())
      elif item.strip()=='origin_trans' and n+3<len(c['args']):origins.append('pivô XYZ = '+' '.join(x.strip() for x in c['args'][n+1:n+4]))
     add(name,'numeric',role,role+' da peça por '+command+'; fator '+factor+'. '+('; '.join(origins) or 'Veja a origem no bloco CFG')+'.',c,i+2)
  elif tag in {'[texttexture]','[texttexture_enh]'}:add(arg(c),'strings','Texto / letreiro','Conteúdo da textura de texto; fonte '+arg(c,1)+'. O texto vem do script.',c)
  elif tag=='[matl_freetex]':add(arg(c,1),'strings','Arquivo de textura','O script fornece o nome do arquivo que substitui a textura '+arg(c)+'.',c,2)
  elif tag in {'[texcoordtransX]','[texcoordtransY]'}:add(arg(c),'numeric','UV','Desloca as coordenadas UV do material em '+tag[-2]+'.',c)
  elif tag=='[interiorlight]':add(arg(c),'numeric','Luz interna','Controla a luz interna em XYZ '+', '.join(arg(c,n) for n in (5,6,7))+'.',c)
  elif tag in {'[light_enh]','[light_enh_2]','[spotlight_2]'}:
   n={'[light_enh]':7,'[light_enh_2]':17,'[spotlight_2]':12}[tag]
   add(arg(c,n),'numeric','Luz','Controla esta luz em XYZ '+', '.join(arg(c,k) for k in range(3))+'.',c,n+1)
  elif tag=='[newtexchangemaster]':add(arg(c,1),'numeric','Troca de textura','Seleciona uma entrada de textura para '+arg(c)+' pelo índice.',c,2)
 return result

def script_usages(text,source):
 result=[];block=''
 for line_number,line in enumerate(text.splitlines(),1):
  code=line.split("'",1)[0]
  for match in re.finditer(r'\{(trigger|macro):([A-Za-z_][A-Za-z_0-9]*)\}',code):
   block=match.group(1)+':'+match.group(2)
   if match.group(1)=='trigger':result.append({'name':match.group(2),'kind':'events','role':'Evento no script','description':'Evento definido no script; consulte o bloco para conhecer sua ação.','source':str(source),'line':line_number,'section':'','mesh':'(script)','material':'','lod':'','command':'{trigger}','excerpt':line})
  for match in re.finditer(r'\((L|S)\.(L|\$)\.([A-Za-z_][A-Za-z_0-9]*)\)',code):
   action='Leitura' if match.group(1)=='L' else 'Escrita'
   result.append({'name':match.group(3),'kind':'strings' if match.group(2)=='$' else 'numeric','role':action+' no script','description':action+' da variável em '+(block or 'bloco não identificado')+'. A finalidade depende da lógica desse bloco.','source':str(source),'line':line_number,'section':'','mesh':'(script)','material':'','lod':'','command':match.group(0),'excerpt':line})
 return result

def build_catalog(cfg_sources=(),profile=None,manual=(),script_sources=()):
 entries={};profile=profile or {}
 def entry(kind,name):
  return entries.setdefault((kind,name),{'kind':kind,'name':name,'origins':[],'usages':[]})
 for key,kind in [('variables','numeric'),('string_variables','strings'),('triggers','events')]:
  for name in profile.get(key,[]):entry(kind,name)['origins'].append('Referência no script' if profile.get('references_only') else 'Perfil do veículo')
 for name in manual:entry('numeric',name)['origins'].append('Manual: declarar e controlar no script')
 for source,text,section in cfg_sources:
  for use in cfg_usages(text,source,section):entry(use['kind'],use['name'])['usages'].append(use)
 for source,text in script_sources:
  for use in script_usages(text,source):entry(use['kind'],use['name'])['usages'].append(use)
 for (kind,name),row in list(entries.items()):
  if kind=='events':
   for suffix in ('_drag','_off'):
    family=entries.get((kind,name+suffix))
    if family:row['usages'].extend(family['usages'])
  row['roles']=sorted({u['role'] for u in row['usages']})
  row['summary']='; '.join(row['roles']) or 'Sem uso localizado no CFG/scripts consultados; finalidade não deduzida pelo nome.'
 return sorted(entries.values(),key=lambda e:(e['name'].casefold(),e['kind']))

def bus_sources(bus):
 from articulated import load_chain
 chain=load_chain(bus);cfgs=[];scripts=[];seen=set();warnings=[]
 for section in chain['sections']:
  cfg=Path(section['cfg']);cfgs.append((str(cfg),txt(cfg),Path(section['bus']).name))
  for c in active_commands(txt(cfg)):
   if c['tag']=='[texchanges]':
    p=resolve(None,index(Path(chain['root'])),arg(c))
    if p:cfgs.append((str(p),txt(p),Path(section['bus']).name))
    else:warnings.append('Arquivo de troca de textura ausente: '+arg(c))
  owner=Path(section['profile_bus']);files=index(owner.parent)
  for c in active_commands(txt(owner)):
   if c['tag']=='[script]':
    count=int(arg(c))
    for name in c['args'][1:count+1]:
     p=resolve(None,files,name.strip())
     if not p:warnings.append('Script ausente: '+name)
     elif p not in seen:scripts.append((str(p),txt(p)));seen.add(p)
 return cfgs,scripts,warnings
