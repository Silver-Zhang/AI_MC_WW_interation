"""Exact physical comparisons; only the closed Stage2 time-field list is excepted."""
from pathlib import Path
import argparse,json,hashlib,gzip,math,struct,sys
T=Path(__file__).resolve().parents[1]
TIME={'p_vTime','p_vLargestTime','p_vFoMPerCycle','p_vFoMTot','p_vFlucFOM','p_vFoMValueCheck','p_vFoMBehaviourCheck'}
errors=[];allowed=[]
def time_field(a,b,path):
 if type(a)!=type(b):errors.append(path+':type');return
 if isinstance(a,list):
  if len(a)!=len(b):errors.append(path+':length');return
  for i,(x,y) in enumerate(zip(a,b)):time_field(x,y,path+'/'+str(i))
 elif isinstance(a,dict):
  if set(a)!=set(b) or set(a)!={'n','element','bits'}:errors.append(path+':keys');return
  if (a['n'],a['element'])!=(b['n'],b['element']):errors.append(path+':shape');return
  if 'double' in a['element']:
   def decode(x):return list(struct.unpack('<'+'d'*x['n'],bytes.fromhex(x['bits'])))
   for x,y in zip(decode(a),decode(b)):
    def kind(z):return 'nan' if math.isnan(z) else 'inf' if math.isinf(z) else 'finite'
    if kind(x)!=kind(y) or (math.isfinite(x) and (x<0 or y<0)):errors.append(path+':numeric-category')
  if 'int' in a['element']:
   for v in (a,b):
    if any(x not in (0,1) for x in struct.unpack('<'+'i'*v['n'],bytes.fromhex(v['bits']))):errors.append(path+':check-domain')
  if a!=b:allowed.append(path)
 elif a!=b:errors.append(path+':unexpected-time-representation')
def compare(a,b,path=''):
 if isinstance(a,(int,float)) and not isinstance(a,bool) and isinstance(b,(int,float)) and not isinstance(b,bool):
  if a!=b:errors.append(path)
  return
 if type(a)!=type(b):errors.append(path+':type');return
 if isinstance(a,dict):
  if set(a)!=set(b):errors.append(path+':keys');return
  for k in a:
   if path.endswith('/statistics') and k in TIME and '/clear/' not in path:
    time_field(a[k],b[k],path+'/'+k)
   else:compare(a[k],b[k],path+'/'+k)
 elif isinstance(a,list):
  if len(a)!=len(b):errors.append(path+':length');return
  for i,(x,y) in enumerate(zip(a,b)):compare(x,y,path+'/'+str(i))
 elif a!=b:errors.append(path)
