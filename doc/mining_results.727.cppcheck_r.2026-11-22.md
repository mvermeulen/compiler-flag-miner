# `cfm mine` results: 727.cppcheck_r on `chicago`, 2026-11-22

This is the eighth intrate benchmark mined on `chicago` (see [`host_chicago.md`](host_chicago.md)). `727.cppcheck_r`
is the Cppcheck static analyzer (C++). This machine's August re-mine accepted PGO alone at +10.79% and rejected
`-flto` at +4.20% ([write-up](mining_results.727.cppcheck_r.2026-08-25.md)). niwot found the same set, `-O3
-fprofile-use`, at +7.78%, with `-flto` CI-clear but under the 1% bar
([write-up](mining_results.727.cppcheck_r.2026-10-19.md)). Its corpus shape is frontend-bound at 71.0%, over the 55%
gate, so the shape filter excluded the same seven candidates as on cpython and llvm.

## Headline result

**`-O3 -fno-stack-protector -fprofile-use`, +8.76% over plain `-O3`** (ratio 47.535 → 51.698).

| Step | Mean | Gain on the step before |
|---|---|---|
| `-O3` | 47.535 | — |
| `-O3 -fno-stack-protector` | 49.238 | +3.58% |
| `+ -fprofile-use` | 51.698 | +5.00% |

- **`-fno-stack-protector` gave +3.58%**, the largest gain for that flag on any intrate benchmark here. It was
  fast-tracked (accepted 3 of 5 in this cluster) and was the only Phase 4 accept, so there was no greedy walk
  beyond it and no pair tournament.
- **PGO added +5.00%**, against +10.79% here in August and +7.78% on niwot (both on plain `-O3`). The stack-protector
  step may take some of what PGO gained alone; the run doesn't show it.
- **`-flto` read +1.31% and was rejected on CI overlap**, the third mine of cppcheck to reject it (+4.20% in August,
  +0.96% on niwot). As on llvm, `-O3 -flto -fprofile-use` was never measured (open item 19).
- **Non-PIE was flat (+0.17%)**, the first intrate benchmark here where it was. Five more flags read +1.08% to +1.89%
  and were rejected on CI overlap against a loose baseline (see Observations).
- **`-march=znver5` (+0.54%) and `-mtune=znver5` (+0.64%) on top of PGO were CI-clear but under the 1% bar.**
  `-march=native` alone read +0.67%.

## Run metadata

