#!/usr/bin/env python3
from pathlib import Path
import argparse, hashlib, json, os, shutil, subprocess, time, shlex, sys
import compare
TASK=Path(__file__).resolve().parents[2]
FIX=TASK/'verification/fixtures'
CASES=json.loads((FIX/'manifest.json').read_text())

def save(path,obj):
    Path(path).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')

def execute(label,rids,binary='probe/F11Driver',mode='diagnostic',area='fresh'):
    folder=TASK/'verification'/area/label
    folder.mkdir(parents=True,exist_ok=False)
    for rid in rids:
        src=FIX/(rid+'.inp');assert hashlib.sha256(src.read_bytes()).hexdigest()==CASES[rid]['input_sha256']
        shutil.copyfile(src,folder/('inp_'+rid))
    seq=folder/'sequence.txt';seq.write_text('\n'.join(CASES[r]['sequence_row'] for r in rids)+'\n')
    build_flavor, executable_name=binary.split('/')
    exe=TASK/'verification/build'/build_flavor/'bin'/executable_name
    cmd=[str(exe),'-i','inp_'+rids[0],'-d','/home/silver/NucXS_Library/RMC_DATA']
    env=os.environ.copy(); overrides={'RMC_DATA_PATH':'/home/silver/NucXS_Library/RMC_DATA','F11_OUTPUT':str(folder),'F11_RUN_ID':rids[0],'F11_MODE':mode,'F11_SEQUENCE':str(seq),'OMP_NUM_THREADS':'1'};env.update(overrides)
    record={'command':cmd,'shell_command':shlex.join(cmd),'cwd':str(folder),'environment_overrides':overrides,'binary_sha256':hashlib.sha256(exe.read_bytes()).hexdigest(),'requested_runs':rids,'parent_start_monotonic_ns':None,'parent_end_monotonic_ns':None,'exit_code':None}
    with (folder/'stdout.txt').open('w') as out,(folder/'stderr.txt').open('w') as err:
        start=time.monotonic_ns();record['parent_start_monotonic_ns']=start
        try:r=subprocess.run(cmd,cwd=folder,env=env,stdout=out,stderr=err,timeout=None if mode=='timing' else 180)
        except subprocess.TimeoutExpired:record['exit_code']='TIMEOUT'
        else:record['exit_code']=r.returncode
        record['parent_end_monotonic_ns']=time.monotonic_ns()
    record['total_seconds']=(record['parent_end_monotonic_ns']-start)/1e9
    save(folder/'execution.json',record)
    print(label,record['exit_code'],round(record['total_seconds'],4),flush=True)
    return folder,record

def valid_run(folder,rec):
    if rec['exit_code']!=0:return False
    for rid in rec['requested_runs']:
        if not (folder/('inp_'+rid+'.Tally')).is_file():return False
    return (folder/'stdout.txt').read_text().count('RMC Calculation Finish.')==len(rec['requested_runs'])

def gates():
    findings=[]
    for rid in ['E1_F1','E2_A']:
        base,b=execute('gate_plain_'+rid,[rid],binary='plain/F11Driver')
        probe,p=execute('gate_probe_'+rid,[rid])
        cli,c=execute('gate_cli_'+rid,[rid],binary='probe/RMC')
        validity=all(valid_run(f,r) for f,r in [(base,b),(probe,p),(cli,c)])
        item={'case':rid,'runs_valid':validity,'plain':str(base),'probe':str(probe),'cli':str(cli)}
        if validity:
            item['p0_endpoint_exact']=compare.compare_end(base,probe,rid,'driver_after_return','driver_after_return')
            item['fresh_driver_vs_cli']=compare.compare_end(probe,cli,rid)
            item['text_equal']=compare.tally_text(base/('inp_'+rid+'.Tally'))==compare.tally_text(probe/('inp_'+rid+'.Tally'))==compare.tally_text(cli/('inp_'+rid+'.Tally'))
            item['end_checks']=compare.end_checks(compare.phase(probe,rid,'driver_after_return'),CASES[rid])
            item['p0_identity_note']='P0-disabled driver reads RNG identity and moments only after original CalcFixedSource returns. Full per-history trace exists in P0 build; no claim of an uninstrumented per-history trace.'
            item['pass']=item['p0_endpoint_exact']['equal'] and item['fresh_driver_vs_cli']['equal'] and item['text_equal'] and all(item['end_checks'].values())
        else:item['pass']=False
        findings.append(item)
        save(TASK/'logs/baseline-gates.json',findings)
        if not item['pass']:
            (TASK/'logs/HARNESS_INVALID.txt').write_text(json.dumps(item,indent=2)+'\n')
            print('HARNESS INVALID; all experiments stopped',flush=True);return False
    (TASK/'logs/p0-noninterference.txt').write_text(json.dumps(findings,ensure_ascii=False,indent=2)+'\n')
    return True

