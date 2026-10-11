"""Read-only checks of production/baseline; writes task evidence and patch snapshots."""
from pathlib import Path
import json,hashlib,subprocess,struct,datetime
T=Path(__file__).resolve().parents[1];ROOT=T.parents[2];R=Path('/tmp/20261011_05_f11-prepared-run-lifecycle');CODE=ROOT/'RMC'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def git(repo,*args):return subprocess.check_output(['git','-C',str(repo),*args],text=True).strip()
approved={x['path'] for x in read(T/'logs/design-revision/planned-files.json')['files']}
tracked=git(CODE,'diff','--name-only').splitlines();new=git(CODE,'ls-files','--others','--exclude-standard').splitlines()
assert set(tracked+new)==approved
start=read(T/'logs/implementation/start.json');assert git(CODE,'rev-parse','HEAD')==start['RMC']['rev-parse HEAD']['stdout'].strip();assert git(ROOT,'rev-parse','HEAD')==start['.']['rev-parse HEAD']['stdout'].strip()
protected=read(T/'logs/design-revision/start.json')['protected_sha256'];unchanged=[]
for name,h in protected.items():
 if name.startswith('RMC/') and name.removeprefix('RMC/') in approved:continue
 assert sha(ROOT/name)==h,name
 unchanged.append(name)
for f,h in start['source_sha256'].items():assert sha(R/'baseline-src'/f)==h,f
source={str(p.relative_to(CODE)):sha(p) for p in (CODE/'src').rglob('*') if p.is_file()}
for f,h in source.items():assert sha(R/'stage2-src'/f)==h,f
for f in approved:assert sha(CODE/f)==sha(R/'stage2-src'/f),f
original=(R/'baseline-src/src/CalcFixedSource.cpp').read_text();current=(CODE/'src/CalcFixedSource.cpp').read_text()
def core(s):return s[s.index('void CDCalMode::ExecuteFixedSourcePrepared'):s.index('void CDCalMode::FinalizeFixedSourceRun')]
assert core(original)==core(current)
(T/'changes.diff').write_bytes(subprocess.check_output(['git','-C',str(CODE),'diff','--binary']))
parts=[]
for name in new:
 result=subprocess.run(['git','diff','--no-index','--binary','--','/dev/null',str(CODE/name)],capture_output=True);assert result.returncode==1
 # Absolute no-index file names are normalized to repo-relative paths for review/apply.
 raw=result.stdout.replace(('a'+str(CODE)+'/').encode(),b'a/').replace(('b'+str(CODE)+'/').encode(),b'b/')
 parts.append(raw)
(T/'new-files.diff').write_bytes(b''.join(parts))
D=T/'logs/gates-04';rows=[]
for seq in ['ff','faf','aa','ww','faf-ww','reuse']:
 assert read(D/seq/'comparison.json')['passed'];assert (D/seq/'compare-command/exitcode.txt').read_text().strip()=='0'
 p=D/seq/'persistent'
 for rfile in sorted(p.glob('receipt-*.json'),key=lambda f:int(f.stem.split('-')[-1])):
  r=read(rfile);i=r['runId'];summary=read(p/f'{i}-trace-summary.json');v=read(p/f'{i}-final.json')['p_OMeshTallyData'];starts=read(p/f'{i}-start.json')
  def last(v):return struct.unpack('<'+'d'*v['n'],bytes.fromhex(v['bits']))[-1]
  rows.append({'sequence':seq,**r,'events':summary['counts'],'trace_sha256':summary['sha256'],'mesh_last_bin_total_Ave':last(v['p_vAve']),'mesh_last_bin_total_RE':last(v['p_vRe']),'cutoffs':starts})
