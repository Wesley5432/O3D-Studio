"""Portable asset names and constrained model-relative paths."""
import re,unicodedata
from pathlib import PurePosixPath
GROUPS=('Exterior','Interior','Painel','Mecanica')
RESERVED={'CON','PRN','AUX','NUL',*[f'COM{i}' for i in range(1,10)],*[f'LPT{i}' for i in range(1,10)]}
def clean_name(value,fallback='Peca',limit=70):
 value=unicodedata.normalize('NFKD',str(value)).encode('ascii','ignore').decode()
 value=re.sub(r'[^A-Za-z0-9_-]+','_',value).strip('_-')[:limit] or fallback
 if value.upper() in RESERVED:value='_'+value
 return value

def source_mesh_name(value,used):
 """Keep the source object spelling; change only invalid Windows characters/collisions."""
 name=str(value).encode('cp1252','replace').decode('cp1252')
 name=re.sub(r'[<>:"/\\|?*\x00-\x1f\[\]]','_',name).rstrip(' .')[:200] or 'Objeto'
 if name.split('.')[0].upper() in RESERVED:name='_'+name
 candidate=name;counter=2
 while (candidate+'.o3d').casefold() in used:candidate=name+'_'+str(counter);counter+=1
 used.add((candidate+'.o3d').casefold());return candidate+'.o3d'

def mesh_path(value):
 if not isinstance(value,str) or any(c in value for c in '\\:\r\n[]\x00'):raise ValueError('Caminho de O3D inválido')
 parts=value.split('/')
 if len(parts)>2 or any(not p or p in {'.','..'} or p.endswith((' ','.')) for p in parts):raise ValueError('Caminho de O3D inválido')
 if len(parts)==2 and parts[0] not in GROUPS:raise ValueError('Pasta de peça deve ser Exterior, Interior, Painel ou Mecanica')
 if not parts[-1].lower().endswith('.o3d') or any(c in parts[-1] for c in '<>"|?*'):raise ValueError('Nome de O3D inválido')
 return PurePosixPath(*parts).as_posix()

def suggest_group(name):
 value=clean_name(name).lower()
 if any(w in value for w in ('painel','volante','botao','botoes','instrument','velocim','tacograf','pedal','letreiro','display','manopla')):return 'Painel'
 if any(w in value for w in ('motor','chassi','suspens','eixo','cardan','diferencial','escap','cataliz','roda','pneu')):return 'Mecanica'
 if any(w in value for w in ('banco','assento','interior','balaustre','corrima','catraca','piso','salon','saloon','cortina')):return 'Interior'
 return 'Exterior'
