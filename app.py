import json, queue, threading, tkinter as tk
from tkinter import ttk, filedialog, messagebox
from engine import run, blender_path
from editor import open_editor

def main(parent=None):
    root = tk.Toplevel(parent) if parent else tk.Tk()
    root.title('O3D Studio — v0.0.2')
    root.geometry('900x720')
    root.minsize(820,650)
    from ui_theme import apply_theme
    apply_theme(root)
    frame = ttk.Frame(root,padding=20); frame.pack(fill='both',expand=True)
    ttk.Label(frame,text='Converter modelo para OMSI 2',font=('Segoe UI',18,'bold')).pack(anchor='w')
    ttk.Label(frame,text='BLEND • 3DS • OBJ → O3D por peça + texturas + trecho CFG').pack(anchor='w',pady=(5,15))
    fields = {}
    def field(key,label,browse=None,value=''):
        row=ttk.Frame(frame); row.pack(fill='x',pady=4)
        ttk.Label(row,text=label,width=16).pack(side='left')
        v=tk.StringVar(value=value); fields[key]=v
        ttk.Entry(row,textvariable=v).pack(side='left',fill='x',expand=True)
        if browse:
            def choose():
                result=browse()
                if result: v.set(result)
            ttk.Button(row,text='Escolher',command=choose).pack(side='right',padx=(6,0))
    field('source','Modelo',lambda:filedialog.askopenfilename(filetypes=[('Modelos','*.blend *.obj *.3ds')]))
    field('destination','Saída direta',filedialog.askdirectory)
    field('texture_directory','Pasta de texturas',filedialog.askdirectory)
    field('blender','Blender executável',lambda:filedialog.askopenfilename(),blender_path())
    field('scale','Escala',value='1')
    field('rotation','Rotação Z (graus)',value='0')
    ttk.Label(frame,text='Convenção de entrada: Z para cima. Escala 1 = uma unidade por metro.\nSaída estática: não gera física, scripts, painel ou animações de portas.').pack(anchor='w',pady=12)
    organize=tk.BooleanVar(value=True)
    ttk.Checkbutton(frame,text='Organizar O3D em Exterior / Interior / Painel / Mecanica (sugestão pelo nome)',variable=organize).pack(anchor='w',pady=6)
    repair=tk.BooleanVar(value=False)
    ttk.Checkbutton(frame,text='Reparar normais nulas e remover triângulos sem área (somente na saída)',variable=repair).pack(anchor='w')
    ttk.Label(frame,text='Sem pasta O3D aleatória. Arquivos existentes recebem backup ZIP.\nApós converter, use o editor para exportar somente a peça selecionada ou todas.',style='Muted.TLabel').pack(anchor='w',pady=8)
    preserve_skin=tk.BooleanVar(value=False)
    ttk.Checkbutton(frame,text='Preservar pesos dos grupos de vértices (coifa / sanfona / smoothskin)',variable=preserve_skin).pack(anchor='w',pady=4)
    last_output=[None]
    status=tk.StringVar(value='Pronto para converter.'); messages=queue.Queue()
    def start():
        values={k:v.get().strip() for k,v in fields.items()}
        if not values['source'] or not values['destination']:
            messagebox.showerror('Dados incompletos','Escolha o modelo e a pasta de saída.'); return
        values['repair_geometry'] = repair.get()
        values['organize'] = organize.get()
        values['preserve_skin'] = preserve_skin.get()
        button.config(state='disabled'); status.set('Convertendo… Aguarde o Blender terminar.')
        def worker():
            try: messages.put((True,str(run(**values))))
            except Exception as exc: messages.put((False,str(exc)))
        threading.Thread(target=worker,daemon=True).start()
    button=ttk.Button(frame,text='Converter para O3D',style='Accent.TButton',command=start); button.pack(anchor='w')
    ttk.Button(frame,text='Abrir editor de peças / gerar CFG',command=lambda:open_editor(root)).pack(anchor='w',pady=5)
    ttk.Button(frame,text='Abrir resultado e revisar peças',command=lambda:open_editor(root,last_output[0]) if last_output[0] else messagebox.showinfo('Resultado','Converta um modelo primeiro.')).pack(anchor='w',pady=5)
    ttk.Label(frame,textvariable=status,wraplength=700).pack(anchor='w',pady=12)
    def poll():
        try:
            ok,text=messages.get_nowait(); button.config(state='normal')
            status.set(('Concluído: ' if ok else 'Falha: ')+text[:500])
            if ok:
                last_output[0]=text
                report=json.loads((__import__('pathlib').Path(text)/'report.json').read_text(encoding='utf8'))
                missing=sum(not t['available'] for t in report['textures'])
                summary=f"{len(report['meshes'])} peças | {len(report['textures'])} texturas | {missing} imagens ausentes | {len(report['warnings'])} avisos"
                status.set(summary+'\n'+text)
                messagebox.showinfo('Conversão concluída',summary+'\n\nAbra o resultado para revisar as peças. Consulte report.json para os avisos.')
            else: messagebox.showerror('Erro de conversão',text)
        except queue.Empty: pass
        root.after(200,poll)
    poll()
    if parent is None: root.mainloop()
if __name__=='__main__':
    from studio import main as studio_main
    studio_main()
