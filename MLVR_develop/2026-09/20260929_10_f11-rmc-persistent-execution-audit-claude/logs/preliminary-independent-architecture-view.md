# Preliminary independent architecture view

**Scope freeze:** This note was written before reading any F02–F10 archive material and without reading the prohibited Codex task directory.

## SOURCE CONFIRMED initial observations

- The production entry point is a conventional single `main`, rather than a visible session or run-controller API. The exact lifecycle evidence will be mapped in the final audit.
- RMC source contains distinct source, transport, tally, weight-window, MPI, and output subsystems. That separation is necessary but does not itself demonstrate repeat-safe re-entry.
- The requested repeated-run safety depends on whether per-calculation state is explicitly reset or reconstructed. Static inspection must therefore treat the absence of an exposed reset path as a risk, not infer safety from container ownership alone.

## INFERENCE to test against source

- A one-shot command-line architecture likely couples input parsing, initialization, output naming, and cleanup to process lifetime.
- A Forward → Adjoint → Forward sequence has stronger requirements than Forward → Forward because mode-sensitive data, source sampling, tally normalization, and transport kernels may capture mode state during initialization.
- Geometry and immutable nuclear data may be reusable if transport only reads them after setup. Weight-window values, source banks, tallies, random-number streams, timers, diagnostics, and output handles are likely calculation-lifetime state.

## UNKNOWN until mapped

- Whether the current fixed-source driver can be called more than once without a process exit.
- Whether MGACE or adjoint support mutates shared cross-section data.
- Whether native mesh weight-window bounds can be replaced without derived-cache rebuild.
- Whether tally state has a complete independent reset plus structured in-memory value/relative-error extraction.
- Whether repeated MPI collectives and output writers are safe across calculations.

This preliminary view is intentionally non-conclusive. The final report will replace each item with exact source evidence or retain it as UNKNOWN.
