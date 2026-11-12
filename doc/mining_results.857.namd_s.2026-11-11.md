# `cfm mine` results: 857.namd_s on `chicago`, 2026-11-11

This is the ninth fpspeed benchmark mined on `chicago` (see [`host_chicago.md`](host_chicago.md)), and the first
`857.namd_s` mine on any host. `857.namd_s` is based on NAMD, a C++ molecular-dynamics code for large biomolecular
systems, parallelized with OpenMP. Its corpus shape is memory-bound at 41.2%, under the 55% shape margin, so no
candidate was excluded on shape.

## Headline result

**`-O3 -march=native`, +17.52% over plain `-O3`** (ratio 2.4912 → 2.9276).

- **`-march=native` gave +17.52%**, with all three reps (2.926-2.931) far above every `-O3` rep (2.490-2.495). It
  was fast-tracked on the memory-bound prior (accepted 14 of 20).
- **Fast-math lost here, the first time on this host**: `-Ofast` -2.83% and `-ffast-math` -2.72%, both CI-clear below
  baseline, built the same code (`27b404c8`). On pot3d_s and nab_s it was the biggest or second-biggest win.
- **Nothing added to `-march=native`.** PGO read +0.47%, PGO with `-fprefetch-loop-arrays` +0.31%, and
  `-mprefer-vector-width=256` +0.57%, all under the 1% bar.
- **`-funroll-loops` read -0.65%** (CI clear below). Every other candidate was within ±0.4% of `-O3`, and
  `-fno-ipa-cp-clone` built the same code as `-O3` and was skipped.

## Run metadata

| | |
|---|---|
| Host | `chicago`: AMD Ryzen AI MAX+ 395 (16 Zen5 cores, 32 threads), 91 GB RAM, power profile `performance` |
| Command | `python3 -m cfm.cli mine 857.namd_s` (uncapped, defaults) |
| Code | `main` at `c8a04ec` (no code changes since `c933ee2`, PR #71) |
| SPEC config | `threads = 32`; `-ftree-parallelize-loops=32` |
| Thread placement | OpenMP: `OMP_PLACES=threads OMP_PROC_BIND=close` |
| Experiment id | 24 |
| Started / finished | 2026-11-11T15:23:05Z / 2026-11-12T05:56:11Z (14h33m) |
| Final status | `converged` |
| Trials | 71 (1071-1141), 1 skipped as unchanged code, no reruns |
| Candidates screened / confirmed | 14 / 13 (plus `-march=native` fast-tracked) |
| Excluded on shape (Phase 2) | none (memory-bound 41.2%, under the 55% margin) |
| Fast-tracked (M4) | `-march=native` (accepted 14 of 20, mean +15.46%) |
| Skipped as unchanged code | `-fno-ipa-cp-clone` (same code as `-O3`) |
| Winning flags | `["-O3", "-march=native"]`, +17.52% |
| Guards | bandwidth gate waited 30 s before 44 of 70 timed runs; no reruns; baseline recheck not flagged (+0.05%) |
| Power | package power median 85.19-85.37 W on every trial; CPU temperature 87.2-91.1°C |

A non-PGO trial took about 10 minutes and a PGO trial about 37, so the six PGO trials took 3.7 of the run's 14.5
hours. Every trial's `.rsf` reads `valid: S` for namd.

## Baseline

Shape from the reference-matrix corpus (`amd-370-64gb`): memory-bound 41.2%, `vectorization_density=high`,
`allocation_pressure=low`.

| Trial | Role | Ratio |
|---|---|---|
| 1071 | warm-up | 2.49357 |
| 1072 | warm-up | 2.49476 |
| 1073 | calibration | 2.49210 |
| 1074 | calibration | 2.48970 |
| 1075 | calibration | 2.49191 |
| 1132 | recheck | 2.49249 (+0.05%) |

The calibration mean is 2.491236, with a 95% CI of [2.48793, 2.49454] (±0.13%). Warm-up settled after the minimum
two reps (1,229 s). Every `-O3` build had the same code fingerprint (`cd9bb5b5`).

## Trials

| Trials | Phase | Flags (on `-O3`) | Mean ratio | Delta | Verdict |
|---|---|---|---|---|---|
| 1076-1089 | screening | 14 candidates | 2.419-2.491 | | all survived (`-fno-ipa-cp-clone` skipped as unchanged code) |
| 1090-1092 | confirmation | `-fprefetch-loop-arrays` | 2.5002 | +0.36% | reject (CI-clear, under the 1% bar) |
| 1093-1095 | confirmation | `-fgraphite-identity` | 2.4935 | +0.09% | reject |
| 1096-1098 | confirmation | `-flto` | 2.4884 | -0.12% | reject |
| 1099-1101 | confirmation | `-fno-pie -no-pie` | 2.4953 | +0.16% | reject |
| 1102-1104 | confirmation | `-fno-stack-protector` | 2.4933 | +0.08% | reject |
| 1105-1107 | confirmation | `-fcf-protection=none` | 2.4932 | +0.08% | reject |
| 1108-1110 | confirmation | `-U_FORTIFY_SOURCE` | 2.4894 | -0.08% | reject |
| 1111-1113 | confirmation | `-funroll-loops` | 2.4749 | -0.65% | reject (CI clear below) |
| 1114-1116 | confirmation | `-Ofast` | 2.4208 | -2.83% | reject (CI clear below) |
| 1117-1119 | confirmation | `-ffast-math` | 2.4234 | -2.72% | reject (CI clear below) |
| 1120-1122 | confirmation | `-fno-math-errno` | 2.4859 | -0.22% | reject |
| 1123-1125 | confirmation | `-fno-unswitch-loops` | 2.4966 | +0.22% | reject |
| 1126-1128 | confirmation | `-fipa-pta` | 2.4985 | +0.29% | reject (CI-clear, under the 1% bar) |
| 1129-1131 | confirmation (fast-tracked) | `-march=native` | 2.9276 | +17.52% | **accept** |
| 1133-1135 | PGO | `-march=native -fprofile-use` | 2.941 | +0.47% | reject |
| 1136-1138 | PGO (near-miss) | `+ -fprefetch-loop-arrays` | 2.937 | +0.31% | reject |
| 1139-1141 | vector width | `-march=native -mprefer-vector-width=256` | 2.944 | +0.57% | reject |

Phase 6 deltas are against `-O3 -march=native`. With one accepted flag, Phase 5 had nothing to combine and ran no
trials. The microarch multiplier was skipped because the winning set already had `-march=native`.

## Observations

- **Fast-math is now 2 wins and 1 loss on fpspeed here.** nab_s and namd_s are both C/C++ molecular-dynamics codes
  under the shape margin, and fast-math gained +4.6% on one and lost 2.7% on the other. Neither run shows why; GCC's
  vectorizer report for both builds would.
- **Two screening trials read low and then confirmed normal.** `-fprefetch-loop-arrays` and `-fipa-pta` screened
  at 2.434 and 2.432 (-2.3% against the last calibration rep) and confirmed at +0.36% and +0.29% with tight reps.
  Both were under the 5% prune bar, so nothing was lost, but nothing in the trial records (bandwidth, power,
  temperature, code fingerprint) explains the two low reads.
- **PGO cost 3.7 hours for under 0.5%.** Each PGO trial took 37 minutes against 10 for a plain one, the training
  run making up most of the difference.
- **niwot hasn't mined namd_s yet.**
