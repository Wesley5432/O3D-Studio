"""Controls for existing CFG lights and explicit donor reference mappings."""
import tkinter as tk,tempfile
from tkinter import ttk,filedialog,messagebox
from pathlib import Path
from vehicle_template import txt
from cfg_adaptation import lights,move_light
from output_files import publish
from project import load_profile
from script_transfer import compatibility,swap_scripts

def light_editor(master):
 win=tk.Toplevel(master);win.title('Coordenadas das luzes — CFG existente');win.geometry('820x600')
 state={'text':'','path':None,'lights':[]};label=tk.StringVar(value='Abra o CFG usado pelo veículo no jogo.')
 ttk.Label(win,textvariable=label,wraplength=780).pack(fill='x',padx=12,pady=8)
 tree=ttk.Treeview(win,columns=('type','xyz'),show='headings');tree.heading('type',text='Tipo de luz');tree.heading('xyz',text='Coordenadas XYZ');tree.pack(fill='both',expand=True,padx=12)
 row=ttk.Frame(win,padding=12);row.pack(fill='x');values=[]
 for axis in 'XYZ':
  ttk.Label(row,text=axis).pack(side='left');v=tk.StringVar();values.append(v);ttk.Entry(row,textvariable=v,width=15).pack(side='left',padx=5)
 def guard(fn):
  try:fn()
  except Exception as e:messagebox.showerror('Não foi possível aplicar',str(e),parent=win)
 def refresh():
  state['lights']=lights(state['text']);tree.delete(*tree.get_children())
  for light in state['lights']:tree.insert('','end',iid=str(light['command']),values=(light['type'],', '.join(map(str,light['xyz']))))
 def select(event=None):
  if not tree.selection():return
  light=next(x for x in state['lights'] if str(x['command'])==tree.selection()[0])
  for v,x in zip(values,light['xyz']):v.set(str(x))
 tree.bind('<<TreeviewSelect>>',select)
 def open_cfg():
  path=filedialog.askopenfilename(parent=win,filetypes=[('Modelo CFG','*.cfg')])
  if not path:return
  text=txt(path);lights(text);state.update(text=text,path=Path(path));refresh();label.set(path)
 def apply():
  if not tree.selection():raise ValueError('Selecione uma luz')
  command=int(tree.selection()[0]);state['text']=move_light(state['text'],command,[float(v.get()) for v in values]);refresh();tree.selection_set(str(command));label.set('Coordenadas aplicadas em memória. Salve o CFG para testar no jogo.')
 def save():
  if not state['path']:raise ValueError('Abra um CFG primeiro')
  path=filedialog.asksaveasfilename(parent=win,initialdir=state['path'].parent,initialfile=state['path'].name,defaultextension='.cfg',filetypes=[('Modelo CFG','*.cfg')])
  if not path:return
  path=Path(path)
  with tempfile.TemporaryDirectory() as temp:
   stage=Path(temp);(stage/path.name).write_bytes(state['text'].replace('\n','\r\n').encode('cp1252'));publish(stage,path.parent)
  label.set('CFG salvo com backup quando havia arquivo anterior: '+str(path))
 actions=ttk.Frame(win,padding=12);actions.pack(fill='x')
 for title,fn in [('Abrir CFG',open_cfg),('Aplicar XYZ',apply),('Salvar CFG',save)]:ttk.Button(actions,text=title,command=lambda f=fn:guard(f)).pack(side='left',padx=5)
 ttk.Label(win,text='Edita spotlight, light_enh_2 e interiorlight já existentes. Coordenadas do CFG; sem prévia 3D.\nNão cria luzes ausentes. Aplique XYZ antes de salvar.',wraplength=780).pack(pady=8)
 return win

