set pagination off
set confirm off
set print pretty off
python
import gdb, json, hashlib, struct
counts = {}
errors = []
digest = hashlib.sha256()
result = {}
inferior = gdb.selected_inferior

def emit(kind, data):
    counts[kind] = counts.get(kind, 0) + 1
    row = json.dumps([kind, data], sort_keys=True, separators=(',', ':'))
    digest.update((row + '\n').encode())
    print('TRACEJSON ' + row)

def obj(v):
    while v.type.code == gdb.TYPE_CODE_REF:
        v = v.referenced_value()
    if v.type.code == gdb.TYPE_CODE_PTR:
        v = v.dereference()
    return v

def val(name):
    return gdb.parse_and_eval(name)

def bits(v):
    return struct.pack('<d', float(v)).hex()

def vector(v):
    b, e = v['_M_impl']['_M_start'], v['_M_impl']['_M_finish']
    n = int(e-b)
    raw = bytes(inferior().read_memory(b, n*b.type.target().sizeof)) if n else b''
    return {'n': n, 'bits': raw.hex()}

def particle(v):
    v = obj(v)
    return {'pos': [bits(v['p_dPos'][i]) for i in range(3)],
            'dir': [bits(v['p_dDir'][i]) for i in range(3)],
            'w': bits(v['p_dWgt']), 'energy': bits(v['p_dErg']),
            'type': int(v['p_eParticleType']), 'adj': bool(v['p_bIsAdjointParticle']),
            'killed': bool(v['p_bIsKilled'])}

def rng(v):
    v = obj(v)
    gen = v['generator']['_M_ptr'].dereference()
    return dict(type=int(v['type']), **{k: int(gen[k]) for k in
                ['RN_SEED0', 'RN_SEED', 'RN_STRIDE', 'RN_POSITION', 'RN_POSITION_PRE']})

def source(v):
    v = obj(v)
    return {'fraction': vector(v['p_vFraction']), 'bias': vector(v['p_vBiasFrac']),
            'initial_n': int(v['p_nFixedInitSrcBankCount']),
            'initial_p': int(v['p_nFixedInitPhoSrcBankCount'])}

def fixed(v):
    v = obj(v)
    return {k: int(v[k]) for k in ['p_llCurTotParNum', 'p_llCurParNumEachPro',
                                 'p_llCurrentBatch', 'p_nFinishCalculate', 'p_nFixedSrcCount']} | \
           {'denominator_bits': bits(v['p_dTotStartWgt'])}

def tally(v, fields):
    v = obj(v)
    out = {}
    for name in ['p_OCellTallyData', 'p_OMeshTallyData']:
        d = v[name]
        out[name] = {k: vector(d[k]) for k in fields}
    registry = v['p_pTallyDataPointer']
    b, e = registry['_M_impl']['_M_start'], registry['_M_impl']['_M_finish']
    n = int(e-b)
    addresses = {int(v[name].address) for name in ['p_OCellTallyData', 'p_OMeshTallyData']}
    out['registry'] = {'n': n, 'owned': [int(b[i]) in addresses for i in range(n)]}
    return out

class Finish(gdb.FinishBreakpoint):
    def __init__(self, callback):
        super().__init__(gdb.newest_frame(), internal=True)
        self.callback = callback
    def stop(self):
        try:
            self.callback()
            return False
        except Exception as ex:
            errors.append(str(ex)); print('PROBE_ERROR '+str(ex)); return True

class Probe(gdb.Breakpoint):
    def __init__(self, spec, callback):
        super().__init__(spec, internal=True)
        self.callback = callback
    def stop(self):
        try:
            self.callback()
            return False
        except Exception as ex:
            errors.append(str(ex)); print('PROBE_ERROR '+str(ex)); return True

original_source_ptr = None
def run_enter():
    global original_source_ptr
    original_source_ptr = obj(val('cExternalSource')).address
    before = source(original_source_ptr.dereference())
    emit('RUN_SOURCE_BEFORE', before)
    def done():
        after = source(original_source_ptr.dereference())
        result['external_source_unchanged'] = before == after
        emit('RUN_SOURCE_AFTER', after)
    Finish(done)

def wrapper_enter():
    result['source_work_is_copy'] = int(obj(val('cExternalSource')).address) != int(original_source_ptr)
    emit('WRAPPER_COPY', result['source_work_is_copy'])

def sample():
    emit('RNG_BEFORE_SAMPLE', rng(val('ORNG')))
    ptr = obj(val('cParticleState')).address
    Finish(lambda: emit('SOURCE', particle(ptr.dereference())))

def track():
    emit('TRACK', particle(val('cParticleState')))

def segment():
    emit('SEGMENT', particle(val('cParticleState')) | {'length': bits(val('dTrackLen'))})

def history():
    emit('HISTORY_SCORE', tally(val('this'), ['p_vScore']))

def ww():
    state = obj(val('cParticleState'))
    w, lo, hi = float(state['p_dWgt']), float(val('dLowWeightBound')), float(val('dUpperWeightBound'))
    if lo and (w < lo or w > hi):
        kind = 'ROULETTE' if w < lo else 'SPLIT'
        emit(kind, particle(state) | {'lo': bits(val('dLowWeightBound')), 'hi': bits(val('dUpperWeightBound'))})

def bank():
    emit('BANK_SAMPLE', {'rng': rng(val('ORNG')), 'type': int(val('particleType'))})

def process():
    emit('PROCESS_ENTRY', fixed(val('cFixedSource')))
    ptr = val('this')
    emit('STAT_BEFORE', tally(ptr, ['p_vScore', 'p_vScoreTemp', 'p_vSum1', 'p_vSum2']))
    def done():
        stats = tally(ptr, ['p_vScore', 'p_vScoreTemp', 'p_vSum1', 'p_vSum2', 'p_vAve', 'p_vRe'])
        result['final_stats'] = stats
        emit('STAT_AFTER', stats)
    Finish(done)

Probe('CDCalMode::RunCalculation', run_enter)
Probe('CDCalMode::CalcFixedSource', wrapper_enter)
Probe('CDFixedSource::InitiateAll', lambda: emit('INIT', 1))
Probe('CDFixedSource::SampleFixSource', sample)
Probe('CDFixedSource::TrackHistory', track)
Probe('CDTally::TallyByTL', segment)
Probe('CDTally::SumUpTally(long long, double)', history)
Probe('CDWeightWindow::DoWeightWindows', ww)
Probe('CDFixedSource::SampleFromParticleBank', bank)
Probe('CDTally::ProcessTally(CDFixedSource&, CDMaterial&, CDAceData&)', process)
Probe('CDFixedSource::PrcoessBatchEnd', lambda: emit('BATCH_END', fixed(val('this'))))
end
run
python
result['counts'] = counts
result['trace_sha256'] = digest.hexdigest()
result['errors'] = errors
print('DIAGNOSTIC_RESULT ' + json.dumps(result, sort_keys=True))
if errors:
    gdb.execute('quit 2')
end
quit
