set pagination off
set confirm off
break CDAceData::HasNonzeroPreparedFissionProduction
run
python
import gdb,json
v=gdb.parse_and_eval('this').dereference();begin=v['p_vNuclides']['_M_impl']['_M_start'];end=v['p_vNuclides']['_M_impl']['_M_finish'];rows=[]
for i in range(1,int(end-begin)):
 n=begin[i];nx=n['NXS']['_M_impl']['_M_start'];jx=n['JXS']['_M_impl']['_M_start'];x=n['XSS']['_M_impl']['_M_start'];groups=int(nx[5]);nu=int(jx[4])+(groups if int(nx[10])>1 else 0);fis=int(jx[3]);rows.append({'nuclide':int(n['p_nZAID']),'groups':groups,'nu':[float(x[nu+g]) for g in range(groups)],'sigma_f':[float(x[fis+g]) for g in range(groups)],'nu_sigma_f':[float(x[nu+g])*float(x[fis+g]) for g in range(groups)]})
open('/home/workspace/AI_MC_WW_interation/MLVR_develop/2026-10/20261011_05_f11-prepared-run-lifecycle/logs/implementation/fission-raw/nu-sigma-f.json','w').write(json.dumps(rows,indent=2))
end
continue
quit
