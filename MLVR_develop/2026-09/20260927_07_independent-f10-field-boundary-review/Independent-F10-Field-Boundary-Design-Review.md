# Independent F10 Field Boundary Design Review

**Review target:** [F10 Field Interface Design](../20260927_06_f10-field-reconstruction-boundary/F10_Field_Interface_Design.md), reviewed only after the independent minimum contract was recorded in [`logs/pre-developer-claim-conclusion.md`](logs/pre-developer-claim-conclusion.md).

**Scope:** first-version MLVR data boundary only. This review does not implement a parser, Field class, reconstruction method, WW generation, RMC change, or scheduler.

## 1. Design summary

The proposed boundary is:

\[
\text{RMC text tally + authoritative run definitions}
\rightarrow \text{Field Adapter}
\rightarrow \text{StatisticalField}
\rightarrow \text{Reconstruction}
\rightarrow \text{ReconstructedField}
\rightarrow \text{WW Builder}.
\]

It limits the entry to standard MGACE fixed-source neutron, Type=1 Cartesian `Energy=-1` `Normalize=1`, serial text `inp.Tally`. It keeps raw MC fields, reconstructed fields, response definition, and WW construction separate. This is the appropriate first-version architectural altitude.

## 2. StatisticalField review

### Accepted elements

The design includes the required semantic members:

| Member | Review |
|---|---|
| `value[i,g]` | Correctly defined as RMC `Ave`, source-normalized Type=1 scalar track-length flux density. |
| `RE[i,g]` | Correctly retained only as raw MC relative uncertainty, with explicit zero-score caveat. |
| `statistical_status[i,g]` | Correctly colocated with values/RE and defined as a score-state rather than physics-quality state. |
| `mesh` | Includes physical boundaries, dimensions, units and flattening rule. |
| `energy_groups` | Uses full physical MeV boundaries and external physical-energy ascending ordering. |
| `field_role`, `stage`, `iteration` | Distinct lifecycle/physical identity labels. |
| `metadata` | Kept as provenance rather than a new field axis. |

The required logical shape is explicit:

\[
\texttt{value.shape=RE.shape=status.shape=[Nspace,G]}.
\]

It also correctly excludes RMC `Tot` rows from the energy dimension. This avoids a common error: treating the all-energy total as a transport group or copying its RE into group entries.

### Minor correction required

The frozen input is Type=1 scalar neutron flux density, whose raw `Ave` should be nonnegative in the qualified scope. The design presently says that both positive and negative nonzero `Ave` are `VALID`. That is appropriate only for a more generic future field type, not this first-version flux contract.

**Correction:** Adapter must reject a finite negative `Ave` for this frozen Type=1 flux entry, without adding a new status enum. `VALID` should mean `Ave>0` with a valid finite RE; `ZERO_SCORE` should mean the specified zero pair. This is a validation rule, not an enum expansion.

## 3. ReconstructedField review

The decision **not** to propagate raw MC `RE` or `statistical_status` into `ReconstructedField` is correct. A reconstruction changes values, so a copied raw tally RE would falsely purport to quantify reconstructed-field uncertainty.

The proposed retained fields—value, same mesh/energy definition, same role/stage/iteration, and processing provenance—are sufficient. No algorithm-specific uncertainty should be invented until an estimator and interpretation are separately defined.

## 4. Mesh contract

The design gives a complete and unique Cartesian contract:

```text
i = ix + Nx*iy + Nx*Ny*iz
```

with zero-based external indices, strictly increasing boundary vectors, physical units, and x-fastest ordering. It explicitly maps RMC one-based text tuples to this canonical zero-based order and rejects shape-only equivalence.

Requiring the same full mesh identity across bootstrap, formal forward, formal adjoint, and reconstruction is the right v1 restriction. It prevents hidden mesh mapping and prevents a reconstruction component from becoming a geometry-remapping service.

No adaptive mesh, distributed mesh, or spatial interpolation contract is introduced. This is appropriately restrained.

## 5. Energy contract

This is the strongest section of the design.

- The external group coordinate is zero-based and physical-energy ascending.
- Full `G+1` MeV boundaries, units, ordering, and definition identity are required.
- RMC internal reverse group indices do not cross the boundary.
- `inp.Tally`'s `Group g+1` becomes external `g` only after validation.
- Only `Energy=-1` is accepted as an exact transport-group field; custom energy grids are excluded rather than silently treated as MG groups.
- The design acknowledges that tally text supplies rounded lower bounds and lacks the final upper bound, requiring authoritative MGACE/run-sidecar definitions before the Adapter may construct a field.

This prevents recurrence of the F04 group-coordinate/physical-energy confusion. The requirement to reject an absent or mismatched authoritative definition is essential and correct.

## 6. Statistical-status semantics

The two-state v1 enum is sufficient:

| Status | Meaning |
|---|---|
| `VALID` | A nonzero raw tally score, whose raw RE is transferable under the F07 limited interpretation. |
| `ZERO_SCORE` | `Ave=0, RE=0`: no observed nonzero score, not zero uncertainty or a confirmed physical zero. |

