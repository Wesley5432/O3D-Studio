"""Preserve a reference vehicle's CFG blocks with explicit per-piece mapping.
No scripts are executed and no source vehicle is modified. GPL-3.0-or-later.
"""
from output_files import publish
import copy,hashlib,json,re,shutil,tempfile,uuid
from pathlib import Path
from asset_paths import mesh_path
from o3d_binary import read as read_o3d, slots, patch_textures
from project import load_profile, number, variable_ok

TAG=re.compile(r'(?m)^[ \t]*(\[[^\]\r\n]+\])[ \t]*$')
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def txt(p):return Path(p).read_bytes().decode('cp1252').replace('\r\n','\n')
def commands(text):
 hits=list(TAG.finditer(text))
 return [{'tag':h.group(1),'start':h.start(),'end':hits[i+1].start() if i+1<len(hits) else len(text),'args':text[h.end():hits[i+1].start() if i+1<len(hits) else len(text)].lstrip('\n').splitlines()} for i,h in enumerate(hits)]
def arg(c,i=0):return c['args'][i].strip() if i<len(c['args']) else ''
def index(root):
 result={}
 for p in Path(root).rglob('*'):
  if p.is_symlink():raise ValueError('Pasta de veículo contém link simbólico')
  if p.is_file():
   k=p.relative_to(root).as_posix().casefold()
   if k in result:raise ValueError('Nomes conflitantes no Windows: '+k)
   result[k]=p
 return result

def resolve(root,files,ref,parent=''):
 parts=[]
 for s in (parent+'/'+ref.replace('\\','/')).split('/'):
  if s in {'','.'}:continue
  if s=='..':
   if not parts:return None
   parts.pop()
  else:
   if ':' in s:return None
   parts.append(s)
 return files.get('/'.join(parts).casefold())
def key(texture,occurrence):return texture+'|'+str(occurrence)
def load_template(bus,cfg_override=None):
 bus=Path(bus).resolve();root=bus.parent;files=index(root);bus_text=txt(bus);cs=commands(bus_text)
 model=next((arg(c) for c in cs if c['tag']=='[model]'),None)
 if not model:raise ValueError('.bus sem [model]')
 cfg=resolve(root,files,model)
 if not cfg:raise ValueError('CFG visual ausente: '+model)
 source_cfg=Path(cfg_override).resolve() if cfg_override else cfg
 text=txt(source_cfg);starts=[c['start'] for c in commands(text) if c['tag']=='[mesh]']
 pieces=[]
 for i,start in enumerate(starts):
  block=text[start:starts[i+1] if i+1<len(starts) else len(text)];bc=commands(block);mesh=arg(bc[0]);p=resolve(root,files,mesh,cfg.parent.relative_to(root).as_posix());meta=read_o3d(p) if p else None
  selectors={};variables=set()
  for c in bc:
   if c['tag'] in {'[matl]','[matl_change]'}:selectors[key(arg(c),int(arg(c,1)))]=(arg(c),int(arg(c,1)))
   if c['tag']=='[newanim]':
    lines=c['args']
    for n,v in enumerate(lines[:-1]):
     if v.strip() in {'anim_rot','anim_trans'}:variables.add(lines[n+1].strip())
  pieces.append({'id':'mesh_%04d'%i,'mesh':mesh,'block':block,'exists':bool(p),'slots':slots(meta) if meta else [],'selectors':selectors,'variables':sorted(variables),'has_origin':bool(meta and meta['matrix'])})
 header=text[:starts[0]] if starts else text
 fonts=sorted({arg(c,1) for c in commands(text) if c['tag'] in {'[texttexture]','[texttexture_enh]'}})
 skins=[{'variable':arg(c),'texture':arg(c,1)} for c in commands(header) if c['tag']=='[CTCTexture]']
 return {'bus':str(bus),'root':str(root),'bus_hash':digest(bus),'cfg':str(cfg),'source_cfg':str(source_cfg),'cfg_hash':digest(source_cfg),'header':header,'pieces':pieces,'fonts':fonts,'skins':skins,'profile':load_profile(bus)}

def new_plan(template,converted):
 return {'version':3,'reference_bus':template['bus'],'reference_cfg':template.get('source_cfg',template['cfg']),'bus_hash':template['bus_hash'],'cfg_hash':template['cfg_hash'],'converted':str(Path(converted).resolve()) if converted else '',
         'name':'Meu_veiculo','engine':'OMSI 2','mapping':{},'font_map':{},'fonts_folder':'','skin_folder':'','skin_targets':{},'base_textures':{}}

