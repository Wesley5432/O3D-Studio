"""Searchable variable/event catalog with exact CFG context and source locations."""
import tkinter as tk
from tkinter import ttk,filedialog,messagebox
from pathlib import Path
from variable_catalog import build_catalog,bus_sources
from vehicle_template import txt

LABELS={'numeric':'Numérica','strings':'Texto','events':'Evento'}

def project_source(project):
 from model_lights import render_lights
 lines=render_lights(project.get('lights',[]))
 for p in project.get('parts',[]):
  lines.extend(['[mesh]',p['file']])
  if p.get('mouseevent'):lines.extend(['[mouseevent]',p['mouseevent']])
  if p.get('visible'):lines.extend(['[visible]',p['visible']['variable'],str(p['visible']['value'])])
  for a in p.get('animations',[]):
   lines.extend(['[newanim]'])
   if p.get('pivot') is None:lines.append('origin_from_mesh')
   else:lines.extend(['origin_trans',*map(str,p['pivot'])])
   for axis,value in zip('xyz',a.get('origin_rotation',[0,0,0])):lines.extend(['origin_rot_'+axis,str(value)])
   lines.extend(['anim_'+a['type'],a['variable'],str(a['factor'])])
  for r in p.get('material_rules',[]):
   if r.get('variable'):lines.extend(['[matl_change]',p['materials'][r['slot']]['texture'],str(p['materials'][r['slot']]['occurrence']),r['variable']])
 return ('Projeto aplicado (em memória)','\n'.join(lines),'Projeto atual')

def show_catalog(master,profile=None,cfg_sources=(),manual=(),bus=None,project=None,on_use=None,on_manual=None):
 win=tk.Toplevel(master);win.title('Variáveis, eventos e usos no CFG');win.geometry('1080x720');win.minsize(880,600)
 sources=list(cfg_sources);scripts=[];warnings=[]
 if project is not None:sources.insert(0,project_source(project))
 if bus:
  try:extra,scripts,warnings=bus_sources(bus);sources.extend(extra)
  except Exception as e:warnings.append(str(e))
 elif (profile or {}).get('references_only'):
  for path in profile.get('selected',{}).get('[script]',[]):
   try:scripts.append((path,txt(path)))
   except Exception as e:warnings.append(str(e))
 rows=[];cache=[];manual=list(manual)
 ttk.Label(win,text='Entenda a função pelo uso no CFG',style='Title.TLabel').pack(anchor='w',padx=16,pady=(14,6))
 ttk.Label(win,text='Selecione um nome para ver peça, tipo, fator, arquivo e linha. Scripts são consultados sem execução.',wraplength=950).pack(anchor='w',padx=16)
 bar=ttk.Frame(win,padding=12);bar.pack(fill='x');search=tk.StringVar();kind=tk.StringVar(value='Todos');only_cfg=tk.BooleanVar(value=False)
 ttk.Entry(bar,textvariable=search).pack(side='left',fill='x',expand=True,padx=(0,8));ttk.Combobox(bar,textvariable=kind,values=['Todos',*LABELS.values()],state='readonly',width=12).pack(side='left')
 ttk.Checkbutton(bar,text='Com uso no CFG',variable=only_cfg).pack(side='left',padx=8)
 pane=ttk.Panedwindow(win,orient='vertical');pane.pack(fill='both',expand=True,padx=12)
 upper=ttk.Frame(pane);lower=ttk.Frame(pane);pane.add(upper,weight=2);pane.add(lower,weight=2)
 table=ttk.Treeview(upper,columns=('name','kind','use'),show='headings',selectmode='browse')
 for k,title,width in [('name','Nome exato',280),('kind','Tipo',90),('use','Uso encontrado',580)]:table.heading(k,text=title);table.column(k,width=width)
 scroll=ttk.Scrollbar(upper,orient='vertical',command=table.yview);table.configure(yscrollcommand=scroll.set);scroll.pack(side='right',fill='y');table.pack(fill='both',expand=True)
 details=tk.Text(lower,wrap='word',padx=12,pady=12,height=12);details.pack(side='left',fill='both',expand=True);ds=ttk.Scrollbar(lower,command=details.yview);ds.pack(side='right',fill='y');details.config(yscrollcommand=ds.set,state='disabled')
 status=tk.StringVar();ttk.Label(win,textvariable=status,wraplength=1000).pack(anchor='w',padx=12,pady=5)
 def refresh(*_):
  table.delete(*table.get_children());q=search.get().casefold()
  for i,row in enumerate(rows):
   if kind.get()!='Todos' and LABELS[row['kind']]!=kind.get():continue
   if only_cfg.get() and not any(u['mesh']!='(script)' for u in row['usages']):continue
   if q not in cache[i]:continue
   table.insert('','end',iid=str(i),values=(row['name'],LABELS[row['kind']],row['summary']))
  status.set(str(len(table.get_children()))+' de '+str(len(rows))+' nomes. '+(' | '.join(warnings[:3]) if warnings else 'A descrição informa o uso observado; não certifica a lógica do script.'))
 def rebuild():
  nonlocal rows,cache
  rows=build_catalog(sources,profile,manual,scripts)
  cache=[' '.join([r['name'],r['summary'],*[str(u[k]) for u in r['usages'] for k in ('mesh','source','section','description')]]).casefold() for r in rows];refresh()
 def select(_=None):
  selection=table.selection()
  if not selection:return
  r=rows[int(selection[0])];text=r['name']+' — '+LABELS[r['kind']]+'\nOrigem: '+(', '.join(r['origins']) or 'Referência encontrada; declaração não verificada')+'\n\n'
  if not r['usages']:text+=r['summary']
  for u in r['usages']:
   text+=u['role']+' · '+u['mesh']+'\n'+u['description']+'\n'+u['source']+':'+str(u['line'])+(' · Seção '+u['section'] if u['section'] else '')+'\n'+u['excerpt']+'\n\n'
  details.configure(state='normal');details.delete('1.0','end');details.insert('1.0',text);details.configure(state='disabled')
 def choose_cfg():
  path=filedialog.askopenfilename(parent=win,filetypes=[('Configuração OMSI','*.cfg')])
  if path:
   try:sources.append((path,txt(path),Path(path).name));rebuild()
   except Exception as e:messagebox.showerror('Ler CFG',str(e),parent=win)
 def use(destination):
  selection=table.selection()
  if not selection:return
  try:on_use(rows[int(selection[0])],destination)
  except Exception as e:messagebox.showerror('Usar referência',str(e),parent=win)
 def add():
  name=on_manual()
  if name:manual.append(name);rebuild()
 buttons=ttk.Frame(win,padding=12);buttons.pack(fill='x')
 ttk.Button(buttons,text='Ler outro CFG',command=choose_cfg).pack(side='left',padx=3)
 if on_use:
  for label,destination in [('Usar na animação','anim'),('Visibilidade','visible'),('Iluminação','light'),('Evento','event')]:ttk.Button(buttons,text=label,command=lambda d=destination:use(d)).pack(side='left',padx=3)
 if on_manual:ttk.Button(buttons,text='Variável manual',command=add).pack(side='left',padx=3)
 search.trace_add('write',refresh);kind.trace_add('write',refresh);only_cfg.trace_add('write',refresh);table.bind('<<TreeviewSelect>>',select);rebuild()
 return win
