from pathlib import Path
import compare_lifecycle as c
import copy,json,struct,sys
T=Path(__file__).resolve().parents[1];src=T/'logs/gates-04/ff/fresh-1/1-legacy.json'
a=json.loads(src.read_text());results=[]
def mutate(name,modify,expect):
 b=copy.deepcopy(a);modify(b);c.errors.clear();c.allowed.clear();c.compare(a,b,'run1/legacy');passed=(bool(c.errors)==expect)
 results.append({'name':name,'expected_rejection':expect,'passed':passed,'errors':list(c.errors),'time_exceptions':list(c.allowed)})
def change(v):
 raw=bytearray.fromhex(v['bits'])
 if not raw:v.update(n=1,bits=struct.pack('<d',1.).hex());return
 raw[0]^=1;v['bits']=raw.hex()
for field in ['p_vRe','p_vSum3']:
 mutate(field,lambda b,f=field:change(b['p_OCellTallyData'][f]),True)
for field in ['p_vpdfx','p_vpdfy','p_vLargestScore','p_vSum3','p_vSum4','p_vMeanBehaviourCheck','p_vVoVValueCheck']:
 mutate('statistics/'+field,lambda b,f=field:change(b['p_OCellTallyData']['statistics'][f]),True)
mutate('unknown-field',lambda b:b['p_OCellTallyData']['statistics'].update(unknown=0),True)
mutate('missing-field',lambda b:b['p_OCellTallyData']['statistics'].pop('p_vSum4'),True)
for field in sorted(c.TIME):
 mutate('allowed/'+field,lambda b,f=field:change(b['p_OCellTallyData']['statistics'][f]),False)
mutate('time-check-domain',lambda b:b['p_OCellTallyData']['statistics']['p_vFoMValueCheck'].update(bits=struct.pack('<i',2).hex()),True)
mutate('time-shape',lambda b:b['p_OCellTallyData']['statistics']['p_vTime'].update(n=100),True)
mutate('time-category',lambda b:b['p_OCellTallyData']['statistics']['p_vFoMTot'].update(bits=struct.pack('<d',float('nan')).hex()),True)
# Receipt flags are exact, never part of the StatisticsTester timing exceptions.
for f in ['unitSourceWeightsVerified','statisticsFomIsRunMetric','statisticsTimingScope','timingScope']:
 x=json.loads((T/'logs/gates-04/ff/persistent/receipt-1.json').read_text());y=copy.deepcopy(x);y[f]=not y[f] if isinstance(y[f],bool) else 'invalid';c.errors.clear();c.compare(x,y,'receipt');results.append({'name':'receipt/'+f,'expected_rejection':True,'passed':bool(c.errors),'errors':list(c.errors)})
(T/'logs/comparator-selftest.json').write_text(json.dumps(results,indent=2));print({'passed':sum(x['passed'] for x in results),'total':len(results)});sys.exit(not all(x['passed'] for x in results))
