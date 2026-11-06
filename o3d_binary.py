"""Read O3D structure and change material names without reserializing geometry."""
import struct
from pathlib import Path

def scan(data,geometry=False):
 p=0;spans=[];textures=[];matrix=None;vertices=[];triangles=[];materials=[];bones=0;bone_names=[];bone_data=[];seen=set()
 def take(fmt):
  nonlocal p
  size=struct.calcsize('<'+fmt)
  if p+size>len(data):raise ValueError('O3D truncado')
  v=struct.unpack_from('<'+fmt,data,p);p+=size;return v
 def skip(n):
  nonlocal p
  if n<0 or p+n>len(data):raise ValueError('O3D truncado')
  p+=n
 def string(material=False):
  start=p;n,=take('B');raw,=take(str(n)+'s');value=raw.decode('cp1252')
  if material:spans.append((start,p,value));textures.append(value)
  return value
 sig,version=take('2sB')
 if sig!=b'\x84\x19' or version not in {1,3,4,5,6,7}:raise ValueError('O3D não suportado')
 flags=take('B')[0] if version>1 else 0
 if flags & ~3:raise ValueError('Flags O3D desconhecidas')
 key=take('I')[0] if version>=4 else None
 if key not in {None,0xffffffff}:raise ValueError('O3D protegido: não será alterado')
 counts={}
 while p<len(data):
  tag,=take('B')
  if tag in seen:raise ValueError('Registro O3D duplicado: '+hex(tag))
  seen.add(tag)
  if tag==0x17:
   count,=take('I' if version>1 else 'H');counts['vertices']=count;start=p;skip(count*32)
   if geometry:vertices=list(struct.iter_unpack('<8f',memoryview(data)[start:p]))
  elif tag==0x49:
   count,=take('I' if version>1 else 'H');counts['triangles']=count;start=p;skip(count*(14 if flags&1 else 8))
   if geometry:triangles=list(struct.iter_unpack('<3IH' if flags&1 else '<4H',memoryview(data)[start:p]))
  elif tag==0x26:
   count,=take('H')
   for _ in range(count):
    values=take('11f');name=string(True)
    if geometry:materials.append({'values':values,'texture':name})
  elif tag==0x79:matrix=list(take('16f'))
  elif tag==0x54:
   count,=take('H');bones=count
   for _ in range(count):
    name=string();bone_names.append(name);n,=take('H');start=p;skip(n*(8 if flags&1 else 6))
    if geometry:bone_data.append({'name':name,'weights':list(struct.iter_unpack('<If' if flags&1 else '<Hf',memoryview(data)[start:p]))})
  else:raise ValueError('Registro O3D desconhecido: '+hex(tag))
 if not {'vertices','triangles'}<=counts.keys():raise ValueError('O3D sem geometria')
 result={'textures':textures,'matrix':matrix,'spans':spans,'version':version,'bones':bones,'bone_names':bone_names,**counts}
 if geometry:
  import math
  if any(not math.isfinite(v) for row in vertices for v in row) or any(not math.isfinite(v) for m in materials for v in m['values']):raise ValueError('O3D contém número não finito')
  if any(max(t[:3])>=len(vertices) or (materials and t[3]>=len(materials)) or (not materials and t[3]!=0) for t in triangles):raise ValueError('Índice de vértice/material inválido no O3D')
  if len(set(bone_names))!=len(bone_names):raise ValueError('Nomes de bones repetidos')
  if any(idx>=len(vertices) or not math.isfinite(w) or not 0<=w<=1 for b in bone_data for idx,w in b['weights']):raise ValueError('Peso de skin inválido')
  result.update(vertex_data=vertices,triangle_data=triangles,material_data=materials,bone_data=bone_data)
 return result

def read(path):return scan(Path(path).read_bytes())

def patch_textures(data,mapping):
 info=scan(data);out=data;mapping={k.casefold():v for k,v in mapping.items()}
 for start,end,old in reversed(info['spans']):
  new=mapping.get(old.casefold(),old);raw=new.encode('cp1252')
  if len(raw)>255 or any(c in new for c in '\r\n'):raise ValueError('Nome de textura incompatível')
  out=out[:start]+struct.pack('<B',len(raw))+raw+out[end:]
 return out

def slots(info):
 counts={};result=[]
 for i,name in enumerate(info['textures']):
  occurrence=counts.get(name.casefold(),0);counts[name.casefold()]=occurrence+1
  result.append({'slot':i,'texture':name,'occurrence':occurrence})
 return result
