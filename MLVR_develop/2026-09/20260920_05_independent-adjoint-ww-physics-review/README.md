# Independent Physics Review Report

- **Task mode:** C — independent physics audit
- **Date:** 2026-09-20
- **Code reviewed:** `RMC` revision `b7d8a946417eea091a30c09c233054aa077570ee`
- **Evidence level:** E1 (static source/test evidence only)
- **Scope:** standard MGACE, fixed-source neutron transport, multigroup neutron adjoint, and native RMC weight windows.
- **Excluded:** continuous-energy adjoint; photon and coupled adjoint; AI/ML; and WW generation algorithms.
- **Independence boundary:** no pre-existing task archive, knowledge-base conclusion, review result, or benchmark interpretation was used. No `RMC/` source file was modified.

## 1. 目标与范围

### 1.1 Review question

Whether the current **multigroup fixed-source adjoint neutron transport + native weight window** path is a physically reliable foundation for deep-penetration bidirectional iterative weight windows.

The governing comparison is the standard phase-space adjoint identity, with the angular convention stated explicitly:

\[
\langle \psi^\dagger,L\psi\rangle=\langle L^\dagger\psi^\dagger,\psi\rangle .
\]

A code path is not classified as physically supported merely because individual routines compile or a reference-result regression exists. It must preserve the transpose kernel, the stochastic change-of-measure weights, and the weight-window unbiasedness condition.

### 1.2 Evidence boundaries

The source tree contains no executable `RMC`/`RMC.exe` in the reviewed checkout, so no dynamic numerical case was run. The test inputs contain three `ADJOINT` occurrences and no input containing both `ADJOINT` and `WEIGHTWINDOW`/`WWMESH`/`WWP`; exact command output is archived at `logs/revision-and-coverage.txt`.

Therefore all source-supported statements below are static-code findings, and all estimator-level claims remain subject to the missing numerical tests in §4.

## 2. 做法与证据

### 2.1 Executive conclusion

**Potential defect — the present combination is not physically supported as a reliable foundation for a multigroup adjoint + native-WW bidirectional framework.**

The multigroup collision construction has a recognizable transpose-kernel implementation and the fixed-source collision weighting is internally consistent with sampling forward free flights. However, native WW queries the particle's stored `p_dErg`; multigroup transport overwrites that field with a *reverse-indexed integer group label*, whereas WW input bins are read as raw user numeric values and are not converted to the MG energy/group representation. No compatibility check or combined test exists. Thus a standard physical-energy WW definition can select the wrong WW bin for both forward MG and adjoint MG histories. This can radically change variance reduction and prevents the claimed combined path from being accepted without correction and dedicated validation.

### 2.2 Adjoint transport audit

#### Particle definition and streaming convention

- **Evidence:** `CDFixedSource::SampleNeutronSource` marks all source histories adjoint when global fixed-source adjoint is enabled; source energy is then transformed by `LocateMgErgGrp`. `LocateMgErgGrp` maps physical energy to a reversed integer group index. The state stores the flag in `p_bIsAdjointParticle` and the temporary adjoint sampling quantity in `p_dTempAdjointxSection`.
- **Direction:** Geometry tracking and source/bank copying retain `p_dDir` unchanged. No general negation of the source direction or of every track direction was found in this path. Hence the code's propagated direction is a **transport-direction label**, not demonstrably the conventional mathematical \(\Omega^\dagger\) without an external convention \(\Omega_{\rm code}=-\Omega^\dagger\).
- **Classification:** **Requires verification.** A same-direction transport implementation can represent the adjoint under that relabeling, but the required input/tally directional convention is not encoded or enforced in the inspected code. The complete angular form of the stated inner-product identity therefore **cannot be verified from current evidence**.

#### Multigroup scattering transpose

