# `cfm mine` results: 827.cppcheck_s on `niwot`, 2026-10-29

The tenth SPECspeed benchmark mined on `niwot`. `827.cppcheck_s` is the speed version of `727.cppcheck_r` (the
cppcheck C/C++ static analyzer). It's tagged `pthread` and runs unpinned. It's the first mine on the code
from PRs #59-#66: warm-up runs until settled, the low-power rerun check, power as a median of 2-second
samples, and #62's spread-relative slow-rep rule.

## Headline result

**`-O3 -fno-stack-protector -fprofile-use`, +12.00% over plain `-O3`** (ratio 1.0595 → 1.1866).

| Step | Mean | Gain on the step before |
|---|---|---|
| `-O3` | 1.0595 | — |
| `-O3 -fno-stack-protector` | 1.0895 | **+2.83%** |
| `+ -fprofile-use` | 1.1866 | **+8.91%** |

- **PR #57 produced its first accepted flags.** `-fno-stack-protector` (+2.92% in Phase 4) is in the winning
  set. `-fno-unswitch-loops` (+1.65%) was also accepted, but lost 0.58% on top of `-fno-stack-protector` and
  was dropped in Phase 5. On llvm_s, the only earlier test, the best of these flags was +0.82%.
- **`-flto` was flat (-0.16%)** despite its 8-of-9 frontend-bound prior. cppcheck_r here also rejected it
  alone (+0.96%), though it added +2.6% on top of PGO in that follow-up. `-O3 -fno-stack-protector -flto
  -fprofile-use` wasn't measured.
- **The baseline was noisier than llvm_s's** (±1.0% against ±0.43%), and so was every rep: confirmation
  CIs ran ±0.6% to ±1.4%. Two flags with means past the 1% bar (`-fno-ipa-cp-clone` +1.84%,
  `-U_FORTIFY_SOURCE` +1.34%) were rejected on CI overlap.
- **#59's warm-up rule ran five warm-ups instead of two**, its first real effect. See "Baseline".

## Run metadata

