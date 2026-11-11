# `cfm mine` results: 816.nab_s on `chicago`, 2026-11-10

This is the fifth fpspeed benchmark mined on `chicago` (see [`host_chicago.md`](host_chicago.md)), and the first
`816.nab_s` mine on any host. `816.nab_s` is based on Nucleic Acid Builder (NAB), a C molecular-modeling code whose
floating-point work ranges from molecular dynamics to linear algebra, parallelized with OpenMP. Its corpus shape is
memory-bound at 46.6%, under the 55% shape margin, so no candidate was excluded on shape.

## Headline result

**`-O3 -ffast-math -march=native -fprofile-use`, +15.10% over plain `-O3`** (ratio 3.3639 → 3.8717).

| Step | Mean | Gain on the step before |
|---|---|---|
| `-O3` | 3.3639 | — |
| `-O3 -ffast-math` | 3.5188 | +4.61% |
| `+ -march=native` | 3.7165 | +5.62% |
| `+ -fprofile-use` | 3.8717 | +4.17% |

- **`-ffast-math` (+4.61%) and `-Ofast` (+4.56%) were both accepted alone**, and built the same code once combined
  (`-Ofast -ffast-math` has the fingerprint of `-Ofast`, `3ff2532a`). This is the second fast-math win in fpspeed
  here after pot3d_s, and again the shape filter only let it through because the memory-bound read was under 55%.
- **`-march=native` gave only +1.37% alone, but +6.4% on top of fast-math.** The `-ffast-math -march=native` pair
  measured 3.745, against 3.519 for `-ffast-math` alone and 3.410 for `-march=native` alone. The likely reason is that
  fast-math lets GCC vectorize floating-point reductions and math it otherwise keeps scalar, and AVX-512 makes those
  vectors wider. I didn't check this against GCC's vectorizer output.
- **PGO added +4.17% on top.** That step is measured against the greedy step's mean, which one low rep pulled down
  (below). Against the pair trials of the same code (3.745), PGO's gain is about +3.4%.
- **Every other candidate was within ±0.25% of `-O3`**, except `-fno-math-errno` (+0.76%). It was CI-clear of
  baseline but under the 1% bar, so Phase 6 tried it as the near-miss PGO variant; `-ffast-math` already implies it,
  and the variant built the same two PGO codes as plain PGO and read +0.04% more.
- **`-fno-unswitch-loops`, carrying the pinned pot3d run's +115.7% accept (1 of 4), read +0.24%** and was rejected.

## Run metadata

