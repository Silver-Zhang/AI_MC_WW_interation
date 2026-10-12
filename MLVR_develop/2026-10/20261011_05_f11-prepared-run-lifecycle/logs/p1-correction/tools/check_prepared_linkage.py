from pathlib import Path
P=Path('/home/workspace/AI_MC_WW_interation/MLVR_develop/2026-10/20261011_05_f11-prepared-run-lifecycle/logs/p1-correction')
from pathlib import Path
import json,subprocess,re
T=P;B=Path('/tmp/20261012-f11-stage2-p1/stage2-build');out=T/'logs/linkage';out.mkdir(exist_ok=True)
records=json.loads((B/'compile_commands.json').read_text());entries={}
for target in ['RMC','RMCPreparedLifecycle']:
 entries[target]={r['file']:r for r in records if '/'+target+'.dir/' in r['output'] or r['output'].startswith('CMakeFiles/'+target+'.dir/')}
 assert entries[target]
common=set(entries['RMC'])&set(entries['RMCPreparedLifecycle']);assert len(common)>300
for f in common:
 def flags(row):return row['command'].split(' -o ')[0]
 assert flags(entries['RMC'][f])==flags(entries['RMCPreparedLifecycle'][f]),f
left=set(entries['RMC'])-common;right=set(entries['RMCPreparedLifecycle'])-common
assert len(left)==1 and next(iter(left)).endswith('/src/main.cpp')
assert {Path(f).name for f in right}=={'driver.cpp','globals.cpp'}
names=['Output','OMeshInfo','OXSParaTableVec','OWeightWindow','OStatus','OTimer','cellVec','OParticleTracker','OController','ORNG','OCalMode','RMC::IO::OLogger','RMC::IO::OProcLogger']
symbols={}
for target in entries:
 text=subprocess.check_output(['nm','-C','--defined-only',str(B/'bin'/target)],text=True);(out/(target+'-nm.txt')).write_text(text)
 parsed=[line.split(maxsplit=2) for line in text.splitlines() if len(line.split(maxsplit=2))==3]
 counts={n:sum(parts[2]==n for parts in parsed) for n in names}
 assert all(v==1 for v in counts.values()),counts;symbols[target]=counts
 assert sum(parts[2]=='main' for parts in parsed)==1
result={'passed':True,'common_production_translation_units':len(common),'ordinary_only':list(left),'harness_only':list(right),'global_definitions':symbols,'compile_options_identical':True}
(out/'result.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
