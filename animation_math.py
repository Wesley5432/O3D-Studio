"""Numerical static preview, independent of Tk/Blender. No OMSI script interpreter."""
import math

def identity():return [[float(i==j) for j in range(4)] for i in range(4)]
def multiply(a,b):return [[sum(a[i][k]*b[k][j] for k in range(4)) for j in range(4)] for i in range(4)]
def transform(m,p):return [sum(m[i][j]*p[j] for j in range(3))+m[i][3] for i in range(3)]
def translation(xyz):
 m=identity()
 for i,v in enumerate(xyz):m[i][3]=float(v)
 return m
def rotation(axis,degrees):
 m=identity();a=math.radians(degrees);c=math.cos(a);s=math.sin(a);i,j={'x':(1,2),'y':(2,0),'z':(0,1)}[axis]
 m[i][i]=c;m[j][j]=c;m[i][j]=-s;m[j][i]=s;return m
def inverse(m):
 rows=[list(row)+eye for row,eye in zip(m,identity())]
 for col in range(4):
  pivot=max(range(col,4),key=lambda r:abs(rows[r][col]))
  if abs(rows[pivot][col])<1e-10:raise ValueError('Matriz de origem singular; configure o pivô XYZ explicitamente')
  rows[col],rows[pivot]=rows[pivot],rows[col];scale=rows[col][col];rows[col]=[x/scale for x in rows[col]]
  for r in range(4):
   if r!=col:
    factor=rows[r][col];rows[r]=[a-factor*b for a,b in zip(rows[r],rows[col])]
 return [r[4:] for r in rows]

def mesh_origin(raw):
 if not raw:return identity()
 if len(raw)!=16 or not all(math.isfinite(x) for x in raw):raise ValueError('Matriz de origem O3D inválida')
 # Convert both world and local bases from D3D Y-up to vehicle Z-up.
 basis=[0,2,1,3];return [[raw[basis[j]*4+basis[i]] for j in range(4)] for i in range(4)]

def origin(part,animation,info):
 if 'origin_steps' in animation:
  m=identity()
  for command,value in animation['origin_steps']:
   if command=='origin_from_mesh':m=mesh_origin(info.get('matrix'))
   elif command=='origin_trans':
    for i,v in enumerate(value):m[i][3]=float(v)
   elif command.startswith('origin_rot_'):m=multiply(m,rotation(command[-1],-float(value)))
  return m
 m=translation(part['pivot']) if part.get('pivot') is not None else mesh_origin(info.get('matrix'))
 for axis,degrees in zip('xyz',animation.get('origin_rotation',[0,0,0])):m=multiply(m,rotation(axis,-float(degrees)))
 return m

def piece_matrix(part,info,values):
 result=identity()
 for animation in part.get('animations',[]):
  if animation['type'] not in {'rot','trans'}:raise ValueError('Tipo de animação inválido')
  value=float(values.get(animation['variable'],0))*float(animation['factor'])
  if not math.isfinite(value):raise ValueError('Valor de animação não finito')
  o=origin(part,animation,info);motion=rotation('x',-value) if animation['type']=='rot' else translation([value,0,0])
  result=multiply(multiply(multiply(o,motion),inverse(o)),result)
 return result

def matrices(project,infos,values):
 byid={p['id']:p for p in project['parts']};result={};visiting=set()
 def visit(id):
  if id in result:return result[id]
  if id in visiting:raise ValueError('Ciclo na hierarquia da prévia')
  if id not in byid or id not in infos:raise ValueError('Peça/controlador ausente: '+id)
  visiting.add(id);p=byid[id];m=piece_matrix(p,infos[id],values)
  if p.get('parent'):m=multiply(visit(p['parent']),m)
  visiting.remove(id);result[id]=m;return m
 for id in infos:visit(id)
 return result

def deformed_vertices(part,info,transforms):
 vertices=[[v[0],v[2],v[1]] for v in info['vertex_data']];bones=info.get('bone_data',[])
 if bones:
  out=[[0.,0.,0.] for _ in vertices];totals=[0.]*len(vertices)
  for bone in bones:
   target=part.get('skin_bindings',{}).get(bone['name'])
   if target not in transforms:raise ValueError('Associe o grupo '+bone['name']+' a uma peça na aba Deformação')
   for index,weight in bone['weights']:
    moved=transform(transforms[target],vertices[index]);totals[index]+=weight
    for axis in range(3):out[index][axis]+=moved[axis]*weight
  if any(abs(total-1)>1e-3 for total in totals):raise ValueError('Os pesos de cada vértice precisam somar 1 para a prévia smoothskin')
  vertices=out
 return [transform(transforms[part['id']],v) for v in vertices]
