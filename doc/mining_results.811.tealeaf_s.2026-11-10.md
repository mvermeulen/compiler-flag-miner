# `cfm mine` results: 811.tealeaf_s on `chicago`, 2026-11-10

This is the fourth fpspeed benchmark mined on `chicago` (see [`host_chicago.md`](host_chicago.md)), and the first
`811.tealeaf_s` mine on any host. `811.tealeaf_s` is TeaLeaf, a C mini-app from the UK Mini-App Consortium that solves the
linear heat-conduction equation with an iterative sparse solver, parallelized with OpenMP. Its corpus shape is
memory-bound at 70.7%.

## Headline result

**No flag beat plain `-O3`** (ratio 1.4308). A clean reject: every candidate measured within ±0.16% of `-O3`.

- **`-march=native` read +0.02%**, its first reject on an fpspeed benchmark here. It was fast-tracked on the
  memory-bound prior (accepted 12 of 14). `-march=znver5` built the same code (`bc6fba74`) and read -0.06%;
  `-mtune=znver5` read -0.08%.
- **PGO read -0.03%**, and each PGO trial took about 88 minutes, most of the run's 7h39m. Its three builds had three
  different code fingerprints.
- **`-flto` -0.04%, `-fprefetch-loop-arrays` +0.02%, `-fgraphite-identity` -0.16%**, all rejected.
- **The shape filter dropped 11 candidates** on the 70.7% memory-bound read.

The flat result fits the code: a sparse solver's time goes to streaming matrix and vector data through memory, and
none of these flags changes how much data moves.

## Run metadata

| | |
|---|---|
| Host | `chicago`: AMD Ryzen AI MAX+ 395 (16 Zen5 cores, 32 threads), 91 GB RAM, power profile `performance` |
| Command | `python3 -m cfm.cli mine 811.tealeaf_s` (uncapped, defaults) |
| Code | `main` at `2ed5eaa` (no code changes since `f31ba64`, only docs) |
| SPEC config | `threads = 32`; `-ftree-parallelize-loops=32` |
| Thread placement | OpenMP: `OMP_PLACES=threads OMP_PROC_BIND=close` |
| Experiment id | 18 |
| Started / finished | 2026-11-10T01:36:59Z / 2026-11-10T09:16:05Z (7h39m) |
| Final status | `converged` |
| Trials | 31 (783-813), 1 rerun, none skipped |
| Candidates screened / confirmed | 3 / 3 (plus `-march=native` fast-tracked, rejected) |
| Excluded on shape (Phase 2) | 11 |
| Fast-tracked (M4) | `-march=native` (accepted 12 of 14, mean +20.62%) |
| Winning flags | `["-O3"]`, +0.00% |
| Guards | bandwidth gate waited 30 s before 17 of 31 runs; one slow-rep rerun (trial 808 → 810); baseline recheck not flagged (+0.03%) |
| Power | package power median 84.99-85.00 W on every trial; CPU temperature 87.4-90.8°C |

A non-PGO trial took about 7 minutes and a PGO trial about 88. Every trial's `.rsf` reads `valid: S` for tealeaf.

## Baseline

Shape from the reference-matrix corpus (`amd-370-64gb`): memory-bound 70.7%, `vectorization_density=high`,
`allocation_pressure=low`.

| Trial | Role | Ratio |
|---|---|---|
| 783 | warm-up | 1.42293 |
| 784 | warm-up | 1.42872 |
| 785 | calibration | 1.42930 |
| 786 | calibration | 1.43126 |
| 787 | calibration | 1.43187 |
| 803 | recheck | 1.43121 (+0.03%) |

The calibration mean is 1.430813, with a 95% CI of [1.42747, 1.43415] (±0.23%). Warm-up settled after the minimum
two reps (837 s). Every `-O3` build had the same code fingerprint (`02845cc0`).

## Trials

| Trials | Phase | Flags (on `-O3`) | Mean ratio | Delta | Verdict |
|---|---|---|---|---|---|
| 788-790 | screening | 3 candidates | 1.431-1.432 | | all survived |
| 791-793 | confirmation | `-fprefetch-loop-arrays` | 1.4311 | +0.02% | reject |
| 794-796 | confirmation | `-fgraphite-identity` | 1.4285 | -0.16% | reject |
| 797-799 | confirmation | `-flto` | 1.4303 | -0.04% | reject |
| 800-802 | confirmation (fast-tracked) | `-march=native` | 1.4311 | +0.02% | reject |
| 804-806 | PGO | `-fprofile-use` | 1.431 | -0.03% | reject |
| 807-810 | microarch | `-march=znver5` | 1.430 | -0.06% | reject (808 re-run as 810) |
| 811-813 | microarch | `-mtune=znver5` | 1.430 | -0.08% | reject |

With nothing accepted, Phase 5 ran no trials and Phase 6 layered on plain `-O3`. The vector-width multiplier was
skipped because the winning set has no `-march=`.

## Observations

- **The first fpspeed benchmark here with nothing to gain**, like lbm_r and nest_r on the rate side. It's also the
  first time `-march=native` has been rejected on a benchmark with a 70%-plus memory-bound read here; every earlier
  reject (gmsh, flightdm, nest) was under the 55% shape margin.
- **The `-march=znver5` rerun**: one rep read 2.9% below its siblings with the same code, and its re-run read
  normal, so the rerun rule caught a one-off slow rep.
- **PGO cost 4.4 hours for nothing.** The training run must be most of each PGO trial. A benchmark this flat is
  where a cheaper PGO screen would pay, but nothing predicts flatness in advance.
- **niwot hasn't mined tealeaf_s yet.**