def script_adapter(master):
 win=tk.Toplevel(master);win.title('Adaptar referências ao doador de scripts');win.geometry('920x720');fields={};bindings={};signature=[None]
 def guard(fn):
  try:fn()
  except Exception as e:messagebox.showerror('Adaptação',str(e),parent=win)
 for key,label in [('target','Veículo que recebe (.bus)'),('donor','Doador (.bus)'),('destination','Saída direta da cópia')]:
  row=ttk.Frame(win,padding=8);row.pack(fill='x');ttk.Label(row,text=label,width=28).pack(side='left');v=tk.StringVar();fields[key]=v;ttk.Entry(row,textvariable=v).pack(side='left',fill='x',expand=True)
  def browse(k=key,value=v):
   path=filedialog.askdirectory(parent=win) if k=='destination' else filedialog.askopenfilename(parent=win,filetypes=[('Veículo','*.bus')])
   if path:value.set(path)
  ttk.Button(row,text='Escolher',command=browse).pack(side='left',padx=5)
 ttk.Label(win,text='Associe nomes ausentes a funções equivalentes do doador. A seleção não transforma a lógica dos scripts.',wraplength=880).pack(padx=12,pady=8)
 canvas=tk.Canvas(win,highlightthickness=0);canvas.pack(fill='both',expand=True,padx=12);scroll=ttk.Scrollbar(canvas,orient='vertical',command=canvas.yview);scroll.pack(side='right',fill='y');canvas.configure(yscrollcommand=scroll.set);rows=ttk.Frame(canvas);item=canvas.create_window((0,0),window=rows,anchor='nw');rows.bind('<Configure>',lambda e:canvas.configure(scrollregion=canvas.bbox('all')));canvas.bind('<Configure>',lambda e:canvas.itemconfigure(item,width=e.width-20))
 status=tk.StringVar(value='Carregue as incompatibilidades para escolher os vínculos.');ttk.Label(win,textvariable=status,wraplength=880).pack(padx=12,pady=10)
 def load():
  target=fields['target'].get();donor=fields['donor'].get();check=compatibility(target,donor);profile=load_profile(donor)
  for child in rows.winfo_children():child.destroy()
  bindings.clear();signature[0]=(target,donor)
  for category,key,options in [('numeric','missing_variables',profile['variables']),('strings','missing_strings',profile['string_variables']),('events','missing_events',sorted({t[:-5] if t.endswith('_drag') else t[:-4] if t.endswith('_off') else t for t in profile['triggers']}))]:
   for old in check[key]:
    row=ttk.Frame(rows,padding=4);row.pack(fill='x');ttk.Label(row,text=category+' · '+old,width=42).pack(side='left');v=tk.StringVar();bindings[(category,old)]=v;ttk.Combobox(row,textvariable=v,values=sorted(options)).pack(side='left',fill='x',expand=True)
  status.set(str(len(bindings))+' referências ausentes. Preencha as equivalências e verifique novamente.')
 def mapping():
  if signature[0]!=(fields['target'].get(),fields['donor'].get()):raise ValueError('Recarregue as incompatibilidades após trocar os veículos')
  result={'numeric':{},'strings':{},'events':{}}
  for (category,old),v in bindings.items():
   if v.get().strip():result[category][old]=v.get().strip()
  return result
 def verify():
  check=compatibility(fields['target'].get(),fields['donor'].get(),mapping());missing=sum(len(check[k]) for k in ('missing_variables','missing_strings','missing_events'));status.set(str(missing)+' referências ainda ausentes. '+check['note']);return check
 def export():
  check=verify()
  if not check['compatible_references']:raise ValueError('Resolva as referências ausentes')
  if not fields['destination'].get():raise ValueError('Escolha a pasta de saída')
  out=swap_scripts(fields['target'].get(),fields['donor'].get(),fields['destination'].get(),mapping());status.set('Cópia adaptada em '+str(out)+'. Teste no jogo; lógica não simulada.')
 actions=ttk.Frame(win,padding=12);actions.pack(fill='x')
 for title,fn in [('Ler incompatibilidades',load),('Verificar vínculos',verify),('Exportar cópia adaptada',export)]:ttk.Button(actions,text=title,command=lambda f=fn:guard(f)).pack(side='left',padx=5)
 return win
