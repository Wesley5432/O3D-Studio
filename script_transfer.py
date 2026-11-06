"""Copy declared script dependencies and replace only BUS script lists."""
import json,re,shutil,tempfile,uuid
from pathlib import Path
from project import load_profile,variable_ok
from output_files import publish
from vehicle_template import index,resolve,txt,commands,arg
TAGS=('[script]','[varnamelist]','[stringvarnamelist]','[constfile]')

def script_bundle(bus):
 bus=Path(bus).resolve();profile=load_profile(bus)
 if profile['missing']:raise ValueError('Dependências ausentes: '+', '.join(profile['missing']))
 files=index(bus.parent);copies={};sections={}
 for tag in TAGS:
  refs=profile['selected'].get(tag,[]);sections[tag]=[]
  for ref in refs:
   path=resolve(bus.parent,files,ref)
   if not path:raise ValueError('Dependência externa/ausente: '+ref)
   relative=path.relative_to(bus.parent).as_posix();copies[relative]=path;sections[tag].append(relative)
 return profile,sections,copies

def replace_sections(text,sections,prefix):
 lines=text.splitlines(True);seen=set();i=0;out=[]
 while i<len(lines):
  tag=lines[i].strip()
  if tag not in TAGS:out.append(lines[i]);i+=1;continue
  if tag in seen:raise ValueError('Lista duplicada no .bus: '+tag)
  seen.add(tag)
  if i+1>=len(lines):raise ValueError('Lista truncada: '+tag)
  count=int(lines[i+1].strip())
  if count<0 or i+2+count>len(lines):raise ValueError('Lista truncada: '+tag)
  refs=sections.get(tag,[]);out.extend([tag+'\n',str(len(refs))+'\n',*[prefix+'\\'+r.replace('/','\\')+'\n' for r in refs]])
  i+=2+count
 for tag in TAGS:
  if tag not in seen and sections.get(tag):out.extend(['\n',tag+'\n',str(len(sections[tag]))+'\n',*[prefix+'\\'+r.replace('/','\\')+'\n' for r in sections[tag]]])
 return ''.join(out)

def compatibility(target_bus,donor_bus,mapping=None):
 profile,sections,copies=script_bundle(donor_bus);target=Path(target_bus).resolve();files=index(target.parent);model=next((arg(c) for c in commands(txt(target)) if c['tag']=='[model]'),None)
 if not model:raise ValueError('Veículo de destino sem [model]')
 cfg=resolve(target.parent,files,model)
 if not cfg:raise ValueError('CFG do veículo de destino não encontrado')
 numeric=set();strings=set();events=set()
 from cfg_adaptation import adapt_references
 adapted=adapt_references(txt(cfg),mapping)
 for c in commands(adapted):
  if c['tag']=='[visible]':numeric.add(arg(c))
  elif c['tag']=='[matl_change]':numeric.add(arg(c,2))
  elif c['tag']=='[interiorlight]':numeric.add(arg(c))
  elif c['tag']=='[light_enh_2]':numeric.add(arg(c,17))
  elif c['tag']=='[mouseevent]':events.add(arg(c))
  elif c['tag'] in {'[texttexture]','[texttexture_enh]'}:strings.add(arg(c))
  elif c['tag']=='[newanim]':
   for i,line in enumerate(c['args'][:-1]):
    if line.strip() in {'anim_rot','anim_trans'}:numeric.add(c['args'][i+1].strip())
 missing_numeric=sorted(v for v in numeric if not variable_ok(v,profile))
 missing_strings=sorted(strings-set(profile.get('string_variables',[])))
 missing_events=sorted(e for e in events if not any(x in profile['triggers'] for x in (e,e+'_drag',e+'_off')))
 return {'target':str(target),'donor':str(Path(donor_bus).resolve()),'missing_variables':missing_numeric,'missing_strings':missing_strings,'missing_events':missing_events,'mapping':mapping or {},'dependency_files':len(copies),'compatible_references':not(missing_numeric or missing_strings or missing_events),'note':'Verifica referências usuais do CFG. Não simula lógica, sons, física ou macros; validar no jogo.'}

