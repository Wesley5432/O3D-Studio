"""Numerical piece editor. Geometry is not moved here. GPL-3+."""
import json, copy, re, tkinter as tk
from pathlib import Path
from tkinter import ttk, filedialog, messagebox, simpledialog
from project import recipe, validate_project, save_project, export_cfg, load_profile, load_scripts

class PieceEditor:
 def __init__(self,master,folder):
  self.folder=Path(folder);self.project=json.loads((self.folder/'project.json').read_text(encoding='utf8'))
  if self.project.get('version')!=2:raise ValueError('Reconverta o modelo com a versão 0.2 para criar project.json.')
  self.history=[];self.current=None;self.draft=None
  self.win=tk.Toplevel(master);self.win.title('Editor de peças — O3D Studio 0.0.1');self.win.geometry('1180x800');self.win.minsize(1000,720)
  from ui_theme import apply_theme
  apply_theme(self.win)
  ttk.Label(self.win,text='Peças e configuração',style='Title.TLabel').pack(anchor='w',padx=16,pady=(14,4))
  from ui_components import action_menu
  top=ttk.Frame(self.win,padding=(12,8));top.pack(fill='x')
  action_menu(top,'Projeto',[('Salvar projeto',self.save),('Desfazer',self.undo),('Organizar / renomear',self.organize)],self.guard).pack(side='left',padx=4)
  action_menu(top,'Scripts',[('Selecionar doador .bus',self.choose_profile),('Ler scripts .osc',self.choose_scripts),('Variáveis e eventos',self.catalog),('Limpar perfil',self.clear_profile)],self.guard).pack(side='left',padx=4)
  action_menu(top,'Exportar',[('O3D selecionado + texturas',lambda:self.export_scope(False)),('Todos os O3D + texturas',lambda:self.export_scope(True)),('Selecionar CFG de saída',self.choose_output),('Gerar CFG',self.export),('Veículo + scripts + .bus',self.export_scripts)],self.guard).pack(side='left',padx=4)
  ttk.Button(top,text='Diagnóstico',command=lambda:self.guard(self.diagnostics)).pack(side='right')
  self.mesh_scope=tk.StringVar(value='Somente a peça selecionada')
  self.status=tk.StringVar(value='Editor numérico. Origem do O3D preservada; movimentos exigem validação no OMSI.')
  ttk.Label(self.win,textvariable=self.status,wraplength=1000).pack(fill='x',padx=10)
  body=ttk.Panedwindow(self.win,orient='horizontal');body.pack(fill='both',expand=True,padx=8,pady=8)
  left=ttk.Frame(body);right=ttk.Frame(body);body.add(left,weight=1);body.add(right,weight=3)
  self.search=tk.StringVar();ttk.Label(left,text='Buscar peça, arquivo ou textura').pack(anchor='w');ttk.Entry(left,textvariable=self.search).pack(fill='x',pady=(2,6))
  self.tree=ttk.Treeview(left,columns=('name','file'),show='headings',selectmode='browse');self.tree.heading('name',text='Objeto original');self.tree.heading('file',text='Pasta / arquivo O3D');self.tree.column('name',width=150);self.tree.column('file',width=230);self.tree.pack(fill='both',expand=True)
  self.populate_parts();self.search.trace_add('write',lambda *a:self.populate_parts())
  self.tree.bind('<<TreeviewSelect>>',lambda e:self.select())
  self.info=tk.StringVar();ttk.Label(right,textvariable=self.info,wraplength=700).pack(anchor='w',pady=6)
  fields=ttk.Frame(right);fields.pack(fill='x');self.fields={}
  for i,(key,label,default) in enumerate([('parent','Parent (ID, vazio = nenhum)',''),('pivot','Pivô XYZ, vazio = origem O3D',''),('event','Evento do mouse',''),('visible','Variável de visibilidade',''),('visible_value','Valor de visibilidade','1')]):
   ttk.Label(fields,text=label).grid(row=i,column=0,sticky='w');v=tk.StringVar(value=default);self.fields[key]=v
   if key=='parent':widget=ttk.Combobox(fields,textvariable=v,values=['']+[p['id'] for p in self.project['parts']])
   else:widget=ttk.Entry(fields,textvariable=v)
   widget.grid(row=i,column=1,sticky='ew',padx=5,pady=2)
  fields.columnconfigure(1,weight=1)
  note=ttk.Notebook(right);note.pack(fill='both',expand=True,pady=8)
  anim=ttk.Frame(note,padding=5);mat=ttk.Frame(note,padding=5);note.add(anim,text='Animações');note.add(mat,text='Materiais')
  row=ttk.Frame(anim);row.pack(fill='x');self.preset=tk.StringVar(value='door')
  presets=ttk.Combobox(row,textvariable=self.preset,values=['static','door','steering','wheel_front','wheel_rear','custom'],state='readonly',width=15);presets.pack(side='left')
  self.var=tk.StringVar(value='door_0');self.factor=tk.StringVar(value='-90');self.axle=tk.StringVar(value='0');self.side=tk.StringVar(value='R')
  presets.bind('<<ComboboxSelected>>',lambda e:self.factor.set('1200' if self.preset.get()=='steering' else '-90'))
  for label,v,width in [('Variável',self.var,18),('Fator',self.factor,8),('Eixo',self.axle,3),('L/R',self.side,3)]:
   ttk.Label(row,text=label).pack(side='left');ttk.Entry(row,textvariable=v,width=width).pack(side='left',padx=2)
  ttk.Button(anim,text='Preparar receita (substitui a lista da peça)',command=lambda:self.guard(self.prepare)).pack(anchor='w',pady=5)
  self.animtree=ttk.Treeview(anim,columns=('type','variable','factor','rotation'),show='headings',height=7)
  for k,label in [('type','Tipo'),('variable','Variável'),('factor','Fator'),('rotation','Rotação da origem XYZ')]:self.animtree.heading(k,text=label);self.animtree.column(k,width=100 if k!='variable' else 200)
  self.animtree.pack(fill='both',expand=True);self.animtree.bind('<<TreeviewSelect>>',lambda e:self.select_anim())
  edit=ttk.Frame(anim);edit.pack(fill='x',pady=5);self.av={}
  for key,value in [('type','rot'),('variable','door_0'),('factor','-90'),('rotation','0 90 0')]:
   v=tk.StringVar(value=value);self.av[key]=v;ttk.Entry(edit,textvariable=v,width=12 if key!='variable' else 20).pack(side='left',padx=2)
  actions=ttk.Frame(anim);actions.pack(fill='x')
  for label,fun in [('Adicionar',lambda:self.edit_anim(False)),('Atualizar',lambda:self.edit_anim(True)),('Remover',self.remove_anim)]:ttk.Button(actions,text=label,command=lambda f=fun:self.guard(f)).pack(side='left')
  ttk.Label(anim,text='Receita volante: use fator 1200 como referência, ajuste ao seu ônibus.\nRoda dianteira: giro + suspensão + direção; escolha eixo/lado corretos.\nCampos de animação: rot/trans, variável, fator, rotações XYZ em graus.',wraplength=650).pack(anchor='w',pady=5)
  self.mats=ttk.Treeview(mat,columns=('slot','texture','occurrence'),show='headings',height=8)
  for k in ('slot','texture','occurrence'):self.mats.heading(k,text=k);self.mats.column(k,width=210 if k=='texture' else 70)
  self.mats.pack(fill='both',expand=True);self.mats.bind('<<TreeviewSelect>>',lambda e:self.select_mat())
  self.alpha=tk.StringVar(value='');self.night=tk.StringVar();self.lightvar=tk.StringVar()
  for label,v in [('Alpha (vazio, 0, 1 ou 2)',self.alpha),('Nightmap (arquivo na pasta texture)',self.night),('Variável da iluminação',self.lightvar)]:
   ttk.Label(mat,text=label).pack(anchor='w');ttk.Entry(mat,textvariable=v).pack(fill='x')
  ttk.Button(mat,text='Aplicar ao material selecionado',command=lambda:self.guard(self.edit_mat)).pack(anchor='w',pady=5)
  ttk.Button(right,text='Aplicar alterações à peça',command=lambda:self.guard(self.apply)).pack(anchor='w')
  ttk.Label(right,text='Trocar de peça descarta campos ainda não aplicados. Pivô não move a malha.\nAs receitas são pontos de partida; não simulam os scripts nem mostram prévia 3D.',wraplength=680).pack(anchor='w',pady=5)
  if self.project['parts']:self.tree.selection_set(self.project['parts'][0]['id'])
 def populate_parts(self):
  self.tree.delete(*self.tree.get_children());query=self.search.get().casefold()
  for p in self.project['parts']:
   text=p['name']+' '+p['file']+' '+' '.join(m.get('texture','') for m in p['materials'])
   if query in text.casefold():self.tree.insert('', 'end',iid=p['id'],values=(p['name'],p['file']))
 def diagnostics(self):
  reportfile=self.folder/'report.json'
  if not reportfile.exists():raise ValueError('report.json não encontrado')
  report=json.loads(reportfile.read_text(encoding='utf8'));win=tk.Toplevel(self.win);win.title('Diagnóstico da conversão');win.geometry('850x560')
  text=tk.Text(win,wrap='word',padx=12,pady=12);text.pack(fill='both',expand=True)
  textures=report.get('textures',[]);missing=[t['texture'] for t in textures if not t['available']]
  header=f"Peças: {len(report.get('meshes',[]))} | Texturas: {len(textures)} | Imagens ausentes: {len(missing)}"
  text.insert('1.0',header+'\n\n'+'\n'.join(report.get('warnings',[])))
  text.config(state='disabled')
 def organize(self):
  from organizer import open_organizer
  open_organizer(self)
 def guard(self,f):
  try:f()
  except Exception as e:messagebox.showerror('Configuração',str(e),parent=self.win)
 def remember(self):self.history.append(copy.deepcopy(self.project));self.history=self.history[-20:]
 def select(self):
  selected=self.tree.selection()
  if not selected:return
  self.current=selected[0];p=next(p for p in self.project['parts'] if p['id']==self.current);self.draft=copy.deepcopy(p)
  self.info.set(p['id']+' — '+p['name']+'\nArquivo: '+p['file']+'\nOrigem mundial: '+str(p.get('origin_xyz')))
  self.fields['parent'].set(p['parent']);self.fields['pivot'].set('' if p['pivot'] is None else ' '.join(map(str,p['pivot'])))
  self.fields['event'].set(p['mouseevent']);self.fields['visible'].set((p.get('visible') or {}).get('variable',''));self.fields['visible_value'].set(str((p.get('visible') or {}).get('value',1)))
  self.refresh_anims();self.mats.delete(*self.mats.get_children())
  for i,m in enumerate(p['materials']):self.mats.insert('','end',iid=str(i),values=(i,m['texture'] or '(sem textura)',m['occurrence']))
 def refresh_anims(self):
  self.animtree.delete(*self.animtree.get_children())
  for i,a in enumerate(self.draft['animations']):self.animtree.insert('','end',iid=str(i),values=(a['type'],a['variable'],a['factor'],' '.join(map(str,a['origin_rotation']))))
 def prepare(self):
  if self.draft is None:return
  self.draft['animations']=recipe(self.preset.get(),self.var.get(),float(self.factor.get()),int(self.axle.get()),self.side.get());self.refresh_anims()
 def select_anim(self):
  sel=self.animtree.selection()
  if not sel:return
  a=self.draft['animations'][int(sel[0])]
  for key in ['type','variable','factor']:self.av[key].set(str(a[key]))
  self.av['rotation'].set(' '.join(map(str,a['origin_rotation'])))
 def edit_anim(self,replace):
  if self.draft is None:return
  a={'type':self.av['type'].get(),'variable':self.av['variable'].get(),'factor':float(self.av['factor'].get()),'origin_rotation':[float(x) for x in self.av['rotation'].get().split()]}
  if replace:
   sel=self.animtree.selection()
   if not sel:raise ValueError('Selecione uma animação')
   self.draft['animations'][int(sel[0])]=a
  else:self.draft['animations'].append(a)
  self.refresh_anims()
 def remove_anim(self):
  sel=self.animtree.selection()
  if sel:self.draft['animations'].pop(int(sel[0]));self.refresh_anims()
 def select_mat(self):
  sel=self.mats.selection()
  if not sel:return
  r=next((r for r in self.draft['material_rules'] if r['slot']==int(sel[0])),{})
  self.alpha.set('' if r.get('alpha') is None else str(r['alpha']));self.night.set(r.get('nightmap',''));self.lightvar.set(r.get('variable',''))
 def edit_mat(self):
  sel=self.mats.selection()
  if not sel:raise ValueError('Selecione um material')
  slot=int(sel[0]);r={'slot':slot,'alpha':int(self.alpha.get()) if self.alpha.get() else None,'nightmap':self.night.get().strip(),'variable':self.lightvar.get().strip()}
  self.draft['material_rules']=[a for a in self.draft['material_rules'] if a['slot']!=slot]+[r]
  self.status.set('Material preparado. Clique em Aplicar alterações à peça.')
 def apply(self):
  if self.draft is None:return
  p=copy.deepcopy(self.draft);p['parent']=self.fields['parent'].get().strip();raw=self.fields['pivot'].get().strip();p['pivot']=[float(x) for x in raw.split()] if raw else None
  p['mouseevent']=self.fields['event'].get().strip();v=self.fields['visible'].get().strip();p['visible']={'variable':v,'value':float(self.fields['visible_value'].get())} if v else None
  selected=self.animtree.selection()
  if selected:
   p['animations'][int(selected[0])]={'type':self.av['type'].get().strip(),'variable':self.av['variable'].get().strip(),'factor':float(self.av['factor'].get()),'origin_rotation':[float(x) for x in self.av['rotation'].get().split()]}
  material=self.mats.selection()
  if material:
   slot=int(material[0]);rule={'slot':slot,'alpha':int(self.alpha.get()) if self.alpha.get() else None,'nightmap':self.night.get().strip(),'variable':self.lightvar.get().strip()}
   p['material_rules']=[r for r in p['material_rules'] if r['slot']!=slot]+[rule]
  candidate=copy.deepcopy(self.project);candidate['parts']=[p if x['id']==p['id'] else x for x in candidate['parts']];validate_project(candidate)
  self.remember();self.project=candidate;self.draft=copy.deepcopy(p);self.status.set('Peça aplicada. Salve o projeto para manter as alterações.')
 def choose_profile(self):
  path=filedialog.askopenfilename(parent=self.win,filetypes=[('Ônibus OMSI','*.bus')])
  if not path:return
  profile=load_profile(path);self.remember();self.project['profile']=profile
  self.status.set(profile['name']+' — '+str(len(profile['variables']))+' variáveis; '+str(len(profile['missing']))+' dependências ausentes.')
  if profile['missing']:messagebox.showwarning('Perfil incompleto','\n'.join(profile['missing'][:12]),parent=self.win)
 def clear_profile(self):
  self.remember();self.project['profile']=None;self.status.set('Perfil removido. Variáveis específicas exigirão uma base válida para exportar.')
 def save(self):save_project(self.folder/'project.json',self.project);self.status.set('Projeto salvo. Apenas alterações aplicadas foram gravadas.')
 def export(self):
  path=export_cfg(self.folder,self.project,self.project.get('cfg_output'));self.save();messagebox.showinfo('CFG gerado',str(path)+'\nIntegre ao .bus e teste no OMSI.',parent=self.win)
 def export_scope(self,all_parts):
  self.mesh_scope.set('Todas as peças' if all_parts else 'Somente a peça selecionada');self.export_geometry()
 def export_geometry(self):
  from output_files import export_meshes
  selected=None if self.mesh_scope.get()=='Todas as peças' else [self.current]
  if selected and not self.current:raise ValueError('Selecione uma peça na lista')
  dest=filedialog.askdirectory(parent=self.win,title='Pasta de saída direta (model e texture)')
  if not dest:return
  out=export_meshes(self.folder,self.project,dest,selected)
  self.status.set('O3D e texturas exportados diretamente em '+str(out))
 def export_scripts(self):
  from script_transfer import package_cfg_scripts
  bus=(self.project.get('profile') or {}).get('source')
  if not bus:bus=filedialog.askopenfilename(parent=self.win,title='Doador de scripts',filetypes=[('Ônibus OMSI','*.bus')])
  if not bus:return
  destination=filedialog.askdirectory(parent=self.win,title='Saída do pacote CFG + scripts')
  if not destination:return
  out=package_cfg_scripts(self.folder,self.project,bus,destination)
  messagebox.showinfo('CFG + scripts',str(out)+'\n.bus e scripts incluídos. Revise física, posições e CFG antes de testar no jogo.',parent=self.win)
 def choose_output(self):
  path=filedialog.asksaveasfilename(parent=self.win,title='Selecionar ou criar CFG de saída',initialdir=self.folder/'model',initialfile='model.cfg',defaultextension='.cfg',filetypes=[('Modelo OMSI','*.cfg')])
  if not path:return
  self.set_output(path)
 def set_output(self,path):
  path=Path(path).resolve()
  if path.suffix.lower()!='.cfg':raise ValueError('Escolha um .cfg')
  if not path.exists() or not path.read_bytes().strip():
   export_cfg(self.folder,self.project,path)
   self.status.set('CFG inicial produzido: '+str(path)+' — configure as peças e gere novamente.')
  else:self.status.set('Saída selecionada: '+str(path)+' — Gerar CFG substituirá o conteúdo com backup.')
  self.project['cfg_output']=str(path)
 def choose_scripts(self):
  paths=filedialog.askopenfilenames(parent=self.win,title='Scripts do veículo (somente leitura)',filetypes=[('Scripts OMSI','*.osc')])
  if not paths:return
  profile=load_scripts(paths);self.remember();self.project['profile']=profile
  self.status.set(str(len(profile['variables']))+' variáveis numéricas lidas. Referências não comprovam declaração nas varlists; confira o .bus.')
  self.catalog()
 def catalog(self):
  win=tk.Toplevel(self.win);win.title('Variáveis e eventos do veículo');win.geometry('650x500')
  ttk.Label(win,text='Scripts são lidos, nunca executados ou alterados. Variáveis manuais\nprecisam ser declaradas e controladas pelos scripts do veículo.').pack(anchor='w',padx=10,pady=8)
  table=ttk.Treeview(win,columns=('type','name'),show='headings',selectmode='browse');table.heading('type',text='Tipo / origem');table.heading('name',text='Nome');table.column('type',width=150);table.column('name',width=350);table.pack(fill='both',expand=True,padx=10)
  def refresh():
   table.delete(*table.get_children());profile=self.project.get('profile') or {}
   for kind,items in [('Numérica',profile.get('variables',[])),('Texto',profile.get('string_variables',[])),('Evento',profile.get('triggers',[])),('Manual',self.project.get('custom_variables',[]))]:
    for name in sorted(items):table.insert('','end',values=(kind,name))
  def use(destination):
   sel=table.selection()
   if not sel:return
   kind,name=table.item(sel[0],'values')
   if destination=='event':
    if kind!='Evento':raise ValueError('Escolha um evento')
    self.fields['event'].set(name)
   else:
    if kind not in {'Numérica','Manual'}:raise ValueError('Escolha uma variável numérica')
    if destination=='anim':self.var.set(name);self.av['variable'].set(name)
    elif destination=='visible':self.fields['visible'].set(name)
    else:self.lightvar.set(name)
   self.status.set('Campo preenchido. Configure e aplique a alteração à peça.')
  def add():
   name=simpledialog.askstring('Variável manual','Nome da variável numérica:',parent=win)
   if name is None:return
   name=name.strip()
   if not re.fullmatch(r'[A-Za-z_][A-Za-z_0-9]*',name):raise ValueError('Use letras, números e _, iniciando com letra ou _')
   self.remember();self.project['custom_variables']=sorted(set(self.project.get('custom_variables',[]))|{name});refresh()
  row=ttk.Frame(win);row.pack(fill='x',padx=8,pady=8)
  for label,dest in [('Animação','anim'),('Visibilidade','visible'),('Iluminação','light'),('Evento','event')]:ttk.Button(row,text=label,command=lambda d=dest:self.guard(lambda:use(d))).pack(side='left')
  ttk.Button(win,text='Adicionar variável manual',command=lambda:self.guard(add)).pack(anchor='w',padx=8,pady=8);refresh()
 def undo(self):
  if self.history:self.project=self.history.pop();self.select();self.status.set('Alteração desfeita; salve o projeto.')

def open_editor(master,folder=None):
 if not folder:folder=filedialog.askdirectory(title='Pasta convertida contendo project.json')
 if not folder:return
 try:return PieceEditor(master,folder)
 except Exception as e:messagebox.showerror('Abrir projeto',str(e),parent=master)
