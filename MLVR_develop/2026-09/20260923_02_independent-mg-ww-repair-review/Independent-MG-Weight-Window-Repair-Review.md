# Independent MG Weight-Window Repair Review

**Review target:** current uncommitted RMC repair on top of `b7d8a946417eea091a30c09c233054aa077570ee`.

**Independence method:** I first reviewed only the current RMC source, uncommitted diff, RMC user documentation, tests, and basic MG/WW theory. The preliminary conclusion was recorded in [`logs/pre-developer-claim-conclusion.md`](logs/pre-developer-claim-conclusion.md) before the developer task archive was opened. The comparison in §7 was then performed against that archive. No RMC source, test, benchmark, or reference result was modified.

## 1. Independent problem definition

### Particle energy state

In RMC MG transport, `CDParticleState::p_dErg` is **not physical energy**. It is a discrete, reverse-indexed group coordinate. `LocateMgErgGrp()` locates physical energy on the ascending library boundary vector, then returns `G - position` ([GetMgCs.cpp:263-297](../../../RMC/src/GetMgCs.cpp#L263-L297)). `ErgGrp()` rounds the same stored value to an integer ([ParticleState.h:1345-1351](../../../RMC/src/ParticleState.h#L1345-L1351)).

The physical group centres and lower boundaries are stored in ascending physical-energy order, while internal group identifiers run in the opposite direction. `GetMgNeuCentErg(g)` explicitly performs `k=G-g` before returning the physical centre ([GetMgCs.cpp:231-234](../../../RMC/src/GetMgCs.cpp#L231-L234)); the initialization comments confirm the reversed storage relation ([CheckMgAceBlock.cpp:38-49](../../../RMC/src/CheckMgAceBlock.cpp#L38-L49)). Thus internal group 1 is the highest physical group and internal group `G` is the lowest.

Adjoint transport changes the current internal group through the transposed kernel, but it still represents a physical group. An adjoint history therefore needs the same group-to-physical mapping for a user-visible energy-dependent importance field; it does not need a separately reversed WW energy axis.

### Correct native `WWE:N` contract

For a native user input, `WWE:N` should be **physical-energy upper boundaries in MeV**. That is the only useful common contract across CE and MG, forward and adjoint, and it is now documented as such in [VarianceReduction.rst](../../../RMC/docs/source-en/usersguide/VarianceReduction.rst).

However, a MG particle has only a group membership, not an unresolved continuous energy. Therefore an energy-dependent WW is fundamentally a function of `(space, group)` in MG. A physical `WWE:N` boundary that cuts an MG group cannot be resolved exactly. A valid implementation must choose and document one deterministic projection. Current code selects by **group centre**. This is a defensible convention, but it is not physically equivalent to resolving the particle’s unknown sub-group energy.

A stronger long-term interface would either:

1. require/validate that `WWE:N` boundaries coincide with MG boundaries; or
2. convert physical `WWE:N` once during input processing into a group-to-WW-bin table, while rejecting or warning for boundaries strictly inside a group.

Using centre energy at runtime is acceptable only with this explicit limitation.

## 2. Was the original defect real?

**Yes.** Before the current diff, native mesh WW passed `cParticleState.p_dErg` directly into `setMeshWeightWindowBound`; pre-repair [DoMeshWeightWindow.cpp:12-44](../../../RMC/src/DoMeshWeightWindow.cpp#L12-L44) from `HEAD` shows the direct state argument. The native parser reads `WWE:N` values literally into `p_vEnergyBins` ([ReadWeightWindow.cpp:56-84](../../../RMC/src/ReadWeightWindow.cpp#L56-L84)), and the lookup compares that argument numerically with those values ([WeightWindows.cpp:45-51](../../../RMC/src/WeightWindows.cpp#L45-L51)).

The old flow was therefore:

\[
E_{\rm physical}\xrightarrow{\texttt{LocateMgErgGrp}}g_{\rm internal}
\xrightarrow{\text{old native WW lookup}}
\text{compare }g_{\rm internal}\text{ to WWE(MeV)}.
\]

That mixes two coordinate systems. It is a real defect whenever `WWE:N` is interpreted as physical energy, as the repaired user documentation now explicitly specifies.

## 3. What the repair actually changed

The uncommitted diff changes nine files; its immutable review copy is [`logs/current-repair.diff`](logs/current-repair.diff).

| Path | Function / change | Assessment |
|---|---|---|
| [WeightWindow.h](../../../RMC/src/WeightWindow.h) | Adds `GetWeightWindowEnergy(CDAceData&, const CDParticleState&)`; threads `CDAceData` through cell/point APIs. | Single native conversion point. |
| [WeightWindows.cpp:72-78](../../../RMC/src/WeightWindows.cpp#L72-L78) | Returns raw state for MCNP WW; otherwise calls `CDAceData::GetErgValue`. | Native MG maps group→centre; CE identity mapping. |
| [DoWeightWindow.cpp](../../../RMC/src/DoWeightWindow.cpp) | Neutron cell WW uses converted lookup energy. | Native cell neutron path covered. |
| [DoMeshWeightWindow.cpp:12-44](../../../RMC/src/DoMeshWeightWindow.cpp#L12-L44) | Native point and track mesh use converted lookup energy. | Native mesh neutron/photon path covered. |
| [GmaGeoTracking.cpp](../../../RMC/src/GmaGeoTracking.cpp) | Passes `CDAceData` to photon cell WW. | MG photon is touched structurally, though not dynamically qualified here. |
| [RayTracking.cpp](../../../RMC/src/RayTracking.cpp), [TrackWithWeightWindow.cpp](../../../RMC/src/TrackWithWeightWindow.cpp) | Propagate `CDAceData` at neutron cell / point-mesh callers. | Completes call chain. |
| English/Chinese VR docs | Adds native `WWE:N` physical-energy and MG centre-energy statement. | Correctly exposes the selected convention. |

Forward and adjoint share this exact helper: there is no adjoint condition in it. This is correct at the coordinate-contract level. CE is passed through by `GetErgValue` ([GetMgCs.cpp:247-260](../../../RMC/src/GetMgCs.cpp#L247-L260)). Electron mesh remains outside the helper, appropriately because MG `GetErgValue` does not support electron.

The MCNP-compatible path is deliberately excluded: `p_bUseMCNPweightwindow` returns raw `p_dErg`. This preserves its old behavior rather than qualifying it. It must not be described as repaired by this change.

## 4. Physics/interface correctness review

### Centre mapping

`GetWeightWindowEnergy()` calls `GetErgValue()`, which maps a neutron group to `GetMgNeuCentErg()` ([WeightWindows.cpp:72-78](../../../RMC/src/WeightWindows.cpp#L72-L78), [GetMgCs.cpp:247-260](../../../RMC/src/GetMgCs.cpp#L247-L260)). It correctly reverses the RMC internal group ordering before selecting the physical centre. No extra adjoint reversal occurs or should occur.

This is **correct with explicit limitations**:

- **WWE boundary exactly at a group boundary:** group-centre selection assigns the entire adjacent group according to its centre; exact floating-point equality of the physical group boundary is not the lookup criterion.
- **WWE boundary inside a group:** physically ambiguous. A centre rule deterministically sends the complete group to one bin; moving the boundary across the centre creates a discontinuous bin change. The code has no input validation or warning for this.
- **Exact WWE boundary comparison:** `GetIntpltPos()` uses `upper_bound`; equality is assigned to the lower-index interval, while the final upper endpoint is clamped back to the last valid interval by [WeightWindows.cpp:50-51](../../../RMC/src/WeightWindows.cpp#L50-L51). This is internally deterministic but undocumented at the equality level.
- **Lowest/highest group:** `GetErgValue` itself correctly maps both extremes through the reverse index. Source values outside the library are clamped by `LocateMgErgGrp` with warnings. The same mapped group then selects its centre’s WW interval.
- **Single interval:** works only by omitting `WWE:N`; native parser already initializes a zero lower edge and later appends infinity. An explicit `WWE:N 0` creates an additional interval. This pre-existing parser behavior remains and is documented in the developer archive but not in user documentation.
- **Multiple intervals:** physical ordering is assumed; no check that `WWE:N` values are ascending, positive, align with MG boundaries, or cover desired physical ranges.

### Layer of repair

The runtime helper fixes the actual immediate defect and is small, shared, and CE-safe. It is therefore not merely cosmetic. But the **input contract remains incomplete** because the parser accepts unresolved within-group boundaries without declaring the centre convention in input validation or warning. A group-to-bin table prepared at input time would make the discrete contract visible and testable. The present repair is consequently correct in its chosen convention, but incomplete as an interface hardening measure.

## 5. Edge cases and hidden risks

1. **Inside-group WWE boundaries — Requires limitation.** The choice of group centre is not an exact physical boundary decision. Require MG-aligned `WWE:N` for unambiguous physics, or warn/reject otherwise.
2. **No direct selected-bin oracle — Requires test.** PTRAC records split/roulette, not chosen WW-bin index or lower bound. Event count is only an indirect signal.
3. **MCNP WW input — Not covered.** The raw group coordinate exception preserves pre-existing semantics and should have an independent contract audit.
4. **MG photon — Not dynamically verified.** The helper supports photons, but test evidence for MG photon is absent here.
5. **Cell and native track-mesh — code-covered.** The helper reaches both. Point mesh is code-covered but not separately dynamics-tested.
6. **CE — structural identity plus independent smoke.** `GetErgValue` returns CE `p_dErg`; a CE native case ran successfully below, but a controlled CE reference regression remains preferable.
7. **Deep test source warning and RNG independence.** The independently generated deep case used a 2 MeV source that RMC warned was above the library range, then clamped. Further, the generated fixed-source input omitted an RNG card because that card’s parser interaction with the ADJOINT input was not part of this review. The five runs are consequently repeat executions, not verified independent seed streams. The deep result is only a deterministic smoke regression, not a valid five-seed statistical study.

## 6. Independent test design and results

### Test A — MG forward bin-selection

**Design.** A three-WW-bin native mesh input used physical boundaries `WWE:N 0.1 0.5` and distinct lower bounds `0.1, 1.0, 5.0`. Source energies 0.01, 0.2, and 1.0 MeV were run in the same 30-group water problem. These do not prove an exact group-bin mapping because PTRAC lacks bin IDs, but the immediate WW outcome changes as expected under centre lookup: 0.01 MeV starts with splitting; 0.2 MeV starts with roulette; 1 MeV starts with roulette against the highest window. Raw PTRAC and summaries are in [`logs/bin-selection/`](logs/bin-selection/).

**Result.** **Supports** physical-centre lookup and rules out the previous obvious integer-vs-MeV comparison for these probes. It does **not** meet the stronger requested standard of directly observing the selected lower bound.

### Test B — MG adjoint bin-selection

**Design.** The same physical-energy boundaries and source probes were run with fixed-source MG adjoint enabled.

**Result.** The corresponding 0.01 MeV run starts with splitting, while 0.2 and 1 MeV runs start with roulette. Code inspection confirms no adjoint branch changes the helper mapping. Each adjoint input emitted the existing source-above-library warning due to its max-adjoint setting/source handling, so this is a behavioral smoke test, not a clean oracle. It supports a shared physical-coordinate lookup but does not directly record bin IDs.

### Test C — boundary cases

**Design required for acceptance.** Three group MG library or test-configured boundaries are needed to test exact equality, inside-group boundary, and extreme groups. The oracle must report the selected WW bin/lower bound—not infer it from random split counts.

**Result.** **Not implemented by current RMC diagnostics. Cannot verify from current evidence.** This is the material remaining gap. The proper test should add a test-only observable or use a public lookup-level unit test, without changing production physics behavior.

### Test D — CE regression

A CE water native-WW smoke case using the same `WWE:N 0.1 0.5` boundaries completed for all three source energies. This is consistent with the identity branch. It is not a reference-result regression and does not prove all CE modes.

### Test E — deep penetration regression

I independently generated a 100 cm water-slab MG-adjoint native-WW-on/off configuration with a physical `WWE:N 1` boundary and duplicated spatial windows across its two energy bins. Both paths completed; the repeated paired output gave \(z=-0.17667\) and an apparent FOM ratio 0.523. **This is not accepted as a statistical validation**, because the generated repeated runs did not establish independent RNG streams and the WW tables were intentionally identical between energy bins. It does show the repaired energy-dependent parser/lookup path did not crash the selected deep geometry.

The developer’s separately claimed deep benchmark is discussed only in §7 and is not adopted as independent evidence.

## 7. Comparison with developer claim

The developer archive was opened only after writing the preliminary conclusion preserved in [`logs/pre-developer-claim-conclusion.md`](logs/pre-developer-claim-conclusion.md).

### Agreement

- The original coordinate defect is real.
- `WWE:N` should be physical energy, and a shared MG group→physical conversion is appropriate.
- `GetErgValue` is the existing RMC centre-energy projection and is correctly reused.
- Forward/adjoint must share the conversion; CE should remain an identity branch.
- Native cell/track/point lookup call chains are the intended scope; MCNP WW is excluded.

### Difference / omissions found

1. The developer conclusion says the repair is complete for its stated contract. I find the **contract itself remains under-specified** for a WWE boundary inside a group. Centre selection is a valid convention, not a physically unique interpretation.
2. The developer V2/V3 uses collision-rate/event behavior as a bin oracle. That is indirect. No test records selected energy-bin index or selected lower bound, leaving Test A/B short of the requested proof and Test C absent.
3. The developer archive itself lists inside-group boundary sensitivity as uncovered. This is not a minor peripheral case: it is the core consequence of presenting `WWE:N` as a physical-energy interface over a discrete MG state.
4. The independent deep smoke cannot reproduce a valid five-independent-seed study because of input/RNG parser constraints encountered here. I do not dispute the developer’s archived result, but I do not treat it as independently reproduced.

## 8. Final verdict

# Repair is correct with explicit limitations

The repair correctly removes the demonstrable native MG coordinate mismatch by mapping the reverse internal group state to the corresponding physical group centre before native `WWE:N` selection. It applies consistently to forward and adjoint use of the shared helper and retains CE behavior through the identity branch. It is the right immediate root-cause fix for native cell and track/point mesh WW lookup.

It is not an unconditional approval because a physical `WWE:N` edge inside an MG group has no unique physical meaning and the code neither validates nor warns about that condition. The next decision should be an interface rule—not a new transport fix: require MG-aligned `WWE:N` boundaries or document/enforce the group-centre projection explicitly at parse time. Add a deterministic selected-bin test covering forward, adjoint, boundaries, and extremes before calling the contract fully qualified.
