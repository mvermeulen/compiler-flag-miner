# `cfm mine` results: 723.llvm_r on `chicago`, 2026-11-22

This is the seventh intrate benchmark mined on `chicago` (see [`host_chicago.md`](host_chicago.md)). `723.llvm_r` is
the LLVM compiler (C++). Both earlier mines found `-O3 -flto -fprofile-use`: +32.23% on this machine in August
([write-up](mining_results.723.llvm_r.2026-08-26.md)) and +24.83% on niwot
([write-up](mining_results.723.llvm_r.2026-10-19.md)). Its corpus shape is frontend-bound at 61.6%, over the 55%
gate, so the shape filter excluded seven candidates, as on cpython.

## Headline result

**`-O3 -fno-pie -no-pie -fno-stack-protector -fprofile-use`, +16.95% over plain `-O3`** (ratio 57.671 → 67.447).

| Step | Mean | Gain on the step before |
|---|---|---|
| `-O3` | 57.671 | — |
| `-O3 -fno-pie -no-pie` | 60.313 | +4.58% |
| `+ -fno-stack-protector` | 61.132 | +1.36% |
| `+ -fprofile-use` | 67.447 | **+10.33%** |

- **`-flto` lost 1.26% here**, with its CI clear below baseline. It was fast-tracked (accepted 3 of 4 in this cluster)
  and was +5.9% on this machine in August and +1.43% on niwot. With LTO rejected, the winning set has no LTO, unlike
  both earlier mines.
- **PGO added +10.33%**, less than half of August's +24.9% and niwot's +23.07%, both of which were on top of `-flto`.
  On niwot's gcc_r follow-up, LTO and PGO together gave more than the sum of their separate gains. So LTO may help
  here once PGO is on, even though it loses alone. The mine can't show that: it never tries a flag that Phase 4
  rejected on top of PGO. Open item 19 on the host page.
- **`-fno-pie -no-pie` gave +4.58%**, the largest single-flag gain on llvm. It wasn't in the catalog when the earlier
  mines ran. Non-PIE is now in five of the seven intrate winning sets here.
- **`-fno-stack-protector` gave +1.88% alone and +1.36% on top of non-PIE.** `-U_FORTIFY_SOURCE` (+0.74%) and
  `-fcf-protection=none` (+0.46%) were CI-clear but under the 1% bar. The PGO near-miss variant with
  `-U_FORTIFY_SOURCE` read 67.81, 0.5% above plain PGO, but the CIs overlapped, so it didn't replace it.
- **`-march=native` lost 0.96%**, `-march=znver5` -0.09% and `-mtune=znver5` -0.33% on top of PGO.

## Run metadata

