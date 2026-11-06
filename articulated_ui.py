"""Edit the coupled sections of an existing articulated reference vehicle."""
import copy,json,tkinter as tk
from pathlib import Path
from tkinter import ttk,filedialog,messagebox
from articulated import load_chain,new_articulated_plan,check_articulated,export_articulated
from project import atomic_text,number
from ui_components import background

class ArticulatedEditor:
 def __init__(self,master):
  self.win=tk.Toplevel(master);self.win.title('Ônibus articulado · v0.0.2');self.win.geometry('1080x680');self.win.minsize(900,600)
  self.plan=None;self.chain=None;self.selected=None;self.points={};self.point_entries={}
  ttk.Label(self.win,text='Dianteira, reboque e articulação',style='Title.TLabel').pack(anchor='w',padx=16,pady=(14,6))
  ttk.Label(self.win,text='Use uma base articulada pronta. Cada seção conserva seu .bus, CFG, física e vínculos de scripts.',wraplength=950).pack(anchor='w',padx=16)
  bar=ttk.Frame(self.win,padding=12);bar.pack(fill='x')
  for label,fn in [('Selecionar dianteira .bus',self.load),('Abrir projeto',self.open),('Salvar projeto',self.save)]:ttk.Button(bar,text=label,command=lambda f=fn:self.guard(f)).pack(side='left',padx=4)
  self.name=tk.StringVar(value='Meu_articulado');self.engine=tk.StringVar(value='OMSI 2')
  row=ttk.Frame(self.win,padding=(16,5));row.pack(fill='x');ttk.Label(row,text='Nome do veículo').pack(side='left');ttk.Entry(row,textvariable=self.name,width=30).pack(side='left',padx=8);ttk.Combobox(row,textvariable=self.engine,values=['OMSI 2','openOMSI'],state='readonly',width=16).pack(side='left')
  self.table=ttk.Treeview(self.win,columns=('bus','cfg','scripts','assembly'),show='headings',height=7,selectmode='browse')
  for key,title,width in [('bus','Seção / arquivo .bus',230),('cfg','CFG da seção',280),('scripts','Scripts',200),('assembly','Modelo',130)]:self.table.heading(key,text=title);self.table.column(key,width=width)
  self.table.pack(fill='both',expand=True,padx=16,pady=8);self.table.bind('<<TreeviewSelect>>',lambda e:self.guard(self.select))
  edit=ttk.LabelFrame(self.win,text='Engates da seção selecionada · coordenadas locais em metros',padding=12);edit.pack(fill='x',padx=16,pady=8)
  for row,side,label in [(0,'front','Engate dianteiro'),(1,'back','Engate traseiro')]:
   ttk.Label(edit,text=label,width=22).grid(row=row,column=0,sticky='w');self.points[side]=[];self.point_entries[side]=[]
   for column,axis in enumerate('XYZ'):
    ttk.Label(edit,text=axis).grid(row=row,column=1+column*2,padx=4);v=tk.StringVar();self.points[side].append(v);entry=ttk.Entry(edit,textvariable=v,width=16);entry.grid(row=row,column=2+column*2,padx=4,pady=4);self.point_entries[side].append(entry)
  ttk.Button(edit,text='Aplicar engates',command=lambda:self.guard(self.apply_points)).grid(row=0,column=7,rowspan=2,padx=12)
  actions=ttk.Frame(self.win,padding=(16,6));actions.pack(fill='x')
  for label,fn in [('Editar peças desta seção',self.edit_section),('Manter modelo original',self.clear_section),('Consultar variáveis',self.catalog)]:ttk.Button(actions,text=label,command=lambda f=fn:self.guard(f)).pack(side='left',padx=(0,6))
  self.status=tk.StringVar(value='Escolha o .bus da dianteira. O programa encontra os reboques pelo [couple_back].')
  ttk.Label(self.win,textvariable=self.status,wraplength=1000).pack(fill='x',padx=16,pady=8)
  ttk.Label(self.win,text='A sanfona precisa de malha/ossos adequados. Esta montagem preserva a base; não cria automaticamente rig, física ou passagens de passageiros.',wraplength=1000,style='Muted.TLabel').pack(anchor='w',padx=16)
  ttk.Button(self.win,text='Validar e exportar articulado',style='Accent.TButton',command=lambda:self.guard(self.export)).pack(anchor='e',padx=16,pady=14)
 def guard(self,fn):
  try:fn()
  except Exception as e:messagebox.showerror('Articulado',str(e),parent=self.win)
 def install(self,plan):
  self.chain=load_chain(plan['head']);self.plan=plan;self.selected=None;self.name.set(plan['name']);self.engine.set(plan.get('engine','OMSI 2'));self.refresh();self.table.selection_set('0')
 def refresh(self):
  self.table.delete(*self.table.get_children())
  for i,s in enumerate(self.chain['sections']):
   self.table.insert('','end',iid=str(i),values=(('Dianteira · ' if i==0 else 'Reboque '+str(i)+' · ')+s['key'],Path(s['cfg']).name,'Compartilhados' if s['scriptshare'] else 'Próprios','Montagem aplicada' if s['key'] in self.plan['section_plans'] else 'Original'))
 def load(self):
  path=filedialog.askopenfilename(parent=self.win,title='Ônibus articulado — arquivo da dianteira',filetypes=[('Ônibus OMSI','*.bus')])
  if path:self.install(new_articulated_plan(path));self.status.set(str(len(self.chain['sections']))+' seções carregadas. Seções sem montagem mantêm as peças da base.')
 def open(self):
  path=filedialog.askopenfilename(parent=self.win,filetypes=[('Projeto de articulado','*.json')])
  if path:
   plan=json.loads(Path(path).read_text(encoding='utf8'));check_articulated(plan);self.install(plan)
 def sync(self):
  if not self.plan:raise ValueError('Carregue uma base articulada')
  self.apply_points();self.plan['name']=self.name.get().strip();self.plan['engine']=self.engine.get()
 def save(self):
  self.sync();path=filedialog.asksaveasfilename(parent=self.win,initialfile='articulado.json',defaultextension='.json',filetypes=[('Projeto articulado','*.json')])
  if path:atomic_text(path,json.dumps(self.plan,ensure_ascii=False,indent=2));self.status.set('Projeto salvo: '+path)
 def select(self):
  sel=self.table.selection()
  if not sel:return
  next_section=self.chain['sections'][int(sel[0])]
  if self.selected and self.selected['key']!=next_section['key']:
   try:self.apply_points()
   except Exception:
    old=self.chain['sections'].index(self.selected);self.table.selection_set(str(old));raise
  self.selected=next_section;s=self.selected;values={**s['points'],**self.plan['points'].get(s['key'],{})}
  for side in self.points:
   for i,(v,entry) in enumerate(zip(self.points[side],self.point_entries[side])):
    v.set(number(values[side][i]) if side in values else '');entry.config(state='normal' if side in values else 'disabled')
  self.status.set(s['key']+' · CFG: '+s['cfg']+' · Perfil: '+Path(s['profile_bus']).name)
 def apply_points(self):
  if not self.selected:return
  data={side:[float(number(v.get().strip())) for v in self.points[side]] for side in self.selected['points']}
  self.plan['points'][self.selected['key']]=data
 def edit_section(self):
  if not self.selected:raise ValueError('Selecione uma seção')
  self.sync();s=copy.deepcopy(self.selected)
  from studio import Studio
  from vehicle_template import load_template,new_plan
  p=copy.deepcopy(self.plan['section_plans'].get(s['key']))
  t=load_template(s['bus'],p.get('reference_cfg') if p else None,s['profile_bus'])
  if not p:p=new_plan(t,'')
  p['name']=self.name.get();p['profile_bus']=s['profile_bus']
  top=tk.Toplevel(self.win);child=Studio(top);child.install(t,p)
  def commit():
   if not self.chain or s not in self.chain['sections']:raise ValueError('A base articulada mudou; reabra a edição desta seção')
   if child.template['bus']!=s['bus']:raise ValueError('A montagem precisa continuar usando o .bus desta seção')
   if child.validate()['errors']:raise ValueError('Resolva as pendências da seção antes de aplicar')
   self.plan['section_plans'][s['key']]=copy.deepcopy(child.plan);self.selected=None;self.refresh();self.table.selection_set(str(self.chain['sections'].index(s)));top.destroy();self.status.set('Montagem aplicada a '+s['key']+'. Exporte o conjunto nesta janela.')
  ttk.Button(top,text='Aplicar esta montagem ao articulado',style='Accent.TButton',command=lambda:self.guard(commit)).pack(fill='x',padx=18,pady=8)
 def clear_section(self):
  if not self.selected:return
  i=self.chain['sections'].index(self.selected);self.plan['section_plans'].pop(self.selected['key'],None);self.refresh();self.table.selection_set(str(i))
 def catalog(self):
  if not self.plan:raise ValueError('Carregue uma base')
  from catalog_ui import show_catalog
  from project import load_profile
  show_catalog(self.win,profile=load_profile(self.plan['head']),bus=self.plan['head'])
 def export(self):
  self.sync();check_articulated(self.plan)
  dest=filedialog.askdirectory(parent=self.win,title='Saída do articulado (Vehicles será gravado aqui)')
  if dest:
   snapshot=copy.deepcopy(self.plan);background(self.win,'Exportando articulado',lambda:export_articulated(snapshot,dest))

def open_articulated(master):return ArticulatedEditor(master)
