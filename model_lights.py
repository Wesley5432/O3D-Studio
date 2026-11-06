"""Project lights in vehicle coordinates (X right, Y forward, Z up)."""
import math

def validate_lights(lights,profile):
 from project import variable_ok,number
 for light in lights:
  if light.get('type') not in {'interiorlight','spotlight'}:raise ValueError('Tipo de luz inválido')
  for field in ('xyz','rgb'):
   if len(light.get(field,[]))!=3:raise ValueError('Luz exige três valores em '+field)
   for value in light[field]:number(value)
  if any(not 0<=float(v)<=255 for v in light['rgb']):raise ValueError('Cor da luz: use RGB de 0 a 255')
  if float(number(light['range']))<=0:raise ValueError('Alcance da luz deve ser positivo')
  if light['type']=='interiorlight':
   if not variable_ok(light.get('variable',''),profile):raise ValueError('Variável da luz não encontrada no perfil: '+light.get('variable',''))
  else:
   direction=light.get('direction',[])
   if len(direction)!=3 or not all(math.isfinite(float(v)) for v in direction) or sum(float(v)**2 for v in direction)<1e-12:raise ValueError('Direção da luz deve ser XYZ não nulo')
   inner=float(number(light['inner']));outer=float(number(light['outer']))
   if not 0<=inner<=outer<180:raise ValueError('Cones da luz: 0 ≤ interno ≤ externo < 180 graus')

def render_lights(lights):
 from project import number
 result=[]
 for light in lights:
  result.append('['+light['type']+']')
  if light['type']=='interiorlight':result.extend([light['variable'],number(light['range']),*map(number,light['rgb']),*map(number,light['xyz'])])
  else:result.extend([*map(number,light['xyz']),*map(number,light['direction']),*map(number,light['rgb']),number(light['range']),number(light['inner']),number(light['outer'])])
  result.append('')
 return result

def light_editor(editor):
 import copy,tkinter as tk
 from tkinter import ttk,messagebox
 from project import number
 win=tk.Toplevel(editor.win);win.title('Luzes e marcadores do Blender');win.geometry('830x660');draft=copy.deepcopy(editor.project.get('lights',[]));selected=[None]
 markers=editor.project.get('markers',[]);fields={}
 ttk.Label(win,text='Coordenadas das luzes',style='Title.TLabel').pack(anchor='w',padx=14,pady=12)
 ttk.Label(win,text='Luz interna usa uma variável. Faróis [spotlight] são selecionados pelo script com Spot_Select.\nMarcadores trazem posição e direção; confira o tipo e a variável antes de aplicar.',wraplength=780).pack(anchor='w',padx=14)
 tree=ttk.Treeview(win,columns=('name','type','xyz'),show='headings',height=5)
 for k,title in [('name','Luz'),('type','Tipo'),('xyz','Coordenadas XYZ')]:tree.heading(k,text=title)
 tree.pack(fill='x',padx=14,pady=8)
 form=ttk.Frame(win,padding=14);form.pack(fill='x')
 specs=[('name','Nome','Luz'),('type','Tipo','interiorlight'),('variable','Variável numérica',''),('xyz','Posição XYZ','0 0 0'),('direction','Direção XYZ (farol)','0 1 0'),('rgb','Cor RGB (0–255)','255 255 255'),('range','Alcance em metros','10'),('inner','Cone interno (graus)','20'),('outer','Cone externo (graus)','40')]
 for i,(key,label,value) in enumerate(specs):
  ttk.Label(form,text=label).grid(row=i,column=0,sticky='w',pady=2);v=tk.StringVar(value=value);fields[key]=v
  widget=ttk.Combobox(form,textvariable=v,values=['interiorlight','spotlight'],state='readonly') if key=='type' else ttk.Entry(form,textvariable=v)
  widget.grid(row=i,column=1,sticky='ew',padx=8)
 form.columnconfigure(1,weight=1)
 marker=tk.StringVar();row=ttk.Frame(win,padding=(14,4));row.pack(fill='x');box=ttk.Combobox(row,textvariable=marker,values=[m['name'] for m in markers],state='readonly');box.pack(side='left',fill='x',expand=True)
 def from_marker():
  m=next((m for m in markers if m['name']==marker.get()),None)
  if m:
   fields['name'].set(m['name']);fields['xyz'].set(' '.join(map(number,m['xyz'])));fields['direction'].set(' '.join(map(number,m['direction'])));fields['variable'].set(m.get('variable',''))
 ttk.Button(row,text='Usar marcador',command=from_marker).pack(side='left',padx=6)
 def refresh():
  tree.delete(*tree.get_children())
  for i,light in enumerate(draft):tree.insert('','end',iid=str(i),values=(light['name'],light['type'],' '.join(map(number,light['xyz']))))
 def select(_=None):
  if not tree.selection():return
  selected[0]=int(tree.selection()[0]);light=draft[selected[0]]
  for key in fields:
   value=light.get(key,'');fields[key].set(' '.join(map(number,value)) if isinstance(value,list) else str(value))
 def apply():
  try:
   light={k:v.get().strip() for k,v in fields.items()}
   for key in ('xyz','direction','rgb'):light[key]=[float(number(x)) for x in light[key].split()]
   for key in ('range','inner','outer'):light[key]=float(number(light[key]))
   profile=copy.deepcopy(editor.project.get('profile') or {});profile['variables']=profile.get('variables',[])+editor.project.get('custom_variables',[]);validate_lights([light],profile)
   if selected[0] is None:draft.append(light)
   else:draft[selected[0]]=light
   editor.remember();editor.project['lights']=copy.deepcopy(draft);refresh();editor.status.set('Luzes aplicadas. Salve o projeto e gere o CFG.');selected[0]=None
  except Exception as e:messagebox.showerror('Luz',str(e),parent=win)
 def remove():
  if selected[0] is not None:
   draft.pop(selected[0]);selected[0]=None;editor.remember();editor.project['lights']=copy.deepcopy(draft);refresh()
 buttons=ttk.Frame(win,padding=14);buttons.pack(fill='x')
 ttk.Button(buttons,text='Nova luz',command=lambda:(selected.__setitem__(0,None),tree.selection_remove(*tree.selection()))).pack(side='left')
 ttk.Button(buttons,text='Aplicar luz ao projeto',style='Accent.TButton',command=apply).pack(side='left',padx=6);ttk.Button(buttons,text='Remover luz',command=remove).pack(side='left');tree.bind('<<TreeviewSelect>>',select);refresh()
