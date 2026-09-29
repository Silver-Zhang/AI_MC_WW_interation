#!/usr/bin/env python3
"""Apply the pre-run contract to saved evidence; never rerun or modify RMC."""
from pathlib import Path
import collections,csv,hashlib,json,math,statistics
import compare
TASK=Path(__file__).resolve().parents[2]
CASES=json.loads((TASK/'verification/fixtures/manifest.json').read_text())
def save(path,x):Path(path).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def all_checks(x):
    if isinstance(x,dict):return all(all_checks(v) for v in x.values())
    if isinstance(x,list):return all(all_checks(v) for v in x)
    return x is True

def e0():
    runs=json.loads((TASK/'verification/E0/runs.json').read_text());raw=[]
    for run in runs:
        if run['kind']!='probe':continue
        d=Path(run['folder']);rid='E0_'+run['role'];execution=json.loads((d/'execution.json').read_text())
        events=[json.loads(x) for x in (d/(rid+'.timing.jsonl')).read_text().splitlines()]
        marks={e['name']:e['ns'] for e in events if e['kind']=='mark'}
        stack=[];spans={};quality=[]
        for ev in events:
            if ev['kind']=='begin':stack.append(ev)
            elif ev['kind']=='end':
                if not stack or stack[-1]['name']!=ev['name']:quality.append('unpaired/overlap '+ev['name']);continue
                begin=stack.pop();spans[ev['name']]=(begin['ns'],ev['ns'])
        if stack:quality.append('unclosed intervals')
        duration=lambda name:(spans[name][1]-spans[name][0])/1e9
        start,end=execution['parent_start_monotonic_ns'],execution['parent_end_monotonic_ns']
        total=(end-start)/1e9;lo,hi=spans['transport_loop']
        times={
          'T_process':(marks['main.enter']-start)/1e9,'T_input':duration('input_with_geometry_check'),
          'T_geometry_material_postinput':duration('model_prepare_inclusive')-duration('xs_load_and_mg_prepare')-duration('output.material')-(duration('adjoint_prepare') if 'adjoint_prepare' in spans else 0),
          'T_xs':duration('xs_load_and_mg_prepare'),
          'T_adjoint_prepare':duration('adjoint_prepare') if 'adjoint_prepare' in spans else None,
          'T_transport_prepare':duration('transport_prepare_inclusive')-duration('model_prepare_inclusive'),
          'T_transport':duration('transport_loop'),'T_tally_finalize':duration('tally_finalize'),
          'T_output_material':duration('output.material'),'T_output_tail':duration('output.fixed_source_tail'),'T_output_ending':duration('output.ending'),
          'T_startup_init':(lo-start)/1e9,'T_finalize_output':(end-hi)/1e9,'T_total':total}
        times['T_output_explicit']=sum(times[k] for k in ['T_output_material','T_output_tail','T_output_ending'])
        times['T_startup_glue']=times['T_startup_init']-sum(times[k] for k in ['T_process','T_input','T_geometry_material_postinput','T_xs','T_transport_prepare','T_output_material'])-(times['T_adjoint_prepare'] or 0)
        times['T_shutdown_glue']=times['T_finalize_output']-sum(times[k] for k in ['T_tally_finalize','T_output_tail','T_output_ending'])
        if any(v<0 for v in times.values() if v is not None):quality.append('negative duration')
        closure=abs(total-sum(times[k] for k in ['T_startup_init','T_transport','T_finalize_output']))
        if closure>max(1e-6,total*1e-6):quality.append('three-way closure')
        exclusive=sum(times[k] for k in ['T_process','T_input','T_geometry_material_postinput','T_xs','T_transport_prepare','T_transport','T_tally_finalize','T_output_explicit','T_startup_glue','T_shutdown_glue'])+(times['T_adjoint_prepare'] or 0)
        if abs(total-exclusive)>max(1e-6,total*1e-6):quality.append('exclusive decomposition closure')
        # These observed scopes must have the ancestry assumed when subtracting children.
        contains=lambda parent,child:spans[parent][0]<=spans[child][0]<=spans[child][1]<=spans[parent][1]
        for par,ch in [('transport_prepare_inclusive','model_prepare_inclusive'),('model_prepare_inclusive','xs_load_and_mg_prepare'),('model_prepare_inclusive','output.material')]+([('model_prepare_inclusive','adjoint_prepare')] if run['role']=='A' else []):
            if not contains(par,ch):quality.append('bad ancestry '+par+'/'+ch)
        raw.append({'role':run['role'],'repetition':run['repetition'],'folder':run['folder'],'timing_seconds':times,'startup_fraction':times['T_startup_init']/total,'closure_seconds':closure,'issues':quality})
    roles={}
    for role in ['F','A']:
        rr=[r for r in raw if r['role']==role];aggregate={}
        for key in rr[0]['timing_seconds']:
            values=[r['timing_seconds'][key] for r in rr]
            aggregate[key]=None if values[0] is None else {'mean_s':statistics.mean(values),'sample_std_s':statistics.stdev(values),'mean_fraction_total':statistics.mean(v/r['timing_seconds']['T_total'] for v,r in zip(values,rr))}
        f=[r['startup_fraction'] for r in rr];tot=[r['timing_seconds']['T_total'] for r in rr]
        plain=[r for r in runs if r['role']==role and r['kind']=='plain']
        pvals=[json.loads((Path(r['folder'])/'execution.json').read_text())['total_seconds'] for r in plain]
        pairs=[]
        for r in rr:
            p=next(p for p in plain if p['repetition']==r['repetition'])
            same=compare.tally_text(Path(r['folder'])/('inp_E0_'+role+'.Tally'))==compare.tally_text(Path(p['folder'])/('inp_E0_'+role+'.Tally'))
            pairs.append({'repetition':r['repetition'],'tally_exact':same})
        overhead=statistics.mean(tot)/statistics.mean(pvals)-1
        checks={'seven_complete':len(rr)==7 and len(plain)==7 and all(r['valid'] for r in runs if r['role']==role and r['kind'] in ['plain','probe']),
          'events_accounting':all(not r['issues'] for r in rr),'total_cv_le_10pct':statistics.stdev(tot)/statistics.mean(tot)<=.10,
          'startup_std_le_005':statistics.stdev(f)<=.05,'observer_overhead_le_5pct':overhead<=.05,'paired_physics_outputs':all(p['tally_exact'] for p in pairs)}
        metadata_checks=[]
        for r in runs:
            if r['role']!=role:continue
            m=json.loads((Path(r['folder'])/('E0_'+role+'.run-metadata.json')).read_text())
            metadata_checks.append(m['requested']==m['completed']==m['completed_rank']==m['denominator']==20000 and m['initial_source_weights']==[1] and m['component_probabilities']==[1] and m['component_bias_probabilities']==[1])
        checks['actual_source_normalization_metadata']=len(metadata_checks)==16 and all(metadata_checks)
        for rep in range(7):
            pp=next(r for r in runs if r['role']==role and r['kind']=='probe' and r['repetition']==rep)
            aa=next(r for r in runs if r['role']==role and r['kind']=='plain' and r['repetition']==rep)
            mp=json.loads((Path(pp['folder'])/('E0_'+role+'.run-metadata.json')).read_text());ma=json.loads((Path(aa['folder'])/('E0_'+role+'.run-metadata.json')).read_text())
            checks['paired_endpoint_metadata_'+str(rep)]=compare.exact_diff(mp,ma) is None

        roles[role]={'stages':aggregate,'startup_fraction_mean':statistics.mean(f),'startup_fraction_sample_std':statistics.stdev(f),'total_cv':statistics.stdev(tot)/statistics.mean(tot),'plain_total_mean_s':statistics.mean(pvals),'observer_relative_mean_overhead':overhead,'checks':checks,'pairs':pairs,'verdict':'PASS' if all(checks.values()) else 'INCONCLUSIVE'}
    save(TASK/'verification/E0/timing-decomposition.json',{'raw':raw,'roles':roles,'verdict':'PASS' if all(r['verdict']=='PASS' for r in roles.values()) else 'INCONCLUSIVE','cache_policy':'warm filesystem cache; no cold measurements'})
    return {'verdict':'PASS' if all(r['verdict']=='PASS' for r in roles.values()) else 'INCONCLUSIVE','roles':roles}

