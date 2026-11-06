"""Numerical piece editor. Geometry is not moved here. GPL-3+."""
import json, copy, re, tkinter as tk
from pathlib import Path
from tkinter import ttk, filedialog, messagebox, simpledialog
from project import recipe, validate_project, save_project, export_cfg, load_profile, load_scripts
RECIPES={'Sem movimento':'static','Porta':'door','Volante':'steering','Roda dianteira':'wheel_front','Roda traseira':'wheel_rear','Palheta':'wiper','Manete / câmbio':'lever','Personalizada':'custom'}

class PieceEditor:
 def __init__(self,master,folder):
  self.folder=Path(folder);self.project=json.loads((self.folder/'project.json').read_text(encoding='utf8'))
  if self.project.get('version')!=2:raise ValueError('Reconverta o modelo com a versão 0.2 para criar project.json.')
  self.history=[];self.current=None;self.draft=None
  self.win=tk.Toplevel(master);self.win.title('Editor de peças — O3D Studio v0.0.2');self.win.geometry('1180x800');self.win.minsize(1000,720)
  from ui_theme import apply_theme
  apply_theme(self.win)
  ttk.Label(self.win,text='Peças e configuração',style='Title.TLabel').pack(anchor='w',padx=16,pady=(14,4))
  from ui_components import action_menu
  top=ttk.Frame(self.win,padding=(12,8));top.pack(fill='x')
  action_menu(top,'Projeto',[('Salvar projeto',self.save),('Desfazer',self.undo),('Organizar / renomear',self.organize),('Luzes e marcadores',self.edit_lights)],self.guard).pack(side='left',padx=4)
  action_menu(top,'Scripts',[('Selecionar doador .bus',self.choose_profile),('Ler scripts .osc',self.choose_scripts),('Variáveis e eventos',self.catalog),('Limpar perfil',self.clear_profile)],self.guard).pack(side='left',padx=4)
  action_menu(top,'Exportar',[('O3D selecionado + texturas',lambda:self.export_scope(False)),('Todos os O3D + texturas',lambda:self.export_scope(True)),('OBJ da peça selecionada',lambda:self.export_obj_scope(False)),('OBJ de todas as peças',lambda:self.export_obj_scope(True)),('Selecionar CFG de saída',self.choose_output),('Gerar CFG',self.export),('Veículo + scripts + .bus',self.export_scripts)],self.guard).pack(side='left',padx=4)
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
   if key=='parent':widget=ttk.Combobox(fields,textvariable=v,values=['']+[p['id']+' — '+p['name'] for p in self.project['parts']]);self.parent_box=widget
   else:widget=ttk.Entry(fields,textvariable=v)
   widget.grid(row=i,column=1,sticky='ew',padx=5,pady=2)
  fields.columnconfigure(1,weight=1)
  markerrow=ttk.Frame(right);markerrow.pack(fill='x',pady=4);self.marker=tk.StringVar()
  ttk.Combobox(markerrow,textvariable=self.marker,values=[m['name'] for m in self.project.get('markers',[])],state='readonly').pack(side='left',fill='x',expand=True)
  ttk.Button(markerrow,text='Usar pivô do Blender',command=lambda:self.guard(self.use_marker)).pack(side='left',padx=4)
  note=ttk.Notebook(right);note.pack(fill='both',expand=True,pady=8)
  anim=ttk.Frame(note,padding=5);mat=ttk.Frame(note,padding=5);note.add(anim,text='Animações');note.add(mat,text='Materiais')
  row=ttk.Frame(anim);row.pack(fill='x');self.preset=tk.StringVar(value='Porta')
  presets=ttk.Combobox(row,textvariable=self.preset,values=list(RECIPES),state='readonly',width=15);presets.pack(side='left')
  self.var=tk.StringVar(value='door_0');self.factor=tk.StringVar(value='-90');self.axle=tk.StringVar(value='0');self.side=tk.StringVar(value='R')
  presets.bind('<<ComboboxSelected>>',lambda e:self.factor.set({'Volante':'1200','Palheta':'-84','Manete / câmbio':'30'}.get(self.preset.get(),'-90')))
  for label,v,width in [('Variável',self.var,18),('Fator',self.factor,8),('Eixo',self.axle,3),('L/R',self.side,3)]:
   ttk.Label(row,text=label).pack(side='left');ttk.Entry(row,textvariable=v,width=width).pack(side='left',padx=2)
  ttk.Button(anim,text='Preparar receita da peça',command=lambda:self.guard(self.prepare)).pack(anchor='w',pady=5)
  self.animtree=ttk.Treeview(anim,columns=('type','variable','factor','rotation'),show='headings',height=7)
  for k,label in [('type','Tipo'),('variable','Variável'),('factor','Fator'),('rotation','Rotação da origem XYZ')]:self.animtree.heading(k,text=label);self.animtree.column(k,width=100 if k!='variable' else 200)
  self.animtree.pack(fill='both',expand=True);self.animtree.bind('<<TreeviewSelect>>',lambda e:self.select_anim())
  edit=ttk.Frame(anim);edit.pack(fill='x',pady=5);self.av={}
  for key,value in [('type','rot'),('variable','door_0'),('factor','-90'),('rotation','0 90 0')]:
   v=tk.StringVar(value=value);self.av[key]=v
   widget=ttk.Combobox(edit,textvariable=v,values=['rot','trans'],state='readonly',width=7) if key=='type' else ttk.Entry(edit,textvariable=v,width=12 if key!='variable' else 20)
   widget.pack(side='left',padx=2)
  actions=ttk.Frame(anim);actions.pack(fill='x')
  for label,fun in [('Aplicar animação',self.apply_animation),('Nova animação',lambda:self.edit_anim(False)),('Remover',self.remove_anim),('Prévia 3D',self.preview_animation)]:ttk.Button(actions,text=label,command=lambda f=fun:self.guard(f)).pack(side='left')
  ttk.Label(anim,text='Receita volante: use fator 1200 como referência, ajuste ao seu ônibus.\nRoda dianteira: giro + suspensão + direção; escolha eixo/lado corretos.\nPalheta (wiper) e manete (lever): escolha a variável, o fator e o eixo; confira na Prévia 3D.',wraplength=650).pack(anchor='w',pady=5)
  self.mats=ttk.Treeview(mat,columns=('slot','texture','occurrence'),show='headings',height=8)
  for k in ('slot','texture','occurrence'):self.mats.heading(k,text={'slot':'Índice','texture':'Textura original','occurrence':'Ocorrência'}[k]);self.mats.column(k,width=210 if k=='texture' else 70)
  self.mats.pack(fill='both',expand=True);self.mats.bind('<<TreeviewSelect>>',lambda e:self.select_mat())
  self.alpha=tk.StringVar(value='');self.night=tk.StringVar();self.lightvar=tk.StringVar()
  for label,v in [('Alpha (vazio, 0, 1 ou 2)',self.alpha),('Nightmap (arquivo na pasta texture)',self.night),('Variável da iluminação',self.lightvar)]:
   ttk.Label(mat,text=label).pack(anchor='w');ttk.Entry(mat,textvariable=v).pack(fill='x')
  ttk.Button(mat,text='Aplicar ao material selecionado',command=lambda:self.guard(self.apply_material)).pack(anchor='w',pady=5)
  self.skin_tab=ttk.Frame(note,padding=8);note.add(self.skin_tab,text='Deformação');self.skin_vars={}
  ttk.Button(right,text='Aplicar alterações à peça',command=lambda:self.guard(self.apply)).pack(anchor='w')
  ttk.Label(right,text='Trocar de peça descarta campos ainda não aplicados. Pivô não move a malha.\nA Prévia 3D testa geometria; scripts e física precisam ser conferidos no jogo.',wraplength=680).pack(anchor='w',pady=5)
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
  self.parent_box.configure(values=['']+[x['id']+' — '+x['name'] for x in self.project['parts'] if x['id']!=p['id']])
  self.fields['parent'].set(next((x['id']+' — '+x['name'] for x in self.project['parts'] if x['id']==p['parent']),p['parent']));self.fields['pivot'].set('' if p['pivot'] is None else ' '.join(map(str,p['pivot'])))
  self.fields['event'].set(p['mouseevent']);self.fields['visible'].set((p.get('visible') or {}).get('variable',''));self.fields['visible_value'].set(str((p.get('visible') or {}).get('value',1)))
  self.populate_skin(p)
  self.refresh_anims();self.mats.delete(*self.mats.get_children())
  for i,m in enumerate(p['materials']):self.mats.insert('','end',iid=str(i),values=(i,m['texture'] or '(sem textura)',m['occurrence']))
 def refresh_anims(self):
  self.animtree.delete(*self.animtree.get_children())
  for i,a in enumerate(self.draft['animations']):self.animtree.insert('','end',iid=str(i),values=(a['type'],a['variable'],a['factor'],' '.join(map(str,a['origin_rotation']))))
 def prepare(self):
  if self.draft is None:return
  self.draft['animations']=recipe(RECIPES.get(self.preset.get(),self.preset.get()),self.var.get(),float(self.factor.get()),int(self.axle.get()),self.side.get());self.refresh_anims()
  if self.draft['animations']:self.animtree.selection_set('0');self.select_anim()
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
 def candidate_piece(self):
  if self.draft is None:raise ValueError('Selecione uma peça')
  p=copy.deepcopy(self.draft);p['parent']=self.fields['parent'].get().split(' — ',1)[0].strip();raw=self.fields['pivot'].get().strip();p['pivot']=[float(x) for x in raw.split()] if raw else None
  p['mouseevent']=self.fields['event'].get().strip();v=self.fields['visible'].get().strip();p['visible']={'variable':v,'value':float(self.fields['visible_value'].get())} if v else None
  selected=self.animtree.selection()
  if selected:
   p['animations'][int(selected[0])]={'type':self.av['type'].get().strip(),'variable':self.av['variable'].get().strip(),'factor':float(self.av['factor'].get()),'origin_rotation':[float(x) for x in self.av['rotation'].get().split()]}
  material=self.mats.selection()
  if material:
   slot=int(material[0]);rule={'slot':slot,'alpha':int(self.alpha.get()) if self.alpha.get() else None,'nightmap':self.night.get().strip(),'variable':self.lightvar.get().strip()}
   p['material_rules']=[r for r in p['material_rules'] if r['slot']!=slot]+[rule]
  if hasattr(self,'skin_vars'):p['skin_bindings']={bone:v.get().split(' — ',1)[0] if v.get() else '' for bone,v in self.skin_vars.items()}
  return p
 def apply(self):
  if self.draft is None:return
  p=self.candidate_piece()
  candidate=copy.deepcopy(self.project);candidate['parts']=[p if x['id']==p['id'] else x for x in candidate['parts']];validate_project(candidate,for_export=False)
  self.remember();self.project=candidate;self.draft=copy.deepcopy(p);self.status.set('Peça aplicada. Salve o projeto para manter as alterações.')
 def apply_animation(self):
  self.edit_anim(bool(self.animtree.selection()));self.apply()
 def apply_material(self):
  self.edit_mat();self.apply()
 def edit_lights(self):
  from model_lights import light_editor
  light_editor(self)
 def use_marker(self):
  marker=next((m for m in self.project.get('markers',[]) if m['name']==self.marker.get()),None)
  if not marker:raise ValueError('Escolha um marcador importado do Blender')
  self.fields['pivot'].set(' '.join(map(str,marker['xyz'])));self.status.set('Pivô preenchido. Confira os eixos na prévia e aplique à peça.')
 def populate_skin(self,p):
  for widget in self.skin_tab.winfo_children():widget.destroy()
  self.skin_vars={}
  ttk.Label(self.skin_tab,text='Coifa / sanfona: cada grupo de vértices acompanha a peça controladora.\nA base pode ficar estática; o topo acompanha a cabeça do câmbio.\nOs pesos devem existir no Blender ou no O3D. Não são gerados pelo nome.',wraplength=650).pack(anchor='w',pady=8)
  values=[x['id']+' — '+x['name'] for x in self.project['parts'] if x['id']!=p['id']]
  for bone in p.get('bones',[]):
   row=ttk.Frame(self.skin_tab);row.pack(fill='x',pady=4);ttk.Label(row,text=bone,width=24).pack(side='left');target=p.get('skin_bindings',{}).get(bone,'');v=tk.StringVar(value=next((value for value in values if value.split(' — ',1)[0]==target),''));self.skin_vars[bone]=v;ttk.Combobox(row,textvariable=v,values=['',*values],state='readonly').pack(side='left',fill='x',expand=True)
  if not p.get('bones'):ttk.Label(self.skin_tab,text='Esta peça não possui pesos. Na conversão, marque Preservar pesos dos grupos de vértices.',wraplength=650).pack(anchor='w',pady=8)
  ttk.Button(self.skin_tab,text='Aplicar vínculos',command=lambda:self.guard(self.apply)).pack(anchor='w',pady=8)
  ttk.Button(self.skin_tab,text='Testar deformação na prévia',command=lambda:self.guard(self.preview_animation)).pack(anchor='w')
 def preview_animation(self):
  from animation_preview import open_preview
  p=self.candidate_piece();candidate=copy.deepcopy(self.project);candidate['parts']=[p if x['id']==p['id'] else x for x in candidate['parts']]
  open_preview(self.win,self.folder,candidate,p['id'])
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
  from catalog_ui import show_catalog
  def use(row,destination):
   kind,name=row['kind'],row['name']
   if destination=='event':
    if kind!='events':raise ValueError('Escolha um evento')
    # A mouse event base invokes its _drag/_off family; use the exact CFG base where available.
    self.fields['event'].set(name)
   else:
    if kind!='numeric':raise ValueError('Escolha uma variável numérica')
    if destination=='anim':self.var.set(name);self.av['variable'].set(name)
    elif destination=='visible':self.fields['visible'].set(name)
    else:self.lightvar.set(name)
   self.status.set('Campo preenchido. Aplique a alteração à peça e gere o CFG.')
  def add():
   name=simpledialog.askstring('Variável manual','Nome da variável numérica:',parent=self.win)
   if name is None:return
   name=name.strip()
   if not re.fullmatch(r'[A-Za-z_][A-Za-z_0-9]*',name):raise ValueError('Use letras, números e _, iniciando com letra ou _')
   self.remember();self.project['custom_variables']=sorted(set(self.project.get('custom_variables',[]))|{name});return name
  profile=self.project.get('profile') or {};show_catalog(self.win,profile=profile,manual=self.project.get('custom_variables',[]),bus=profile.get('source'),project=self.project,on_use=use,on_manual=lambda:self.guard_catalog_add(add))
 def guard_catalog_add(self,fn):
  try:return fn()
  except Exception as e:messagebox.showerror('Variável',str(e),parent=self.win)
 def export_obj_scope(self,all_parts):
  from obj_export import export_project_obj
  from obj_export_ui import done
  from ui_components import background
  if not all_parts and not self.current:raise ValueError('Selecione uma peça')
  dest=filedialog.askdirectory(parent=self.win,title='Pasta de saída dos OBJ e MTL')
  if not dest:return
  selected=None if all_parts else [self.current];snapshot=copy.deepcopy(self.project)
  background(self.win,'Exportando OBJ',lambda:export_project_obj(self.folder,snapshot,dest,selected),lambda result:done(self.win,result))
 def undo(self):
  if self.history:self.project=self.history.pop();self.select();self.status.set('Alteração desfeita; salve o projeto.')

def open_editor(master,folder=None):
 if not folder:folder=filedialog.askdirectory(title='Pasta convertida contendo project.json')
 if not folder:return
 try:return PieceEditor(master,folder)
 except Exception as e:messagebox.showerror('Abrir projeto',str(e),parent=master)
