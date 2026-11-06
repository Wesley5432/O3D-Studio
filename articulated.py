"""Assembly of existing articulated donors; preserve physics, scripts and bellows."""
import copy,json,math,re,shutil,tempfile
from pathlib import Path
from cfg_reader import active_commands
from vehicle_template import arg,txt,index,resolve,set_arg,digest
from project import number
from output_files import publish

def load_chain(head_bus):
 head=Path(head_bus).resolve();root=head.parent;files=index(root);sections=[];seen=set();current=head;owner=None
 while current:
  key=current.relative_to(root).as_posix()
  if current.parent!=root:raise ValueError('Nesta montagem, os .bus das seções devem ficar na mesma pasta da dianteira')
  if key.casefold() in seen:raise ValueError('Ciclo de acoplamento: '+key)
  seen.add(key.casefold());text=txt(current);cs=active_commands(text)
  def one(tag):
   found=[c for c in cs if c['tag']==tag]
   if len(found)>1:raise ValueError(key+': comando duplicado '+tag)
   return found[0] if found else None
  model=one('[model]');cfg=resolve(None,files,arg(model) if model else '',current.parent.relative_to(root).as_posix())
  if not cfg:raise ValueError(key+': CFG de [model] não encontrado')
  shared=one('[scriptshare]') is not None
  if not shared:owner=current
  if shared and owner is None:raise ValueError('Selecione o .bus da dianteira para ler os scripts compartilhados')
  points={}
  for side in ('front','back'):
   c=one('[coupling_'+side+']')
   if c:
    try:xyz=[float(arg(c,n)) for n in range(3)]
    except ValueError:raise ValueError(key+': engate '+side+' exige XYZ numérico')
    if not all(math.isfinite(x) for x in xyz):raise ValueError(key+': engate contém número não finito')
    points[side]=xyz
  link=one('[couple_back]');front_link=one('[couple_front]')
  if front_link:raise ValueError(key+': montagem com [couple_front] não suportada; use uma base articulada encadeada por [couple_back]')
  next_bus=None
  if link:
   if arg(link,1).casefold() not in {'false','0'}:raise ValueError(key+': seção invertida não suportada nesta montagem; a base deve usar reversed=false')
   next_bus=resolve(None,files,arg(link),current.parent.relative_to(root).as_posix())
   if not next_bus or next_bus.suffix.casefold()!='.bus':raise ValueError(key+': .bus acoplado ausente: '+arg(link))
   if 'back' not in points:raise ValueError(key+': falta [coupling_back]')
  if sections and 'front' not in points:raise ValueError(key+': falta [coupling_front] no reboque')
  sections.append({'key':key,'bus':str(current),'cfg':str(cfg),'profile_bus':str(owner),'scriptshare':shared,'points':points,'next':str(next_bus) if next_bus else None,'bus_hash':digest(current),'cfg_hash':digest(cfg)})
  current=next_bus
 return {'head':str(head),'root':str(root),'sections':sections}

def new_articulated_plan(bus):
 chain=load_chain(bus)
 if len(chain['sections'])<2:raise ValueError('A base precisa ter dianteira e reboque ligados por [couple_back]')
 return {'type':'articulated','version':1,'head':chain['head'],'name':'Meu_articulado','engine':'OMSI 2','snapshots':{s['key']:[s['bus_hash'],s['cfg_hash']] for s in chain['sections']},'points':{},'section_plans':{}}

def check_articulated(plan):
 if plan.get('type')!='articulated' or plan.get('version')!=1:raise ValueError('Projeto de articulado inválido')
 chain=load_chain(plan['head']);keys={s['key'] for s in chain['sections']}
 if len(keys)<2:raise ValueError('A base não possui reboque')
 if set(plan.get('snapshots',{}))!=keys:raise ValueError('As seções da base mudaram; recarregue o articulado')
 if (set(plan.get('points',{}))|set(plan.get('section_plans',{})))-keys:raise ValueError('Configuração aponta para uma seção desconhecida')
 cfgs=set();prepared=[]
 from vehicle_template import load_template,scan_plan,render_cfg
 for i,s in enumerate(chain['sections']):
  if plan['snapshots'][s['key']]!=[s['bus_hash'],s['cfg_hash']]:raise ValueError('A base mudou: '+s['key']+'. Recarregue o articulado')
  points=plan.get('points',{}).get(s['key'],{})
  for side,xyz in points.items():
   if side not in s['points'] or not isinstance(xyz,list) or len(xyz)!=3:raise ValueError('Engate inválido em '+s['key'])
   for value in xyz:number(value)
  p=copy.deepcopy(plan.get('section_plans',{}).get(s['key']))
  if p:
   if Path(p['reference_bus']).resolve()!=Path(s['bus']):raise ValueError('Montagem pertence a outra seção: '+s['key'])
   p['profile_bus']=s['profile_bus'];p['namespace']='_S%02d'%i
   t=load_template(s['bus'],p.get('reference_cfg'),s['profile_bus']);check=scan_plan(t,p);cfg,names=render_cfg(t,p,check)
   # A shared CFG cannot describe distinct replacements for two sections.
   if sum(other['cfg']==s['cfg'] for other in chain['sections'])>1:raise ValueError('As seções usam o mesmo CFG; separe os CFGs da base antes de substituir peças')
   cfgs.add(s['cfg']);prepared.append((t,p,check,cfg,names))
 return chain,prepared

def export_articulated(plan,destination):
 chain,prepared=check_articulated(plan);dest=Path(destination).resolve();root=Path(chain['root']);name=plan.get('name','')
 if not re.fullmatch(r'[A-Za-z0-9_-]{1,64}',name):raise ValueError('Nome: use letras sem acentos, números, _ ou -')
 roots=[root]+[Path(p['converted']).resolve() for _,p,_,_,_ in prepared if p.get('converted')]
 if any(dest==r or dest.is_relative_to(r) for r in roots):raise ValueError('Escolha uma saída fora das pastas de origem')
 from vehicle_template import write_section
 with tempfile.TemporaryDirectory() as tmp:
  stage=Path(tmp);vehicle=stage/'Vehicles'/name;shutil.copytree(root,vehicle)
  for t,p,check,cfg,names in prepared:write_section(t,p,check,cfg,names,vehicle,stage)
  for s in chain['sections']:
   bus=vehicle/s['key'];text=txt(bus)
   for side,xyz in plan.get('points',{}).get(s['key'],{}).items():
    for n,value in enumerate(xyz):text=set_arg(text,'[coupling_'+side+']',n,number(value))
   if s['bus']==chain['head']:text=set_arg(text,'[friendlyname]',1,name)
   bus.write_bytes(text.replace('\n','\r\n').encode('cp1252'))
  load_chain(vehicle/Path(chain['head']).name)
  (stage/'articulado.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2),encoding='utf8')
  (stage/'LEIA_ARTICULADO.txt').write_text('Montagem de base articulada existente. Seções sem montagem conservam o modelo original.\nEngates usam coordenadas locais XYZ de cada seção. Física, amortecimento, eixos, câmeras e passagens de passageiros são herdados.\nA sanfona conserva os ossos e animações originais quando mantida. OBJ não transporta estes vínculos.\nConfira alinhamento, curvas, marcha à ré, portas e circulação de passageiros no OMSI 2/openOMSI. Não testado nos jogos pelo programa.\n',encoding='utf8')
  publish(stage,dest)
 return dest
