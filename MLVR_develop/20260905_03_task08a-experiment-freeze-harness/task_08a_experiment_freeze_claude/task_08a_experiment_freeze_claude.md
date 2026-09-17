# Task 08A — Corrected Journal Experiment Freeze

## Baseline
`develop` baseline: `13e0db852a5d22f84b3acb673194c8289eba5c3f`.

## Freeze
Historical `results/` are immutable. Corrected output is restricted to `results/task08_corrected/<experiment_id>/`. Formal method matrix: J0 Analog, J1 exponential empirical WW, J2 plain, J3 feature, J4 prior-residual DNN, J5 prior-residual PINN; A1 one-shot PINN and A2 current-only PINN. U-Net is supplementary post-conference only.

Particle counts mean **total source histories across all equal batches**. Formal: 400,000 total/iteration in 50 batches (8,000/batch), 400,000,000 final in 100 batches (4,000,000/batch), 30 iterations, group 1, early stopping off.

## Confirmed pre-repair defects
- Config seed was dead: MC, model initialization, collocation, split and HPO used `GLOBAL_SEED`.
- Non-divisible training totals silently truncated histories.
- Final response samples, timing contract, manifest, replicate identity, current-only ablation and corrected collector were absent.

## Repair
Added Task08 config validation, namespace seed derivation, MC seed-base plumbing, learning seed-base hooks, formal output gate, manifest sidecar/HDF5 mirror, current-only training horizon, explicit one-shot label, exact particle datasets, final response samples/physical samples, transport/E2E FOM fields, timing provenance, and corrected manifest collector/runner.

Seed namespaces are deterministic and range-bounded. Distinct root/replicate/namespace/iteration/item tuples yield no collisions in the frozen audit matrix. Transport event law is unchanged.

## Timing and metrics
`FOM_transport=1/(RE_final^2*T_final_transport)`. `FOM_e2e=1/(RE_final^2*T_algorithm_total)`. Final response samples are the atomic detector statistic. Pairwise response comparison uses `z=(R_i-R_j)/sqrt(SE_i^2+SE_j^2)` and never averages cell-wise RE.

## Restrictions
No 4e8 journal matrix ran. No pilot result is publication evidence. Baseline runner wiring for J0/J1 remains an implementation completion item unless the Task08 corrected baseline runner is used. Full Task08B requires predeclared replicate reporting; no best-replicate selection.
