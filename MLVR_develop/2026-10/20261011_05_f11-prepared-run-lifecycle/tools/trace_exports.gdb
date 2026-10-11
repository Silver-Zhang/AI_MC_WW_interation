set pagination off
set confirm off
python
import gdb,os,json,shutil,struct
from pathlib import Path
out=Path(os.environ['F11_TRACE_DIR']);run=0;pdf=[];errors=[]
def deref(v):
 while v.type.code==gdb.TYPE_CODE_REF:v=v.referenced_value()
 return v.dereference() if v.type.code==gdb.TYPE_CODE_PTR else v
def vec(v):
 b=v['_M_impl']['_M_start'];e=v['_M_impl']['_M_finish'];n=int(e-b);typ=b.type.strip_typedefs().target().strip_typedefs()
 return {'n':n,'element':str(typ),'bits':bytes(gdb.selected_inferior().read_memory(b,n*typ.sizeof)).hex() if n else ''}
class Finish(gdb.FinishBreakpoint):
 def __init__(self,cb):super().__init__(gdb.newest_frame(),internal=True);self.cb=cb
 def stop(self):
  try:self.cb();return False
  except Exception as e:errors.append(str(e));return True
class Probe(gdb.Breakpoint):
 def __init__(self,name,cb):super().__init__(name,internal=True);self.cb=cb
 def stop(self):
  try:self.cb();return False
  except Exception as e:errors.append(str(e));return True
def pdf_call():
 p=gdb.parse_and_eval('this');idx=int(gdb.parse_and_eval('nTallyPtr'))
 def after():
  o=deref(p);pdf.append({'kind':int(o['p_cTallyType']),'bin':idx,'x':vec(o['p_vpdfx']),'y':vec(o['p_vpdfy']),'slope':vec(o['p_vSlope'])})
 Finish(after)
def export_call():
 def after():
  global run,pdf
  run+=1;shutil.copyfile('inp.Result.h5',out/f'{run}-result.h5');(out/f'{run}-pdf.json').write_text(json.dumps(pdf,sort_keys=True));pdf=[]
 Finish(after)
Probe('CDStatisticsTester::PrintPdfChart',pdf_call)
Probe('CDTally::OutputTallyh5',export_call)
end
run
python
(out/'observer.json').write_text(json.dumps({'errors':errors,'runs':run}))
if errors:gdb.execute('quit 3')
code=gdb.parse_and_eval('$_exitcode')
if code.type.code==gdb.TYPE_CODE_VOID:gdb.execute('quit 4')
if int(code)!=0:gdb.execute('quit '+str(int(code)))
end
quit
