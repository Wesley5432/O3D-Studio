"""Runs only inside Blender. GPL-3.0-or-later."""
import sys, json, math, re, hashlib, shutil, collections
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import bpy
from mathutils import Matrix
from vendor import meshio as o3d
from asset_paths import GROUPS, clean_name, suggest_group, source_mesh_name
from material_graph import diffuse_image, mapping_values

def convert(job):
    src, out = Path(job['source']), Path(job['output'])
    scale = float(job.get('scale', 1))
    if not math.isfinite(scale) or scale <= 0:
        raise ValueError('Escala deve ser positiva e finita.')
    if src.suffix.lower() == '.blend':
        bpy.ops.wm.open_mainfile(filepath=str(src), load_ui=False, use_scripts=False)
    else:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        if src.suffix.lower() == '.obj':
            bpy.ops.wm.obj_import(filepath=str(src), forward_axis='Y', up_axis='Z')
        elif src.suffix.lower() == '.3ds':
            from vendor.import_3ds import load_3ds
            load_3ds(str(src), bpy.context, CONSTRAIN=0, IMAGE_SEARCH=False,
                     FILTER={'MESH'}, KEYFRAME=False, APPLY_MATRIX=True,
                     CONVERSE=Matrix.Identity(4))
        else:
            raise ValueError('Formato não suportado. Use .blend, .obj ou .3ds.')
    out.mkdir(parents=True, exist_ok=True)
    (out/'model').mkdir()
    (out/'texture').mkdir()
    warnings, entries, textures = [], [], {}
    organize=bool(job.get('organize',False))
    if organize:
        for group in GROUPS:(out/'model'/group).mkdir()
    search_roots=[src.parent]
    if job.get('texture_directory'):search_roots=[Path(job['texture_directory'])]
    image_lookup=collections.defaultdict(list)
    for root in search_roots:
        for path in root.rglob('*'):
            if path.is_file() and path.suffix.lower() in {'.png','.bmp','.jpg','.jpeg','.tga','.dds'} and not path.is_relative_to(out):
                path=path.resolve()
                if path not in image_lookup[path.name.casefold()]:image_lookup[path.name.casefold()].append(path)
    material_cache={};uv_maps={}
    repair = bool(job.get('repair_geometry', False))
    texture_records, used_names = [], {}
    def texture(image):
        if image.name in textures:
            return textures[image.name]
        if image.source not in {'FILE', 'GENERATED'}:
            warnings.append('Imagem animada/UDIM ignorada: '+image.name)
            return ''
        original = image.filepath.replace('\\','/').rsplit('/',1)[-1] or image.name
        # Keep a safe CP1252 filename whenever possible, including a missing image.
        stem = re.sub(r'[<>:"/\\|?*\x00-\x1f\[\]]', '_', original).rstrip(' .') or 'texture'
        stem = stem.encode('cp1252',errors='replace').decode('cp1252').replace('?','_')
        if stem.split('.')[0].upper() in {'CON','PRN','AUX','NUL',*[f'COM{i}' for i in range(1,10)],*[f'LPT{i}' for i in range(1,10)]}:
            stem = '_'+stem
        supported = Path(stem).suffix.lower() in {'.png','.bmp','.tga','.dds','.jpg','.jpeg'}
        if not supported: stem = Path(stem).stem+'.png'
        source_path = Path(bpy.path.abspath(image.filepath, library=image.library)) if image.filepath else None
        if not image.packed_file and (not source_path or not source_path.is_file()):
            candidates=image_lookup.get(original.casefold(),[])
            if len(candidates)==1:
                source_path=candidates[0];warnings.append('Textura localizada por nome: '+original)
            elif len(candidates)>1:warnings.append('Textura ambígua; escolha uma pasta sem duplicatas: '+original)
        raw = bytes(image.packed_file.data) if image.packed_file else (source_path.read_bytes() if source_path and source_path.is_file() else None)
        identity = hashlib.sha256(raw).hexdigest() if raw else str(source_path or image.name)
        if raw is None and len(image.pixels):
            stem=Path(stem).stem+'.png'
        name = Path(stem).stem[:160]+Path(stem).suffix
        if name.casefold() in used_names and used_names[name.casefold()] != identity:
            name = Path(name).stem+'_'+hashlib.sha256(identity.encode()).hexdigest()[:10]+Path(name).suffix
        used_names[name.casefold()] = identity
        textures[image.name] = name
        present = False
        if raw is not None and supported:
            (out/'texture'/name).write_bytes(raw); present = True
        else:
            if len(image.pixels): _ = image.pixels[0]
            if image.has_data:
                name = Path(name).stem+'.png'
                image.filepath_raw = str(out/'texture'/name); image.file_format='PNG'; image.save(); present=True
                textures[image.name]=name
        if not present: warnings.append('Textura ausente (referência preservada): '+image.name)
        texture_records.append({'image':image.name,'source_texture':original,'texture':name,'available':present})
        return name
    def material(mat):
        if mat and mat.as_pointer() in material_cache:return material_cache[mat.as_pointer()]
        color = tuple(mat.diffuse_color) if mat else (0.8, 0.8, 0.8, 1)
        tex = ''
        if mat and mat.use_nodes:
            principals = [n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED']
            if principals:
                socket = principals[0].inputs.get('Base Color')
                color = tuple(socket.default_value)
                if socket.is_linked:
                    node=diffuse_image(socket,warnings,mat.name)
                    if node:
                        tex=texture(node.image);color=(1,1,1,color[3])
                        uv_maps[mat.as_pointer()]=mapping_values(node,warnings,mat.name)
            else:warnings.append('Material sem Principled: '+mat.name)
        result=o3d.Material(diffuse=o3d.ColorRGBA(*color), texture=tex)
        if mat:material_cache[mat.as_pointer()]=result
        return result
    preserve_skin=bool(job.get('preserve_skin',False))
    if preserve_skin or any(o.get('omsi_smoothskin',False) for o in bpy.context.scene.objects):
        for rig in bpy.context.scene.objects:
            if rig.type=='ARMATURE':rig.data.pose_position='REST'
        bpy.context.view_layer.update()
    deps = bpy.context.evaluated_depsgraph_get()
    # Match the O3D convention used by Road-hog123: Z-up RH -> Y-up LH.
    axis = Matrix(((1,0,0,0),(0,0,1,0),(0,1,0,0),(0,0,0,1)))
    rotation = Matrix.Rotation(math.radians(float(job.get('rotation', 0))), 4, 'Z')
    markers=[];marker_ids=set();used_mesh_names=set()
    for obj in bpy.context.scene.objects:
        prefix=obj.name.split('__',1)[0].casefold()
        kind=str(obj.get('omsi_marker','')).casefold()
        if not kind and prefix in {'pivot','pivo','luz','light'}:kind='light' if prefix in {'luz','light'} else 'pivot'
        if not kind and obj.type in {'EMPTY','LIGHT'}:kind='light' if obj.type=='LIGHT' else 'pivot'
        if kind not in {'light','pivot'}:continue
        matrix=rotation @ Matrix.Scale(scale,4) @ obj.matrix_world
        direction=matrix.to_3x3() @ __import__('mathutils').Vector((0,0,-1) if obj.type=='LIGHT' else (0,1,0))
        if direction.length:direction.normalize()
        target=str(obj.get('omsi_target',obj.name.split('__',1)[1] if '__' in obj.name else ''))
        markers.append({'name':obj.name,'kind':kind,'target':target,'xyz':list(matrix.translation),'direction':list(direction),'variable':str(obj.get('omsi_variable',''))})
        marker_ids.add(obj.as_pointer())
    objects = sorted((o for o in bpy.context.scene.objects if o.type == 'MESH' and not o.hide_render and o.as_pointer() not in marker_ids), key=lambda o:o.name)
    for index, obj in enumerate(objects):
        ev = obj.evaluated_get(deps)
        me = ev.to_mesh(preserve_all_data_layers=True, depsgraph=deps)
        try:
            me.calc_loop_triangles()
            if not me.loop_triangles:
                warnings.append('Peça sem faces: '+obj.name)
                continue
            transform = axis @ rotation @ Matrix.Scale(scale,4) @ obj.matrix_world
            if abs(transform.to_3x3().determinant()) < 1e-15:
                raise ValueError('Transformação singular: '+obj.name)
            normals = transform.to_3x3().inverted().transposed()
            mesh = o3d.Mesh()
            # O3D stores this animation-origin matrix transposed in X,Z,Y coordinates.
            origin = (transform @ axis).transposed()
            mesh.matrix = tuple(tuple(row) for row in origin)
            occurrences = collections.Counter()
            mesh.materials = [material(m) for m in me.materials] or [material(None)]
            material_records=[]
            for slot,m in enumerate(mesh.materials):
                material_records.append({'slot':slot,'name':me.materials[slot].name if slot<len(me.materials) and me.materials[slot] else '', 'texture':m.texture, 'occurrence':occurrences[m.texture.casefold()]})
                occurrences[m.texture.casefold()]+=1
            uv = me.uv_layers.active
            if not uv:
                warnings.append('Peça sem UV: '+obj.name)
            lookup = {};weight_lists=collections.defaultdict(list)
            skinned=bool(obj.vertex_groups) and (preserve_skin or bool(obj.get('omsi_smoothskin',False)))
            group_names={g.index:g.name for g in obj.vertex_groups}
            if skinned:
                for name in group_names.values():
                    raw=name.encode('cp1252')
                    if len(raw)>255 or any(c in name for c in '\r\n'):raise ValueError('Nome de grupo incompatível: '+name)
            degenerate_count = repaired_normals = invalid_normals = 0
            for tri in me.loop_triangles:
                local_co = [me.vertices[i].co for i in tri.vertices]
                geometric_normal = (local_co[1]-local_co[0]).cross(local_co[2]-local_co[0])
                if geometric_normal.length_squared == 0:
                    degenerate_count += 1
                    if repair:
                        continue
                indices = []
                loops = list(tri.loops)
                if transform.to_3x3().determinant() < 0:
                    loops.reverse()
                for li in loops:
                    pos = transform @ me.vertices[me.loops[li].vertex_index].co
                    source_normal = me.corner_normals[li].vector
                    if source_normal.length_squared < 1e-12:
                        invalid_normals += 1
                        if repair:
                            source_normal = geometric_normal.normalized()
                            repaired_normals += 1
                    norm = (normals @ source_normal).normalized()
                    coords = uv.data[li].uv if uv else (0,0)
                    u,v=float(coords[0]),float(coords[1])
                    mat=me.materials[tri.material_index] if tri.material_index<len(me.materials) else None
                    mapping=uv_maps.get(mat.as_pointer()) if mat else None
                    if mapping:
                        loc,angle,tiling,kind=mapping
                        if kind=='TEXTURE':
                            x,y=u-loc[0],v-loc[1]
                            u=(x*math.cos(angle)+y*math.sin(angle))/tiling[0];v=(-x*math.sin(angle)+y*math.cos(angle))/tiling[1]
                        else:
                            x,y=u*tiling[0],v*tiling[1]
                            u=x*math.cos(angle)-y*math.sin(angle)+loc[0];v=x*math.sin(angle)+y*math.cos(angle)+loc[1]
                    data = (*pos, *norm, u, 1-v)
                    if not all(math.isfinite(v) for v in data):
                        raise ValueError('Geometria contém valores inválidos: '+obj.name)
                    weights=()
                    if skinned:
                        groups=me.vertices[me.loops[li].vertex_index].groups
                        values=[(group_names[g.group],float(g.weight)) for g in groups if g.group in group_names and g.weight>0]
                        total=sum(w for _,w in values)
                        if total<=0:raise ValueError('Smoothskin: vértice sem peso em '+obj.name+'. Pinte todos os vértices ou desmarque a opção de pesos.')
                        weights=tuple(sorted((name,w/total) for name,w in values))
                    vertex_key=(data,weights)
                    if vertex_key not in lookup:
                        lookup[vertex_key] = len(mesh.vertices)
                        for name,weight in weights:weight_lists[name].append(o3d.SkinWeight(len(mesh.vertices),weight))
                        mesh.vertices.append(o3d.Vertex(o3d.Vector3(*data[:3]), o3d.Vector3(*data[3:6]), o3d.Vector2(*data[6:])))
                    indices.append(lookup[vertex_key])
                mesh.triangles.append(o3d.Triangle(tuple(indices), min(tri.material_index,len(mesh.materials)-1)))
            if degenerate_count:
                warnings.append(('Triângulos sem área removidos da saída' if repair else 'Triângulos sem área detectados')+': '+obj.name+' ('+str(degenerate_count)+')')
            if invalid_normals:
                warnings.append(('Normais nulas substituídas pela normal da face' if repair else 'Normais nulas detectadas')+': '+obj.name+' ('+str(invalid_normals)+' ocorrências)')
            if not mesh.triangles:
                warnings.append('Peça sem faces exportáveis: '+obj.name)
                continue
            if skinned:
                if any(len(values)>65535 for values in weight_lists.values()):raise ValueError('Smoothskin: grupo com mais de 65535 pesos; divida a malha: '+obj.name)
                mesh.bones=[o3d.Bone(name,tuple(values)) for name,values in sorted(weight_lists.items())]
            name = source_mesh_name(obj.name,used_mesh_names)
            group=suggest_group(obj.name)
            if organize:name=group+'/'+name
            (out/'model'/name).write_bytes(o3d.dump(mesh, o3d.MeshFormatSpec(7)))
            entries.append({'object':obj.name, 'file':name,'group':group,'vertices':len(mesh.vertices),'triangles':len(mesh.triangles), 'zero_area_detected':degenerate_count, 'zero_area_removed':degenerate_count if repair else 0, 'normal_corners_repaired':repaired_normals, 'origin_xyz':list((rotation @ Matrix.Scale(scale,4) @ obj.matrix_world).translation), 'origin_matrix_o3d':[list(row) for row in mesh.matrix], 'materials':material_records,'bones':sorted(weight_lists)})
        finally:
            ev.to_mesh_clear()
    if not entries:
        raise ValueError('Nenhuma malha com faces encontrada.')
    (out/'model'/'meshes.cfg').write_text('\n'.join('[mesh]\n'+e['file'].replace('/','\\')+'\n' for e in entries),encoding='cp1252')
    report = {'format_version':2, 'markers':markers, 'preserve_skin':preserve_skin, 'organized':organize, 'textures':texture_records, 'repair_geometry':repair, 'source':str(src), 'blender':bpy.app.version_string,'meshes':entries,'warnings':sorted(set(warnings)),
              'note':'Geometria estática. meshes.cfg é um trecho de configuração, não um veículo completo.'}
    (out/'report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf8')
    from project import new_project, save_project
    save_project(out/'project.json',new_project(report))
    print('CONVERSION_OK', flush=True)

if __name__ == '__main__':
    convert(json.loads(Path(sys.argv[sys.argv.index('--')+1]).read_text(encoding='utf8')))
