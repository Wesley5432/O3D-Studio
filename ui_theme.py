"""Shared desktop visual theme."""
from tkinter import ttk

def apply_theme(root):
 root.configure(background='#eef3f9')
 style=ttk.Style(root);style.theme_use('clam')
 style.configure('.',font=('Segoe UI',10),background='#eef3f9',foreground='#24344b')
 style.configure('TFrame',background='#eef3f9')
 style.configure('TLabel',background='#eef3f9')
 style.configure('Title.TLabel',font=('Segoe UI',22,'bold'),foreground='#142c4e')
 style.configure('Muted.TLabel',foreground='#536983')
 style.configure('TButton',padding=(12,8),background='#ffffff',borderwidth=1)
 style.map('TButton',background=[('active','#dceafb'),('disabled','#e4eaf2')])
 style.configure('Accent.TButton',background='#2463d5',foreground='white',font=('Segoe UI',10,'bold'))
 style.map('Accent.TButton',background=[('active','#194da9'),('disabled','#a7b7ce')],foreground=[('disabled','#f1f4f9')])
 style.configure('TEntry',fieldbackground='white',padding=6)
 style.configure('TCombobox',fieldbackground='white',padding=5)
 style.configure('TNotebook',background='#eef3f9',borderwidth=0)
 style.configure('TNotebook.Tab',padding=(18,11),background='#e0e8f3')
 style.map('TNotebook.Tab',background=[('selected','#ffffff')],foreground=[('selected','#1c54b0')])
 style.configure('Treeview',rowheight=30,background='white',fieldbackground='white',borderwidth=0)
 style.configure('Treeview.Heading',padding=8,font=('Segoe UI',10,'bold'),background='#dde7f4')
 style.map('Treeview',background=[('selected','#2463d5')],foreground=[('selected','white')])
