# Independent Review — F11 Task 13 E0–E4 Dynamic Evidence

> **Scope:** Independent review of Task 13’s task-private dynamic evidence. No RMC transport was rerun.  
> **Overall verdict:** **ACCEPT WITH LIMITATIONS.** The preserved dynamic evidence supports E0–E4 only under the explicit serial H2O experimental lifecycle contract. Archive integrity has one README manifest mismatch, so local auditability is reduced from the claimed fully clean state.

## 1. Scope

Task 13 claims E0–E4 PASS for a task-private experimental lifecycle. This review tested whether its raw evidence, fresh oracles, comparator and lifecycle implementation substantiate those limited claims.

The review does not decide F11 architecture and does not treat a passing test harness as evidence that the current production `main` already supports a persistent session.

## 2. Independent criteria

The pre-Task 13 criteria are in [pre-task13-review-criteria.md](logs/pre-task13-review-criteria.md). They required fresh-process oracles, direct state evidence, post-finalization comparisons, true WW lookup evidence, G+1 physical-energy metadata and an explicit unit-source normalization boundary.

They also required P1 to be evaluated as an experimental control seam, rather than as passive instrumentation or a production-ready capability.

## 3. Provenance

**Accepted with limitations.**

- Shared RMC remains clean at `5cfb0f771d0c5a2127c90d57e51ce672a4e3b616`.
- The task-private snapshot is present. Its complete source hash list validates locally.
- All preserved v1/v2 binary hashes validate locally.
- Task 13 build metadata records an optimized GNU C++ build with serial scope. It has no MPI, OpenMP or AIS enablement.
- The private patch modifies build support, guarded source probes, a conditional friend access seam, and an endpoint collector. It does not alter collision/scattering/fission formulas, tally formulas, relative-error formulas, source sampling mathematics, or splitting/roulette mathematics.

The patch is nevertheless more than observation. P1 skips `InitiateAll` after the driver has prepared a new run state. The resulting evidence proves this explicit driver contract, not default RMC behavior.

## 4. Harness validity

**Accepted with limitations.**

Fresh mode parses input and uses the original `CalcFixedSource` complete initialization and original transport loop. The fresh and same-process E1–E4 records use the same archived v1 probe-driver binary.

Same-process mode retains geometry, material, raw MGACE, tally owner/definitions/registry and WW topology. It does not reread input or reconstruct those objects for second and later runs. The driver explicitly:

- clears fixed-source counters, banks, denominators, source banks, tally statistical arrays and touched indices;
- resets RNG state and population/source position;
- clears mode-derived adjoint arrays and rebuilds only required adjoint data;
- destructs and reconstructs per-particle scratch state in place;
- recomputes WW survival and upper values through the original `ProcessWeightWindow` path;
- consumes the one-use token that bypasses `InitiateAll` for that prepared run.

This behavior follows [run-reset-contract.md](../20260929_13_f11-persistent-session-e0-e4-execution/logs/run-reset-contract.md) and [driver_body.inc](../20260929_13_f11-persistent-session-e0-e4-execution/verification/harness/driver_body.inc). It is deliberately a specific lifecycle implementation. It should not be generalized into a claim that RMC discovers/reset these fields automatically.

No hidden recreation of geometry, material, raw MGACE or tally owner was found in second-run preparation. Reconstructing `CDParticleState` is explicit per-run scratch-state rebuilding and is correctly classified as such.

## 5. Baseline gates

**ACCEPT WITH LIMITATIONS.**

Task 13 has exact fresh-driver versus CLI gates for one Forward and one Adjoint fixture, plus P0-on versus P0-off endpoint comparisons and text output comparisons. The gate records show equal finalized states, equal text and valid run invariants.

This demonstrates that the task-private driver and probes did not change the checked physics outputs for those two fresh cases. It does not prove that the probes are noninterfering for every RMC mode, tally type or threading configuration.

## 6. E0 — performance decomposition

**ACCEPT WITH LIMITATIONS.**

The independent analyzer reran against preserved timing events with writes disabled. It reproduced PASS for both roles.

| Role | Startup/init fraction | Sample standard deviation | Total-time coefficient of variation | Probe overhead |
|---|---:|---:|---:|---:|
| Forward | 2.9563% | 0.00313 | 0.00854 | 0.6832% |
| Adjoint | 36.8838% | 0.02290 | 0.04291 | 0.8400% |

The evidence includes a warmup, seven measured probe/plain pairs for each role, explicit warm-filesystem-cache policy, timing closure gates, paired tally agreement and endpoint normalization metadata.

