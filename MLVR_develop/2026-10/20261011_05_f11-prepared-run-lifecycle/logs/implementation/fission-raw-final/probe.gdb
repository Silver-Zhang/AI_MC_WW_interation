set pagination off
set confirm off
break CDAceData::HasNonzeroPreparedFissionProduction
run
python
import gdb,json
v=gdb.parse_and_eval('this').dereference();begin=v['p_vNuclides']['_M_impl']['_M_start'];end=v['p_vNuclides']['_M_impl']['_M_finish'];rows=[]
for i in range(1,int(end-begin)):
 n=begin[i];nx=n['NXS']['_M_impl']['_M_start'];jx=n['JXS']['_M_impl']['_M_start'];x=n['XSS']['_M_impl']['_M_start'];groups=int(nx[5]);nu=int(jx[4])+(groups if int(nx[10])>1 else 0);fis=int(jx[3]);rows.append({'nuclide':int(n['p_nZAID']),'groups':groups,'nu':[float(x[nu+g]) for g in range(groups)],'sigma_f':[float(x[fis+g]) for g in range(groups)],'nu_sigma_f':[float(x[nu+g])*float(x[fis+g]) for g in range(groups)]})
m=gdb.parse_and_eval('material')
while m.type.code==gdb.TYPE_CODE_REF:m=m.referenced_value()
b=m['p_vMatSet']['_M_impl']['_M_start'];e=m['p_vMatSet']['_M_impl']['_M_finish'];materials=[]
for i in range(1,int(e-b)):
 mat=b[i];ib=mat['p_vMatNucIndex']['_M_impl']['_M_start'];ie=mat['p_vMatNucIndex']['_M_impl']['_M_finish'];db=mat['p_vMatNucAtomDen']['_M_impl']['_M_start'];de=mat['p_vMatNucAtomDen']['_M_impl']['_M_finish'];indices=[int(ib[j]) for j in range(int(ie-ib))];density=[float(db[j]) for j in range(int(de-db))];macro=[0.]*int(v['p_nNeuMltGrpNum'])
 for index,den in zip(indices,density):
  if index>0:
   for g,x in enumerate(rows[index-1]['nu_sigma_f']):macro[g]+=den*x
 materials.append({'id':i,'nuclide_indices':indices,'density_1e24_per_cm3':density,'nuSigmaF_per_cm':macro})
open('/home/workspace/AI_MC_WW_interation/MLVR_develop/2026-10/20261011_05_f11-prepared-run-lifecycle/logs/implementation/fission-raw-final/nu-sigma-f.json','w').write(json.dumps({'nuclides':rows,'materials':materials},indent=2))
end
continue
python
gdb.execute("quit "+str(int(gdb.parse_and_eval("$_exitcode"))))
end
quit
