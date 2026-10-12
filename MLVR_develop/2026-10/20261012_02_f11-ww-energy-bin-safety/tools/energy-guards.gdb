set pagination off
set confirm off
set breakpoint pending on
python
import gdb,os,json
from pathlib import Path
counts={};throws=[]
class Count(gdb.Breakpoint):
 def __init__(self,name,label):
  super().__init__(name,internal=True);self.label=label;counts[label]=0
 def stop(self):counts[self.label]+=1;return False
for name,label in [('CDCalMode::InitializeFixedSourceModel','initialize'),('CDCalMode::PrepareFixedSourceRun','prepare'),('CDFixedSource::ResetRunState','clear'),('CDCalMode::ExecuteFixedSourcePrepared','execute'),('CDFixedSource::SampleFixSource','source'),('CDWeightWindow::ValidatePreparedNativeDefinition','validate'),('CDWeightWindow::InstallPreparedNativeState','install')]:Count(name,label)
class Throw(gdb.Breakpoint):
 def stop(self):
  names=[];f=gdb.newest_frame()
  while f and len(names)<12:
   names.append(f.name());f=f.older()
  throws.append(names);return False
Throw('__cxa_throw',internal=True)
def done(event):
 Path(os.environ['ENERGY_GUARD_COUNTS']).write_text(json.dumps({'counts':counts,'throws':throws,'inferior_exit':getattr(event,'exit_code',None)},indent=2))
gdb.events.exited.connect(done)
end
run
