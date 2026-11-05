"""Subprocess boundary. No shell interpolation, no source modification."""
from output_files import publish
import json, math, os, shutil, subprocess, sys, tempfile, uuid
from pathlib import Path
BASE = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent))
def blender_path():
    root = Path(sys.executable).parent if getattr(sys,'frozen',False) else BASE
    candidates = [root/'runtime'/'blender.exe', root/'runtime'/'blender', os.environ.get('BLENDER_PATH',''), shutil.which('blender')]
    return next((str(p) for p in candidates if p and Path(p).is_file()), '')
def run(source, destination, blender='', scale=1, rotation=0, repair_geometry=False, organize=False, texture_directory=''):
    src = Path(source).resolve()
    if not src.is_file() or src.suffix.lower() not in {'.blend','.obj','.3ds'}:
        raise ValueError('Selecione um arquivo .blend, .obj ou .3ds válido.')
    scale, rotation = float(scale), float(rotation)
    if not math.isfinite(scale) or scale <= 0 or not math.isfinite(rotation):
        raise ValueError('Escala positiva e rotação finita são necessárias.')
    exe = blender or blender_path()
    if not exe or not Path(exe).is_file():
        raise ValueError('Selecione blender.exe ou inclua o Blender portátil em runtime/.')
    if texture_directory and not Path(texture_directory).is_dir():raise ValueError('Pasta de texturas não encontrada')
    parent = Path(destination).resolve()
    parent.mkdir(parents=True, exist_ok=True)
    final = parent
    with tempfile.TemporaryDirectory(prefix='.o3d-',dir=parent) as temp:
        temp = Path(temp)
        stage = temp/'result'
        job = temp/'job.json'
        job.write_text(json.dumps({'source':str(src),'output':str(stage),'scale':scale,'rotation':rotation,'repair_geometry':bool(repair_geometry),'organize':bool(organize),'texture_directory':str(Path(texture_directory).resolve()) if texture_directory else ''}),encoding='utf8')
        proc = subprocess.run([str(exe),'--background','--factory-startup','--disable-autoexec','--python-exit-code','1','--python',str(BASE/'backend.py'),'--',str(job)],
                              stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf8',errors='replace',timeout=1800,
                              creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        if proc.returncode or not (stage/'report.json').is_file():
            raise RuntimeError('Conversão falhou.\n'+proc.stdout[-12000:])
        (stage/'conversion.log').write_text(proc.stdout,encoding='utf8')
        publish(stage,final)
    return final
