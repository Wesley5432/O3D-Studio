"""Explicit desktop workflows for existing O3D and script-only replacement."""
import json,queue,threading,tkinter as tk
from tkinter import ttk,filedialog,messagebox
from pathlib import Path

def dialog(master,title,fields,actions):
 win=tk.Toplevel(master);win.title(title);win.geometry('850x540');values={};jobs=queue.Queue();buttons=[]
 for key,label,kind in fields:
  row=ttk.Frame(win,padding=8);row.pack(fill='x');ttk.Label(row,text=label,width=27).pack(side='left');value=tk.StringVar();values[key]=value;ttk.Entry(row,textvariable=value).pack(side='left',fill='x',expand=True)
  def browse(v=value,k=kind):
   path=filedialog.askdirectory(parent=win) if k=='folder' else filedialog.askopenfilename(parent=win,filetypes=[('Veículo OMSI','*.bus')])
   if path:v.set(path)
  ttk.Button(row,text='Escolher',command=browse).pack(side='left',padx=5)
 output=tk.Text(win,wrap='word',height=12);output.pack(fill='both',expand=True,padx=10,pady=8)
 def start(fn,callback):
  data={k:v.get().strip() for k,v in values.items()}
  for b in buttons:b.config(state='disabled')
  output.delete('1.0','end');output.insert('1.0','Processando…')
  def worker():
   try:jobs.put((True,fn(data),callback))
   except Exception as exc:jobs.put((False,str(exc),None))
  threading.Thread(target=worker,daemon=True).start()
 row=ttk.Frame(win,padding=10);row.pack(fill='x')
 for label,fn,callback in actions:
  button=ttk.Button(row,text=label,command=lambda f=fn,c=callback:start(f,c));button.pack(side='left',padx=4);buttons.append(button)
 def poll():
  try:
   ok,result,callback=jobs.get_nowait()
   for b in buttons:b.config(state='normal')
   output.delete('1.0','end')
   if isinstance(result,dict) and 'compatible_references' in result:
    summary=('Referências verificadas: sem incompatibilidades detectadas.' if result['compatible_references'] else 'Troca bloqueada: faltam referências nos scripts doadores.')
    for key,label in [('missing_variables','Variáveis numéricas'),('missing_strings','Variáveis de texto'),('missing_events','Eventos')]:
     if result[key]:summary+='\n'+label+': '+', '.join(result[key])
    summary+='\nArquivos de dependências: '+str(result['dependency_files'])+'\n\n'+result['note']
   else:summary=json.dumps(result,ensure_ascii=False,indent=2) if isinstance(result,dict) else str(result)
   output.insert('1.0',summary)
   if ok and callback:callback(result)
  except queue.Empty:pass
  win.after(200,poll)
 win.after(200,poll);return win

def import_dialog(master,on_created):
 from existing_o3d import import_o3d
 def work(d):
  if not d['source'] or not d['destination']:raise ValueError('Escolha entrada e saída')
  return import_o3d(d['source'],d['destination'],d['textures'] or None)
 return dialog(master,'Usar O3D pronto — sem Blender', [('source','Pasta com O3D','folder'),('textures','Texturas (opcional)','folder'),('destination','Pasta de saída','folder')],[('Criar projeto e model.cfg',work,on_created)])

def scripts_dialog(master):
 from script_transfer import compatibility,swap_scripts
 def check(d):
  if not d['target'] or not d['donor']:raise ValueError('Selecione o veículo de destino e o doador de scripts')
  return compatibility(d['target'],d['donor'])
 def build(d):
  check(d)
  if not d['destination']:raise ValueError('Escolha a pasta para a cópia')
  return swap_scripts(d['target'],d['donor'],d['destination'])
 return dialog(master,'Trocar somente scripts — gera uma cópia do veículo',[('target','Ônibus que recebe (.bus)','bus'),('donor','Doador dos scripts (.bus)','bus'),('destination','Saída da cópia','folder')],[('Verificar referências do CFG',check,None),('Criar cópia com novos scripts',build,None)])