| | |
|---|---|
| Host | `niwot`: AMD Ryzen AI 7 350 (4 Zen5 + 4 Zen5c, 16 threads), 60 GB RAM |
| Command | `CFM_SPEC_CONFIG=ryzen350_64gb.gcc_O3.cfg cfm mine 827.cppcheck_s` (uncapped, queued after `823.llvm_s`) |
| Code | `main` at `fcf7e05` (PRs #59-#66) |
| Experiment id | 183 |
| Started / finished | 2026-10-28T20:36:24Z / 2026-10-29T15:03:13Z (18h27m) |
| Final status | `converged` |
| Trials | 58 (1179-1236) |
| Candidates screened / confirmed | 7 / 2 (plus 1 fast-tracked, rejected) |
| Fast-tracked (M4) | `-flto` (8 of 9, rejected) |
| Skipped as unchanged code (#58) | none |
| Winning flags | `["-O3", "-fno-stack-protector", "-fprofile-use"]`, +12.00% |
| Thread placement | pthread, not pinned |
| Guards | bandwidth gate 42.8-45.7 GB/s before every run, waited only before the first (30 s); no slow-rep or low-power reruns; no audit warnings; baseline recheck not flagged (+0.27%) |
| Power profile | `balanced`; CPU temp 91.5-95.8°C; package power (median during the run) 40.0 W for every non-PGO trial, 37-39 W for PGO |

About 19 minutes per trial, 20 for PGO.

**Power figures aren't comparable with earlier write-ups.** Since #59 the figure is the median of about 500
two-second samples during the timed run. Before, it was a single reading. llvm_s's 21 W single readings and
cppcheck_s's 40 W medians describe different things, not a doubling of power. The non-PGO medians are 40.0 W
to within 0.07 W on every trial, which looks like a sustained package power limit rather than load. Not
checked further.

## Baseline

| Trial | Role | Ratio |
|---|---|---|
| 1179 | warm-up (excluded from CI) | 1.0813 |
| 1180 | warm-up (excluded from CI) | 1.0688 |
| 1181 | warm-up (excluded from CI) | 1.0463 |
| 1182 | warm-up (excluded from CI) | 1.0641 |
| 1183 | warm-up (excluded from CI) | 1.0593 |
| 1184 | calibration | 1.0547 |
| 1185 | calibration | 1.0608 |
| 1186 | calibration | 1.0629 |
| 1218 | recheck after Phase 4 | 1.0623 (+0.27%, not flagged) |

Calibration mean **1.0595**, 95% CI **[1.0488, 1.0701]** (±1.0%). All nine `-O3` reps share one code fingerprint.

**Warm-up settled after five reps (95 minutes).** The first read 2% high after idle, as on every speed mine
so far, then 1181 read 1.0463, the lowest `-O3` number in the run. The old fixed count would have started
calibrating at 1181, and a CI including it would have been wider still. Rule: the last two warm-ups within
`WARMUP_SETTLE_PCT` (1%). 1180→1181 differed by 2.1% and 1181→1182 by 1.7%; 1182→1183 (0.45%) settled it.

The run never got quieter than this. The six `-fno-stack-protector` reps spanned 1.0854-1.0973 (1.1%), and the
six `-O3` reps from 1182 on spanned 1.0547-1.0641 (0.9%).

**Shape: `frontend-bound`, 74.1%**, `vectorization_density=low`, `allocation_pressure=moderate`, from the corpus
(`reference-matrix:amd-370-64gb`). The most confident shape of any mine here; cppcheck_r's read 71.0%.

## Phase 2 and M4

| Excluded | Tagged |
|---|---|
| `-funroll-loops` | compute- and backend-bound |
| `-Ofast`, `-ffast-math`, `-fno-math-errno` | compute-bound |
| `-fipa-pta` | backend-bound |
| `-fprefetch-loop-arrays` | memory-bound-corroborated |
| `-fgraphite-identity` | backend-bound, memory-bound-corroborated |
| `-mprefer-vector-width=256` | vectorization-density-high (the shape reads low) |

`-flto` was fast-tracked. The prior-knowledge line for `-fprofile-use` now reads "tried in Phase 6" (#59's
wording fix). That left the same seven candidates as llvm_s: #57's six frontend-tagged flags and
`-march=native`.

## Phase 3 screening (vs. most recent calibration rep, 1.0629)

| Flags | Ratio | Delta |
|---|---|---|
| `-fno-stack-protector` | 1.0996 | **+3.45%** |
| `-fno-unswitch-loops` | 1.0875 | **+2.32%** |
| `-fno-ipa-cp-clone` | 1.0802 | +1.63% |
| `-fcf-protection=none` | 1.0715 | +0.81% |
| `-U_FORTIFY_SOURCE` | 1.0678 | +0.46% |
| `-march=native` | 1.0678 | +0.46% |
| `-fno-pie -no-pie` | 1.0573 | -0.53% |

All seven survived.

## Phase 4 confirmation (3 reps each, vs. baseline CI [1.0488, 1.0701])

| Flags | Ratios | Mean | 95% CI | Delta | Verdict |
|---|---|---|---|---|---|
| `-fno-stack-protector` | 1.0878, 1.0863, 1.0973 | 1.0904 | [1.0756, 1.1053] | **+2.92%** | **accept** |
| `-fno-ipa-cp-clone` | 1.0842, 1.0745, 1.0780 | 1.0789 | [1.0667, 1.0912] | +1.84% | reject (CIs overlap) |
| `-fno-unswitch-loops` | 1.0796, 1.0747, 1.0765 | 1.0770 | [1.0707, 1.0832] | **+1.65%** | **accept** |
| `-U_FORTIFY_SOURCE` | 1.0772, 1.0680, 1.0757 | 1.0736 | [1.0613, 1.0859] | +1.34% | reject (CIs overlap) |
| `-fno-pie -no-pie` | 1.0733, 1.0637, 1.0676 | 1.0682 | [1.0562, 1.0802] | +0.82% | reject |
| `-march=native` | 1.0678, 1.0676, 1.0691 | 1.0682 | [1.0663, 1.0701] | +0.82% | reject |
| `-fcf-protection=none` | 1.0616, 1.0660, 1.0545 | 1.0607 | [1.0463, 1.0751] | +0.12% | reject |
| `-flto` (fast-tracked) | 1.0643, 1.0559, 1.0531 | 1.0578 | [1.0432, 1.0723] | -0.16% | reject |

- **`-fno-unswitch-loops` passed on a tight CI; `-fno-ipa-cp-clone` failed on a wide one** despite a
  higher mean. With a ±1% baseline, three reps can't separate effects this size reliably.
- **`-march=native`'s CI touches the baseline's upper bound exactly** (1.0701), so it isn't CI-clear and isn't
  a near-miss. No Phase 4 reject qualified as one, so Phase 6 had no near-miss variant.
- **The hardening opt-outs differ by benchmark.** `-fno-stack-protector` paid on both frontend-bound speed
  mines (+0.82% llvm_s, +2.92% here). `-fcf-protection=none` and `-fno-pie -no-pie` paid a little on llvm_s
  and nothing clear here.

## Phase 5 combination

| Step | Flags | Ratios | Mean | 95% CI | Delta | Verdict |
|---|---|---|---|---|---|---|
| 1 | `-O3 -fno-stack-protector` | 1.0953, 1.0878, 1.0854 | 1.0895 | [1.0767, 1.1023] | +2.83% vs baseline | accept |
| 2 | `+ -fno-unswitch-loops` | 1.0825, 1.0792, 1.0877 | 1.0831 | [1.0725, 1.0937] | -0.58% vs step 1 | reject |
| Pair | `-fno-stack-protector` + `-fno-unswitch-loops` | 1.0899, 1.0763, 1.0778 | 1.0814 | [1.0628, 1.0999] | +2.07% vs baseline | reject (CIs overlap) |

With two accepted flags, the pair tournament's only pair is the same flagset as greedy step 2, so it was
measured twice (the same fingerprint, six reps, mean 1.0822). Together the two flags read about 0.7% below
`-fno-stack-protector` alone, so `-fno-unswitch-loops`'s +1.65% alone doesn't carry over. That fits an
effect this small being partly noise, though the combination could also genuinely interact.

## Phase 6 multipliers (on `-O3 -fno-stack-protector`)

| Stage | Flags | Ratios | Mean | 95% CI | Delta | Verdict |
|---|---|---|---|---|---|---|
| PGO | `+ -fprofile-use` | 1.1899, 1.1845, 1.1853 | 1.1866 | [1.1792, 1.1939] | **+8.91%** | **accept** |
| Microarch | `+ -march=znver5` (on PGO) | 1.2038, 1.1821, 1.1904 | 1.1921 | [1.1649, 1.2194] | +0.47% | reject |
| Microarch | `+ -mtune=znver5` (on PGO) | 1.1794, 1.1923, 1.1989 | 1.1902 | [1.1656, 1.2148] | +0.31% | reject |
| Vector width | — | | | | | skipped (no deferred candidates) |

The audit confirmed `-O3 -fno-stack-protector -fprofile-use` in the winning binary.

**PGO build variance (#32):** all nine PGO builds have different code fingerprints again, as on llvm_s. This
time none was an outlier: the nine measured 1.1794-1.2038, a 2.1% spread, against 1.1% for the six reps of
the one `-fno-stack-protector` binary. The microarch CIs (±2.1-2.3%) are wide partly for that reason.

**PGO drew less power than everything else.** Every PGO trial's median was 37-39 W against 40.0 W for every
non-PGO trial: 3-7% lower for a faster binary. That's under #59's 8% low-power threshold, so nothing was
re-run, but it's close. A benchmark where PGO lowers power a little more would have its PGO reps re-run
for a reason that isn't a fault. This is the cross-flagset weakness noted when #59 was reviewed: the threshold
compares every rep against the `-O3` baseline's power.

## Compared with `727.cppcheck_r`

| | `727.cppcheck_r` (2026-10-19, plus 2026-10-22 follow-up) | `827.cppcheck_s` (this run) |
|---|---|---|
| Copies / threads | 16 copies | one process, pthreads, unpinned |
| Shape | frontend-bound 71.0% | frontend-bound 74.1% |
| Mine's winner | `-O3 -fprofile-use`, +7.78% | `-O3 -fno-stack-protector -fprofile-use`, +12.00% |
| `-flto` alone | +0.96% (CI-clear, under the bar) | -0.16% |
| PGO on top | +7.78% (on `-O3`) | +8.91% (on `-fno-stack-protector`) |
| `-flto` with PGO | +2.6% over PGO alone (follow-up) | not measured |

PR #57's flags didn't exist when cppcheck_r was mined. Unlike llvm and ntest, PGO paid about as much here as in
rate.

## Knowledge table after this run (`frontend-bound`, `niwot`)

| Flag | n | Accepted | Mean delta |
|---|---|---|---|
| `-flto` | 10 | 8 | +7.74% |
| `-fprofile-use` | 11 | 8 | +7.45% |
| `-march=native` | 11 | 2 | +4.13% |
| `-fno-stack-protector` | 2 | 1 | +1.87% |
| `-fno-unswitch-loops` | 2 | 1 | +0.91% |
| `-fno-ipa-cp-clone` | 2 | 0 | +0.91% |
| `-U_FORTIFY_SOURCE` | 2 | 0 | +0.74% |
| `-fno-pie -no-pie` | 2 | 0 | +0.62% |
| `-fcf-protection=none` | 2 | 0 | +0.28% |
| `-march=znver5` | 10 | 0 | +0.19% |
| `-mtune=znver5` | 10 | 0 | +0.06% |

`-fno-stack-protector` and `-fno-unswitch-loops` are at 1 of 2, short of the strict majority the fast track
needs.

## Follow-ups

- `-O3 -fno-stack-protector -flto -fprofile-use`: cppcheck_r's follow-up found LTO paying on top of PGO
  though not alone. Three PGO reps, about an hour.
