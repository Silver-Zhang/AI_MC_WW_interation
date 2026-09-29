# Pre-review source questions

**Independence boundary:** Written before reading any F11 architecture-design task output. Task 15 is prohibited and will not be read.

## Questions the current source must answer

1. What does one normal fixed-source calculation actually do from `main` to output and process exit? Which initialization, transport, finalization and output operations are inseparable today?
2. Which problem objects are local to `main`, which objects are globals, which `RunCalculation` arguments are copied, and which mutable state can survive a second call?
3. What exactly distinguishes a formal MLVR iteration, a forward/adjoint half-run, an RMC batch, a source history and its split/secondary descendants? Does v1 need a new transport batch parameter?
4. Is the existing `Control` subsystem a calculation workflow controller or a different concern? Which class already owns mode dispatch and fixed-source transport?
5. Where does an input block enter parsing, validation, generated-input output and long-lived configuration ownership? Which owner best fits K, NPS, TARGET, command, workdir and seed policy?
6. Which Forward/Adjoint changes occur in `CDFixedSource`, `CDAceData`, `CDParticleState`, source objects and multigroup collision code? Which are safe to keep, clear, set or rebuild?
7. How are external sources represented and sampled? For selected Cartesian cells and physical energy groups, can a production target reuse source machinery, and where must target-volume/group-probability semantics be added?
8. Who owns mesh tally Ave/RE, statistical state, mesh edges and MG energy metadata? What is the smallest reliable point to export `field.h5` after a half-run?
9. Who owns runtime native WW topology and lower/survival/upper bounds? Can a dynamic import update the existing object directly while reusing the original bound-derivation path?
10. Does RMC already launch external commands? If not, what existing layer can own a fail-fast command, per-run work directory and HDF5 validation without creating a parallel framework?
11. What is the narrowest source change that reuses exactly one production history loop and preserves ordinary fixed-source behavior? Is a reusable execution core preferable to a wrapper or an entry-mode flag?
12. Does the orchestration need a new class or directory, or can existing `CDCalMode` plus a small number of focused source files own it without creating a monolithic function?
