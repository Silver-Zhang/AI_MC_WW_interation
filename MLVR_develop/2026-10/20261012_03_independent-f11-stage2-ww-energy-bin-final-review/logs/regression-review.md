# 回归与动态证据复核

## Artifact verified (Task02 saved results; not rerun here)

- Build/G0: 694 common production translation units, compile options identical, 13 global definitions each exactly once; ordinary and prepared targets recorded successful.
- CTest: `10/10`.
- Production owner lookup: `15/15`; finite queries cover below/at first, both sides of internal boundaries, terminal equality and above terminal. Returned bins are `0,1,2`; direct NaN/`+Inf`/`-Inf` are rejected by `WW lookup: nonfinite particle energy`.
- Ordinary native WW: single/multi 500-history pre/post binaries compare at physical tolerance zero. Single observed 22,518 WW queries, 1,108 splits, 1,781 roulette; multi observed 18,450 queries across intervals `[0,1,2]`, 894 splits and 1,063 roulette. Recorded output checks cover text/tally/material and HDF files.
- Persistent/fresh: `38` paired executions at physical tolerance zero and no saved comparison errors: FF 2, FAF 3, AA 2, WW OFF→1→2→OFF 4, FAF+WW 3, resource reuse 20, multi-energy 4. Every recorded run has completed histories equal to its normalization denominator.
- Targeted sanitizer: `80/80`, ASan+UBSan+`_GLIBCXX_ASSERTIONS`; only `PrepareFixedSourceRun.cpp`, `WeightWindows.cpp` and the driver are instrumented; `detect_leaks=0`.

## Independently recomputed

The JSON result grouping confirms `78 = 26×3` malformed entries and `38 = 2+3+2+4+3+20+4` persistent/fresh entries. This is arithmetic/review of saved output, not an independent execution.

## Not verified

No fresh build/test/sanitizer execution was performed in this read-only review. Task02 itself lists MPI/OMP runtime or new parallel build, ordinary malformed parser safety, ordinary MCNP-specific WW regression, full-program sanitizer/leaks, physical MC transport at `1e22`, and Stage3 TARGET/Field/FOM as unverified. The source-level P1 gaps in `logs/source-audit.md` additionally remain.
