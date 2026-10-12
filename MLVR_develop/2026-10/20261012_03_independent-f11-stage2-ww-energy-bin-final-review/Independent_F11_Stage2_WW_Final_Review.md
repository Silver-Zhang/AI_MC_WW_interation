# Independent F11 Stage 2 Native WW Energy-Bin Final Review

## Classification

```text
NEEDS CORRECTION
```

## Decision table

| Review item | Classification | Basis |
|---|---|---|
| Prepared WW definition/container contract | PASS, restricted native profile | The common owner validator checks neutron outer/inner shape before indexing, finite strict boundaries, `0`/finite-`1e22` endpoints, scalar constraints, and installed mesh dimensions. |
| WW-OFF lifecycle | PASS | The enabled-only validation and installer return preserve the no-neutron-bin WW-OFF case. |
| Prepared lifecycle validation order | PASS | Bind validation precedes model initialization; run validation precedes definition fingerprint and CLEAR; enabled installation validates before neutron-bin access or state mutation. |
| Endpoint selection in direct native lookup | PASS | Boundary interval indices are clamped to `B-2`; the recorded production-owner lookup covers first/internal/final/above-terminal values and rejects non-finite values passed directly to that method. |
| Non-finite physical MG energy path | **FAIL (P1)** | Native transport converts the raw particle energy with `int(dParticleErg + 0.5)` before it reaches the downstream finite-energy guard. NaN/Inf therefore lack the required controlled rejection before conversion/indexing. |
| Direct prepared installer lower values | **FAIL (P1)** | The separately callable installer validates topology and lower-vector length only. It accepts NaN, non-positive, overflow-producing or split-ratio-invalid lower values and can mutate WW/mode/cutoff state; the corresponding checks exist only in `RunPreparedFixedSource()`. |
| Task02 negative and regression corpus | Artifact-verified, not independently rerun | Archive arithmetic, recorded production guard stacks, deterministic comparisons, and manifest coverage are internally consistent; this review did not rebuild or execute the corpus. |
| Stage 2 final technical acceptance / freeze / submission | Not approved | The two P1s above violate the predeclared controlled-rejection and independent-installer criteria. |
| Stage 3 | Not ready | No Stage 3 work is authorized or implied by this review. |

## What is closed

