# Stage 2 Independent Source Call-Graph Audit

**Review basis:** current `RMC` at `330f091eb0296e0d0124237ba7d9a22b81aee852`, inspected on 2026-10-11. This file records source facts and distinguishes them from the Stage 2 proposal.

## SOURCE FACT — current ordinary fixed-source path

```text
main
  → CDCalMode::RunCalculation
       (several model/work objects passed by value)
  → CDCalMode::CalcFixedSource
       → InitializeFixedSourceModel
            → CDFixedSource::InitiateAll
       → ExecuteFixedSourcePrepared
            → the one existing six-mode source/batch/history/descendant loop
       → FinalizeFixedSourceRun
            → CDTally::ProcessTally
       → ordinary output and process-facing tail
```

- `RunCalculation` receives neutron transport, geometry, material, particle state, tally, burnup and sampling by value, while ACE data, fixed source, RNG and external source are passed by reference ([RunCalculation.cpp:6-13](../../../../RMC/src/RunCalculation.cpp#L6-L13)). A caller cannot use repeated `RunCalculation` calls as a persistent-model interface: the calculation acts on new copies of several objects and tally registration keeps object-internal pointers.
- The ordinary fixed-source wrapper starts its timer, constructs a local `CBurnup`, then calls the three Stage 1 helpers in order ([CalcFixedSource.cpp:67-83](../../../../RMC/src/CalcFixedSource.cpp#L67-L83)). Its external source remains an **ordinary-call local copy** ([CalMode.h:223-227](../../../../RMC/src/CalMode.h#L223-L227)).
- `InitializeFixedSourceModel` executes the full existing initialization via `CDFixedSource::InitiateAll` and subsequent particle/electron preparation ([CalcFixedSource.cpp:114-139](../../../../RMC/src/CalcFixedSource.cpp#L114-L139)). It is explicitly documented as a one-time initialization, not a repeat-run reset ([CalMode.h:229-235](../../../../RMC/src/CalMode.h#L229-L235)).
- `ExecuteFixedSourcePrepared` is **private**, not a public lifecycle interface ([CalMode.h:172-247](../../../../RMC/src/CalMode.h#L172-L247)). It contains the sole production transport suite: in neutron mode it adds a sentinel, distributes batches, samples each source history, transports/drains descendants, reduces each history, and finishes batches ([CalcFixedSource.cpp:156-259](../../../../RMC/src/CalcFixedSource.cpp#L156-L259)). The other five particle-mode branches are in the same function.
- `FinalizeFixedSourceRun` contains the only `CTally.ProcessTally` call in this suite ([CalcFixedSource.cpp:772-775](../../../../RMC/src/CalcFixedSource.cpp#L772-L775)). Ordinary output, optional WWG/MPI/Python tail and timer stop remain in the wrapper ([CalcFixedSource.cpp:85-112](../../../../RMC/src/CalcFixedSource.cpp#L85-L112)).

## SOURCE FACT — no current production Stage 2 entry

A source-tree symbol search found only the Stage 1 helpers. None of the designed Stage 2 symbols exists in `RMC/src`:

```text
InitializePreparedFixedSourceRuns  absent
RunPreparedFixedSource             absent
FinishPreparedFixedSourceRuns      absent
PrepareFixedSourceRun              absent
ResetRunState / ResetRunScores     absent
ClearPreparedDerivedData           absent
ConfigurePreparedType2Substream    absent
ResetForPreparedRun                absent
```

The `RMC` diff from `330f091e` to current `HEAD` is empty. Therefore the existing helpers are a safe extraction seam for ordinary one-shot execution, but they are not callable proof of a prepared repeated-run contract.

## INFERENCE — required production topology

The Stage 2 proposal's direction is structurally appropriate: a caller holding one stable set of model objects would need a separately named public series API, while the three Stage 1 helpers remain private implementation details. Such an API must call the existing core exactly once per half-run and must not call `RunCalculation` repeatedly or copy an initialized tally/model owner.

## REVIEW CONCLUSION

The “one execution loop / no hidden bypass token” prerequisite is satisfied by Stage 1 source structure. The repeated-run lifecycle prerequisite is **not implemented**. No current caller can establish the proposed persistent owner binding, prepare a run, or finalize and return a receipt under a formal contract.
