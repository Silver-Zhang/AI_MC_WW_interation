#!/usr/bin/env python3
"""Frozen deterministic comparisons. No result-dependent tolerance changes."""
import csv, json, math, struct
from pathlib import Path

def read_snapshots(folder, rid):
    return [json.loads(x) for x in (Path(folder)/(rid+'.snapshots.jsonl')).read_text().splitlines()]

def phase(folder,rid,name):
    rows=[x for x in read_snapshots(folder,rid) if x['phase']==name]
    if len(rows)!=1: raise ValueError((folder,rid,name,len(rows)))
    return rows[0]

def tally_text(path):
    rows=[]
    for line in Path(path).read_text().splitlines():
        x=line.split()
        if len(x)==7 and x[:3]==['1','1','1'] or len(x)==7 and x[:3]==['2','1','1']:
            rows.append((x[3],x[4],x[5],x[6]))
        elif len(x)==4 and x[0].isdigit(): rows.append(tuple(x))
        elif len(x)==3 and x[0]=='Tot': rows.append((x[0],None,x[1],x[2]))
    if len(rows)!=62: raise ValueError(('expected 62 text rows',path,len(rows)))
    return rows

def exact_diff(a,b,path=''):
    if isinstance(a,dict) and isinstance(b,dict):
        if set(a)!=set(b):return {'path':path,'left_keys':sorted(a),'right_keys':sorted(b)}
        for key in a:
            d=exact_diff(a[key],b[key],path+'/'+str(key))
            if d:return d
    elif isinstance(a,list) and isinstance(b,list):
        if len(a)!=len(b):return {'path':path,'left_length':len(a),'right_length':len(b)}
        for i,(x,y) in enumerate(zip(a,b)):
            d=exact_diff(x,y,path+'/'+str(i))
            if d:return d
    elif isinstance(a,(float,int)) and isinstance(b,(float,int)):
        if isinstance(a,int) and isinstance(b,int):ok=a==b
        else:ok=struct.pack('!d',float(a))==struct.pack('!d',float(b))
        if not ok:return {'path':path,'left':a,'right':b}
    elif a!=b:return {'path':path,'left':a,'right':b}
    return None

def canonical(s):
    s=json.loads(json.dumps(s))
    for k in ['run_id','phase','addresses','cumulative_calls']:s.pop(k,None)
    s['tally']['statistics'].pop('timing_dependent',None)
    return s

def compare_end(folder1,folder2,rid,phase1='after_tally_finalize_before_output',phase2='after_tally_finalize_before_output'):
    a=phase(folder1,rid,phase1);b=phase(folder2,rid,phase2)
    d=exact_diff(canonical(a),canonical(b))
    return {'equal':d is None,'first_divergence':d,'left_phase':phase1,'right_phase':phase2}

def end_checks(s,case):
    t=s['tally']; n=case['population']
    checks={'completed':s['completed']==n and s['completed_rank']==n,
      'normalization':s['starting_weight_denominator']==n,
      'source_weight':s['sources_type_fraction_weight_energy_points']==[[1,1,1,2,case['source_x'],0,0]],
      'empty_descendants':s['raw_particle_stacks']==[0,1,0,0],
      'no_external_banks':s['external_neutron_bank']==s['external_photon_bank']==s['external_neutron_count']==s['external_photon_count']==0,
      'registry':s['registry_size']==1 and s['registry_points_to_mesh_owner']==[1],
      'field_shape':len(t['p_vAve'])==62 and len(s['mg_lowers_MeV'])==30,
      'finish':s['finish']==5,
      'active_role':bool(s['fixed_adjoint'])==bool(s['ace_adjoint'])==bool(s['particle']['role'])==case['adjoint'],
      'touched_empty':all(not t[k] for k in ['p_setScoreIndex','p_vScoreIndex2','p_vScoreStride'])}
    return checks

def reset_checks(s,n):
    t=s['tally'];stats=t['statistics']
    checks={k:all(v==0 for v in t[k]) for k in ['p_vScore','p_vScoreTemp','p_vSum1','p_vSum2','p_vAve','p_vRe']}
    checks.update({'touched_empty':all(not t[k] for k in ['p_setScoreIndex','p_vScoreIndex2','p_vScoreStride']),
      'banks_empty':s['raw_particle_stacks']==[0,0,0,0], 'completed_zero':s['completed']==s['completed_rank']==0,
      'denominator_zero':s['starting_weight_denominator']==0,'finish_ready':s['finish']==-1,
      'registry':s['registry_size']==1 and s['registry_points_to_mesh_owner']==[1],
      'unique_stat_indices':len(stats['p_vIndexOfTallyData'])==len(set(stats['p_vIndexOfTallyData']))})
    for key in ['p_vSum1','p_vSum2','p_vSum3','p_vSum4','p_vNpsStored','p_vCurrentBatch','p_vNonZeroNum','p_vTempNum','p_vTempScores','p_vLargestScore']:
        checks['statistics/'+key]=all(x==0 for x in stats[key])
    for key in ['Time','LargestTime']:
        checks['statistics/'+key]=all(x==0 for x in stats['timing_dependent'][key])
    checks['stat_batch_population']=all(x==n//20 for x in stats['p_vNpsPerBatch'])
    return checks

def memory_text(s,path):
    rows=tally_text(path);t=s['tally'];checks=[]
    for i,(group,lower,ave,re) in enumerate(rows):
        checks.append(ave==format(t['p_vAve'][i],'.4E') and re==format(t['p_vRe'][i],'.4E'))
        if i%31==30:checks.append(group=='Tot')
        else:checks.append(group==str(i%31+1) and lower==format(s['mg_lowers_MeV'][i%31],'.4E'))
    return {'equal':all(checks),'rows':len(rows),'first_bad_check':next((i for i,x in enumerate(checks) if not x),None)}

def boundary_checks(s):
    e=s['physical_edges_MeV'];c=s['mg_centres_MeV'];l=s['mg_lowers_MeV']
    close=lambda a,b:abs(a-b)<=max(1e-14,1e-12*max(abs(a),abs(b)))
    checks={'length31':len(e)==31,'finite':all(math.isfinite(x) for x in e),'ascending':all(a<b for a,b in zip(e,e[1:])),
      'highest_upper':close(e[-1],2*c[-1]-l[-1]),'lower_memory':e[:-1]==l,'unit':'MeV'}
    for i,(nc,nw) in enumerate(zip(s['nuclide_centres_MeV'],s['nuclide_widths_MeV'])):
        checks[f'nuclide{i+1}_centre_width']=all(close(e[g],nc[g]-nw[g]/2) and close(e[g+1],nc[g]+nw[g]/2) for g in range(30))
    return checks

def field(s):
    t=s['tally'];return {'value':[t['p_vAve'][i*31:i*31+30] for i in range(2)],'RE':[t['p_vRe'][i*31:i*31+30] for i in range(2)],'Tot':[t['p_vAve'][30],t['p_vAve'][61]],'Tot_RE':[t['p_vRe'][30],t['p_vRe'][61]],'physical_edges_MeV':s['physical_edges_MeV'],'shape':[2,30], 'group_order':'physical ascending','normalization_denominator':s['starting_weight_denominator'],'unit':'source-normalized track-length flux density; cm^-2 per unit starting source weight'}