**SOURCE VERIFIED.** `INFINITY_ENERGY` is the finite value `1.0E+22`, not IEEE infinity ([Constants.h:197](../../../RMC/src/Constants.h#L197)). `ValidatePreparedNativeDefinition()` verifies the outer neutron entry before accessing it, requires `2 <= B <= INT_MAX`, finite/strictly-increasing boundaries, exactly `0` and `INFINITY_ENERGY`, scalar validity, mesh/interval capacity, and installed neutron-only shape ([WeightWindows.cpp:307-346](../../../RMC/src/WeightWindows.cpp#L307-L346)).

**SOURCE VERIFIED.** Prepared initialization invokes the owner validator before model initialization when WW is enabled ([PrepareFixedSourceRun.cpp:171-175](../../../RMC/src/PrepareFixedSourceRun.cpp#L171-L175)). Prepared runs invoke it before definition comparison and before the later CLEAR/reset sequence ([PrepareFixedSourceRun.cpp:248-253](../../../RMC/src/PrepareFixedSourceRun.cpp#L248-L253)). The enabled installer invokes it before the neutron `p_vEnergyBins` access and before updating mode/cutoff state; the disabled path returns without an energy-bin access ([WeightWindows.cpp:354-366](../../../RMC/src/WeightWindows.cpp#L354-L366)).

**SOURCE VERIFIED.** `GetIntpltPos()` maps the terminal boundary and values above it to `B-1` ([GlobeFun.h:141-151](../../../RMC/src/GlobeFun.h#L141-L151)); `setMeshWeightWindowBound()` clamps that result to `B-2`, validates the outer lookup container and direct query energy, and checks serial installed-mesh shape ([WeightWindows.cpp:48-78](../../../RMC/src/WeightWindows.cpp#L48-L78)). Thus B boundaries map to only the legal `0 ... B-2` WW intervals in that method.

**ARTIFACT VERIFIED.** Task02's saved result files record 26 malformed definition mutations in each of bind, post-successful-run, and direct-install phases (78/78); each record names the expected production exception and a `ValidatePreparedNativeDefinition` guard stack. The saved post-run records retain the first `100` histories and report rejection before a second run. The 15/15 owner-lookup output includes final equality, above-terminal finite energy, and direct NaN/±Inf rejection. These are saved Task02 results, not new executions by this review.

**INDEPENDENTLY RECOMPUTED.** The archive count is 78 = 26 mutations × 3 phases. The saved persistent/fresh total is 38 = FF 2 + FAF 3 + AA 2 + WW 4 + FAF+WW 3 + reuse 20 + multi-energy 4. All recorded comparison objects report zero physical tolerance and no comparison errors.

## Remaining P1s

### P1-01 — MG non-finite particle energy reaches conversion before the lookup guard

`DoPointMeshWeightWindow()` and `DoTrackMeshWeightWindow()` call `GetWeightWindowEnergy()` before `setMeshWeightWindowBound()` ([DoMeshWeightWindow.cpp:17-18](../../../RMC/src/DoMeshWeightWindow.cpp#L17-L18), [DoMeshWeightWindow.cpp:42-43](../../../RMC/src/DoMeshWeightWindow.cpp#L42-L43)). For multi-group neutrons, `GetWeightWindowEnergy()` calls `CDAceData::GetErgValue()` ([WeightWindows.cpp:84-90](../../../RMC/src/WeightWindows.cpp#L84-L90)), which converts raw particle energy through `int(dParticleErg + 0.5)` and uses it to index the group-centre array ([GetMgCs.cpp:247-253](../../../RMC/src/GetMgCs.cpp#L247-L253)).

Consequently, the finite guard at [WeightWindows.cpp:57](../../../RMC/src/WeightWindows.cpp#L57) is too late for raw NaN/Inf in the MG transport path. A conversion from non-finite/out-of-range floating point to `int` is not the specified controlled rejection and can precede invalid array access. Task02's 15/15 test injects energy at the owner lookup after conversion, so it does not close this path.

**Minimal correction criterion:** reject non-finite raw particle energy before `GetErgValue()` converts it (or make `GetErgValue()` safely reject it), then add transport-path tests for NaN, `+Inf`, and `-Inf showing the production exception and no out-of-bounds/sanitizer finding.

### P1-02 — `InstallPreparedNativeState()` does not independently validate lower values

The direct installer checks role, enabled topology and lower-vector **length**, then resets mode/cutoff and calls `ProcessWeightWindow()` ([WeightWindows.cpp:354-370](../../../RMC/src/WeightWindows.cpp#L354-L370)). It does not verify each lower value is finite and positive, that derived survival/upper values remain finite and ordered, or that the split/cross-window bounds are representable. Those checks live only in `RunPreparedFixedSource()` ([PrepareFixedSourceRun.cpp:269-285](../../../RMC/src/PrepareFixedSourceRun.cpp#L269-L285)).

A caller that invokes the public installer directly with correctly sized NaN, zero, negative, overflow-producing, or ratio-invalid lowers can therefore write malformed window values and alter lifecycle state. This contradicts the pre-review rule that a separately callable installer cannot rely on run validation for its safety.

**Minimal correction criterion:** centralize the existing per-lower derived-bound and split-ratio validation in a non-mutating helper used by both Run and enabled Install. Add direct-install negatives for NaN, zero/negative, overflow and cross-window ratio inputs; prove the exception precedes any WW/mode/cutoff mutation.

## Scope and limitations

The two P1s do **not** negate the substantial Task02 repair for malformed prepared native definition containers or terminal interval indexing. They prevent final acceptance because the independently written criteria require controlled non-finite energy handling along the real native path and independent installer safety.

Not verified in this review: a fresh independent build or rerun; MPI/OMP runtime/build; ordinary malformed parser input; ordinary MCNP-specific WW regression; full-program sanitizer/leak checking; a physical MC source at the finite `1e22` sentinel; and Stage3 TARGET/Field/FOM. The MPI shared-memory branch also lacks the serial branch's mesh-index/shape checks ([WeightWindows.cpp:62-70](../../../RMC/src/WeightWindows.cpp#L62-L70)); prepared mode rejects MPI, so this is recorded as an out-of-profile residual rather than a third Stage2 prepared P1.

No RMC source, test input, nuclear data, reference, frozen design, branch, commit, or push was changed by this review.