def target_parts(folder):
 folder=Path(folder);p=json.loads((folder/'project.json').read_text(encoding='utf8'));result={}
 for part in p['parts']:
  f=part['file']
  mesh_path(f)
  path=folder/'model'/f
  result[f]={**part,'slots_actual':slots(read_o3d(path))}
 return result

def set_arg(block,tag,n,value):
 if any(x in value for x in '\r\n'):raise ValueError('Valor deve ocupar uma linha')
 cs=[c for c in commands(block) if c['tag']==tag]
 for c in reversed(cs):
  sub=block[c['start']:c['end']];lines=sub.splitlines(True)
  # These OMSI commands use direct positional arguments, without intervening blank lines.
  if len(lines)<=n+1:raise ValueError('Comando incompleto: '+tag)
  line=lines[n+1];body=line.rstrip('\r\n');ending=line[len(body):]
  leading=body[:len(body)-len(body.lstrip(' \t'))];trailing=body[len(body.rstrip(' \t')):]
  if not body.strip():raise ValueError('Parâmetro vazio em '+tag)
  lines[n+1]=leading+value+trailing+ending;block=block[:c['start']]+''.join(lines)+block[c['end']:]
 return block

def variable_patch(block,mapping):
 for c in reversed([c for c in commands(block) if c['tag']=='[newanim]']):
  sub=block[c['start']:c['end']]
  sub=re.sub(r'(?m)^([ \t]*(?:anim_rot|anim_trans)[ \t]*\n)([ \t]*)([^\s]+)([ \t]*)$',lambda m:m.group(1)+m.group(2)+mapping.get(m.group(3),m.group(3))+m.group(4),sub)
  block=block[:c['start']]+sub+block[c['end']:]
 return block

def pivot_patch(block,pivot):
 if pivot is None:return block
 if len(pivot)!=3:raise ValueError('Pivô exige XYZ')
 replacement='origin_trans\n'+'\n'.join(number(x) for x in pivot)
 for c in reversed([c for c in commands(block) if c['tag']=='[newanim]']):
  sub=block[c['start']:c['end']]
  if '\norigin_from_mesh' in sub:sub=sub.replace('origin_from_mesh',replacement,1)
  elif re.search(r'(?m)^origin_trans$',sub):sub=re.sub(r'(?m)^origin_trans\n[^\n]+\n[^\n]+\n[^\n]+',replacement,sub,count=1)
  else:sub=sub.replace('[newanim]','[newanim]\n'+replacement,1)
  block=block[:c['start']]+sub+block[c['end']:]
 return block

