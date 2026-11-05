import json, math, struct, subprocess, sys, tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from engine import run

def read(path):
    data=path.read_bytes(); p=0
    def take(fmt):
        nonlocal p
        values=struct.unpack_from('<'+fmt,data,p); p+=struct.calcsize('<'+fmt)
        return values
    assert take('2sB')==(b'\x84\x19',7)
    flags,key=take('BI'); assert key==0xffffffff
    assert take('B')==(0x17,)
    n,=take('I'); vertices=[take('8f') for _ in range(n)]
    assert take('B')==(0x49,)
    n,=take('I'); faces=[take('3IH' if flags&1 else '4H') for _ in range(n)]
    assert take('B')==(0x26,)
    n,=take('H'); mats=[]
    for _ in range(n):
        values=take('11f'); size,=take('B'); name,=take(str(size)+'s'); mats.append(name.decode('cp1252'))
    if p<len(data):
        assert take('B')==(0x79,)
        matrix=take('16f')
        assert all(math.isfinite(x) for x in matrix)
    assert p==len(data)
    for face in faces:
        assert max(face[:3])<len(vertices) and face[3]<len(mats)
    for v in vertices:
        assert all(math.isfinite(x) for x in v)
        assert abs(sum(x*x for x in v[3:6])-1)<1e-5
    return vertices,faces,mats

def chunk(code,body): return struct.pack('<HI',code,len(body)+6)+body

def main():
    with tempfile.TemporaryDirectory() as d:
        d=Path(d)
        (d/'fixture.obj').write_text('o test\nv 0 0 0\nv 2 0 0\nv 0 3 0\nvt 0 0\nvt 1 0\nvt 0 1\nf 1/1 2/2 3/3\n')
        vertices=chunk(0x4110,struct.pack('<H9f',3,0,0,0,2,0,0,0,3,0))
        faces=chunk(0x4120,struct.pack('<H4H',1,0,1,2,0))
        uv=chunk(0x4140,struct.pack('<H6f',3,0,0,1,0,0,1))
        (d/'fixture.3ds').write_bytes(chunk(0x4d4d,chunk(0x3d3d,chunk(0x4000,b'test\0'+chunk(0x4100,vertices+faces+uv)))))
        script=d/'make.py'
        script.write_text('''import bpy, sys
bpy.ops.wm.read_factory_settings(use_empty=True)
m=bpy.data.meshes.new('triangle'); m.from_pydata([(0,0,0),(2,0,0),(0,3,0)],[],[(0,1,2)]); m.update()
o=bpy.data.objects.new('piece',m); bpy.context.collection.objects.link(o)
p=bpy.data.objects.new('parent',None); bpy.context.collection.objects.link(p); p.location.x=10; o.parent=p; o.scale=(2,1,1)
u=m.uv_layers.new(); u.data[0].uv=(0,0); u.data[1].uv=(1,0); u.data[2].uv=(0,1)
mat=bpy.data.materials.new('paint'); mat.use_nodes=True
im=bpy.data.images.new('paint',width=2,height=2); im.generated_color=(1,0,0,1); im.pack()
n=mat.node_tree.nodes.new('ShaderNodeTexImage'); n.image=im
mat.node_tree.links.new(n.outputs['Color'],mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color']); m.materials.append(mat)
bpy.ops.wm.save_as_mainfile(filepath=sys.argv[-1])
''')
        subprocess.run(['blender','-b','--factory-startup','--python-exit-code','1','--python',str(script),'--',str(d/'fixture.blend')],check=True,stdout=subprocess.PIPE)
        for ext in ('obj','3ds','blend'):
            out=run(d/('fixture.'+ext),d/'outputs')
            path=next((out/'model').glob('*.o3d'))
            v,f,m=read(path)
            assert len(v)==3 and len(f)==1
            expected={(0,0,0),(2,0,0),(0,0,3)} if ext!='blend' else {(10,0,0),(14,0,0),(10,0,3)}
            assert {tuple(round(x,4) for x in row[:3]) for row in v}==expected, v
            assert {tuple(row[6:]) for row in v}=={(0,1),(1,1),(0,0)}
            if ext=='blend':
                assert (out/'texture'/m[0]).is_file()
                report=json.loads((out/'report.json').read_text())
                assert report['meshes'][0]['origin_xyz']==[10,0,0]
                # Translation and nonuniform scale expected independently from fixture.
                matrix=struct.unpack('<16f',path.read_bytes()[-64:])
                assert matrix==(2,0,0,0,0,1,0,0,0,0,1,0,10,0,0,1),matrix
                assert m[0]=='paint.png',m
                assert (out/'project.json').exists()
            print('PASS',ext,'positions, normals, UVs, indices, materials, report')
        (d/'degenerate.obj').write_text('o mixed\nv 0 0 0\nv 2 0 0\nv 0 3 0\nv 1 0 0\nf 1 2 3\nf 1 4 2\n')
        raw=run(d/'degenerate.obj',d/'outputs')
        repaired=run(d/'degenerate.obj',d/'outputs',repair_geometry=True)
        rr=json.loads((repaired/'report.json').read_text())
        rawr=json.loads((raw/'report.json').read_text())
        assert sum(x['triangles'] for x in rawr['meshes'])==2
        assert sum(x['triangles'] for x in rr['meshes'])==1
        assert sum(x['zero_area_removed'] for x in rr['meshes'])==1
        read(next((repaired/'model').glob('*.o3d')))
        print('PASS optional repair removes only zero-area triangle; default preserves input')
        try: run(d/'missing.obj',d/'outputs')
        except ValueError: print('PASS missing input rejected')
        else: raise AssertionError('missing input accepted')
        (d/'empty.obj').write_text('# empty\n')
        count=len(list((d/'outputs').iterdir()))
        try: run(d/'empty.obj',d/'outputs')
        except RuntimeError: pass
        else: raise AssertionError('empty model accepted')
        assert len(list((d/'outputs').iterdir()))==count
        print('PASS empty mesh rejected, no partial output')
if __name__=='__main__': main()
