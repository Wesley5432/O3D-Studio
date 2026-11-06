"""Desktop assembly studio; explicit donor-to-target associations."""
import json,queue,threading,tkinter as tk
from tkinter import ttk,filedialog,messagebox
from pathlib import Path
from vehicle_template import load_template,new_plan,target_parts,scan_plan,render_cfg,build,preview_piece
from project import atomic_text

class Studio:
 def __init__(self,root):
  self.root=root;self.template=None;self.plan=None;self.targets={};self.selected=None;self.jobs=queue.Queue();self.busy=False
  root.title('O3D Studio v0.0.2');root.geometry('1280x850');root.minsize(1050,720)
  from ui_theme import apply_theme
  apply_theme(root)
  outer=ttk.Frame(root,padding=18);outer.pack(fill='both',expand=True)
  ttk.Label(outer,text='O3D Studio',style='Title.TLabel').pack(anchor='w')
  ttk.Label(outer,text='Prepare seu modelo. Associe as peças. Exporte.',style='Muted.TLabel').pack(anchor='w',pady=(3,12))
  from ui_components import action_menu,disclosure
  bar=ttk.Frame(outer);bar.pack(fill='x',pady=(0,8))
  action_menu(bar,'Importar',[('BLEND / OBJ / 3DS',self.converter),('O3D já exportado',self.import_ready)],self.guard).pack(side='left',padx=(0,6))
  action_menu(bar,'Projeto',[('Abrir montagem',self.open),('Salvar montagem',self.save)],self.guard).pack(side='left',padx=(0,6))
  action_menu(bar,'Ferramentas',[('Editor de peças / CFG independente',self.universal),('Adaptar scripts',self.script_only),('Coordenadas das luzes',self.lights),('Ônibus articulado',self.articulated),('Variáveis e usos no CFG',self.catalog),('O3D → OBJ',self.export_obj)],self.guard).pack(side='left')
  self.tabs=ttk.Notebook(outer);self.tabs.pack(fill='both',expand=True,pady=8)
  self.base=self.tab('1  Base');self.parts=self.tab('2  Peças');self.assets=self.tab('3  Aparência');self.validation=self.tab('4  Exportar')
  self.fields={}
  self.field(self.base,'bus','Veículo base (.bus)',lambda:filedialog.askopenfilename(filetypes=[('Veículo OMSI','*.bus')]))
  self.field(self.base,'converted','Projeto do modelo novo',filedialog.askdirectory)
  self.field(self.base,'name','Nome do veículo',default='Meu_veiculo')
  self.fields['engine']=tk.StringVar(value='OMSI 2')
  row=ttk.Frame(self.base);row.pack(fill='x',pady=6);ttk.Label(row,text='Motor de destino',width=31).pack(side='left');ttk.Combobox(row,textvariable=self.fields['engine'],values=['OMSI 2','openOMSI'],state='readonly').pack(side='left')
  advanced=disclosure(self.base,'Usar outro CFG de referência (opcional)')
  self.field(advanced,'cfg','CFG de referência',lambda:filedialog.askopenfilename(filetypes=[('CFG visual','*.cfg')]))
  ttk.Button(self.base,text='Carregar base',style='Accent.TButton',command=lambda:self.guard(self.load)).pack(anchor='w',pady=12)
  self.info=ttk.Label(self.base,text='Escolha a base e o projeto convertido para começar.',wraplength=950);self.info.pack(anchor='w',pady=10)
  helpbox=disclosure(self.base,'Sobre a montagem e compatibilidade')
  ttk.Label(helpbox,text='A base fornece scripts e estrutura. Associe cada peça nova à sua função.\nFísica, câmeras, luzes e compatibilidade precisam de revisão no jogo.\nO editor independente não copia os blocos da base.',wraplength=900,style='Muted.TLabel').pack(anchor='w')
  pane=ttk.Panedwindow(self.parts,orient='horizontal');pane.pack(fill='both',expand=True)
  left=ttk.Frame(pane);right=ttk.Frame(pane,padding=10);pane.add(left,weight=2);pane.add(right,weight=3)
  self.search=tk.StringVar();ttk.Entry(left,textvariable=self.search).pack(fill='x');self.search.trace_add('write',lambda *a:self.refresh())
  self.tree=ttk.Treeview(left,columns=('mode',),selectmode='browse');self.tree.heading('#0',text='Peça na referência');self.tree.heading('mode',text='Ação');self.tree.column('#0',width=310);self.tree.column('mode',width=80)
  self.tree.pack(fill='both',expand=True);self.tree.bind('<<TreeviewSelect>>',lambda e:self.guard(self.select))
  ttk.Button(left,text='Sugerir associações pelo nome',command=lambda:self.guard(self.suggest)).pack(fill='x',pady=4)
  ttk.Button(left,text='Manter todas as peças ainda pendentes',command=lambda:self.guard(self.keep_pending)).pack(fill='x',pady=8)
  self.part_title=ttk.Label(right,text='Selecione uma peça',wraplength=580);self.part_title.pack(anchor='w')
  self.mode=tk.StringVar(value='pending');ttk.Combobox(right,textvariable=self.mode,values=['pending','replace','keep','remove'],state='readonly').pack(fill='x',pady=5)
  ttk.Label(right,text='pending = pendente · replace = substituir · keep = manter · remove = remover').pack(anchor='w')
  self.target=tk.StringVar();self.targetbox=ttk.Combobox(right,textvariable=self.target,state='readonly');self.targetbox.pack(fill='x',pady=7);self.targetbox.bind('<<ComboboxSelected>>',lambda e:self.guard(self.materials))
  detail=ttk.Notebook(right);detail.pack(fill='both',expand=True,pady=8)
  materials_tab=ttk.Frame(detail,padding=8);animation_tab=ttk.Frame(detail,padding=8);cfg_tab=ttk.Frame(detail,padding=8)
  detail.add(materials_tab,text='Materiais');detail.add(animation_tab,text='Animação');detail.add(cfg_tab,text='Código CFG');skin_tab=ttk.Frame(detail,padding=8);detail.add(skin_tab,text='Deformação')
  ttk.Label(skin_tab,text='Cada grupo com peso acompanha uma peça controladora da referência.\nOs índices do CFG são recalculados ao exportar.',wraplength=560).pack(anchor='w')
  self.skin_frame=self.scroll_area(skin_tab,height=240);self.bone_vars={}
  self.material_frame=self.scroll_area(materials_tab,height=240);self.material_vars={}
  ttk.Label(animation_tab,text='Variáveis da peça',style='Muted.TLabel').pack(anchor='w',pady=(4,8))
  self.variable_frame=self.scroll_area(animation_tab,height=160);self.variable_vars={}
  ttk.Label(animation_tab,text='Pivô XYZ em metros · vazio mantém a origem').pack(anchor='w',pady=(12,4))
  self.pivot=tk.StringVar();ttk.Entry(animation_tab,textvariable=self.pivot).pack(fill='x')
  self.confirmed=tk.BooleanVar();ttk.Checkbutton(animation_tab,text='Pivô e eixos conferidos',variable=self.confirmed).pack(anchor='w',pady=10)
  ttk.Button(animation_tab,text='Prévia 3D da animação',command=lambda:self.guard(self.preview_animation)).pack(anchor='w',pady=6)
  self.marker=tk.StringVar();self.marker_box=ttk.Combobox(animation_tab,textvariable=self.marker,state='readonly');self.marker_box.pack(fill='x',pady=4)
  ttk.Button(animation_tab,text='Usar coordenadas do marcador Blender',command=lambda:self.guard(self.use_marker)).pack(anchor='w')
  ttk.Button(right,text='Aplicar associação',style='Accent.TButton',command=lambda:self.guard(self.apply)).pack(anchor='e',pady=8)
  ttk.Button(cfg_tab,text='Atualizar prévia adaptada',command=lambda:self.guard(self.preview)).pack(anchor='w',pady=(0,8))
  self.block=tk.Text(cfg_tab,height=10,wrap='none',background='#14243a',foreground='#dce8f8',insertbackground='white',font=('Consolas',10),padx=12,pady=10,relief='flat');self.block.pack(fill='both',expand=True)
  self.field(self.assets,'skin_folder','Pasta de skins (.cti + imagens)',filedialog.askdirectory)
  self.field(self.assets,'skin_file','Skin específica (.cti)',lambda:filedialog.askopenfilename(filetypes=[('Repaint','*.cti')]))
  self.field(self.assets,'fonts_folder','Pasta Fonts (.oft + imagens)',filedialog.askdirectory)
  ttk.Button(self.assets,text='Atualizar lista de fontes da pasta',command=lambda:self.guard(self.refresh_fonts)).pack(anchor='w',pady=4)
  ttk.Label(self.assets,text='Fontes do letreiro/painel, canais de pintura e textura base. As variáveis de skin devem corresponder ao .cti.').pack(anchor='w',pady=8)
  self.asset_controls=self.scroll_area(self.assets,height=380);self.font_vars={};self.skin_vars={};self.base_overrides={}
  ttk.Label(self.asset_controls,text='Carregue a base na primeira aba para listar os canais de skin e as fontes do CFG.').pack(anchor='w',pady=8)
  actions=ttk.Frame(self.validation);actions.pack(fill='x')
  ttk.Button(actions,text='Verificar montagem',command=lambda:self.guard(self.validate)).pack(side='left')
  self.export_button=ttk.Button(actions,text='Exportar pacote',style='Accent.TButton',command=lambda:self.guard(self.export));self.export_button.pack(side='left',padx=8)
  self.result=tk.Text(self.validation,wrap='word');self.result.pack(fill='both',expand=True,pady=10)
  self.status=tk.StringVar(value='Pronto para começar.');ttk.Label(outer,textvariable=self.status).pack(anchor='w')
  self.poll_job=root.after(200,self.poll)
  root.bind('<Destroy>',self.on_destroy,add='+')
 def scroll_area(self,parent,height):
  container=ttk.Frame(parent);container.pack(fill='both',expand=True)
  canvas=tk.Canvas(container,height=height,highlightthickness=0);scroll=ttk.Scrollbar(container,orient='vertical',command=canvas.yview);canvas.configure(yscrollcommand=scroll.set)
  scroll.pack(side='right',fill='y');canvas.pack(side='left',fill='both',expand=True)
  body=ttk.Frame(canvas);window=canvas.create_window((0,0),window=body,anchor='nw')
  body.bind('<Configure>',lambda e:canvas.configure(scrollregion=canvas.bbox('all')));canvas.bind('<Configure>',lambda e:canvas.itemconfigure(window,width=e.width))
  return body
 def populate_assets(self):
  for w in self.asset_controls.winfo_children():w.destroy()
  self.font_vars={};self.font_boxes=[];self.skin_vars={};self.base_overrides=dict(self.plan.get('base_textures',{}));parent=self.asset_controls
  ttk.Label(parent,text='Fontes · nome usado nos blocos de texto',font=('Segoe UI',12,'bold')).pack(anchor='w',pady=8)
  for font in self.template['fonts']:
   row=ttk.Frame(parent);row.pack(fill='x',pady=2);ttk.Label(row,text=font,width=38).pack(side='left');v=tk.StringVar(value=self.plan.get('font_map',{}).get(font,font));self.font_vars[font]=v;box=ttk.Combobox(row,textvariable=v);box.pack(side='left',fill='x',expand=True);self.font_boxes.append(box)
   ttk.Button(row,text='Escolher .oft',command=lambda value=v:self.guard(lambda:self.choose_font(value))).pack(side='left')
  ttk.Label(parent,text='Canais de skin · selecione a textura do modelo convertido',font=('Segoe UI',12,'bold')).pack(anchor='w',pady=8)
  textures=sorted({s['texture'] for p in self.targets.values() for s in p['slots_actual'] if s['texture']})
  skin_options=sorted(set(textures)|{skin['texture'] for skin in self.template['skins']})
  for skin in self.template['skins']:
   row=ttk.Frame(parent);row.pack(fill='x',pady=2);ttk.Label(row,text=skin['variable']+' · '+skin['texture'],width=38).pack(side='left');v=tk.StringVar(value=self.plan.get('skin_targets',{}).get(skin['variable'],''));self.skin_vars[skin['variable']]=v;ttk.Combobox(row,textvariable=v,values=['']+skin_options,state='readonly').pack(side='left',fill='x',expand=True)
  ttk.Label(parent,text='Textura base · substituição opcional no mesmo formato',font=('Segoe UI',12,'bold')).pack(anchor='w',pady=8)
  self.override_texture=tk.StringVar();ttk.Combobox(parent,textvariable=self.override_texture,values=textures,state='readonly').pack(fill='x')
  ttk.Button(parent,text='Escolher imagem para esta textura',command=lambda:self.guard(self.choose_override)).pack(anchor='w',pady=5)
  ttk.Button(parent,text='Limpar substituição selecionada',command=self.clear_override).pack(anchor='w')
  self.override_info=ttk.Label(parent,text='',wraplength=950);self.override_info.pack(anchor='w',pady=6);self.update_overrides();self.refresh_fonts()
 def refresh_fonts(self):
  folder=Path(self.fields['fonts_folder'].get()) if self.fields['fonts_folder'].get() else None
  names=sorted({p.stem for p in folder.glob('*') if p.suffix.lower()=='.oft'}) if folder and folder.is_dir() else []
  for box in getattr(self,'font_boxes',[]):box['values']=names
 def choose_font(self,value):
  path=filedialog.askopenfilename(filetypes=[('Fonte OMSI','*.oft')])
  if path:
   value.set(Path(path).stem);self.fields['fonts_folder'].set(str(Path(path).parent));self.refresh_fonts()
 def update_overrides(self):self.override_info.config(text='\n'.join(k+' → '+v for k,v in self.base_overrides.items()) or 'Sem substituições de textura base.')
 def choose_override(self):
  name=self.override_texture.get()
  if not name:raise ValueError('Escolha a textura do modelo primeiro')
  p=filedialog.askopenfilename(title='Imagem substituta no mesmo formato')
  if p:self.base_overrides[name]=p;self.update_overrides()
 def clear_override(self):self.base_overrides.pop(self.override_texture.get(),None);self.update_overrides()
 def tab(self,name):
  frame=ttk.Frame(self.tabs,padding=14);self.tabs.add(frame,text=name);return frame
 def field(self,parent,key,label,browse=None,default=''):
  row=ttk.Frame(parent);row.pack(fill='x',pady=6);ttk.Label(row,text=label,width=31).pack(side='left');v=tk.StringVar(value=default);self.fields[key]=v;ttk.Entry(row,textvariable=v).pack(side='left',fill='x',expand=True)
  if browse:
   def choose():
    p=browse()
    if p:v.set(p)
   ttk.Button(row,text='Escolher',command=choose).pack(side='left',padx=6)
 def guard(self,fn):
  try:fn()
  except Exception as e:messagebox.showerror('Confira os dados',str(e),parent=self.root)
 def import_ready(self):
  from workflow_ui import import_dialog
  def done(path):
   self.fields['converted'].set(str(path));self.status.set('O3D importado: '+str(path))
   from editor import open_editor
   open_editor(self.root,path)
  import_dialog(self.root,done)
 def articulated(self):
  from articulated_ui import open_articulated
  open_articulated(self.root)
 def export_obj(self):
  from obj_export_ui import export_files_dialog
  export_files_dialog(self.root)
 def catalog(self):
  from catalog_ui import show_catalog
  if self.template:
   from vehicle_template import txt
   show_catalog(self.root,profile=self.template['profile'],cfg_sources=[(self.template['source_cfg'],txt(self.template['source_cfg']),Path(self.template['bus']).name)],bus=self.template.get('profile_bus',self.template['bus']))
  else:
   path=filedialog.askopenfilename(parent=self.root,title='CFG para consultar variáveis',filetypes=[('Configuração OMSI','*.cfg')])
   if path:
    from vehicle_template import txt
    show_catalog(self.root,cfg_sources=[(path,txt(path),'')])
 def lights(self):
  from adaptation_ui import light_editor
  light_editor(self.root)
 def script_only(self):
  from adaptation_ui import script_adapter
  script_adapter(self.root)
 def converter(self):
  from app import main
  main(self.root)
 def universal(self,cfg=None):
  from editor import open_editor
  editor=open_editor(self.root,self.fields['converted'].get() or None)
  if editor and cfg:editor.set_output(cfg)
 def load(self):
  cfg=self.fields['cfg'].get()
  if cfg and not Path(cfg).read_bytes().strip():
   self.universal(cfg);return
  profile_bus=self.plan.get('profile_bus') if self.plan and self.template and self.fields['bus'].get()==self.template['bus'] else None
  template=load_template(self.fields['bus'].get(),self.fields['cfg'].get() or None,profile_bus);plan=new_plan(template,self.fields['converted'].get());self.install(template,plan)
 def install(self,template,plan):
  self.template=template;self.plan=plan;self.selected=None
  self.targets=target_parts(plan['converted']) if plan.get('converted') else {}
  for k in ('converted','name','engine','skin_folder','skin_file','fonts_folder'):self.fields[k].set(plan.get(k,''))
  self.fields['cfg'].set(plan.get('reference_cfg',''))
  self.fields['bus'].set(template['bus']);self.targetbox['values']=list(self.targets)
  self.info.config(text=f"Base: {Path(template['bus']).name} · Scripts: {len(template['profile']['selected'].get('[script]',[]))}\n{len(template['pieces'])} peças · {len(template['fonts'])} fontes · {len(template['skins'])} canais de skin\n{template['cfg']}")
  self.markers=json.loads((Path(plan['converted'])/'project.json').read_text(encoding='utf8')).get('markers',[]) if plan.get('converted') else []
  self.marker_box['values']=[m['name'] for m in self.markers];self.marker.set('')
  self.populate_assets();self.refresh()
 def refresh(self):
  if not self.template:return
  self.tree.delete(*self.tree.get_children());query=self.search.get().casefold()
  for p in self.template['pieces']:
   if query in p['mesh'].casefold():self.tree.insert('','end',iid=p['id'],text=p['mesh'],values=(self.plan['mapping'].get(p['id'],{}).get('mode','pending'),))
 def select(self):
  selected=self.tree.selection()
  if not selected:return
  self.selected=next(p for p in self.template['pieces'] if p['id']==selected[0]);m=self.plan['mapping'].get(self.selected['id'],{})
  self.part_title.config(text=self.selected['mesh']);self.mode.set(m.get('mode','pending'));self.target.set(m.get('target',''));self.pivot.set(', '.join(map(str,m['pivot'])) if m.get('pivot') else '');self.confirmed.set(m.get('confirmed',False));self.materials(m.get('materials',{}));self.populate_variables(m.get('variables',{}));self.populate_bones(m.get('bones',{}))
  self.block.delete('1.0','end');self.block.insert('1.0',self.selected['block']);self.status.set('Bloco original para consulta. Clique Aplicar para guardar as alterações da peça.')
 def preview(self):
  if not self.selected:raise ValueError('Selecione uma peça')
  try:
   block=preview_piece(self.selected,self.plan['mapping'].get(self.selected['id'],{}),self.targets)
   if block:
    from skin_cfg import patch_skin
    block=patch_skin(block,self.template,self.plan,self.selected,self.targets)
  except (KeyError,IndexError):raise ValueError('Aplique a associação e preencha todos os materiais antes da prévia')
  self.block.delete('1.0','end');self.block.insert('1.0',block or 'Peça marcada para remoção.')
  self.status.set('Prévia do bloco adaptado. A exportação ainda verifica a montagem completa.')
 def materials(self,maps=None):
  for w in self.material_frame.winfo_children():w.destroy()
  self.material_vars={}
  if not self.selected:return
  slots=self.targets.get(self.target.get(),{}).get('slots_actual',[]);values=[str(s['slot'])+' · '+s['texture']+' #'+str(s['occurrence']) for s in slots]
  for k in self.selected['selectors']:
   row=ttk.Frame(self.material_frame);row.pack(fill='x');ttk.Label(row,text=k,width=28).pack(side='left');v=tk.StringVar();self.material_vars[k]=v
   ttk.Combobox(row,textvariable=v,values=values,state='readonly').pack(side='left',fill='x',expand=True)
   if maps and k in maps and 0<=maps[k]<len(values):v.set(values[maps[k]])
  self.populate_bones({})
 def populate_bones(self,mapping):
  for widget in self.skin_frame.winfo_children():widget.destroy()
  self.bone_vars={}
  if not self.selected:return
  bones=self.targets.get(self.target.get(),{}).get('bones_actual',[])
  values=[p['id']+' — '+p['mesh'] for p in self.template['pieces'] if p['id']!=self.selected['id'] and p.get('lod',0)==0]
  for bone in bones:
   row=ttk.Frame(self.skin_frame);row.pack(fill='x',pady=4);ttk.Label(row,text=bone,width=22).pack(side='left');id=mapping.get(bone,'');v=tk.StringVar(value=next((value for value in values if value.split(' — ',1)[0]==id),''));self.bone_vars[bone]=v;ttk.Combobox(row,textvariable=v,values=['',*values],state='readonly').pack(side='left',fill='x',expand=True)
 def populate_variables(self,mapping):
  for w in self.variable_frame.winfo_children():w.destroy()
  self.variable_vars={}
  values=sorted(set(self.template['profile']['variables']+self.selected['variables']+['brake','throttle','clutch']))
  for old in self.selected['variables']:
   row=ttk.Frame(self.variable_frame);row.pack(fill='x',pady=2);ttk.Label(row,text=old,width=28).pack(side='left');v=tk.StringVar(value=mapping.get(old,old));self.variable_vars[old]=v;ttk.Combobox(row,textvariable=v,values=values).pack(side='left',fill='x',expand=True)
 def association(self):
  if not self.selected:raise ValueError('Selecione uma peça')
  variables={k:v.get().strip() for k,v in self.variable_vars.items() if v.get().strip()!=k}
  pivot=[float(v.strip()) for v in self.pivot.get().split(',')] if self.pivot.get().strip() else None
  return {'mode':self.mode.get(),'target':self.target.get(),'materials':{k:int(v.get().split(' · ')[0]) for k,v in self.material_vars.items() if v.get()},'variables':variables,'bones':{bone:v.get().split(' — ',1)[0] for bone,v in self.bone_vars.items() if v.get()},'pivot':pivot,'confirmed':self.confirmed.get()}
 def apply(self):
  self.plan['mapping'][self.selected['id']]=self.association();self.refresh();self.status.set('Associação aplicada. Salve a montagem para continuar depois.')
 def use_marker(self):
  marker=next((m for m in self.markers if m['name']==self.marker.get()),None)
  if not marker:raise ValueError('Escolha um marcador importado do Blender')
  self.pivot.set(', '.join(map(str,marker['xyz'])));self.status.set('Pivô preenchido. Confira o eixo na prévia antes de aplicar.')
 def preview_animation(self):
  import copy
  from assembly_preview import preview_project
  from animation_preview import open_preview
  if not self.selected:raise ValueError('Selecione uma peça')
  plan=copy.deepcopy(self.plan);plan['mapping'][self.selected['id']]=self.association()
  if plan['mapping'][self.selected['id']]['mode']=='remove':raise ValueError('A peça está marcada para remoção')
  project=preview_project(self.template,plan,self.targets);open_preview(self.root,plan.get('converted') or self.template['root'],project,self.selected['id'])
 def suggest(self):
  if not self.plan:raise ValueError('Carregue uma base e o projeto do modelo novo')
  from vehicle_template import suggest_mappings
  self.plan['mapping'],count=suggest_mappings(self.template,self.targets,self.plan['mapping']);self.refresh()
  self.status.set(str(count)+' associações sugeridas. Revise materiais, pivôs e eixos; nenhuma sugestão foi confirmada automaticamente.')
 def keep_pending(self):
  if not self.plan:return
  for p in self.template['pieces']:
   if self.plan['mapping'].get(p['id'],{}).get('mode','pending')=='pending':self.plan['mapping'][p['id']]={'mode':'keep'}
  self.refresh()
 def sync(self):
  if not self.plan:raise ValueError('Carregue uma variante .bus primeiro')
  if self.fields['cfg'].get()!=self.plan.get('reference_cfg',''):raise ValueError('Recarregue a estrutura após trocar o CFG de exemplo')
  if self.fields['bus'].get()!=self.template['bus'] or self.fields['converted'].get()!=self.plan['converted']:raise ValueError('Recarregue a estrutura após trocar a base ou a pasta convertida')
  for k in ('name','engine','skin_folder','skin_file','fonts_folder'):self.plan[k]=self.fields[k].get()
  if self.plan.get('skin_file'):self.plan['skin_folder']=str(Path(self.plan['skin_file']).parent)
  self.plan['font_map']={k:v.get() for k,v in self.font_vars.items() if v.get()!=k}
  self.plan['skin_targets']={k:v.get() for k,v in self.skin_vars.items() if v.get()}
  self.plan['base_textures']=dict(self.base_overrides)
 def save(self):
  self.sync();p=filedialog.asksaveasfilename(defaultextension='.json',initialfile='montagem.json')
  if p:atomic_text(p,json.dumps(self.plan,ensure_ascii=False,indent=2));self.status.set('Montagem salva: '+p)
 def open(self):
  p=filedialog.askopenfilename(filetypes=[('Montagem','*.json')])
  if p:
   plan=json.loads(Path(p).read_text(encoding='utf8'));self.install(load_template(plan['reference_bus'],plan.get('reference_cfg'),plan.get('profile_bus')),plan)
 def validate(self):
  self.sync();check=scan_plan(self.template,self.plan)
  if not check['errors']:
   try:render_cfg(self.template,self.plan,check)
   except Exception as e:check['errors'].append(str(e))
  self.result.delete('1.0','end');self.result.insert('1.0',json.dumps(check['counts'],ensure_ascii=False)+'\n\n'+('\n'.join('ERRO: '+e for e in check['errors']) or 'Associações verificadas.')+'\n\n'+'\n'.join('REVISAR: '+w for w in check['warnings']));self.tabs.select(self.validation);return check
 def export(self):
  if self.busy:return
  if self.validate()['errors']:raise ValueError('Resolva as pendências antes de exportar')
  dest=filedialog.askdirectory(title='Pasta de saída direta (Vehicles e Fonts serão gravados aqui)')
  if not dest:return
  self.busy=True;self.export_button.config(state='disabled');self.status.set('Montando uma cópia do veículo…')
  plan=json.loads(json.dumps(self.plan));template=self.template
  def worker():
   try:self.jobs.put((True,str(build(template,plan,dest))))
   except Exception as e:self.jobs.put((False,str(e)))
  threading.Thread(target=worker,daemon=True).start()
 def on_destroy(self,event):
  if event.widget==self.root and getattr(self,'poll_job',None):
   self.root.after_cancel(self.poll_job);self.poll_job=None
 def poll(self):
  try:
   ok,result=self.jobs.get_nowait();self.busy=False;self.export_button.config(state='normal');self.status.set(('Pacote criado: ' if ok else 'Falha: ')+result)
   (messagebox.showinfo if ok else messagebox.showerror)('Montagem',result,parent=self.root)
  except queue.Empty:pass
  self.poll_job=self.root.after(200,self.poll)

def main():
 root=tk.Tk();Studio(root);root.mainloop()
if __name__=='__main__':main()