| | |
|---|---|
| Host | `chicago`: AMD Ryzen AI MAX+ 395 (16 Zen5 cores, 32 threads), 91 GB RAM, power profile `performance`, kernel 7.0.0-43 |
| Command | `python3 -m cfm.cli mine 723.llvm_r` (uncapped, defaults) |
| Code | `main` at `2e83596` (no code changes since `3b15833`, PR #72) |
| SPEC config | `gcc_O3.cfg`, `copies = 32` |
| Experiment id | 35 |
| Started / finished | 2026-11-21T13:39:48Z / 2026-11-22T00:33:05Z (10h53m) |
| Final status | `converged` |
| Trials | 59 (1809-1867), none skipped, no reruns |
| Candidates screened / confirmed | 8 / 8 (plus `-flto` fast-tracked) |
| Excluded on shape (Phase 2) | `-funroll-loops`, `-fprefetch-loop-arrays`, `-mprefer-vector-width=256`, `-Ofast`, `-ffast-math`, `-fipa-pta`, `-fgraphite-identity` (frontend-bound 61.6%, over the gate) |
| Fast-tracked (M4) | `-flto` (accepted 3 of 4, mean +6.72%) |
| Accepted in Phase 4 | `-fno-pie -no-pie` +4.58%, `-fno-stack-protector` +1.88% |
| Winning flags | `["-O3", "-fno-pie -no-pie", "-fno-stack-protector", "-fprofile-use"]`, +16.95% |
| Guards | throttle stop not triggered; bandwidth gate waited 30 s before 1 of 59 timed runs; no reruns; baseline recheck not flagged (+0.00%) |
| Power | package power median 84.97-85.00 W on every trial; CPU temperature 86.5-93.6°C |

A trial took about 9.5 minutes, an LTO trial about 15, and a PGO trial about 15.5.

## Baseline

Shape from the reference-matrix corpus (`amd-370-64gb`): frontend-bound 61.6%, `vectorization_density=low`,
`allocation_pressure=moderate`.

| Trial | Role | Ratio |
|---|---|---|
| 1809 | warm-up | 57.678 |
| 1810 | warm-up | 57.684 |
| 1811 | calibration | 57.693 |
| 1812 | calibration | 57.723 |
| 1813 | calibration | 57.598 |
| 1849 | recheck | 57.674 (+0.00%) |

The calibration mean is 57.671, with a 95% CI of [57.509, 57.833] (±0.28%). Warm-up settled after the minimum two
reps (1195 s). Every `-O3` build had the same code fingerprint (`9413052e`).

## Trials

| Trials | Phase | Flags (on `-O3`) | Mean ratio | Delta | Verdict |
|---|---|---|---|---|---|
| 1814-1821 | screening | 8 candidates | 56.79-60.21 | | all survived |
| 1822-1824 | confirmation | `-fno-pie -no-pie` | 60.313 | +4.58% | **accept** (the greedy start) |
| 1825-1827 | confirmation | `-fno-stack-protector` | 58.754 | +1.88% | **accept** |
| 1828-1830 | confirmation | `-fcf-protection=none` | 57.938 | +0.46% | reject (CI-clear, under the 1% bar) |
| 1831-1833 | confirmation | `-U_FORTIFY_SOURCE` | 58.096 | +0.74% | reject (CI-clear, under the 1% bar) |
| 1834-1836 | confirmation | `-fno-ipa-cp-clone` | 57.613 | -0.10% | reject |
| 1837-1839 | confirmation | `-fno-unswitch-loops` | 57.801 | +0.23% | reject |
| 1840-1842 | confirmation | `-march=native` | 57.119 | -0.96% | reject |
| 1843-1845 | confirmation | `-fno-math-errno` | 57.776 | +0.18% | reject |
| 1846-1848 | confirmation (fast-tracked) | `-flto` | 56.946 | -1.26% | reject (CI-clear, below baseline) |
| 1849 | baseline recheck | `-O3` | 57.674 | +0.00% | not flagged |
| 1850-1852 | combination (greedy) | `-fno-pie -no-pie -fno-stack-protector` | 61.132 | +1.36% | **accept** |
| 1853-1855 | combination (pair) | `-fno-pie -no-pie -fno-stack-protector` | 61.071 | +5.90% | accept, same code as the winner |
| 1856-1858 | PGO | winner `+ -fprofile-use` | 67.447 | +10.33% | **accept** |
| 1859-1861 | PGO (near-miss variant) | winner `+ -U_FORTIFY_SOURCE -fprofile-use` | 67.810 | +10.92% | accept, CI overlaps plain PGO's |
| 1862-1864 | microarch | winner + PGO `+ -march=znver5` | 67.389 | -0.09% | reject |
| 1865-1867 | microarch | winner + PGO `+ -mtune=znver5` | 67.225 | -0.33% | reject |

Phase 4 and pair deltas are against `-O3`, the greedy-step delta against `-O3 -fno-pie -no-pie`, and Phase 6 deltas
against the set they were layered on. The greedy walk started from the Phase 4 `-fno-pie -no-pie` result rather than
re-measuring it. The vector-width multiplier had no candidate (the shape filter had excluded `256`).

## Observations

- **This baseline was the tightest of the seven intrate mines here** (±0.28%; every `-O3` run 57.60-57.72), which is
  why two +0.5-0.7% flags came out CI-clear.
- **`-flto`'s gain on llvm has fallen with each mine**: +5.9% in August, +1.43% on niwot, -1.26% here. The August run
  predates the non-PIE flag, but LTO was tested alone here, on plain `-O3`, so non-PIE doesn't explain the loss.
  Something in the intervening changes (the compiler, SPEC tools or config) may have changed; the run doesn't show
  which.
- **The three PGO reps were three different binaries** (`44013223`, `2eb570ce`, `4dedf736`) and read 67.16-67.63
  (0.7%). The near-miss variant's reps (67.63-68.01) overlapped them.
- **The pair tournament re-measured the winner's code** (`55f1ca84`: 61.07 against 61.13), its only pair, three timed
  runs (niwot opportunity #35).
