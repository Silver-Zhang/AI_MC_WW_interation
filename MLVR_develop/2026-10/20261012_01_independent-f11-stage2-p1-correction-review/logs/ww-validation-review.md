# Native WW Validation Review

## SOURCE FACT — closed scalar/derived portion

`RMC/src/PrepareFixedSourceRun.cpp:63-75` validates the WWP parameter vector shape before indexing it and requires:

- finite `WUPN > 2`;
- finite `1 < WSURVN < WUPN`;
- finite integral `MXSPLN` in `[2, INT_MAX]`.

It is called at bind time (`:187`) and each prepared run before definition comparison (`:263-266`). Derived lower/survival/upper and split representation checks occur at `:291-301`.

These checks match native roulette/splitting operations in `RMC/src/WeightWindows.cpp:130-152`, including a `double` to `int` split count conversion and possible increment.

## SOURCE FACT — remaining blocker

The WW energy-bin topology is not validated before neutron indexing:

```cpp
const auto &bins = OWeightWindow.p_vEnergyBins[1];
```

at `RMC/src/PrepareFixedSourceRun.cpp:286`. The later inner-size check at `:287-288` is too late. `checkNativeParameters()` covers only `p_vWeightWindowPara`, not `p_vEnergyBins`. `RMC/src/WeightWindows.cpp:310-312` also indexes the same neutron energy-bin entry during native prepared-state installation.

Because `p_vEnergyBins` is public caller-visible `vector<vector<double>>` state, clearing it or shrinking it to one outer entry can cause out-of-bounds access before the intended prepared rejection.

A second native precondition is also unvalidated. `RMC/src/WeightWindows.cpp:45-66` calls `GetIntpltPos` with `max = bins.size()-1`. That helper returns `max` when `erg >= bins.back()` (`RMC/src/GlobeFun.h:141-151`), but the native adjustment only handles `erg > bins.back()` (`WeightWindows.cpp:50-52`). Therefore `erg == bins.back()` reaches `p_vMeshInformation[...][ergPos]` with `ergPos == bins.size()-1`, while valid WW-window indices end at `bins.size()-2`. Prepared validation does not require finite, strictly increasing boundaries or a valid terminal boundary; `ReadWeightWindow.cpp:56-82` accepts raw WWE values before appending the nominal infinite endpoint at `:419-427`.

## DYNAMIC EVIDENCE

Task05's 51 P1 negatives prove intended scalar/derived guards both before binding and after a valid first run, including preserved state on post-run rejection. The driver has no mutation hook or negative case for an empty/short outer energy-bin vector or a neutron entry with fewer than two boundaries.

## REVIEW CONCLUSION

`FAIL`. The P1-02 requirement is not fully closed. Future repair must validate outer and neutron-entry energy-bin shapes before every prepared neutron index, then add initial and post-run malformed-shape regression cases proving rejection before CLEAR.
