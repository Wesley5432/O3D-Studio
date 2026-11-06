"""Lightweight wireframe inspection of applied or pending piece animations."""
import math,time,tkinter as tk
from pathlib import Path
from tkinter import ttk
from o3d_binary import scan
from animation_math import matrices,deformed_vertices,origin,transform,identity

class Preview:
 def __init__(self,master,folder,project,selected):
  self.project=project;self.byid={p['id']:p for p in project['parts']};self.part=self.byid[selected];self.infos={};self.edges={};self.points={};self.rest={};self.yaw=35.;self.pitch=25.;self.zoom=1.;self.center=[0,0,0];self.radius=1.;self.running=False;self.timer=None;self.mouse=None
  def load(id):
   if id in self.infos:return
   p=self.byid[id];path=Path(p['preview_source']) if p.get('preview_source') else Path(folder)/'model'/p['file'];info=scan(path.read_bytes(),geometry=True);self.infos[id]=info
   edges=set()
   for tri in info['triangle_data']:
    a,b,c=tri[:3];edges.update(tuple(sorted(e)) for e in ((a,b),(b,c),(c,a)))
   # Preview only: thin the displayed edges on large meshes; exported geometry is unchanged.
   edges=sorted(edges);stride=max(1,math.ceil(len(edges)/6000));edges=edges[::stride]
   used=sorted({i for edge in edges for i in edge});remap={old:new for new,old in enumerate(used)}
   info['vertex_data']=[info['vertex_data'][i] for i in used];info['triangle_data']=[]
   for bone in info.get('bone_data',[]):bone['weights']=[(remap[i],w) for i,w in bone['weights'] if i in remap]
   self.edges[id]=[(remap[a],remap[b]) for a,b in edges]
   self.rest[id]=[[v[0],v[2],v[1]] for v in info['vertex_data']]
   if p.get('parent'):load(p['parent'])
   for target in p.get('skin_bindings',{}).values():
    if target and target!=id:load(target)
  load(selected)
  self.win=tk.Toplevel(master);self.win.title('Prévia de animação — '+self.part['name']);self.win.geometry('1040x760');self.win.minsize(840,600)
  ttk.Label(self.win,text=self.part['name'],style='Title.TLabel').pack(anchor='w',padx=14,pady=(12,4))
  ttk.Label(self.win,text='Arraste para girar a câmera; roda do mouse aproxima. Azul: peça · cinza: repouso/controladores · amarelo: pivô.\nPrévia geométrica simplificada: sem scripts, colisões, amortecimento ou materiais do jogo.',wraplength=980).pack(anchor='w',padx=14)
  notices=sorted({note for id in self.infos for note in self.byid[id].get('preview_notices',[])})
  if notices:ttk.Label(self.win,text='Atenção: '+'; '.join(notices),foreground='#a34800',wraplength=980).pack(anchor='w',padx=14)
  controls=ttk.Frame(self.win,padding=12);controls.pack(fill='x');self.variable=tk.StringVar();self.value=tk.DoubleVar(value=0);self.minimum=tk.StringVar(value='-1');self.maximum=tk.StringVar(value='1');self.ghost=tk.BooleanVar(value=True)
  names=sorted({a['variable'] for id in self.infos for a in self.byid[id].get('animations',[])})
  if names:self.variable.set(names[0])
  ttk.Label(controls,text='Variável').pack(side='left');ttk.Combobox(controls,textvariable=self.variable,values=names,state='readonly',width=26).pack(side='left',padx=6)
  for label,value in [('Mín.',self.minimum),('Máx.',self.maximum)]:ttk.Label(controls,text=label).pack(side='left');ttk.Entry(controls,textvariable=value,width=7).pack(side='left',padx=4)
  ttk.Button(controls,text='Atualizar faixa',command=self.set_range).pack(side='left',padx=5);ttk.Checkbutton(controls,text='Mostrar repouso',variable=self.ghost,command=self.draw).pack(side='left')
  self.slider=ttk.Scale(self.win,from_=-1,to=1,variable=self.value,command=lambda _:self.draw());self.slider.pack(fill='x',padx=16)
  self.canvas=tk.Canvas(self.win,background='#14243a',highlightthickness=0);self.canvas.pack(fill='both',expand=True,padx=14,pady=10)
  self.status=tk.StringVar();ttk.Label(self.win,textvariable=self.status,wraplength=980).pack(anchor='w',padx=14)
  actions=ttk.Frame(self.win,padding=12);actions.pack(fill='x')
  for label,fn in [('Executar / pausar',self.toggle),('Repouso',self.reset),('Enquadrar',self.fit),('Frente',lambda:self.view(0,0)),('Lateral',lambda:self.view(90,0)),('Superior',lambda:self.view(0,90)),('Isométrica',lambda:self.view(35,25))]:ttk.Button(actions,text=label,command=fn).pack(side='left',padx=3)
  self.canvas.bind('<Configure>',lambda e:self.draw());self.canvas.bind('<ButtonPress-1>',lambda e:setattr(self,'mouse',(e.x,e.y)));self.canvas.bind('<B1-Motion>',self.drag);self.canvas.bind('<MouseWheel>',lambda e:self.zoom_by(1.12 if e.delta>0 else 1/1.12));self.canvas.bind('<Button-4>',lambda e:self.zoom_by(1.12));self.canvas.bind('<Button-5>',lambda e:self.zoom_by(1/1.12));self.variable.trace_add('write',lambda *a:self.draw());self.win.protocol('WM_DELETE_WINDOW',self.close);self.fit()
 def close(self):
  self.running=False
  if self.timer:self.win.after_cancel(self.timer)
  self.win.destroy()
 def set_range(self):
  try:
   low,high=float(self.minimum.get()),float(self.maximum.get())
   if not math.isfinite(low+high) or not math.isfinite(high-low) or low>=high:raise ValueError('Faixa exige mínimo menor que máximo')
   self.slider.configure(from_=low,to=high);self.value.set(max(low,min(high,self.value.get())));self.draw()
  except ValueError as e:self.status.set(str(e))
 def toggle(self):
  if self.timer:self.win.after_cancel(self.timer);self.timer=None
  self.running=not self.running
  if self.running:self.started=time.monotonic();self.tick()
 def tick(self):
  self.timer=None
  if not self.running:return
  low=float(self.slider.cget('from'));high=float(self.slider.cget('to'));phase=((time.monotonic()-self.started)/2)%2;self.value.set(low+(high-low)*(phase if phase<1 else 2-phase));self.draw();self.timer=self.win.after(70,self.tick)
 def reset(self):
  self.running=False
  if self.timer:self.win.after_cancel(self.timer);self.timer=None
  self.value.set(0);self.draw()
 def view(self,yaw,pitch):self.yaw=yaw;self.pitch=pitch;self.draw()
 def drag(self,e):
  if self.mouse:self.yaw+=(e.x-self.mouse[0])*.4;self.pitch=max(-90,min(90,self.pitch+(e.y-self.mouse[1])*.4));self.mouse=(e.x,e.y);self.draw()
 def zoom_by(self,factor):self.zoom=max(.03,min(50,self.zoom*factor));self.draw()
 def update_points(self):
  values={self.variable.get():self.value.get()};transforms=matrices(self.project,self.infos,values)
  self.points={id:deformed_vertices(self.byid[id],info,transforms) for id,info in self.infos.items()}
  return transforms
 def fit(self):
  try:self.update_points()
  except ValueError:self.points=dict(self.rest)
  points=self.points.get(self.part['id'],[]) or [[0,0,0]]
  low=[min(p[i] for p in points) for i in range(3)];high=[max(p[i] for p in points) for i in range(3)];self.center=[(a+b)/2 for a,b in zip(low,high)];self.radius=max(.05,max(b-a for a,b in zip(low,high)));self.zoom=1;self.draw()
 def project_point(self,p):
  x,y,z=[p[i]-self.center[i] for i in range(3)];yaw,pitch=math.radians(self.yaw),math.radians(self.pitch);a=x*math.cos(yaw)-y*math.sin(yaw);b=x*math.sin(yaw)+y*math.cos(yaw);height=z*math.cos(pitch)-b*math.sin(pitch);scale=min(max(1,self.canvas.winfo_width()),max(1,self.canvas.winfo_height()))*.7/self.radius*self.zoom
  return (self.canvas.winfo_width()/2+a*scale,self.canvas.winfo_height()/2-height*scale)
 def lines(self,id,points,color):
  coords={i:self.project_point(points[i]) for edge in self.edges[id] for i in edge}
  for a,b in self.edges[id]:self.canvas.create_line(*coords[a],*coords[b],fill=color)
 def draw(self):
  if not hasattr(self,'canvas'):return
  self.canvas.delete('all')
  try:
   transforms=self.update_points()
   if self.ghost.get():self.lines(self.part['id'],self.rest[self.part['id']],'#3c4d65')
   for id,points in self.points.items():self.lines(id,points,'#69baff' if id==self.part['id'] else '#8996a9')
   animations=self.part.get('animations',[])
   frames=[origin(self.part,a,self.infos[self.part['id']]) for a in animations] or [origin(self.part,{},self.infos[self.part['id']])]
   parent=transforms.get(self.part.get('parent'),identity())
   for frame in frames:
    pivot=transform(parent,transform(frame,[0,0,0]));x,y=self.project_point(pivot);self.canvas.create_oval(x-4,y-4,x+4,y+4,fill='#ffd166',outline='');self.canvas.create_text(x+7,y-12,text='Pivô',fill='#ffd166',anchor='w')
    for i,(axis,color) in enumerate(zip('XYZ',('#ff6868','#68d391','#82aaff'))):
     end=[0.,0.,0.];end[i]=self.radius*.3;end=transform(parent,transform(frame,end));xy=self.project_point(end);self.canvas.create_line(x,y,*xy,fill=color,width=2,arrow='last');self.canvas.create_text(*xy,text=axis,fill=color,anchor='sw')
   for light in self.project.get('lights',[]):
    x,y=self.project_point(light['xyz']);self.canvas.create_oval(x-4,y-4,x+4,y+4,outline='#ffe7a0');self.canvas.create_text(x+7,y,text=light.get('name','Luz'),fill='#ffe7a0',anchor='w')
   self.status.set(self.variable.get()+' = '+format(self.value.get(),'.5g')+' · '+str(self.infos[self.part['id']]['vertices'])+' vértices no arquivo · aramado limitado a 6.000 arestas por peça. Outros valores ficam em zero.')
  except Exception as e:self.status.set('Prévia: '+str(e));self.canvas.create_text(25,35,text=str(e),fill='#ffaaaa',anchor='nw',width=800)

def open_preview(master,folder,project,selected):return Preview(master,folder,project,selected)