assert len(rows)==34
resource=[l.split('\t') for l in (D/'reuse/persistent/resources.tsv').read_text().splitlines()]
summary={'half_runs':len(rows),'histories_per_side':sum(r['completedHistories'] for r in rows),'rss_warm4_kib':int(resource[3][1]),'rss_run20_kib':int(resource[-1][1]),'rss_growth_kib':int(resource[-1][1])-int(resource[3][1]),'fd_count_including_directory_entries':int(resource[0][2]),'rows':rows}
(T/'logs/gate-results.json').write_text(json.dumps(summary,indent=2))
neg=read(T/'logs/negative-final-02/results.json');assert len(neg)==66 and all(r['passed'] for r in neg)
assert all(r['hdf_pass'] and r['all_emitted_pdf_pass'] for r in read(T/'logs/exports-final/ff/comparison.json'))
assert read(T/'logs/ordinary-comparison-final-03/results.json')['all_passed']
assert all(r['passed'] for r in read(T/'logs/comparator-selftest.json'))
assert (T/'logs/implementation/final-ctest-02/exitcode.txt').read_text().strip()=='0'
binaries={n:{'path':str(R/'stage2-build/bin'/n),'sha256':sha(R/'stage2-build/bin'/n)} for n in ['RMC','RMCPreparedLifecycle']}
assert binaries['RMC']['sha256']==read(T/'logs/refactor-binary.json')['sha256']
base=read(T/'logs/baseline-freeze.json');db={f:sha(Path(f)) for f in base['database']};assert db==base['database']
assert sha(R/'baseline-build/bin/RMC')==base['binary_sha256']
manifest={'time':datetime.datetime.now().astimezone().isoformat(),'root_head':git(ROOT,'rev-parse','HEAD'),'root_branch':git(ROOT,'branch','--show-current'),'rmc_head':git(CODE,'rev-parse','HEAD'),'rmc_branch':git(CODE,'branch','--show-current'),'rmc_upstream_ahead_behind':git(CODE,'rev-list','--left-right','--count','HEAD...@{upstream}'),'rmc_status':git(CODE,'status','--short'),'source_sha256':source,'approved_files':sorted(approved),'tracked_modified':tracked,'new_files':new,'source_matches_built_private_copy':True,'baseline_sources_and_binary_unchanged':True,'unchanged_protected_file_count':len(unchanged),'transport_core_byte_unchanged':True,'binaries':binaries,'database':db,'build_identity':{str(p):sha(p) for p in [R/'stage2-build/CMakeCache.txt',R/'stage2-build/compile_commands.json',R/'stage2-build/CMakeFiles/RMC.dir/flags.make']},'patch_sha256':{name:sha(T/name) for name in ['changes.diff','new-files.diff']},'final_gate_label':'gates-04','all_restricted_gates_passed':True,'independent_review':'pending','commits_or_pushes_by_agent':False}
(T/'logs/implementation/final-manifest.json').write_text(json.dumps(manifest,indent=2))
lines=['# 最终逐run摘要','', '原始RMC mesh第4空间bin总能群Ave/RE，不是新增Field API。所有N/D/W0及IEEE位模式的完整证据见logs/gates-04；计时含调试观察开销，不能用于性能评价。','', '| 序列/run | role | N = D = W0 | effective seed | max draws | 原始Ave | RE | split/roulette/bank |','|---|---|---:|---:|---:|---:|---:|---|']
for r in rows:
 e=r['events'];lines.append(f"| {r['sequence']}/{r['runId']} | {r['role']} | {r['completedHistories']} | {r['effectiveSeed']} | {r['maximumHistoryDraws']} | {r['mesh_last_bin_total_Ave']:.17g} | {r['mesh_last_bin_total_RE']:.17g} | {e.get('SPLIT',0)}/{e.get('ROULETTE',0)}/{e.get('BANK',0)} |")
(T/'run-results.md').write_text('\n'.join(lines)+'\n')
print(json.dumps({'passed':True,'modified_files':len(approved),'half_runs':34,'histories_per_side':summary['histories_per_side'],'rss_growth_kib':summary['rss_growth_kib'],'binaries':binaries},indent=2))