def scan_plan(template,plan):
 errors=[];warnings=[];targets={};counts={'replace':0,'keep':0,'remove':0,'pending':0}
 if plan.get('version')!=3:errors.append('Versão de projeto inválida')
 if plan.get('bus_hash')!=template['bus_hash'] or plan.get('cfg_hash')!=template['cfg_hash']:errors.append('A referência mudou; recarregue a variante e revise as associações')
 if template['profile']['missing']:errors.append('Base com scripts/variáveis/constantes ausentes: '+', '.join(template['profile']['missing'][:5]))
 if any(not p['exists'] for p in template['pieces']):errors.append('A referência contém malhas ausentes')
 if any(m.get('mode')=='replace' for m in plan['mapping'].values()):
  try:targets=target_parts(plan['converted'])
  except Exception as e:errors.append('Modelo convertido: '+str(e))
 texture_files=index(Path(plan['converted'])/'texture') if targets else {}
 used={};surviving=[];material_destinations={}
 for piece in template['pieces']:
  m=plan['mapping'].get(piece['id'],{});mode=m.get('mode','pending')
  if mode not in counts:errors.append('Ação inválida: '+piece['id']);continue
  counts[mode]+=1
  if mode=='pending':continue
  if mode=='remove':
   if any(c['tag'] in {'[light_enh_2]','[interiorlight]','[spotlight]','[smoke]','[LOD]','[texttexture]','[texttexture_enh]','[CTC]','[CTCTexture]'} for c in commands(piece['block'])):errors.append('Bloco contém efeitos/luzes; mantenha-o até reconfigurar: '+piece['mesh'])
   continue
  surviving.append(piece)
  for old,new in m.get('variables',{}).items():
   if old not in piece['variables'] or not variable_ok(new,template['profile']):errors.append('Variável de animação inválida: '+old+' -> '+new)
  if mode=='replace':
   if any(c['tag'] in {'[setbone]','[smoothskin]'} for c in commands(piece['block'])):errors.append('Peça com esqueleto exige adaptação de bones fora desta versão: '+piece['mesh'])
   target=targets.get(m.get('target'))
   if not target:errors.append('Peça de destino ausente: '+piece['mesh']);continue
   if m['target'] in used and used[m['target']]!=piece['mesh']:errors.append('Mesma malha usada em funções distintas: '+m['target'])
   used[m['target']]=piece['mesh'];maps=m.get('materials',{});destslots=set()
   for k,(texture,occurrence) in piece['selectors'].items():
    slot=maps.get(k)
    if not isinstance(slot,int) or not 0<=slot<len(target['slots_actual']):errors.append('Associe o material '+k+' em '+piece['mesh']);continue
    if slot in destslots:errors.append('Dois materiais funcionais apontam para um mesmo slot: '+piece['mesh'])
    destslots.add(slot);dest=target['slots_actual'][slot]['texture']
    if not dest:errors.append('Material de destino sem textura: '+piece['mesh'])
    material_destinations.setdefault(texture,set()).add(dest)
   for s in target['slots_actual']:
    texture=s['texture']
    if texture and not resolve(Path(plan['converted']),texture_files,texture):
     # Check using a Texture-root index; source names may have subdirectories.
     errors.append('Textura de destino ausente: '+texture)
   if not m.get('confirmed'):errors.append('Confirme pivô/eixos da peça '+piece['mesh'])
   try:pivot_patch(piece['block'],m.get('pivot'))
   except Exception as e:errors.append(str(e))
 if not surviving and not counts['pending']:errors.append('O veículo precisa manter ao menos uma peça')
 if counts['pending']:errors.append(str(counts['pending'])+' peças ainda sem decisão')
 ids={arg(c) for p in surviving for c in commands(p['block']) if c['tag']=='[mesh_ident]'}
 for p in surviving:
  for c in commands(p['block']):
   if c['tag']=='[animparent]' and arg(c) not in ids:errors.append('Parent removido/ausente: '+arg(c))
 identities={};edges={}
 for p in surviving:
  cs=commands(p['block']);parents=[arg(c) for c in cs if c['tag']=='[animparent]']
  for c in cs:
   if c['tag']=='[mesh_ident]':
    name=arg(c)
    if name in identities:errors.append('mesh_ident duplicado: '+name)
    identities[name]=p['id'];edges[name]=parents
 done=set();active=set()
 def visit(name):
  if name in active:errors.append('Ciclo de animparent: '+name);return
  if name in done:return
  active.add(name)
  for parent in edges.get(name,[]):visit(parent)
  active.remove(name);done.add(name)
 for name in edges:visit(name)
 needed={s['texture'] for f in used if f in targets for s in targets[f]['slots_actual'] if s['texture']}
 for variable,texture in plan.get('skin_targets',{}).items():
  if variable not in {s['variable'] for s in template['skins']} or (texture not in needed and not any(s['variable']==variable and s['texture']==texture for s in template['skins'])):errors.append('Canal de skin sem textura válida: '+variable)
 for texture,source in plan.get('base_textures',{}).items():
  if texture not in needed or not Path(source).is_file():errors.append('Substituição de textura base inválida: '+texture)
  elif Path(source).suffix.casefold()!=Path(texture).suffix.casefold():errors.append('Formato diferente na textura base: '+texture)
 if plan.get('skin_folder'):
  folder=Path(plan['skin_folder'])
  if not folder.is_dir() or not any(p.suffix.casefold()=='.cti' for p in folder.rglob('*')):errors.append('Pasta de skins inexistente ou sem .cti')
  if not any(c['tag']=='[CTC]' for c in commands(template['header'])):errors.append('Referência sem bloco CTC para receber skins')
 if plan.get('skin_file'):
  skin=Path(plan['skin_file'])
  if not skin.is_file() or skin.suffix.lower()!='.cti':errors.append('Selecione um arquivo .cti válido')
  else:
   if not plan.get('skin_folder') or skin.parent.resolve()!=Path(plan['skin_folder']).resolve():errors.append('A skin selecionada deve estar na pasta de skins indicada')
   skinfiles=index(skin.parent);items=[c for c in commands(txt(skin)) if c['tag'].lower()=='[item]']
   if not items:errors.append('Skin sem blocos [item]')
   for c in items:
    if arg(c,1) not in {s['variable'] for s in template['skins']}:errors.append('Canal do repaint não existe na base: '+arg(c,1))
    if not resolve(skin.parent,skinfiles,arg(c,2)):errors.append('Imagem do repaint ausente: '+arg(c,2))
 for old,new in plan.get('font_map',{}).items():
  if old not in template['fonts'] or not new or any(c in new for c in '\r\n/\\[]:'):errors.append('Fonte inválida: '+str(new))
 if plan.get('fonts_folder'):
  try:
   if not Path(plan['fonts_folder']).is_dir():raise ValueError('Pasta inexistente')
   fontfiles=index(Path(plan['fonts_folder']))
   for font in template['fonts']:
    name=plan.get('font_map',{}).get(font,font)
    if (name+'.oft').casefold() not in fontfiles:
     (errors if font in plan.get('font_map',{}) else warnings).append('Fonte .oft não localizada na pasta fornecida: '+name)
  except Exception as e:errors.append('Pasta de fontes: '+str(e))
 else:warnings.append('Fontes globais não verificadas; precisam existir na instalação do jogo')
 if counts['keep']:warnings.append(str(counts['keep'])+' blocos mantêm peças originais da referência; isto não é uma conversão integral')
 warnings.extend(['Física, câmeras, luzes e caminhos herdados precisam de ajuste ao novo veículo.','OMSI 2 e openOMSI: pacote não executado nos motores; validar no jogo e conferir logfile.'])
 return {'errors':list(dict.fromkeys(errors)),'warnings':list(dict.fromkeys(warnings)),'counts':counts,'targets':targets,'material_destinations':{k:sorted(v) for k,v in material_destinations.items()}}

