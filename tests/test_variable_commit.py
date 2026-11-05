import unittest
from types import SimpleNamespace
import test_template
from vehicle_template import render_cfg,variable_patch,scan_plan
from editor import PieceEditor
from project import new_project,render_cfg as universal_cfg

class Value:
 def __init__(self,v=''):self.v=v
 def get(self):return self.v
 def set(self,v):self.v=v

class VariableCommitTests(unittest.TestCase):
 def test_kept_mesh_applies_variable(self):
  case=test_template.TemplateTests();case.setUp()
  try:
   case.p['mapping']['mesh_0000'].update(variables={'brake':'throttle'})
   cfg,_=render_cfg(case.t,case.p);self.assertIn('anim_rot\nthrottle\n-90',cfg)
   case.p['mapping']['mesh_0000']['variables']={'brake':'unknown'}
   self.assertTrue(scan_plan(case.t,case.p)['errors'])
  finally:case.tearDown()
 def test_indented_animation_variable(self):
  self.assertEqual(variable_patch('[newanim]\n  anim_rot  \n  brake  \n1200\n',{'brake':'throttle'}),'[newanim]\n  anim_rot  \n  throttle  \n1200\n')
 def test_apply_commits_selected_animation_fields(self):
  project=new_project({'meshes':[{'object':'wheel','file':'wheel.o3d','materials':[]}]});p=project['parts'][0];p['animations']=[{'type':'rot','variable':'brake','factor':90,'origin_rotation':[0,90,0]}]
  editor=SimpleNamespace(draft=p,project=project,fields={k:Value(v) for k,v in {'parent':'','pivot':'','event':'','visible':'','visible_value':'1'}.items()},av={k:Value(v) for k,v in {'type':'rot','variable':'throttle','factor':'1200','rotation':'0 90 0'}.items()},animtree=SimpleNamespace(selection=lambda:['0']),mats=SimpleNamespace(selection=lambda:[]),remember=lambda:None,status=Value())
  p['materials']=[{'slot':0,'texture':'panel.png','occurrence':0}]
  editor.mats=SimpleNamespace(selection=lambda:['0']);editor.alpha=Value('');editor.night=Value('panel_lm.png');editor.lightvar=Value('throttle')
  PieceEditor.apply(editor)
  self.assertEqual(editor.project['parts'][0]['material_rules'][0]['variable'],'throttle')
  self.assertEqual(editor.project['parts'][0]['animations'][0]['variable'],'throttle')
  self.assertIn('anim_rot\nthrottle\n1200',universal_cfg(editor.project))