- **Evidence:** `CDAceData::treatAdjointMaterial` loops over the forward incident group `jg` and forward outgoing group `jh`, adding the forward P0 scattering entry into `p_vAdjointCrossSection[...][jh]`. Thus, at adjoint current group \(jh\), its aggregate collision cross section includes all forward transitions \(jg\!\rightarrow\!jh\): the required row/column interchange.
- `GetMgAdjNeuExitErgMu` starts from the current adjoint group and scans allowable predecessor groups; it selects from the original MG P0 table and then samples the associated angular distribution. Its comment and indexing make the intended energy change upward in physical energy, consistent with reversal of ordinary neutron downscatter.
- **Angular distribution:** the routine reuses the forward tabulated cosine distribution for the reversed transition. Because the scattering cosine is \(\Omega\!\cdot\!\Omega'\), this is compatible with adjoint reciprocity only under the direction relabeling above and provided the MG library's tabulated differential kernel has the corresponding reciprocal convention. That library-level premise was not dynamically checked.
- **Classification:** **Physically supported** for the P0 energy-kernel transpose at source level; **Requires verification** for the full anisotropic/angular adjoint identity.

#### Free flight, nuclide selection, reaction selection, and weight correction

- `SampleFreeFlyDist` samples distance using the ordinary material macro total \(\Sigma_t(g)\), not the aggregate adjoint collision sum. This is physically admissible: the total/removal term is diagonal under the transpose. It is a forward-free-flight proposal for the adjoint collision kernel.
- `CalcMacroXS` separately constructs `adjointAccumulatedCrossSection[g]` as the material-number-fraction-weighted adjoint microscopic collision sum. `SampleColliNuc` samples a nuclide in proportion to its adjoint contribution. `SampleColliType_FixedSrc` samples fission versus scattering from that adjoint contribution.
- After either adjoint scatter or fission selection, the code multiplies history weight by

  \[
  C(g)=\frac{\bar\sigma_{\rm adj}(g)}{\Sigma_t(g)/N_{\rm atom}},
  \]

  which is the change-of-measure factor converting the forward-total collision proposal into the adjoint collision kernel. Multiplying this by the subsequent nuclide/reaction probabilities gives the intended macroscopic transpose kernel divided by the forward collision proposal. Static inspection therefore found **no inherent \(E[W_{\rm adjoint}]\ne W_{\rm physical}\)** error in this specific collision correction.
- The code applies no implicit-capture attenuation for MG adjoint (`TreatImpliCapt` returns immediately), avoiding a second absorption treatment in this path.
- **Classification:** **Physically supported** as a source-level importance-sampling construction, conditional on the stored MG P0 entries and density helper functions having their expected meanings. **Requires verification** by an identity test because the implementation relies on several index/density conventions and does not expose an estimator proof.

#### Adjoint fission

- `treatAdjointMaterial` accumulates \(\nu\Sigma_f(jg)\) over forward parent group \(jg\), then adds \(\chi(jh)\nu\Sigma_f(jg)\) to the adjoint collision sum at current group \(jh\). This matches

  \[
  F^\dagger(jh\!\rightarrow\!jg)=\chi(jh)\,\nu\Sigma_f(jg).
  \]

- `SampleColliType_FixedSrc` first selects the fission part \(\chi(jh)\sum_{jg}\nu\Sigma_f(jg)\), divides out \(\chi(jh)\), then samples `exitGrp` proportional to \(\nu\Sigma_f(jg)\). `GetFissionNeuState` forces one descendant for an adjoint history, restores this sampled group after using the ordinary fission routine only to obtain an isotropic direction, and banks the particle at the corrected parent-history weight.
- The sampled adjoint fission path does not inspect/store a precursor-group state and uses a prompt isotropic direction. For the declared static MG fixed-source scope, this is consistent only when delayed-neutron/precursor physics is excluded from the desired adjoint operator. The source-level \(\nu\) and \(\chi\) transpose is present; delayed terms are not independently verified.
- **Classification:** **Physically supported** for the inspected prompt MG fission transpose; **Requires verification** for library data conventions and any delayed-precursor interpretation.

### 2.3 Weight-window audit

#### Invocation locations

- **Cell WW:** invoked immediately after a successful surface crossing into the new cell, before the next free-flight sample.
- **Track-mesh WW:** for each mesh subsegment, invoked before scoring/moving through that subsegment.
- **Point-mesh WW:** invoked after a fixed mean-free-path substep and before the next substep.

These placements are compatible with standard splitting/roulette, provided each banked clone restarts from the exact event state. WW is not a collision-kernel correction and does not itself change the expected tally when its weight transforms are unbiased.

#### State variables and group convention

- Mesh WW uses position (`GetUniversalMeshIndex`), `p_eParticleType`, `p_dErg`, and weight; it does **not** use direction. A direction-independent WW is theoretically valid, though it cannot exploit directional importance.
- The neutron type remains `Neutron` for adjoint histories. This is expected—the WW should act on the same particle species—but there is no separate adjoint WW type or semantic guard.
- **Potential defect:** in MG transport, `p_dErg` is replaced by integer group number 1…G. WW lookup uses that raw numeric value (`setMeshWeightWindowBound`/cell lookup). `ReadWeightWindowBlock` reads `WWE:N` energy boundaries as raw values and does not call `LocateMgErgGrp` or otherwise translate them. Consequently, a WW entered in conventional physical-energy units (e.g., MeV) is indexed against group labels rather than physical energy. The input interface neither documents nor checks the required alternate representation.
- **Classification:** **Potential defect.** It directly affects the group selected by WW and therefore applies to both MG analog and MG adjoint histories; it is more serious for bidirectional use because a forward/adjoint WW field must share an unambiguous physical group contract.

#### Splitting, roulette, and banking

- Roulette selects survival probability \(w/w_s\) and sets the survivor weight to \(w_s\), so \(E[w_{\rm survive}]=w\).
- Splitting sets the current particle and each of `nNum-1` banked descendants to `tempWeight`; `nNum` is stochastic-rounded from \(w/w_s\). Without the maximum-split cap, total split weight is exactly \(n w_s\) for the realized `n`, and its expectation is \(w\). With the cap, each child is assigned \(w/n_{\max}\), retaining exact total \(w\).
- `CDFixBank` carries position, direction, group-valued energy, weight, time, particle attributes and traversal sets. It does not store `p_bIsAdjointParticle`; on replay `PopParticleOutofStack` restores it from the global fixed-source `p_bIsAdjoint` mode. In a pure global adjoint fixed-source run, this reconstructs the flag. It is not a self-contained bank representation and would be unsafe for a future mixed forward/adjoint particle bank.
- **Classification:** **Physically supported** for expected-weight roulette/splitting and pure-mode replay; **Requires verification** for actual Monte Carlo conservation over many histories and **Potential defect** if the design ever permits a mixed-mode bank.

### 2.4 Adjoint + WW coupling audit

#### Double correction

The adjoint collision correction \(C(g)\) and WW operations have distinct roles. WW roulette/splitting operates on the already-corrected particle weight and has conditional expectation equal to that input weight. Static tracing shows WW does not reference `p_dTempAdjointxSection`, `adjointAccumulatedCrossSection`, or reapply \(C(g)\). **No direct double-adjoint-correction path was found.**

**Classification: Physically supported** at source level, conditional on the WW group lookup being correct.

#### State consistency

The decisive inconsistency is not an explicit adjoint flag loss during pure-mode replay; it is the **MG-energy representation mismatch** between transport and WW lookup. The same `p_dErg` field serves two incompatible meanings:

1. physical energy when native WW input is read; and
2. reverse-indexed discrete group label after MG source sampling.

No conversion layer, metadata tag, or run-time assertion bridges them. Therefore the combination cannot establish a common physical \((\mathbf r,E,\Omega)\) WW field.

**Classification: Potential defect.**

#### Bank state

Split bank copies retain direction, group label, and post-adjoint-correction weight. The global replay restores the adjoint flag. Thus there is no evidence of a *pure-adjoint* split clone silently becoming a forward history. However, this is an implicit global invariant, not data carried by the clone.

**Classification: Requires verification** for full event-state equivalence; **Potential defect** for any mixed-mode extension.

## 3. 决策

### Reviewer determination

- **Do not treat the current MG adjoint + native WW combination as a reliable physical basis** for deep-penetration bidirectional iterative weight windows.
- This is not a proposal to change source code in this task. No code, benchmark, reference result, or model was changed.
- The blocking issue is the unverified/likely incorrect WW energy-group contract; it must be resolved and then falsified with independent numerical tests before any physics claim is made.

### Required disposition before use

1. Define one explicit contract for a WW energy coordinate in MG runs: physical energy boundaries with conversion at lookup, or discrete group indices with validated ordering. The contract must state the forward and adjoint mapping.
2. Demonstrate the complete adjoint identity numerically, including an anisotropic scattering case if angular data are supported.
3. Demonstrate WW unbiasedness on the exact adjoint+WW path—not a separate forward WW regression and not an adjoint-only reference comparison.

## 4. 结论与边界

### 4.1 Confirmed correct items

| Item | Classification | Basis |
|---|---|---|
| MG scattering P0 aggregate is assembled by forward incident-to-outgoing entries into the adjoint current group. | **Physically supported** | Static loop/index structure in `treatAdjointMaterial`. |
| Prompt MG fission transpose structurally forms \(\chi(g')\nu\Sigma_f(g)\). | **Physically supported** | Adjoint fission aggregate and conditional parent-group sampling. |
| Forward-total free-flight proposal plus collision factor \(\bar\sigma_{adj}/\bar\sigma_t\) is a valid importance-sampling form. | **Physically supported** | Static probability/weight chain. |
| WW roulette and splitting conserve weight in expectation, including the split cap branch. | **Physically supported** | Direct algebra of `DoWeightWindows`. |
| WW does not visibly apply the adjoint collision correction a second time. | **Physically supported** | Separate code paths and variables. |

### 4.2 Potential physics risks

| Risk | Classification | Evidence and consequence |
|---|---|---|
| MG stored group index is used directly as WW “energy”; WW input boundaries are not translated to group coordinates. | **Potential defect** | Can choose an incorrect WW bin, invalidating a physical \(E\)-dependent window for forward and adjoint runs. |
| Full angular adjoint convention is implicit. | **Requires verification** | No global direction reversal; correctness depends on an unstated \(\Omega_{code}=-\Omega^\dagger\) interpretation and compatible source/tally conventions. |
| No combined adjoint+WW regression/physics test. | **Requires verification** | Test input search found no test that activates both. Separate regressions cannot establish coupled unbiasedness. |
| Split bank does not carry an adjoint-mode flag. | **Requires verification** in the pure global mode; **Potential defect** for mixed-mode extension | Replay restores the flag only from global `p_bIsAdjoint`. |
| Delayed precursor-group adjoint treatment is not established. | **Requires verification** | Scope/source evidence only supports the prompt MG fission path. |

### 4.3 Missing verification: minimum independent test suite

#### Test A — adjoint identity test

Construct a finite, fixed-source, two-region two- or three-group neutron problem with non-symmetric downscatter plus upscatter and optional fission. Use a prescribed forward source \(q\) and adjoint source \(q^\dagger\), and score the same phase-space quadrature/tallies on both sides:

\[
I_1=\langle \psi^\dagger,L\psi\rangle,\qquad
I_2=\langle L^\dagger\psi^\dagger,\psi\rangle.
\]

Requirements:

- run with no WW;
- use known MG boundaries and print both physical-energy and stored-group mappings;
- include a directional source/crossing tally that can distinguish \(\Omega\) from \(-\Omega\);
- report \((I_1-I_2)/\sqrt{\sigma_{I_1}^2+\sigma_{I_2}^2}\), not only relative difference;
- acceptance: statistically consistent with zero at a predeclared threshold (for example, absolute normalized difference \(\le 2\));
- repeat with prompt fission on and off. A delayed case is separate unless the delayed adjoint operator is explicitly specified.

#### Test B — WW unbiasedness test

Use the same fixed-source MG geometry and response, then run independent random seeds for:

1. analog forward or the defined adjoint baseline, as appropriate to the response;
2. the identical problem with native WW enabled; and
3. the exact MG adjoint + WW combination.

Use deliberately nonuniform spatial and group-dependent windows that force both roulette and splitting. For each response compare

\[
Z=\frac{R_{WW}-R_{analog}}{\sqrt{\sigma_{WW}^2+\sigma_{analog}^2}}.
\]

Acceptance: predeclare \(|Z|\le2\) for each response/group, with no selective exclusion of zero-score bins. Repeat the exact case using (a) physical-energy WW boundaries and (b) explicitly translated group boundaries. A discrepancy between (a) and (b) is a direct falsification of the present interface contract.

#### Test C — single-particle weight conservation

Instrument a deterministic unit/integration harness around `DoWeightWindows`, independent of production tallies:

- roulette: fixed \(w<w_l\), at least \(10^6\) RNG trials; verify the sample mean total alive weight against \(w\), with standard error;
- splitting: test integer and noninteger \(w/w_s\), and the `MXSPLN` cap path; verify each realization’s total clone weight and the ensemble mean;
- replay each banked clone through one free-flight/collision and assert preservation of position, direction, group label, weight, particle type, and adjoint mode;
- run under the exact global adjoint fixed-source mode.

### 4.4 Final assessment

| Question | Assessment | Basis |
|---|---|---|
| Is the MG adjoint collision construction plausibly a transpose implementation? | **Physically supported**, with angular/data convention limits | Transposed P0/fission aggregation and matched proposal-weight correction are present. |
| Does the inspected code prove \(\langle\psi^\dagger,L\psi\rangle=\langle L^\dagger\psi^\dagger,\psi\rangle\)? | **Requires verification** | Static source cannot establish the full directional, angular, tally, and data-library identity. |
| Is native WW algebraically unbiased when applied to a valid state/window? | **Physically supported** | Roulette/splitting expected-weight algebra is correct. |
| Is current MG adjoint + native WW physically ready for bidirectional iterative deep-penetration use? | **Potential defect** | WW group/energy semantic mismatch plus absence of any combined numerical test prevents a reliable physical claim. |

**Cannot verify from current evidence:** numerical adjoint reciprocity, anisotropic-kernel correctness, benchmark-level response unbiasedness, delayed-neutron adjoint behavior, MPI behavior, and the correctness of any WW field generated outside the native input path.

## 5. 过程

1. Created an independent Mode-C audit record.
2. Inspected only `RMC` source files and test inputs relevant to MG adjoint fixed-source transport and native WW; no prior reports, knowledge base, or historical conclusions were consulted.
3. Traced source conversion, free flight, nuclide/reaction selection, scattering/fission sampling, WW invocation, split banking, and bank replay.
4. Searched test inputs for combined `ADJOINT` and WW activation; none was found.
5. No source, test, reference result, benchmark, branch, commit, or push operation was performed.
