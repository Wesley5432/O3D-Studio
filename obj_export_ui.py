"""Static OBJ export from selected O3D files or an existing project."""
from pathlib import Path
from tkinter import filedialog,messagebox
from ui_components import background

def done(master,result):
 text=str(len(result['files']))+' modelos OBJ exportados com MTL.\n'+result['note']
 if result['warnings']:text+='\n\n'+'\n'.join(result['warnings'][:8])+'\nConfira relatorio_obj.json.'
 messagebox.showinfo('Exportação OBJ',text,parent=master)

def export_files_dialog(master):
 from asset_paths import clean_name
 from obj_export import export_obj
 paths=filedialog.askopenfilenames(parent=master,title='Selecione um ou vários modelos O3D',filetypes=[('Modelos OMSI','*.o3d')])
 if not paths:return
 texture=filedialog.askdirectory(parent=master,title='Pasta das texturas (Cancelar exporta somente geometria e materiais)')
 destination=filedialog.askdirectory(parent=master,title='Pasta de saída dos arquivos OBJ e MTL')
 if not destination:return
 names=set();sources=[]
 for value in paths:
  name=clean_name(Path(value).stem);candidate=name;count=2
  while candidate.casefold() in names:candidate=name+'_'+str(count);count+=1
  names.add(candidate.casefold());sources.append((value,candidate+'.obj'))
 background(master,'Exportando O3D para OBJ',lambda:export_obj(sources,destination,[texture] if texture else []),lambda result:done(master,result))