def texture_names(targets):
 return {s['texture']:'CV_'+hashlib.sha256(s['texture'].casefold().encode()).hexdigest()[:12]+Path(s['texture'].replace('\\','/')).suffix.lower() for t in targets.values() for s in t['slots_actual'] if s['texture']}

def preview_piece(piece,m,targets):
 if m.get('mode')=='remove':return ''
 if m.get('mode') not in {'keep','replace'}:raise ValueError('Escolha manter ou substituir a peça')
 names=texture_names(targets)
 block=piece['block']
 if m['mode']=='replace':
  target=targets[m['target']]
  block=set_arg(block,'[mesh]',0,'Convertidos\\'+m['target'].replace('/','\\'))
  for c in reversed(commands(block)):
   if c['tag'] not in {'[matl]','[matl_change]'}:continue
   slot=target['slots_actual'][m['materials'][key(arg(c),int(arg(c,1)))]]
   sub=set_arg(block[c['start']:c['end']],c['tag'],0,names[slot['texture']]);sub=set_arg(sub,c['tag'],1,str(slot['occurrence']))
   block=block[:c['start']]+sub+block[c['end']:]
  block=pivot_patch(block,m.get('pivot'))
 block=variable_patch(block,m.get('variables',{}))
 return block

def render_cfg(template,plan,check=None):
 check=check or scan_plan(template,plan)
 if check['errors']:raise ValueError('\n'.join(check['errors']))
 names=texture_names(check['targets'])
 header=template['header'];blocks=[]
 for c in reversed(commands(header)):
  sub=header[c['start']:c['end']]
  if c['tag']=='[CTCTexture]':
   selected=plan.get('skin_targets',{}).get(arg(c))
   options=check['material_destinations'].get(arg(c,1),[])
   if selected:
    if selected in names:sub=set_arg(sub,c['tag'],1,names[selected])
    elif selected!=arg(c,1):raise ValueError('Textura de skin desconhecida: '+selected)
   elif options:raise ValueError('Escolha a textura da skin: '+arg(c))
  elif c['tag']=='[CTC]' and plan.get('skin_folder'):sub=set_arg(sub,c['tag'],1,'Texture\\Pinturas_Convertidas')
  header=header[:c['start']]+sub+header[c['end']:]
 for piece in template['pieces']:
  m=plan['mapping'][piece['id']]
  if m['mode']=='remove':continue
  block=preview_piece(piece,m,check['targets'])
  blocks.append(block)
 result=header+''.join(blocks)
 for c in reversed(commands(result)):
  if c['tag'] in {'[texttexture]','[texttexture_enh]'}:
   sub=set_arg(result[c['start']:c['end']],c['tag'],1,plan.get('font_map',{}).get(arg(c,1),arg(c,1)))
   result=result[:c['start']]+sub+result[c['end']:]
 return result,names