def swap_scripts(target_bus,donor_bus,destination,mapping=None):
 check=compatibility(target_bus,donor_bus,mapping)
 if not check['compatible_references']:raise ValueError('Scripts incompatíveis com referências do CFG:\n'+json.dumps(check,ensure_ascii=False,indent=2))
 target=Path(target_bus).resolve();donor=Path(donor_bus).resolve();dest=Path(destination).resolve();index(target.parent)
 if any(dest==root or dest.is_relative_to(root) for root in (target.parent,donor.parent)):raise ValueError('Escolha uma saída fora dos dois veículos')
 profile,sections,copies=script_bundle(donor);dest.mkdir(parents=True,exist_ok=True);stage=Path(tempfile.mkdtemp(prefix='.scripts-',dir=dest));final=dest;prefix='Script_Importado_'+uuid.uuid4().hex[:8]
 try:
  shutil.copytree(target.parent,stage,dirs_exist_ok=True)
  if mapping:
   from cfg_adaptation import adapt_references
   files=index(stage);model=next(arg(c) for c in commands(txt(stage/target.name)) if c['tag']=='[model]');cfg=resolve(stage,files,model)
   cfg.write_bytes(adapt_references(txt(cfg),mapping).replace('\n','\r\n').encode('cp1252'))
  for relative,src in copies.items():
   out=stage/prefix/relative;out.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,out)
  (stage/target.name).write_bytes(replace_sections(txt(target),sections,prefix).replace('\n','\r\n').encode('cp1252'))
  (stage/'troca_scripts.json').write_text(json.dumps(check,ensure_ascii=False,indent=2),encoding='utf8');publish(stage,final);shutil.rmtree(stage);return final
 except Exception:shutil.rmtree(stage,ignore_errors=True);raise

def package_cfg_scripts(folder,project,donor_bus,destination):
 from project import export_cfg,save_project
 import copy
 folder=Path(folder).resolve();dest=Path(destination).resolve()
 if any(dest==r or dest.is_relative_to(r) for r in (folder,Path(donor_bus).resolve().parent)):raise ValueError('Saída deve ficar fora da pasta do modelo')
 profile,sections,copies=script_bundle(donor_bus);candidate=copy.deepcopy(project);candidate['profile']=profile
 dest.mkdir(parents=True,exist_ok=True);stage=Path(tempfile.mkdtemp(prefix='.cfg-scripts-',dir=dest));final=dest;prefix='Script_Importado'
 try:
  for part in candidate['parts']:
   from asset_paths import mesh_path
   mesh_path(part['file'])
  donor=Path(donor_bus).resolve();index(donor.parent)
  from articulated import load_chain
  chain=load_chain(donor)
  if len(chain['sections'])>1:raise ValueError('Use Ferramentas → Ônibus articulado para gerar CFGs separados da dianteira e do reboque')
  shutil.copytree(donor.parent,stage,dirs_exist_ok=True)
  # Canonicalize resource directories on case-sensitive hosts too.
  for child in list(stage.iterdir()):
   if child.is_dir() and child.name.casefold() in {'model','texture'} and child.name!=child.name.lower():child.rename(stage/child.name.lower())
  shutil.copytree(folder/'model',stage/'model',dirs_exist_ok=True);
  if (folder/'texture').exists():shutil.copytree(folder/'texture',stage/'texture',dirs_exist_ok=True)
  for relative,src in copies.items():
   out=stage/prefix/relative;out.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,out)
  export_cfg(stage,candidate,stage/'model'/'model.cfg');candidate.pop('cfg_output',None);save_project(stage/'project.json',candidate)
  from vehicle_template import set_arg
  bus_text=set_arg(replace_sections(txt(donor),sections,prefix),'[model]',0,'model\\model.cfg')
  if not any(c['tag']=='[model]' for c in commands(bus_text)):raise ValueError('Doador sem [model]')
  (stage/donor.name).write_bytes(bus_text.replace('\n','\r\n').encode('cp1252'))
  (stage/'INCLUIR_NO_BUS.txt').write_text('[model]\nmodel\\model.cfg\n'+replace_sections('',sections,prefix),encoding='cp1252')
  (stage/'LEIA.txt').write_text('Inclui o .bus do doador, scripts e recursos locais. O [model] aponta para o CFG gerado. Física, posições e lógica herdadas exigem revisão; o CFG universal não importa os blocos da base. Recursos externos ainda podem faltar.\n',encoding='utf8');publish(stage,final);shutil.rmtree(stage);return final
 except Exception:shutil.rmtree(stage,ignore_errors=True);raise
