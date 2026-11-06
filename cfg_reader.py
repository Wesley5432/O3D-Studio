"""Read active, unindented OMSI blocks, preserving source offsets for diagnostics."""
import re

def active_commands(text):
 lines=text.splitlines(keepends=True);hits=[];boundaries=[];offset=0;enabled=True
 for number,line in enumerate(lines,1):
  value=line.rstrip('\r\n')
  if value=='-<DISABLED>-':enabled=False;boundaries.append(offset)
  elif value=='-<ENABLED>-':enabled=True
  elif enabled and re.fullmatch(r'\[[^\]\r\n]+\]',value):hits.append((offset,offset+len(line),value,number))
  offset+=len(line)
 result=[]
 for i,(start,body,tag,line) in enumerate(hits):
  end=hits[i+1][0] if i+1<len(hits) else len(text)
  end=min([end,*[point for point in boundaries if body<=point<end]])
  result.append({'tag':tag,'start':start,'end':end,'line':line,'args':text[body:end].splitlines()})
 return result