`LOW_STATISTICS`, `OUTLIER`, algorithm/interpolation states, and physical-validity states are not first-version blockers. They represent either F07/reconstruction diagnostics or future semantics. The design correctly rejects malformed input instead of silently folding it into `ZERO_SCORE`.

Subject to the Type=1 negative-value correction in §2, the status contract is minimal and adequate.

## 7. Role, stage, iteration semantics

The design correctly distinguishes:

- `field_role`: what physical field the values represent;
- `stage`: bootstrap vs formal lifecycle;
- `iteration`: label of a formal field, not a data axis.

The valid combinations are explicit and avoid a common ambiguity between “bootstrap forward” and “formal forward at iteration 0.” Bootstrap is `BOOTSTRAP_FORWARD / BOOTSTRAP / none`; formal forward and adjoint use `FORMAL / k≥1`. This is coherent.

## 8. Adapter boundary

The Adapter has the right responsibility boundary:

```text
RMC text tally + controlled run metadata + authoritative mesh/MG definitions
→ canonical StatisticalField
```

It correctly must:

- choose the declared unique neutron Type=1 Cartesian tally;
- verify `Energy=-1`, `Normalize=1`, and frozen serial scope;
- map one-based spatial text indices to canonical ordering;
- map text group rows to physical ascending external groups;
- exclude `Tot` rows;
- construct `VALID`/`ZERO_SCORE` only after structural validation;
- bind role/stage/iteration from workflow metadata rather than filename heuristics;
- reject missing, duplicate, inconsistent, nonfinite, or incompatible input.

The Adapter does not reconstruct, generate WW, define response values, schedule iterations, or run RMC. This is correct.

## 9. Reconstruction boundary

The conceptual signature

```text
ReconstructedField reconstruct(const StatisticalField& input)
```

is intentionally noncommittal about language and class hierarchy. Reconstruction does not parse RMC output, reinterpret RMC group coordinates, invoke RMC, own `ResponseDefinition`, generate a WW, or schedule an iteration. It preserves mesh, energy, role, stage, and iteration exactly.

This is a clean pure boundary. It avoids placing policy hidden inside an algorithm component.

## 10. WW Builder boundary

The handoff relationship is correctly outside reconstruction:

| Reconstructed field | WW-builder handoff |
|---|---|
| Bootstrap forward | `WW_A(1)` |
| Formal adjoint at `k` | `WW_F(k)` |
| Formal forward at `k` | `WW_A(k+1)` |

No WW formula, RMC input emission, or iteration scheduler has been placed into reconstruction. This is correct.

## 11. Three-path consistency

All three required paths share the same `StatisticalField → ReconstructedField` shape and canonical coordinate contract:

1. `BOOTSTRAP_FORWARD`: \(\phi_0,RE_0,status_0\) → reconstructed bootstrap field → `WW_A(1)`;
2. `ADJOINT` at `k`: \(\phi_k^\dagger,RE_k^\dagger,status_k^\dagger\) → reconstructed adjoint field → `WW_F(k)`;
3. `FORWARD` at `k`: \(\phi_k,RE_k,status_k\) → reconstructed forward field → `WW_A(k+1)`.

The role tag distinguishes physics; stage distinguishes lifecycle; iteration distinguishes the formal run label. None is misused as an array dimension.

## 12. Over-design findings

**None found.** The design explicitly excludes all of the following from v1:

- class hierarchy or ABI commitment;
- plugins, database/persistent-field store, or distributed field;
- HDF5 schema commitment;
- angle/time/history axes;
- adaptive mesh or group mapping;
- historical field arrays;
- ML feature tensors and algorithm choices;
- response/FOM values;
- reconstruction and WW algorithms;
- scheduler/F11 scope.

The `metadata` contract remains minimal provenance, not a hidden geometry/material/ML tensor.

## 13. Required corrections

1. **Reject negative raw `Ave` in the frozen Type=1 scalar flux Adapter.** Do not classify it as `VALID`; reject it as incompatible input. No new status enum is needed.
2. **Make source-normalization provenance explicit.** `metadata` should record the actual tally source-normalization denominator/identity (e.g., actual total starting source weight) in addition to source-history count, so `value`'s “per source” semantics remain auditable if future non-unit source modes are considered.
3. **State the value unit explicitly.** For this frozen contract, record the convention as source-normalized track-length flux density, conventionally cm⁻² per source weight when RMC geometry uses cm. This avoids a later ambiguity between raw \(\sum w\ell\) and normalized flux density.

These are narrowly scoped semantic/provenance corrections. They do not require an implementation or broader design revision.

## 14. Final recommendation

# ACCEPT WITH MINOR CORRECTIONS

The F10 design meets the independent first-version boundary requirements. It provides a canonical raw statistical field, prevents internal group-index leakage, explicitly handles zero-score RE semantics, separates reconstruction from WW building, maintains shared mesh/group identity across all three paths, and avoids premature implementation architecture.

Approval should be conditional only on the three small corrections in §13—especially rejection of negative `Ave` under the frozen Type=1 flux scope. No RMC source change or F11/F10 implementation should begin as part of this design review.