def load(p):return json.loads(p.read_text())
def pair(p,f,number,expected):
 for artifact in ['clear','before-finalize','final','legacy','derived','raw','start','end']:
  compare(load(p/f'{number}-{artifact}.json'),load(f/f'1-{artifact}.json'),f'run{number}/{artifact}')
 a=load(p/f'{number}-trace-summary.json');b=load(f/'1-trace-summary.json')
 compare(a,b,f'run{number}/trace')
 for directory,n in [(p,number),(f,1)]:
  h=hashlib.sha256()
  with gzip.open(directory/f'{n}-trace.jsonl.gz','rb') as inp:
   for line in inp:
    h.update(line)
    kind,event=json.loads(line)
    if kind=='WW_QUERY':
     w=expected['ww'];lower=([.1,1.,.1,1.] if w==1 else [.05,.5,.05,.5])[event['mesh']]
     for key,number_value in [('lower',lower),('survive',lower*3),('upper',lower*5)]:
      if event[key]!=struct.pack('<d',number_value).hex():errors.append(f'run{number}/WW-independent-{key}')
    if kind=='SOURCE' and not(event['adj']==event['aceAdj']==event['fixedAdj']==(expected['role']=='A')):errors.append('transport role mismatch')
  if h.hexdigest()!=load(directory/f'{n}-trace-summary.json')['sha256']:errors.append('trace hash mismatch')
 r=load(p/f'receipt-{number}.json');N=expected['N']
 for name,wanted in [('requestedHistories',N),('completedHistories',N),('normalizationDenominator',N),('effectiveSeed',expected['seed']),('historyOffset',expected['offset']),('unitSourceWeightsVerified',True),('statisticsFomIsRunMetric',False),('statisticsTimingScope','legacy_mixed_not_per_run'),('timingScope','prepare+transport+finalize')]:
  if r[name]!=wanted:errors.append(f'run{number}/receipt/{name}')
 compare(r['sourceWeightAudit'],{'sampledHistories':N,'nonUnitHistories':0,'initialWeightSum':float(N),'minimumInitialWeight':1.,'maximumInitialWeight':1.},f'run{number}/audit')
 # JSON integer/double lexical forms are equivalent numeric evidence here.
 terms=[r[k] for k in ['prepareSeconds','transportSeconds','tallyFinalizeSeconds']]
 if any(not math.isfinite(x) or x<0 for x in terms) or terms[0]+terms[1]+terms[2]!=r['mcSeconds']:errors.append('timing sum')
 if abs(r['mcSeconds']-r['measuredMcSeconds'])>8*sys.float_info.epsilon*max(1,abs(r['measuredMcSeconds'])):errors.append('timing boundary')
 if r['maximumHistoryDraws']>r['stride']:errors.append('stride overflow accepted')
 if expected['ww'] and (a['counts'].get('SPLIT',0)==0 or a['counts'].get('ROULETTE',0)==0 or a['counts'].get('BANK',0)==0):errors.append(f'run{number}/WW coverage')
 if not expected['ww'] and a['counts'].get('WW_QUERY',0):errors.append('WW OFF query')
 if any(v!=1 for v in a['initcounts'].values()):errors.append('model reinitialized')
 if a['counts'].get('FINALIZE_ENTRY')!=1 or a['counts'].get('SOURCE')!=N:errors.append('source/finalize count')
 return r
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('sequence');ap.add_argument('--label',default='gates-01');ap.add_argument('--fresh-label');a=ap.parse_args()
 rows=load(T/'logs/lifecycle-plans.json')[a.sequence];root=T/'logs'/a.label/a.sequence;p=root/'persistent';fresh=T/'logs'/(a.fresh_label or a.label)/a.sequence
 for row in rows:pair(p,fresh/('fresh-'+str(row['id'])),row['id'],row)
 identities=[load(p/f"{row['id']}-identity.json") for row in rows]
 if any(x!=identities[0] for x in identities):errors.append('model owner/raw identity changed')
 resource=[line.split('\t') for line in (p/'resources.tsv').read_text().splitlines()]
 if len(resource)!=len(rows) or any(x[2:-4]!=resource[0][2:-4] for x in resource):errors.append('FD/registry identity growth')
 if any([v.split(':')[0] for v in x[-4:]]!=['0','1','0','0'] for x in resource):errors.append('live bank remains')
 if a.sequence=='reuse' and any(x[-4:]!=resource[3][-4:] for x in resource[3:]):errors.append('fixed-workload bank capacity growth after warmup')
 if len(resource)>=20 and int(resource[-1][1])-int(resource[3][1])>4096:errors.append('RSS exceeds prespecified 4MiB')
 if a.sequence=='ff':
  gaps=[line.split() for line in (p/'command/stdout.txt').read_text().splitlines() if line.startswith('INTER_RUN_GAP')]
  if len(gaps)!=2 or any(float(x[4])-float(x[3])<.09 for x in gaps):errors.append('Total gap not continuous')
 result={'passed':not errors,'physical_tolerance':0,'errors':errors,'time_exceptions':allowed}
 (root/'comparison.json').write_text(json.dumps(result,indent=2));print(json.dumps(result));sys.exit(bool(errors))
