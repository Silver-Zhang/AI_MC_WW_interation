from pathlib import Path
import subprocess,concurrent.futures,json,sys,os
P=Path(__file__).resolve().parents[1];R=Path('/tmp/20261012-f11-stage2-p1')
def command(name,argv):
 return name,subprocess.call(['python3',str(P/'tools/run_command.py'),'--log',str(P/name),'--timeout','1500','--',*argv])
commands=[
 ('ordinary-cases-command',['python3',str(P/'tools/run_cases.py'),'refactor']),
 ('ordinary-existing-command',['python3',str(P/'tools/capture_existing.py'),'refactor']),
 ('ordinary-diagnostic-command',['python3',str(P/'tools/diagnose.py'),'refactor']),
 ('gates-command',['python3',str(P/'tools/run_all_lifecycle.py'),'gates-p1-01']),
 ('existing-negatives-command',['python3',str(P/'tools/run_negatives.py'),'negative-p1-01']),
 ('p1-negatives-command',['python3',str(P/'tools/run_p1_negatives.py'),'p1-negative-01']),
 ('universe-persistent-command',['python3',str(P/'tools/run_lifecycle.py'),'universe','--label','universe-01','--trace']),
 ('universe-fresh-command',['python3',str(P/'tools/run_lifecycle.py'),'universe','--label','universe-01','--trace','--fresh']),
 ('linkage-command',['python3',str(P/'tools/check_prepared_linkage.py')]),
 ('ctest-command',['env','-u','RMC_MPI_TEST','-u','RMC_OMP_TEST','RMC_DATA_PATH=/home/silver/NucXS_Library/RMC_DATA','RMC_PATH='+str(R/'stage2-build/bin'),'OMP_NUM_THREADS=1','ctest','--test-dir',str(R/'stage2-build'),'--output-on-failure','-R','^(test_(fixed_source_1|fixed_source_4|fixed_source_adjoint|var_reduce_wwmesh_n|fixed_source_photon|fixed_source_electron|fixed_source_photon_and_electron|fixed_source_neutron_and_photon_and_electron|RestartFixRead)|prepared_source_weight_audit)$'])]
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:results=dict(pool.map(lambda x:command(*x),commands))
for name,cmd in [('ordinary-compare-command',['python3',str(P/'tools/compare.py'),'--label','ordinary-comparison-p1-01']),('universe-compare-command',['python3',str(P/'tools/compare_lifecycle.py'),'universe','--label','universe-01'])]:
 k,v=command(name,cmd);results[k]=v
(P/'regression-command-results.json').write_text(json.dumps(results,indent=2));print(results);sys.exit(any(results.values()))
