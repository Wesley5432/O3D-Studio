"""Organize a converted project in a new copy, preserving the source."""
import copy,json,os,re,shutil,tempfile,uuid
from pathlib import Path
from asset_paths import GROUPS,clean_name,mesh_path,suggest_group
from project import save_project

def organize_copy(folder,project,choices=None):
 folder=Path(folder).resolve();choices=choices or {};project=copy.deepcopy(project);mapping={};used=set()
 for i,part in enumerate(project['parts']):
  old=mesh_path(part['file']);choice=choices.get(part['id'],{})
  group=choice.get('group',old.split('/')[0] if '/' in old else suggest_group(part['name']))
  if group not in GROUPS:raise ValueError('Pasta inválida')
  label=choice.get('name',part['name']);name='%04d_%s.o3d'%(i,clean_name(label));new=group+'/'+name
  if new.casefold() in used or old in mapping:raise ValueError('Nomes duplicados no projeto')
  if not (folder/'model'/old).is_file():raise ValueError('O3D ausente: '+old)
  mapping[old]=new;used.add(new.casefold());part['file']=new
 final=folder.with_name(folder.name+'_organizado_'+uuid.uuid4().hex[:8]);stage=Path(tempfile.mkdtemp(prefix='.organizar-',dir=folder.parent))
 try:
  shutil.copytree(folder,stage,dirs_exist_ok=True)
  model=stage/'model';shutil.rmtree(model);model.mkdir()
  for group in GROUPS:(model/group).mkdir()
  # Preserve non-mesh model resources, updating references in every model CFG.
  for src in (folder/'model').rglob('*'):
   if not src.is_file() or src.suffix.lower()=='.o3d':continue
   dst=model/src.relative_to(folder/'model');dst.parent.mkdir(parents=True,exist_ok=True)
   if src.suffix.lower()!='.cfg':shutil.copy2(src,dst);continue
   text=src.read_bytes().decode('cp1252');lines=text.splitlines(True)
   for j,line in enumerate(lines[:-1]):
    if line.strip()=='[mesh]':
     value=lines[j+1].strip().replace('\\','/')
     full=(src.parent/value).resolve()
     try:old=full.relative_to(folder/'model').as_posix()
     except ValueError:continue
     if old in mapping:
      relative=os.path.relpath(model/mapping[old],dst.parent).replace(os.sep,'\\');ending='\r\n' if lines[j+1].endswith('\r\n') else '\n' if lines[j+1].endswith('\n') else ''
      lines[j+1]=relative+ending
   dst.write_bytes(''.join(lines).encode('cp1252'))
  for old,new in mapping.items():shutil.copy2(folder/'model'/old,model/new)
  (model/'meshes.cfg').write_text('\n'.join('[mesh]\n'+p['file'].replace('/','\\')+'\n' for p in project['parts']),encoding='cp1252')
  reportfile=stage/'report.json'
  if reportfile.exists():
   report=json.loads(reportfile.read_text(encoding='utf8'))
   for piece in report.get('meshes',[]):
    if piece['file'] in mapping:piece['file']=mapping[piece['file']];piece['group']=piece['file'].split('/')[0]
   report['organized']=True;reportfile.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
  if project.get('cfg_output'):
   try:relative=Path(project['cfg_output']).resolve().relative_to(folder)
   except ValueError:project.pop('cfg_output',None)
   else:project['cfg_output']=str(final/relative)
  save_project(stage/'project.json',project)
  (stage/'organizacao.json').write_text(json.dumps(mapping,ensure_ascii=False,indent=2),encoding='utf8')
  stage.rename(final);return final
 except Exception:
  shutil.rmtree(stage,ignore_errors=True);raise

def open_organizer(editor):
 import tkinter as tk
 from tkinter import ttk,messagebox
 from editor import open_editor
 win=tk.Toplevel(editor.win);win.title('Organizar e renomear peças');win.geometry('880x620')
 ttk.Label(win,text='Revise as pastas sugeridas pelo nome. Salvar cria uma cópia organizada do projeto.\nAs peças originais permanecem intactas. Aplique as edições do editor antes de abrir esta janela.',padding=12).pack(anchor='w')
 choices={p['id']:{'group':p['file'].split('/')[0] if '/' in p['file'] else suggest_group(p['name']),'name':p['name']} for p in editor.project['parts']}
 tree=ttk.Treeview(win,columns=('name','group','new'),show='headings')
 for k,label in [('name','Objeto original'),('group','Pasta'),('new','Nome corrigido')]:tree.heading(k,text=label)
 tree.pack(fill='both',expand=True,padx=12)
 for i,p in enumerate(editor.project['parts']):tree.insert('','end',iid=p['id'],values=(p['name'],choices[p['id']]['group'],'%04d_%s.o3d'%(i,clean_name(p['name']))))
 row=ttk.Frame(win,padding=12);row.pack(fill='x');group=tk.StringVar(value='Exterior');name=tk.StringVar()
 ttk.Combobox(row,textvariable=group,values=GROUPS,state='readonly',width=15).pack(side='left');ttk.Entry(row,textvariable=name).pack(side='left',fill='x',expand=True,padx=8)
 def select(event=None):
  selected=tree.selection()
  if selected:choice=choices[selected[0]];group.set(choice['group']);name.set(choice['name'])
 tree.bind('<<TreeviewSelect>>',select)
 def apply():
  selected=tree.selection()
  if not selected:return
  key=selected[0];choices[key]={'group':group.get(),'name':name.get()};values=list(tree.item(key,'values'));values[1]=group.get();values[2]=clean_name(name.get())+'.o3d';tree.item(key,values=values)
 ttk.Button(row,text='Aplicar à peça',command=apply).pack(side='left')
 def save():
  try:
   out=organize_copy(editor.folder,editor.project,choices);messagebox.showinfo('Cópia organizada',str(out)+'\nReabra associações de montagem que utilizavam os caminhos antigos.',parent=win);win.destroy();open_editor(editor.win,out)
  except Exception as exc:messagebox.showerror('Organização',str(exc),parent=win)
 ttk.Button(win,text='Salvar cópia com as quatro pastas',command=save).pack(anchor='e',padx=12,pady=12)
