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
