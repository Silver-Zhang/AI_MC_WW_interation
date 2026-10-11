# Independent source judgment before reading experiment evidence

## Question

For a Cartesian Type=1 mesh track-length tally, does `Ave` already include spatial-bin volume normalization, and what must an independent validation demonstrate?

## SOURCE FACTS TO ESTABLISH FROM CURRENT CODE

This note is frozen before reading the target task report or result files. The following must be resolved by source inspection:

1. Track-length scoring must show whether a score contribution is divided by mesh volume when it is entered into `p_OMeshTallyData.p_vScore`.
2. `Sum1`/`Sum2` aggregation and `CalcAveRe` must show whether the only remaining denominator is total starting source weight or whether an additional mesh-volume factor appears.
3. The `Normalize` tally option and any mesh `volume` metadata must be located. A test cannot use the reported Ave itself as a reference for the volume correction it claims to validate.
4. Uniform and heterogeneous mesh definitions must be checked as distinct geometry paths with identical physical boundaries and equal bin volumes.

## Preliminary acceptance criteria

A convincing stage-0 experiment must provide all of the following:

- Same source, material, particle mode, energy groups, NPS, seed policy and output/tally options for uniform and heter mesh cases.
- Physical mesh boundaries that represent exactly the same bins, with non-unit bin volumes, and execution evidence that uniform and heter branches were selected.
- A separate reference constructed from raw per-history track-length contribution or an independently accumulated track length divided by `V × actual starting-weight denominator`, not from `Ave` and not from the text tally after it has already been normalized.
- A field comparison for every tested bin/group, including zero-score bins. It must define whether zero score means exact zero estimate and distinguish that from zero statistical uncertainty.
- Explicit verification of requested/completed histories, actual total starting source weight, source component weight/probability, Normalize semantics, physical group ordering and any text rounding policy.
- A conclusion restricted to the tested track-length Cartesian mesh path. Equal uniform/heter output alone does not prove correct volume normalization if both paths share the same defective formula.

## Potential false positives

- Both mesh representations use identical but wrong volume arithmetic.
- An external reference calls the same function or reads `Ave`, making the test circular.
- A raw score is divided by volume twice, or not at all, while a compensating normalization hides it in a unit-volume bin.
- A script ignores histories with zero contribution and changes the effective denominator.
- A rounded `.Tally` output is treated as binary-exact data.
- Internal MG group indices are mistaken for physical group order or physical energy.
