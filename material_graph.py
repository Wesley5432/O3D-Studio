"""Follow diffuse image connections without guessing between multiple images."""
def diffuse_image(socket,warnings,label):
 seen=set();images={};approx=False
 def walk(sock):
  nonlocal approx
  if not sock.is_linked:return
  node=sock.links[0].from_node
  if node.as_pointer() in seen:return
  seen.add(node.as_pointer())
  if node.type=='TEX_IMAGE' and node.image:images[node.image.as_pointer()]=node;return
  if node.type=='REROUTE':walk(node.inputs[0]);return
  if node.type=='MIX_RGB' and node.blend_type=='MIX' and not node.inputs[0].is_linked:
   factor=node.inputs[0].default_value
   if factor==0:walk(node.inputs[1]);return
   if factor==1:walk(node.inputs[2]);return
  approx=True
  for input in node.inputs:
   if input.is_linked:walk(input)
 walk(socket)
 if len(images)>1:
  warnings.append('Mistura com múltiplas imagens exige bake: '+label);return None
 if not images:
  warnings.append('Cor procedural sem imagem recuperável: '+label);return None
 if approx:warnings.append('Textura recuperada com aproximação de mistura; confira cor/bake: '+label)
 return next(iter(images.values()))

def mapping_values(node,warnings,label):
 """Return supported POINT/TEXTURE mapping for UV, otherwise leave UV with a warning."""
 vector=node.inputs.get('Vector')
 if not vector or not vector.is_linked:return None
 source=vector.links[0].from_node
 if source.type=='UVMAP':
  if source.uv_map:warnings.append('Camada UV explícita; confirme que corresponde à UV ativa exportada: '+label)
  return None
 if source.type=='TEX_COORD' and vector.links[0].from_socket.name=='UV':return None
 if source.type=='MAPPING' and source.vector_type in {'POINT','TEXTURE'}:
  upstream=source.inputs['Vector']
  valid=upstream.is_linked and upstream.links[0].from_node.type=='TEX_COORD' and upstream.links[0].from_socket.name=='UV'
  if valid and all(not source.inputs[n].is_linked for n in ('Location','Rotation','Scale')):
   loc=tuple(source.inputs['Location'].default_value);rot=tuple(source.inputs['Rotation'].default_value);scale=tuple(source.inputs['Scale'].default_value)
   if rot[0]==0 and rot[1]==0 and scale[0]!=0 and scale[1]!=0:return loc,rot[2],scale,source.vector_type
 warnings.append('Mapeamento de textura não suportado; UV original mantida: '+label)
 return None