def matrix():
    gate=json.loads((TASK/'logs/baseline-gates.json').read_text())
    assert len(gate)==2 and all(x['pass'] for x in gate), 'baseline gates not passed'
    records={}
    for exp in range(1,5):
        ids=[rid for rid in CASES if rid.startswith(f'E{exp}_')]
        fresh={}
        for rid in ids:
            f,r=execute(rid,[rid]);fresh[rid]=str(f)
            if not valid_run(f,r):
                save(TASK/'logs/HARNESS_INVALID.json',{'phase':'fresh','case':rid,'execution':r});return
        seq,rec=execute(f'E{exp}',ids,area='same_process')
        result={'experiment':f'E{exp}','fresh':fresh,'same_process':str(seq),'execution':rec,'comparisons':{},'checks':{},'verdict':'INCONCLUSIVE'}
        if valid_run(seq,rec):
            for index,rid in enumerate(ids):
                f=Path(fresh[rid]);end=compare.phase(seq,rid,'after_tally_finalize_before_output')
                result['comparisons'][rid]=compare.compare_end(f,seq,rid)
                result['checks'][rid]={'end':compare.end_checks(end,CASES[rid]),'memory_text':compare.memory_text(end,seq/('inp_'+rid+'.Tally')),
                  'text_exact':compare.tally_text(f/('inp_'+rid+'.Tally'))==compare.tally_text(seq/('inp_'+rid+'.Tally')),
                  'history_trace_exact':(f/(rid+'.histories.jsonl')).read_bytes()==(seq/(rid+'.histories.jsonl')).read_bytes()}
                if index:result['checks'][rid]['reset']=compare.reset_checks(compare.phase(seq,rid,'after_clear'),CASES[rid]['population'])
                save(TASK/f'verification/E{exp}'/(rid+'.field.json'),compare.field(end))
            result['verdict']='PENDING_ANALYSIS'
        else:
            result['failure']='sequence did not complete; preserve pre/post/hard-fail evidence; category to inspect'
        records[f'E{exp}']=result
        save(TASK/f'verification/E{exp}/comparison.json',result)
    save(TASK/'logs/matrix-execution.json',records)

def e0():
    assert all(x['pass'] for x in json.loads((TASK/'logs/baseline-gates.json').read_text()))
    records=[]
    # Warm-up role F/A; then 7 alternating measured probe runs and paired plain CLI runs.
    for rid in ['E0_F','E0_A']:
        f,r=execute('warmup_'+rid,[rid],binary='probe/RMC',mode='timing',area='E0');records.append({'role':rid[-1],'kind':'warmup','folder':str(f)})
        f,r=execute('warmup_plain_'+rid,[rid],binary='plain/RMC',mode='timing',area='E0');records.append({'role':rid[-1],'kind':'plain_warmup','folder':str(f)})
    for k in range(7):
        for rid in ['E0_F','E0_A']:
            # Alternate pair ordering to avoid always favouring the second process in cache state.
            for b in (['probe','plain'] if k%2==0 else ['plain','probe']):
                f,r=execute(f'measured_{rid}_{k}_{b}',[rid],binary=b+'/RMC',mode='timing',area='E0')
                records.append({'role':rid[-1],'kind':b,'repetition':k,'folder':str(f),'valid':valid_run(f,r)})
    save(TASK/'verification/E0/runs.json',records)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['gates','matrix','e0']);a=p.parse_args()
    if a.stage=='gates':sys.exit(0 if gates() else 2)
    elif a.stage=='matrix':matrix()
    else:e0()
