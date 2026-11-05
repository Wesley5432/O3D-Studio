"""Explicit CFG reference adaptation; never invent script behavior."""
import re
from vehicle_template import commands,arg,set_arg,variable_patch
from project import number
LIGHT_POS={'[spotlight]':(0,1,2),'[light_enh_2]':(0,1,2),'[interiorlight]':(5,6,7)}
NUMERIC={'[visible]':0,'[matl_change]':2,'[interiorlight]':0,'[light_enh_2]':17}

def lights(text):
 result=[]
 for i,c in enumerate(commands(text)):
  if c['tag'] in LIGHT_POS:
   xyz=[float(arg(c,n)) for n in LIGHT_POS[c['tag']]]
   result.append({'command':i,'type':c['tag'],'xyz':xyz})
 return result

def move_light(text,command,xyz):
 cs=commands(text)
 if command<0 or command>=len(cs):raise ValueError('Luz não encontrada')
 c=cs[command]
 if c['tag'] not in LIGHT_POS or len(xyz)!=3:raise ValueError('Selecione uma luz e informe XYZ')
 sub=text[c['start']:c['end']]
 for n,value in zip(LIGHT_POS[c['tag']],xyz):sub=set_arg(sub,c['tag'],n,number(float(value)))
 return text[:c['start']]+sub+text[c['end']:]

def adapt_references(text,mapping=None):
 mapping=mapping or {};allowed={'numeric','strings','events'}
 if set(mapping)-allowed:raise ValueError('Categorias válidas: numeric, strings, events')
 for category,values in mapping.items():
  if not isinstance(values,dict):raise ValueError('Cada categoria exige origem: destino')
  for old,new in values.items():
   if not isinstance(old,str) or not isinstance(new,str) or not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*',old) or not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*',new):raise ValueError('Nome de variável/evento inválido')
 text=variable_patch(text,mapping.get('numeric',{}))
 for c in reversed(commands(text)):
  tag=c['tag'];category=None;n=0
  if tag in NUMERIC:category='numeric';n=NUMERIC[tag]
  elif tag in {'[texttexture]','[texttexture_enh]'}:category='strings'
  elif tag=='[mouseevent]':category='events'
  if category and arg(c,n) in mapping.get(category,{}):
   sub=set_arg(text[c['start']:c['end']],tag,n,mapping[category][arg(c,n)])
   text=text[:c['start']]+sub+text[c['end']:]
 return text