The timing is valid only for this serial H2O fixture and warm-cache environment. It does not estimate large-model startup savings or prove that a persistent process is faster in production.

## 7. E1 — Forward → Forward

**ACCEPT.**

The second run demonstrably executes its configured history count and matches fresh Forward exactly after tally finalization. The analyzer checks final history count, denominator, bank state, finish value, RNG history sequence, tally data, registry, text output, pre-transport state, one model initialization and one prepared token for Run 2.

The independent reanalysis re-ran those checks without modifying Task 13 evidence. It also spot-checked zero-score and nonzero bins from both runs. The same-process and fresh values match for Sum1, Sum2, Ave and RE in each sampled bin.

This accepts only the explicit lifecycle contract. It does not establish repeated-run support through an ordinary production invocation.

## 8. E2 — Forward → Adjoint → Forward

**ACCEPT WITH LIMITATIONS.**

The final Forward matches its fresh oracle exactly. The preserved snapshots demonstrate Forward, Adjoint and final Forward role flags; physical and internal cutoffs; zero bases before derived-array rebuild; rebuilt adjoint arrays; reset particle cache; and a matching final Forward state.

The direct zero-base evidence matters because `TreatAdjointMaterial` accumulates with `+=`. The driver clears adjoint vectors before invoking it, preventing previous-run accumulation under this contract.

The result does not validate nonzero adjoint-fission rebuild. The H2O fixture is nonfissile and has only the expected zero fission contribution. It also does not validate CE, coupled particles, MPI or OpenMP.

## 9. E3 — WW hot update

**ACCEPT.**

Raw fresh and same-process WW traces are locally present. The independent analyzer reproduced:

- exact full ordered trace SHA-256 equality for WW1 and WW2;
- direct check of selected mesh/physical-group/WW-bin coordinates;
- direct lower, survival and upper bound checks for every recorded event;
- selected source-group coverage in both spatial bins.

WW2 has 1,247,301 actual lookup events. Its selected source-group examples read lower/survival/upper of `0.125/0.375/0.625` in mesh bin zero and `0.0625/0.1875/0.3125` in mesh bin one. These are the expected WW2 values and differ from WW1.

This is a strong result for a fixed 2×1×1 mesh and 30-group serial contract. It does not cover MPI replicas, other meshes, other particle types or arbitrary WW mutation policies.

## 10. E4 — tally reset and memory Field extraction

**ACCEPT.**

The same tally owner, mesh definition and registry remain stable between runs. Before Run 2, the driver explicitly clears numerical tally arrays and touched/index sets while retaining the owner/definition. The reset assertions require zero Score, ScoreTemp, Sum1, Sum2, Ave and RE, empty touched sets, empty banks, zero completed count and denominator, stable registry, and cleared/re-sized statistics state.

After `ProcessTally`, the full 2×30 Field plus separate Tot values and RE values match fresh snapshots exactly. The memory-to-text comparison validates the sixty group rows plus two Tot rows using the output precision. Independent sampling confirmed zero and nonzero bins for each E4 run.

This is an experiment export, not a production F10 API.

## 11. G+1 physical-energy extraction

**ACCEPT.**

The extracted edge sequence has thirty-one finite, strictly increasing values and ends at 17 MeV. The independent boundary check validates lower-edge identity, final upper-edge construction from centre/lower, and centre/width consistency for both loaded nuclides.

The evidence supports: **RMC MGACE memory contains enough information to construct G+1 physical edges for this fixture.** It does not imply that `.Tally` alone contains a G+1 edge vector. The tally mapping remains explicitly physical ascending while transport group indexing is reversed internally.

## 12. Normalization

**ACCEPT WITH LIMITATIONS.**

Task 13 records requested histories, completed histories, actual denominator, initial component weight, component probability and bias probability. The independent reanalysis confirms the records have unit source weights and probabilities, with denominator equal to completed histories for the frozen fixture.

This equality is fixture-specific. It must not become a general identity for non-unit or multi-component source distributions.

## 13. v1/v2 consistency

**ACCEPT WITH LIMITATIONS.**

E1–E4 use preserved v1 binaries. Final E0 and baseline gates use v2 binaries. The recorded v2 change adds a common post-calculation metadata collector for requested/completed histories, denominator, source weights/probabilities and RNG state.

The diff does not change the reset contract, P1 gate, transport loop, WW logic, comparator thresholds or physics formulas. It does alter the binaries and therefore v2 E0 must be treated separately, as Task 13 does. The v2 baseline gates re-establish fresh CLI/driver and P0 endpoint agreement for one Forward and one Adjoint case.

