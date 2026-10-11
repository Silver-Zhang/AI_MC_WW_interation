set pagination off
set confirm off
python
import gdb,json,os,struct
from pathlib import Path
out=Path(os.environ['F11_TRACE_DIR']);rows=[]
def obj(v):
 while v.type.code==gdb.TYPE_CODE_REF:v=v.referenced_value()
 return v.dereference() if v.type.code==gdb.TYPE_CODE_PTR else v
def bits(v):return struct.pack('<d',float(v)).hex()
class Probe(gdb.Breakpoint):
 def stop(self):
  f=obj(gdb.parse_and_eval('cFixedSource'));n=obj(gdb.parse_and_eval('cNeutronTransport'));a=obj(gdb.parse_and_eval('CAceData'))
  rows.append({'role':'A' if bool(f['p_bIsAdjoint']) else 'F','fixed_max_neutron':bits(f['p_dMaxAdjointNeutronEnergy']),'fixed_max_photon':bits(f['p_dMaxAdjointPhotonEnergy']),'neutron_energy_cutoff':bits(n['p_dEg0CutOff']),'weight_cutoff':bits(n['p_dWgtCutOff']),'ace_adjoint':bool(a['p_bIsAdjoint'])});return False
Probe('CDCalMode::ExecuteFixedSourcePrepared',internal=True)
end
run
python
(out/'cutoffs.json').write_text(json.dumps(rows,indent=2))
code=gdb.parse_and_eval('$_exitcode')
if code.type.code==gdb.TYPE_CODE_VOID:gdb.execute('quit 4')
if int(code)!=0:gdb.execute('quit '+str(int(code)))
end
quit