| | |
|---|---|
| Host | `chicago`: AMD Ryzen AI MAX+ 395 (16 Zen5 cores, 32 threads), 91 GB RAM, power profile `performance`, kernel 7.0.0-43 |
| Command | `python3 -m cfm.cli mine 727.cppcheck_r` (uncapped, defaults; started by `~/cfm-logs/queue/run_queue.sh`) |
| Code | `main` at `9e18971` (no code changes since `3b15833`, PR #72) |
| SPEC config | `gcc_O3.cfg`, `copies = 32` |
| Experiment id | 36 |
| Started / finished | 2026-11-22T00:34:00Z / 2026-11-22T05:32:38Z (4h59m) |
| Final status | `converged` |
| Trials | 49 (1868-1916), none skipped, no reruns |
| Candidates screened / confirmed | 7 / 7 (plus `-flto` and `-fno-stack-protector` fast-tracked) |
| Excluded on shape (Phase 2) | `-funroll-loops`, `-fprefetch-loop-arrays`, `-mprefer-vector-width=256`, `-Ofast`, `-ffast-math`, `-fipa-pta`, `-fgraphite-identity` (frontend-bound 71.0%, over the gate) |
| Fast-tracked (M4) | `-flto` (accepted 3 of 5, mean +5.13%), `-fno-stack-protector` (accepted 3 of 5, mean +1.29%) |
| Accepted in Phase 4 | `-fno-stack-protector` +3.58% |
| Winning flags | `["-O3", "-fno-stack-protector", "-fprofile-use"]`, +8.76% |
| Guards | throttle stop not triggered; bandwidth gate waited 30 s before 2 of 49 timed runs; no reruns; baseline recheck not flagged (+0.61%) |
| Power | package power median 84.99-85.00 W on every trial; CPU temperature 90.6-94.6°C |

A trial took about 5 minutes, an LTO trial about 7, and a PGO trial about 10.

## Baseline

Shape from the reference-matrix corpus (`amd-370-64gb`): frontend-bound 71.0%, `vectorization_density=low`,
`allocation_pressure=moderate`.

| Trial | Role | Ratio |
|---|---|---|
| 1868 | warm-up | 47.987 |
| 1869 | warm-up | 47.932 |
| 1870 | calibration | 47.629 |
| 1871 | calibration | 47.267 |
| 1872 | calibration | 47.709 |
| 1907 | recheck | 47.826 (+0.61%) |

The calibration mean is 47.535, with a 95% CI of [46.950, 48.120] (±1.23%). Warm-up settled after the minimum two
reps (643 s). Every `-O3` build had the same code fingerprint (`aec6a30f`).

## Trials

| Trials | Phase | Flags (on `-O3`) | Mean ratio | Delta | Verdict |
|---|---|---|---|---|---|
| 1873-1879 | screening | 7 candidates | 47.54-48.54 | | all survived |
| 1880-1882 | confirmation | `-fno-pie -no-pie` | 47.614 | +0.17% | reject |
| 1883-1885 | confirmation | `-fcf-protection=none` | 48.047 | +1.08% | reject (CI overlap) |
| 1886-1888 | confirmation | `-U_FORTIFY_SOURCE` | 48.152 | +1.30% | reject (CI overlap) |
| 1889-1891 | confirmation | `-fno-ipa-cp-clone` | 48.290 | +1.59% | reject (CI overlap) |
| 1892-1894 | confirmation | `-fno-unswitch-loops` | 48.432 | +1.89% | reject (CI overlap) |
| 1895-1897 | confirmation | `-march=native` | 47.851 | +0.67% | reject |
| 1898-1900 | confirmation | `-fno-math-errno` | 47.823 | +0.61% | reject |
| 1901-1903 | confirmation (fast-tracked) | `-flto` | 48.158 | +1.31% | reject (CI overlap) |
| 1904-1906 | confirmation (fast-tracked) | `-fno-stack-protector` | 49.238 | +3.58% | **accept** (the greedy start) |
| 1907 | baseline recheck | `-O3` | 47.826 | +0.61% | not flagged |
| 1908-1910 | PGO | `-fno-stack-protector -fprofile-use` | 51.698 | +5.00% | **accept** |
| 1911-1913 | microarch | winner + PGO `+ -march=znver5` | 51.976 | +0.54% | reject (CI-clear, under the 1% bar) |
| 1914-1916 | microarch | winner + PGO `+ -mtune=znver5` | 52.031 | +0.64% | reject (CI-clear, under the 1% bar) |

Phase 4 deltas are against `-O3`, Phase 6 deltas against the set they were layered on. With one accept, Phase 5 had
nothing to add or pair. No Phase 4 reject was CI-clear above baseline, so PGO had no near-miss variant; the
vector-width multiplier had no candidate (the shape filter had excluded `256`).

## Observations

- **One low calibration rep set the bar for five flags.** Trial 1871 read 47.27; the other four `-O3` runs read
  47.63-47.99 (mean 47.86). The CI (±1.23%) swallowed five flags at +1.08% to +1.89%. Against 47.86 they read +0.4%
  to +1.2%, so only `-fno-unswitch-loops` (48.43, +1.2%) would clear the 1% bar there, and it was rejected on
  this cluster's five other mines (mean -0.23%). The rejects look right except perhaps that one.
- **PGO's three reps built identical code** (`ad883b1f`), as omnetpp's plain PGO reps did, so cppcheck's training
  run looks deterministic. On cpython, gcc and llvm every PGO rep was a different binary. The reps read 51.65-51.74.
- **The microarch flags were consistent but small.** `-march=znver5`'s three reps read 51.95-52.00 and `-mtune=znver5`'s
  52.02-52.04, each with identical code across its reps, so both CIs were narrow and clear of PGO's. Neither reached
  1%.