## 14. Archive completeness

**Reproducibility: MEDIUM.** The local task directory contains the private snapshot, preserved binaries, raw WW traces, snapshots, HDF5/text outputs and execution metadata. Snapshot and binary dedicated manifests validate.

**Auditability: MEDIUM.** The raw large assets are locally available and E3 traces were independently reanalyzed. However, `sha256sum --check logs/artifact-manifest.sha256` reports one mismatch: `README.md`. The manifest expects SHA-256 `1f334…`, while local README has `49cb2…`. The README was modified after the manifest timestamp. Therefore the archive cannot claim a fully clean manifest validation in this checkout.

The task’s archived manifest scope explicitly excludes the private source snapshot and build trees, which have separate manifests. It claims large raw assets will not enter Git. Their local presence is enough for this review, but transfer to another checkout needs those assets and corrected manifest provenance.

## 15. Claims audit

| Claim | Assessment | Reason |
|---|---|---|
| A. F→F stays independent under the experimental contract | SUPPORTED | Fresh exact endpoint/state/history comparisons and reset assertions pass. |
| B. F→A→F stays fresh-equivalent under the experimental contract | SUPPORTED WITH LIMITATION | Tested in nonfissile serial H2O only. |
| C. WW lower-bound update enters next transport run | SUPPORTED | Raw full event traces verify actual lower/survival/upper reads. |
| D. Tally definition can remain while statistics reset | SUPPORTED | Same owner/registry retained and Run 2 matches fresh. |
| E. Field value/RE can be directly read from RMC memory | SUPPORTED | Post-`ProcessTally` memory matches text and fresh data for this tally. |
| F. G+1 physical groups can be constructed from MGACE memory | SUPPORTED | Centre/width/lower relations and final upper edge validate. |
| G. Production RMC already supports persistent session | NOT SUPPORTED | P1 and task-private driver explicitly provide the lifecycle. |
| H. Persistent RMC is certainly faster than fresh processes | NOT SUPPORTED | E0 is one small warm-cache timing decomposition, not a comparative production speed study. |

## 16. Final verdict

| Item | Verdict |
|---|---|
| Baseline gates | ACCEPT WITH LIMITATIONS |
| E0 | ACCEPT WITH LIMITATIONS |
| E1 | ACCEPT |
| E2 | ACCEPT WITH LIMITATIONS |
| E3 | ACCEPT |
| E4 | ACCEPT |
| G+1 extraction | ACCEPT |
| Normalization evidence | ACCEPT WITH LIMITATIONS |

**Overall: ACCEPT WITH LIMITATIONS.**

## 17. Architecture readiness

**YES WITH EXPLICIT LIMITATIONS.**

The dynamic evidence is enough to begin F11 architecture design, provided that the design preserves these hard constraints:

- immutable/persistent base model state must be separated from per-run CLEAR state and mode-derived REBUILD state;
- Forward/Adjoint transitions require explicit array/cache/cutoff/source rebuilding;
- WW updates require a bounds lifecycle that recomputes derived survival and upper values;
- tally definition/registry ownership must remain distinct from per-run statistics;
- a post-finalization in-memory Field contract must carry physical-edge and normalization metadata;
- research-variable reconstruction, response, iteration policy and convergence criteria must remain outside the executor mechanism;
- the first production design must retain the serial MGACE/native track-mesh scope until additional coverage is authorized.

## 18. Remaining limitations

- No CE, photon/electron coupling, MPI, OpenMP, burnup, restart, multiple source components, non-unit source weight or arbitrary WW topology was tested.
- E2 excludes nonzero adjoint-fission rebuild.
- The experimental reset contract is manual and task-specific.
- E0 has no large-model or cold-cache inference.
- Task 13’s top-level manifest has one README integrity mismatch.

## 19. Questions for human

1. Should F11 architecture design now proceed within the verified serial MGACE/native track-mesh boundary?
2. Should a separate validation task extend the Forward/Adjoint lifecycle to a fissile case before the architecture commits to general adjoint support?
3. Should archive governance repair the Task 13 README manifest mismatch before the evidence is treated as portable or release-quality?

---

## Independent reanalysis

The read-only analyzer/comparator rerun, raw-event sampling and archive checks are saved in [independent-reanalysis.txt](logs/independent-reanalysis.txt), [evidence-sampling.md](logs/evidence-sampling.md) and [archive-verification.txt](logs/archive-verification.txt). No RMC transport was rerun.