def experiments():
    verdicts={}
    for exp in range(1,5):
        out=TASK/f'verification/E{exp}';result=json.loads((out/'comparison.json').read_text());seq=Path(result['same_process']);ids=list(result['fresh']);checks={};state_diffs=[]
        if result['verdict']!='PENDING_ANALYSIS':
            result['verdict']='INCONCLUSIVE';save(out/'verdict.json',result);verdicts[f'E{exp}']=result;continue
        ready=[]
        keys=['model_base','model_base_hash_fnv1a64','raw_mgace_hash_fnv1a64','tally_mesh_geometry','ww_mesh_geometry','mesh_definitions','mg_centres_MeV','mg_lowers_MeV','physical_edges_MeV','ww_energy_bins','ww_parameters','ww_bounds','fixed_adjoint','ace_adjoint','internal_cutoff','internal_photon_cutoff','sources_type_fraction_weight_energy_points','source_probabilities','source_bias_probabilities','rng','requested','completed','completed_rank','finish','starting_weight_denominator','raw_particle_stacks','registry_size','registry_points_to_mesh_owner','tally']
        for index,rid in enumerate(ids):
            fresh=Path(result['fresh'][rid]);before=compare.phase(seq,rid,'before_transport');fb=compare.phase(fresh,rid,'before_transport');end=compare.phase(seq,rid,'after_tally_finalize_before_output');ready.append(before)
            ck=result['checks'][rid]
            checks[rid+'/exact_end']=result['comparisons'][rid]['equal']
            checks[rid+'/end_invariants']=all(ck['end'].values())
            checks[rid+'/text_memory']=ck['memory_text']['equal'] and ck['text_exact']
            checks[rid+'/history_seeds']=ck['history_trace_exact']
            if index:checks[rid+'/reset_zero']=all(ck['reset'].values())
            a={k:before[k] for k in keys};b={k:fb[k] for k in keys}
            a['tally']['statistics'].pop('timing_dependent',None);b['tally']['statistics'].pop('timing_dependent',None)
            d=compare.exact_diff(a,b)
            checks[rid+'/pre_transport_state']=d is None
            if d:state_diffs.append({'case':rid,'phase':'before_transport','divergence':d})
            pa=before['particle'].copy();pb=fb['particle'].copy()
            early_role=(index>0 and CASES[rid]['adjoint'])
            if early_role:
                checks[rid+'/declared_early_particle_role']=pa['role']==1 and pb['role']==0
                pa.pop('role');pb.pop('role')
            d=compare.exact_diff(pa,pb)
            checks[rid+'/particle_cache_pre']=d is None
            if d:state_diffs.append({'case':rid,'phase':'particle_before_transport','divergence':d})
            calls=end['cumulative_calls'];checks[rid+'/one_model_init']=all(calls.get(k)==1 for k in ['input_with_geometry_check','model_prepare_inclusive','xs_load_and_mg_prepare'])
            events=[json.loads(x) for x in (seq/(rid+'.timing.jsonl')).read_text().splitlines()]
            marks=collections.Counter(e['name'] for e in events if e['kind']=='mark')
            checks[rid+'/one_use_token']=marks['prepared_token.armed']==marks['prepared_token.consumed']==(1 if index else 0)
        stable_keys=['geometry','material','ace','nuclides','particle','tally','mesh_data','ww','ww_mesh','ww_energy']
        checks['stable_object_identities']=all(all(s['addresses'][key]==ready[0]['addresses'][key] for key in stable_keys) for s in ready)
        immutable_keys=['model_base','raw_mgace_hash_fnv1a64','mesh_definitions','tally_mesh_geometry','ww_mesh_geometry','ww_energy_bins','ww_parameters','physical_edges_MeV']
        checks['stable_immutable_contents']=all(all(s[key]==ready[0][key] for key in immutable_keys) for s in ready)
        evidence={}
        inconclusive=[]
        if exp==2:
            states=[]
            for rid in ids[1:]:
                z=compare.phase(seq,rid,'mode_zero_base');reb=compare.phase(seq,rid,'after_rebuild_before_arm');fin=compare.phase(seq,rid,'after_tally_finalize_before_output')
                checks[rid+'/adjoint_zero_base']=all(not x for x in z['adjoint_xs']) and all(not x for x in z['adjoint_fission_xs'])
                states.append({'run_id':rid,'physical_cutoff_MeV':reb['physical_max_adjoint_energy_MeV'],'internal_cutoff':reb['internal_cutoff'],'flags_rebuilt':[reb['fixed_adjoint'],reb['ace_adjoint'],reb['particle']['role']], 'flags_final':[fin['fixed_adjoint'],fin['ace_adjoint'],fin['particle']['role']], 'zero_base_adjoint':z['adjoint_xs'],'zero_base_fission':z['adjoint_fission_xs'],'rebuilt_adjoint':reb['adjoint_xs'],'rebuilt_fission':reb['adjoint_fission_xs'],'pre_cache':reb['particle']})
            evidence['role_transition']=states;evidence['limitation']='H2O nonfissile: no validation of nonzero adjoint-fission contributions'
        if exp==3:
            for rid in ids:
                f=Path(result['fresh'][rid]);p=seq/(rid+'.ww.tsv');q=f/(rid+'.ww.tsv')
                sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
                checks[rid+'/full_ordered_ww_trace']=sha(p)==sha(q)
                count=0;bins=collections.Counter();first={};bad=None
                with p.open() as stream:
                    for row in csv.DictReader(stream,delimiter='\t'):
                        count+=1;i=int(row['mesh']);g=int(row['physical_group0']);bin0=int(row['ww_bin0']);low=2.**(-1-i-g%2)/(4 if CASES[rid]['ww']==2 else 1)
                        bins[(i,g)]+=1;first.setdefault((i,g),row)
                        if bad is None and (bin0!=g or float(row['lower'])!=low or float(row['survival'])!=3*low or float(row['upper'])!=5*low or 30-int(float(row['internal_group']))!=g):bad={'event':count,'row':row}
                checks[rid+'/lookup_correct_bounds_and_coordinates']=bad is None
                centres=ready[0]['mg_centres_MeV'];edges=ready[0]['physical_edges_MeV'];sourceg=next(g for g in range(30) if edges[g]<=2<edges[g+1])
                covered=all(bins[(i,sourceg)]>0 for i in [0,1])
                if not covered:inconclusive.append(rid+' source-group selected bin coverage missing')
                evidence[rid]={'events':count,'source_physical_group0':sourceg,'selected_bin_counts':[bins[(i,sourceg)] for i in [0,1]],'selected_first_events':[first.get((i,sourceg)) for i in [0,1]],'all_bin_counts':{f'{i},{g}':n for (i,g),n in sorted(bins.items())},'trace_sha256':sha(p),'first_invalid_lookup':bad}
        if exp==4:
            fractions=[]
            for rid in ids:
                end=compare.phase(seq,rid,'after_tally_finalize_before_output');bc=compare.boundary_checks(end)
                checks[rid+'/boundaries']=all(v for v in bc.values())
                field=compare.field(end);save(out/(rid+'.physical-edges-MeV.json'),end['physical_edges_MeV'])
                save(out/(rid+'.boundary-checks.json'),bc)
                f=compare.phase(Path(result['fresh'][rid]),rid,'after_tally_finalize_before_output')
                fraction=f['tally']['p_vAve'][30]/(f['tally']['p_vAve'][30]+f['tally']['p_vAve'][61]);fractions.append(fraction)
            evidence['fresh_left_flux_fractions']=fractions;evidence['absolute_difference']=abs(fractions[0]-fractions[1]);
            if evidence['absolute_difference']<=.10:inconclusive.append('field patterns not sufficiently discriminating')
        failed=[k for k,v in checks.items() if not v]
        result.update({'checks_frozen_contract':checks,'state_divergences':state_diffs,'direct_evidence':evidence,'coverage_limitations':inconclusive,'failed_checks':failed,'verdict':'FAIL' if failed else ('INCONCLUSIVE' if inconclusive else 'PASS')})
        save(out/'verdict.json',result);verdicts[f'E{exp}']={'verdict':result['verdict'],'failed_checks':failed,'state_divergences':state_diffs,'direct_evidence':evidence,'coverage_limitations':inconclusive}
    return verdicts

if __name__=='__main__':
    results={'E0':e0(),**experiments()}
    save(TASK/'logs/experiment-summary.json',results)
    for k,v in results.items():print(k,v['verdict'],v.get('failed_checks',[]),v.get('coverage_limitations',[]))
