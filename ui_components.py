"""Compact controls shared by the desktop screens."""
import tkinter as tk
from tkinter import ttk

def action_menu(parent,label,actions,guard):
 button=ttk.Menubutton(parent,text=label+' ▾',direction='below')
 menu=tk.Menu(button,tearoff=False)
 for title,callback in actions:
  menu.add_command(label=title,command=lambda f=callback:guard(f))
 button.configure(menu=menu)
 return button

def disclosure(parent,title):
 frame=ttk.Frame(parent);frame.pack(fill='x',pady=6)
 body=ttk.Frame(frame,padding=(10,6));opened=tk.BooleanVar(value=False)
 def toggle():
  if opened.get():body.pack(fill='x')
  else:body.pack_forget()
 ttk.Checkbutton(frame,text=title,variable=opened,command=toggle).pack(anchor='w')
 return body

def background(master,title,work,on_success=None):
 """Run file work outside Tk and return results on the Tk thread."""
 import queue,threading
 from tkinter import messagebox
 win=tk.Toplevel(master);win.title(title);win.geometry('460x125');win.transient(master);win.grab_set();win.protocol('WM_DELETE_WINDOW',lambda:None)
 ttk.Label(win,text=title+'…',padding=16).pack(fill='x')
 bar=ttk.Progressbar(win,mode='indeterminate');bar.pack(fill='x',padx=16);bar.start();jobs=queue.Queue()
 def worker():
  try:jobs.put((True,work()))
  except Exception as e:jobs.put((False,str(e)))
 def poll():
  try:ok,value=jobs.get_nowait()
  except queue.Empty:win.after(120,poll);return
  bar.stop();win.grab_release();win.destroy()
  if not ok:messagebox.showerror(title,value,parent=master)
  elif on_success:on_success(value)
  else:messagebox.showinfo(title,'Concluído: '+str(value),parent=master)
 threading.Thread(target=worker,daemon=True).start();win.after(120,poll)