def build(template,plan,destination):
 # Reload reference to detect edits made since the project was opened.
 template=load_template(template['bus'],plan.get('reference_cfg'));check=scan_plan(template,plan);cfg,names=render_cfg(template,plan,check)
 name=plan.get('name','')
 if not re.fullmatch(r'[A-Za-z0-9_-]{1,64}',name):raise ValueError('Nome da pasta: use 1–64 letras sem acentos, números, _ ou -')
 dest=Path(destination).resolve();source=Path(template['root']).resolve()
 if dest==source or dest.is_relative_to(source):raise ValueError('Saída deve ficar fora da pasta de referência')
 dest.mkdir(parents=True,exist_ok=True);final=dest;stage=Path(tempfile.mkdtemp(prefix='.montagem_',dir=dest))
 try:
  vehicle=stage/'Vehicles'/name;shutil.copytree(source,vehicle)
  for bus in vehicle.glob('*.bus'):
   if bus.name!=Path(template['bus']).name:bus.unlink()
  cfgpath=vehicle/Path(template['cfg']).relative_to(source);cfgpath.write_bytes(cfg.replace('\n','\r\n').encode('cp1252'))
  buspath=vehicle/Path(template['bus']).name
  buspath.write_bytes(set_arg(txt(buspath),'[friendlyname]',1,name).replace('\n','\r\n').encode('cp1252'))
  texture_root=next((p for p in vehicle.iterdir() if p.name.casefold()=='texture'),vehicle/'Texture');texture_root.mkdir(exist_ok=True)
  texture_files=index(Path(plan['converted'])/'texture') if check['counts']['replace'] else {}
  used={m['target'] for m in plan['mapping'].values() if m['mode']=='replace'}
  meshes=cfgpath.parent/'Convertidos';meshes.mkdir(exist_ok=True)
  for f in used:
   raw=(Path(plan['converted'])/'model'/f).read_bytes();(meshes/f).parent.mkdir(parents=True,exist_ok=True);(meshes/f).write_bytes(patch_textures(raw,names))
  needed={s['texture'] for f in used for s in check['targets'][f]['slots_actual'] if s['texture']}
  for original in needed:
   target=texture_root/names[original]
   if target.exists():raise ValueError('Colisão com textura da referência: '+target.name)
   override=plan.get('base_textures',{}).get(original)
   src=Path(override) if override else resolve(None,texture_files,original)
   if not src or not src.is_file():raise ValueError('Textura não encontrada: '+original)
   if override and src.suffix.casefold()!=target.suffix.casefold():raise ValueError('A textura substituta precisa ter o mesmo formato: '+original)
   shutil.copy2(src,target)
  if plan.get('skin_folder'):
   src=Path(plan['skin_folder']);files=index(src)
   if not any(p.suffix.casefold()=='.cti' for p in files.values()):raise ValueError('Pasta de skins sem .cti')
   destination=texture_root/'Pinturas_Convertidas'
   if destination.exists():shutil.rmtree(destination)
   selected=Path(plan['skin_file']).resolve() if plan.get('skin_file') else None
   for file in files.values():
    if selected and file.suffix.lower()=='.cti' and file.resolve()!=selected:continue
    target=destination/file.relative_to(src);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(file,target)
  if plan.get('fonts_folder'):
   src=Path(plan['fonts_folder']);index(src);shutil.copytree(src,stage/'Fonts')
  (stage/'montagem.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2),encoding='utf8')
  (stage/'LEIA_ANTES_DE_INSTALAR.txt').write_text('Pacote de montagem. Faça backup antes de instalar.\nMotor selecionado: '+plan['engine']+'\n\n'+'\n'.join(check['warnings'])+'\n\nCopie Vehicles e, se fornecida, Fonts para a instalação de teste. Recursos externos de som podem continuar dependendo do veículo original. Confira o logfile do jogo.\n',encoding='utf8')
  publish(stage,final);shutil.rmtree(stage);return final
 except Exception:
  shutil.rmtree(stage,ignore_errors=True);raise

def suggest_mappings(template,targets,mapping):
 """Suggest only unique normalized names; every replacement still needs review."""
 from asset_paths import clean_name
 def normalized(value):
  name=Path(value.replace('\\','/')).stem
  name=re.sub(r'^\d{4}_','',name)
  return re.sub(r'[^a-z0-9]','',clean_name(name).lower())
 result=copy.deepcopy(mapping);count=0
 for piece in template['pieces']:
  if result.get(piece['id'],{}).get('mode','pending')!='pending':continue
  keyname=normalized(piece['mesh'])
  candidates=[(f,t) for f,t in targets.items() if keyname in {normalized(f),normalized(t.get('name',f))}]
  if len(candidates)!=1:continue
  f,target=candidates[0];materials={}
  for selector,(texture,occurrence) in piece['selectors'].items():
   slots=[s['slot'] for s in target['slots_actual'] if s['texture'].casefold()==texture.casefold() and s['occurrence']==occurrence]
   if len(slots)==1:materials[selector]=slots[0]
  result[piece['id']]={'mode':'replace','target':f,'materials':materials,'variables':{},'pivot':None,'confirmed':False};count+=1
 return result,count