| | |
|---|---|
| Host | `chicago`: AMD Ryzen AI MAX+ 395 (16 Zen5 cores, 32 threads), 91 GB RAM, power profile `performance` |
| Command | `python3 -m cfm.cli mine 816.nab_s` (uncapped, defaults) |
| Code | `main` at `4559c91` (no code changes since `9d832ae`, PR #70) |
| SPEC config | `threads = 32`; `-ftree-parallelize-loops=32` |
| Thread placement | OpenMP: `OMP_PLACES=threads OMP_PROC_BIND=close` |
| Experiment id | 20 |
| Started / finished | 2026-11-10T17:12:57Z / 2026-11-11T01:59:30Z (8h47m) |
| Final status | `converged` |
| Trials | 89 (877-965), no reruns, none skipped |
| Candidates screened / confirmed | 14 / 14 (all survived screening; plus `-march=native` fast-tracked) |
| Excluded on shape (Phase 2) | none (memory-bound 46.6%, under the 55% margin) |
| Fast-tracked (M4) | `-march=native` (accepted 12 of 16, mean +18.05%) |
| Accepted in Phase 4 | `-ffast-math` +4.61%, `-Ofast` +4.56%, `-march=native` +1.37% |
| Winning flags | `["-O3", "-ffast-math", "-march=native", "-fprofile-use"]`, +15.10% |
| Guards | bandwidth gate waited 30 s before 30 of 89 runs; no reruns; baseline recheck not flagged (-0.07%) |
| Power | package power median 85.02-85.08 W on every trial; CPU temperature 85.8-89.8°C |

A trial took about 6 minutes, PGO included. Every trial's `.rsf` reads `valid: S` for nab.

## Baseline

Shape from the reference-matrix corpus (`amd-370-64gb`): memory-bound 46.6%, `vectorization_density=high`,
`allocation_pressure=low`.

| Trial | Role | Ratio |
|---|---|---|
| 877 | warm-up | 3.36345 |
| 878 | warm-up | 3.36211 |
| 879 | calibration | 3.36161 |
| 880 | calibration | 3.36266 |
| 881 | calibration | 3.36729 |
| 941 | recheck | 3.36163 (-0.07%) |

The calibration mean is 3.363853, with a 95% CI of [3.35634, 3.37136] (±0.22%). Warm-up settled after the minimum
two reps (727 s). Every `-O3` build had the same code fingerprint (`e036b902`).

## Trials

| Trials | Phase | Flags (on `-O3`) | Mean ratio | Delta | Verdict |
|---|---|---|---|---|---|
| 882-895 | screening | 14 candidates | 3.357-3.519 | | all survived |
| 896-898 | confirmation | `-fprefetch-loop-arrays` | 3.3562 | -0.23% | reject |
| 899-901 | confirmation | `-fgraphite-identity` | 3.3665 | +0.08% | reject |
| 902-904 | confirmation | `-flto` | 3.3680 | +0.12% | reject |
| 905-907 | confirmation | `-fno-pie -no-pie` | 3.3687 | +0.15% | reject |
| 908-910 | confirmation | `-fno-stack-protector` | 3.3705 | +0.20% | reject |
| 911-913 | confirmation | `-fcf-protection=none` | 3.3604 | -0.10% | reject |
| 914-916 | confirmation | `-U_FORTIFY_SOURCE` | 3.3680 | +0.12% | reject |
| 917-919 | confirmation | `-funroll-loops` | 3.3617 | -0.06% | reject |
| 920-922 | confirmation | `-Ofast` | 3.5173 | +4.56% | **accept** |
| 923-925 | confirmation | `-ffast-math` | 3.5188 | +4.61% | **accept** (the greedy start) |
| 926-928 | confirmation | `-fno-math-errno` | 3.3894 | +0.76% | reject (CI-clear, under the 1% bar) |
| 929-931 | confirmation | `-fno-ipa-cp-clone` | 3.3654 | +0.05% | reject |
| 932-934 | confirmation | `-fno-unswitch-loops` | 3.3719 | +0.24% | reject |
| 935-937 | confirmation | `-fipa-pta` | 3.3616 | -0.07% | reject |
| 938-940 | confirmation (fast-tracked) | `-march=native` | 3.4098 | +1.37% | **accept** |
| 942-944 | combination (greedy) | `-ffast-math -Ofast` | 3.519 | +0.01% | reject (same code as `-Ofast`) |
| 945-947 | combination (greedy) | `-ffast-math -march=native` | 3.7165 | +5.62% | **accept** |
| 948-950 | combination (pair) | `-Ofast -march=native` | 3.744 | +11.28% | accept, didn't replace the winner |
| 951-953 | combination (pair) | `-Ofast -ffast-math` | 3.519 | +4.62% | accept, didn't replace the winner |
| 954-956 | combination (pair) | `-ffast-math -march=native` | 3.744 | +11.31% | accept, same flagset as the winner |
| 957-959 | PGO | `-ffast-math -march=native -fprofile-use` | 3.8717 | +4.17% | **accept** |
| 960-962 | PGO (near-miss) | `+ -fno-math-errno` | 3.873 | +4.21% | accept, didn't replace (same codes) |
| 963-965 | vector width | `+ -mprefer-vector-width=256` | 3.864 | -0.18% | reject |

Greedy-step deltas are against the step before, pair deltas against `-O3`, and Phase 6 deltas against
`-O3 -ffast-math -march=native`. The greedy walk started from the Phase 4 `-ffast-math` result rather than re-measuring
it. The microarch multiplier was skipped because the winning set already had `-march=native`.

## Observations

- **One low rep shaped how the gain splits, not the total.** Trial 945 read 3.6716, 1.8% under its two siblings
  (3.734, 3.744) with the same code (`f1b225b5`). That's under the 10% slow-rep bar and the spread rule's 2% minimum,
  so it wasn't re-run. It pulled the greedy step's mean to 3.7165, so the pairs (3.744) didn't clear it to replace the
  winner and PGO's step reads +4.17% instead of about +3.4%. The final +15.10% is measured directly and doesn't
  depend on it. Open item 5 (a rerun rule for small outliers when the spread is tiny) covers this case too.
- **The PGO builds alternated between two codes** (`c6fe327e`, `228b97ee`) across both PGO variants, and every rep
  agreed within 0.15%, so retraining per build (CLAUDE.md's 2026-10-28 trap) didn't matter here.
- **Fast-math is now 2 of 2 on fpspeed benchmarks where the shape filter let it run** (pot3d_s, nab_s), and was never
  measured on the three it excluded (open item 14).
- **niwot hasn't mined nab_s yet.**
