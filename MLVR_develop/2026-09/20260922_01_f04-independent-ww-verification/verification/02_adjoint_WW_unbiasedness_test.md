# 1. Environment

```text
RMC commit: b7d8a946417eea091a30c09c233054aa077570ee
Branch: Neural_Network_WW_Iteration
Compiler: g++ 13.3.0
CMake: 3.28.3
Build option: mpi=OFF, openmp=OFF
RMC binary SHA256: 53f4fbf4d623f207f7fea09bd2f30767b5dde31d5298f281ea5ca260aa980639
MG library: standard ASCII 30-group H2O, `1001.50m/8016.50m`, `MGACE ERGGRP=30 12`
Platform: Linux
```

No RMC source, benchmark, reference result, or model was modified.

# 2. Test problem

A uniform 5 cm radius H2O sphere is driven by a fixed neutron source in multigroup adjoint mode:

```text
FIXEDSOURCE
  PARTICLE POPULATION=200000
  RNG TYPE=2, seed = 211/223/227/229/233, STRIDE=1000000
  ADJOINT ADJOINTCALCULATION=1 MAXADJOINTENERGY=16 16

EXTERNALSOURCE
  neutron, cell 1, weight 1, physical source energy 0.2435 MeV

TALLY
  cell 1, neutron track-length flux, all 30 groups
```

The observable is output tally group 16, the first nonzero source-connected group in this configuration. Each case uses 200,000 histories and five independent seeds.

Case A is analog adjoint transport. Case B differs only by the native WW block:

```text
WEIGHTWINDOW
WWE:N 0.1 0.2 0.3 0.4 0.5 0.6 0.7 0.8 0.9 1 2 3 4 5 6
WWMESH:N 0.02 0.03 0.04 0.05 0.06 0.07 0.08 0.09 0.10 0.11 0.12 0.13 0.14 0.15 0.16 0.17
WWP:N 5 3 5
WEIGHTWINDOWMESH ScopeX=1 BoundX=-5 5 ScopeY=1 BoundY=-5 5 ScopeZ=1 BoundZ=-5 5
```

The source has numerical MG coordinate 16 while its selected WW lower bound is 0.17; the upper bound is 0.85, below source weight 1, so Case B necessarily enters the split branch on its first track-mesh segment.

All inputs, stdout/stderr and `inp.Tally` files are retained under `verification/cases/`.

# 3. Case A result

Inverse-variance aggregate across five independent runs:

| Metric | Analog adjoint |
|---|---:|
| Response mean | 1.44845798 |
| Combined uncertainty | 0.00127416 |
| Combined RE | 0.000879665 |
| Mean fixed-source time | 0.268416 s |
| Mean per-run FOM | 962949.40 |

Every run exited 0 and reported exactly 200,000 source histories.

# 4. Case B result

| Metric | Adjoint + native WWMESH |
|---|---:|
| Response mean | 1.44657885 |
| Combined uncertainty | 0.000988232 |
| Combined RE | 0.000683151 |
| Mean fixed-source time | 0.522256 s |
| Mean per-run FOM | 820602.59 |

Every run exited 0 and reported exactly 200,000 source histories.

# 5. Comparison

## Response unbiasedness

For each seed, calculate:

$$
z=\frac{R_{WW}-R_A}{\sqrt{\sigma_{WW}^2+\sigma_A^2}}.
$$

| Seed | $z$ |
|---:|---:|
| 211 | -2.01648 |
| 223 | -0.02776 |
| 227 | +0.05551 |
| 229 | -0.60911 |
| 233 | -0.02785 |
| Combined | **-1.16537** |

All individual and combined values satisfy $|z|\le3$. At the tested precision, the WW case is statistically compatible with the analog adjoint response.

## Efficiency

$$
FOM=\frac{1}{RE^2T}.
$$

| Case | RE | Mean time | Mean FOM |
|---|---:|---:|---:|
| Analog | 0.000879665 | 0.268416 s | 962949.40 |
| WW | 0.000683151 | 0.522256 s | 820602.59 |

WW reduced RE by approximately 22.3%, but increased elapsed fixed-source time by approximately 94.6%. In this uniform single-mesh problem, the FOM ratio is $820602.59/962949.40=0.8522$: **the tested WW configuration does not improve FOM**, despite lower statistical uncertainty. This is expected to be problem/WW-dependent; it is not evidence that WW cannot improve efficiency in a deep-penetration problem.

## Particle history behavior

- WW-on has $w_{source}=1>w_{upper}=5\times0.17=0.85$, so its first track segment triggers splitting by construction.
- Source inspection shows split bank records position, direction, MG coordinate, weight and time in `SaveSplitParticles.cpp`; `PopParticleOutofStack` restores particle type and, when fixed-source adjoint is enabled, sets `p_bIsAdjointParticle=true` (`SampleNeutronSource.cpp:304-307`).
- A standalone PTRAC probe was not relied on: neutron fixed-source history output does not flush the event buffer at normal history completion, so an empty PTRAC file is not evidence that splitting did not occur.
- For roulette, the implementation uses survival probability $p=w/w_s$ and survivor weight $w_s$, so its conditional expected post-roulette weight is $p w_s=w$. The split branch chooses an integer multiplicity around $w/w_s$ and assigns `dSurvivalWeight` or an adjusted cap weight; the paired response experiment is the dynamic check that the overall estimator remains statistically compatible.

# 6. Conclusion

## Claude concern verification

**Potential mismatch.**

MG source sampling overwrites `p_dErg` with a discrete group coordinate. Native WW lookup compares that numeric value to literal `WWE:N` values without MG conversion. Therefore a `WWE:N` card written in physical MeV boundaries is not compatible with the lookup coordinate. Detailed evidence is in [01_WW_energy_group_contract.md](01_WW_energy_group_contract.md).

The independent WW-on experiment intentionally uses group-coordinate boundaries, so its statistical pass does **not** invalidate this contract concern.

## Adjoint+WW unbiasedness

**Passed within statistics** for the stated frozen scope: fixed-source neutron adjoint, standard ASCII 30-group H2O, native WWMESH track mesh, Linux MPI-off serial, one spatial mesh and output group 16. The paired result has combined $z=-1.16537$.

## Efficiency conclusion

**No FOM gain was demonstrated** for this particular uniform sphere / near-uniform WW design: lower RE was offset by increased runtime. This verification only establishes that the selected WW configuration was statistically compatible with analog adjoint response, not that it is a good production importance map.

## Boundaries

No conclusion is made for physical-energy `WWE:N` input, MCNP `WWINP`, multiple meshes, other response groups, deep-penetration production geometries, MPI/OpenMP, photon/electron/combined transport, continuous energy, reflective boundaries, or cross-node execution.
