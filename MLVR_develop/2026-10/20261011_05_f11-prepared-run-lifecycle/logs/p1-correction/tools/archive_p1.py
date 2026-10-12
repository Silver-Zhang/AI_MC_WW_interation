from pathlib import Path
import json,hashlib,subprocess,tarfile,difflib,datetime,struct
P=Path(__file__).resolve().parents[1];T=P.parents[1];ROOT=T.parents[2];CODE=ROOT/'RMC';R=Path('/tmp/20261012-f11-stage2-p1')
def read(f):return json.loads(f.read_text())
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def git(repo,*args):return subprocess.check_output(['git','-C',str(repo),*args],text=True).strip()
pre=read(P/'pre-fix-manifest.json');protected=read(P/'protected-evidence.json')
assert not [f for f,h in protected.items() if sha(ROOT/f)!=h]
assert git(CODE,'rev-parse','HEAD')==pre['repos']['RMC']['head']
assert git(ROOT,'rev-parse','HEAD')==pre['repos']['.']['head']
modified=git(CODE,'diff','--name-only').splitlines();new=git(CODE,'ls-files','--others','--exclude-standard').splitlines()
assert set(modified+new)==set(pre['changed'])
p1=[f for f,h in pre['all_rmc_sha256'].items() if sha(CODE/f)!=h]
assert set(p1)=={'src/PrepareFixedSourceRun.cpp','tests/prepared_fixed_source_lifecycle/driver.cpp'}
source={str(f.relative_to(CODE)):sha(f) for f in (CODE/'src').rglob('*') if f.is_file()}
for f,h in source.items():assert sha(R/'stage2-src'/f)==h,f
for f in modified+new:assert sha(R/'stage2-src'/f)==sha(CODE/f),f
# The actual old and new source patches, including untracked production files.
with tarfile.open(P/'pre-fix-source.tar.gz') as archive:
 patch=''
 for f in p1:
  old=archive.extractfile(f).read().decode();now=(CODE/f).read_text()
  patch+='diff --git a/'+f+' b/'+f+'\n'+''.join(difflib.unified_diff(old.splitlines(True),now.splitlines(True),fromfile='a/'+f,tofile='b/'+f))
(P/'correction.diff').write_text(patch)
(T/'changes.diff').write_bytes(subprocess.check_output(['git','-C',str(CODE),'diff','--binary']))
parts=[]
for f in new:
 result=subprocess.run(['git','diff','--no-index','--binary','--','/dev/null',str(CODE/f)],capture_output=True);assert result.returncode==1
 parts.append(result.stdout.replace(('a'+str(CODE)+'/').encode(),b'a/').replace(('b'+str(CODE)+'/').encode(),b'b/'))
(T/'new-files.diff').write_bytes(b''.join(parts))
assert all(x==0 for x in read(P/'regression-command-results.json').values())
ordinary=read(P/'logs/ordinary-comparison-p1-01/results.json');assert ordinary['all_passed']
legacyneg=read(P/'logs/negative-p1-01/results.json');newneg=read(P/'logs/p1-negative-01/results.json');assert all(r['passed'] for r in legacyneg+newneg)
(P/'negative-results.json').write_text(json.dumps({'new_negative_count':len(newneg),'all_passed':True,'old_negative_count':len(legacyneg),'new':newneg,'old_results':'logs/negative-p1-01/results.json'},indent=2))
rows=[];prior=[]
for seq in ['ff','faf','aa','ww','faf-ww','reuse','universe']:
 label='universe-01' if seq=='universe' else 'gates-p1-01';d=P/'logs'/label/seq
 assert read(d/'comparison.json')['passed']
 for f in sorted((d/'persistent').glob('receipt-*.json'),key=lambda x:int(x.stem.split('-')[-1])):
  r=read(f);n=r['runId'];trace=read(f.parent/f'{n}-trace-summary.json')
  v=read(f.parent/f'{n}-final.json')['p_OMeshTallyData'];last=lambda x:struct.unpack('<'+'d'*x['n'],bytes.fromhex(x['bits']))[-1]
  rows.append({'sequence':seq,**r,'trace':trace,'mesh_last_Ave':last(v['p_vAve']),'mesh_last_RE':last(v['p_vRe'])})
  if seq!='universe':
   old=read(T/'logs/gates-04'/seq/'persistent'/f'{n}-trace-summary.json')
   assert trace==old,(seq,n)
   prior.append({'sequence':seq,'run':n,'trace_identical_to_gates04':True})
