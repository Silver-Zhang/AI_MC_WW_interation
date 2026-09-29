# Endpoint metadata amendment before final E0

E0 v1 passed timing/physics gates but its timing-only mode omitted per-run in-memory source denominator metadata. To satisfy Task 13 section16, add a common endpoint collector after the original calculation returns, in both CLI variants and the driver. It reads source history counts, actual denominator, unit-source weights/probabilities and RNG identity, then writes one JSON. It performs no RNG call and no simulation-state write.

This endpoint collector is common to P0-on and P0-off, lies outside history transport, and is charged to finalize/output in E0. Therefore the final A binary is precisely 'internal P0/P1 disabled, common external endpoint collector enabled', not a claim of zero observational instructions anywhere. Original transport/default-off physics equivalence remains intact. Gate comparisons remain exact. No lifecycle contract or threshold changes.

Preserve implementation/binary v1, original gates, E0 v1 raw evidence and result tables; E1-E4 numerical evidence remains v1 and is not rerun. Build metadata v2, rerun both baseline gates and the predeclared E0 1+7 pairs per role with v2-prefixed directories, use only E0 v2 for final performance figures. V1 E0 is explicitly preliminary/incomplete metadata evidence, never pooled with v2.
