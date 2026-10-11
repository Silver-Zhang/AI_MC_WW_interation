# Source-level scoring and normalization audit

## SOURCE FACT — score formation

`CDTally::ScoreMeshTallyByTL` selects the mesh splitter according to `p_bIsHeterMesh`: uniform Cartesian uses `CDMesh::CalcMeshTrck`; heter Cartesian uses `CDMesh::CalcHeterMeshTrck ([RMC/src/ScoreMeshTally.cpp:39-50](../../../RMC/src/ScoreMeshTally.cpp#L39-L50)). For every returned segment, it accumulates

```text
p_vScore[mesh, energy] += score(weight) × returned_track_length
```

at [RMC/src/ScoreMeshTally.cpp:60-117](../../../RMC/src/ScoreMeshTally.cpp#L60-L117). There is no later volume factor at that call site.

The uniform splitter records real track length into `CDMeshTrack` ([RMC/src/MeshFun.cpp:270-385](../../../RMC/src/MeshFun.cpp#L270-L385)); the caller’s `p_bUseVol` flag is not consulted by this path. The heter splitter initializes volume to one and, only when `p_bUseVol`, computes `dx×dy×dz` then returns `dTrackLen / dMeshVol` ([RMC/src/MeshFun.cpp:442-485](../../../RMC/src/MeshFun.cpp#L442-L485)). The same volume transformation is used on its crossed-bin path.

## SOURCE FACT — final average

Fixed-source `ProcessTally` sets `dM = p_dTotStartWgt` and `dDiv = 1`, then calls mesh `CalcAveRe` ([RMC/src/ProcessTally.cpp:330-393](../../../RMC/src/ProcessTally.cpp#L330-L393)). `CalcAveRe` uses `Ave = Sum1 / (M × Div)` and computes RE from the history second moment ([RMC/src/TallyData.cpp:83-100](../../../RMC/src/TallyData.cpp#L83-L100)). It performs no spatial volume division.

## Independent conclusion

For the tested Cartesian Type=1 track-length route:

| Representation | Normalize flag | score entering Sum1 | Ave meaning | Field conversion c_i |
|---|---:|---|---|---:|
| uniform | 0 or 1 | w × L | source-normalized weighted track length | 1/V_i |
| heter | 0 | w × L | source-normalized weighted track length | 1/V_i |
| heter | 1 | w × L/V_i | source-normalized volume-average scalar-flux density | 1 |

The test evidence dynamically covers nonunit-volume equal Cartesian bins. The source establishes the path distinction; the dynamic result establishes the stated arithmetic in the frozen fixture.

## MG order

`Energy=-1` substitutes the loaded MG lower-bin vector into the mesh tally at [RMC/src/SingleTally.cpp:875-899](../../../RMC/src/SingleTally.cpp#L875-L899). Source energy is converted to an internal MG group at [RMC/src/SampleNeutronSource.cpp:253-277](../../../RMC/src/SampleNeutronSource.cpp#L253-L277), while mesh scoring uses physical energy through `GetErgValue` before finding the tally bin ([RMC/src/ScoreMeshTally.cpp:87-101](../../../RMC/src/ScoreMeshTally.cpp#L87-L101)). The test correctly records text group 18 and internal group 13 for the 0.6 MeV source; it does not use raw internal group order as Field order.