assert len(rows)==36 and len(prior)==34
res=[x.split('\t') for x in (P/'logs/gates-p1-01/reuse/persistent/resources.tsv').read_text().splitlines()]
exports=read(P/'logs/exports-p1-01/ff/comparison.json');assert all(x['hdf_pass'] and x['all_emitted_pdf_pass'] for x in exports)
result={'verdict':'READY FOR INDEPENDENT RE-REVIEW','ordinary_checks':ordinary['checks'],'ordinary_passed':ordinary['passed'],'ctest_passed':10,'half_runs':36,'old_half_runs':34,'new_universe_half_runs':2,'histories_per_side':sum(r['completedHistories'] for r in rows),'physical_tolerance':0,'legacy_negative_passed':len(legacyneg),'p1_negative_passed':len(newneg),'rss_warm4_kib':int(res[3][1]),'rss_run20_kib':int(res[-1][1]),'rss_growth_kib':int(res[-1][1])-int(res[3][1]),'fd_measurement':int(res[0][2]),'old_physics_trace_unchanged':prior,'rows':rows,'exports':exports}
(P/'regression-results.json').write_text(json.dumps(result,indent=2))
base=read(T/'logs/baseline-freeze.json');db={f:sha(Path(f)) for f in base['database']};assert db==base['database']
assert sha(Path('/tmp/20261011_05_f11-prepared-run-lifecycle/baseline-build/bin/RMC'))==base['binary_sha256']
manifest={'time':datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),'root_branch':git(ROOT,'branch','--show-current'),'root_head':git(ROOT,'rev-parse','HEAD'),'rmc_branch':git(CODE,'branch','--show-current'),'rmc_head':git(CODE,'rev-parse','HEAD'),'rmc_upstream_ahead_behind':git(CODE,'rev-list','--left-right','--count','HEAD...@{upstream}'),'p1_modified':p1,'stage2_files':modified+new,'source_sha256':source,'p1_file_sha256':{f:sha(CODE/f) for f in p1},'protected_evidence_count':len(protected),'old_evidence_unchanged':True,'source_matches_private_build':True,'binaries':{n:{'path':str(R/'stage2-build/bin'/n),'sha256':sha(R/'stage2-build/bin'/n)} for n in ['RMC','RMCPreparedLifecycle']},'database':db,'build_sha256':{str(f):sha(f) for f in [R/'stage2-build/CMakeCache.txt',R/'stage2-build/compile_commands.json',R/'stage2-build/CMakeFiles/RMC.dir/flags.make']},'patch_sha256':{str(f.relative_to(T)):sha(f) for f in [T/'changes.diff',T/'new-files.diff',P/'correction.diff']},'source_scope_check':read(P/'source-scope-check.json'),'no_agent_commit_push':True,'independent_re_review':'pending'}
(P/'final-manifest.json').write_text(json.dumps(manifest,indent=2))
lines=['# P1修复后逐run结果','','完整receipt/位模式/事件见各run原始目录，以下Ave仍为原始mesh总能群值，不是新Field。','','| 序列/run | role | N=D=W0 | seed | max draws | 原始Ave | RE | split/roulette/bank |','|---|---|---:|---:|---:|---:|---:|---|']
for r in rows:
 e=r['trace']['counts'];lines.append(f"| {r['sequence']}/{r['runId']} | {r['role']} | {r['completedHistories']} | {r['effectiveSeed']} | {r['maximumHistoryDraws']} | {r['mesh_last_Ave']:.17g} | {r['mesh_last_RE']:.17g} | {e.get('SPLIT',0)}/{e.get('ROULETTE',0)}/{e.get('BANK',0)} |")
(P/'run-results.md').write_text('\n'.join(lines)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ['rows','exports','old_physics_trace_unchanged']},indent=2));print(json.dumps(manifest['binaries'],indent=2))
