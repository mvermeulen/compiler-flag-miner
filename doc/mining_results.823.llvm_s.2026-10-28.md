# `cfm mine` results: 823.llvm_s on `niwot`, 2026-10-28

The ninth SPECspeed benchmark mined on `niwot`. `823.llvm_s` is the speed version of `723.llvm_r` (LLVM's
`llc`). Its `object.pm` tags it `pthread` and also sets `$multiprocess`, so it runs unpinned (it wasn't
affected by the gcc_s placement bug fixed in PR #60). It's the first frontend-bound mine since PR #57, so
the first real test of #57's hardening and opt-out candidates.

## Headline result

**`-O3 -flto -fprofile-use`, +19.96% over plain `-O3`** (ratio 0.9252 → 1.1099). The same winning set as
`723.llvm_r` here (+24.83%), but the split between the two steps is reversed:

| Step | Mean | Gain on the step before |
|---|---|---|
| `-O3` | 0.9252 | — |
| `-O3 -flto` | 0.9917 | **+7.18%** |
| `+ -fprofile-use` | 1.1099 | **+11.92%** |

- **LTO pays five times more in speed than in rate** (+7.2% here, +1.4% on llvm_r). That's the opposite of ns3
  and gem5, where speed got about half the rate LTO gain.
- **PGO pays about half its rate gain** (+11.9% here, +23.1% on llvm_r). That matches ntest_s (+3.7% against +11.3%). See
  "PGO in the speed version" below.
- **#57's seven new candidates were all screened and all rejected.** The best, `-fno-stack-protector`, was
  +0.82%, CI-clear of baseline but under the 1% bar. The four hardening opt-outs together might clear it;
  nothing measured that.
- **One PGO rep read 28% slow (0.802), and the slow-rep rule replaced it.** Every PGO rebuild produces
  different code, so that rep was probably a genuinely worse binary, not a noisy measurement. This is the
  main caveat in this write-up. See "One bad PGO build" below.

## Run metadata

| | |
|---|---|
| Host | `niwot`: AMD Ryzen AI 7 350 (4 Zen5 + 4 Zen5c, 16 threads), 60 GB RAM |
| Command | `CFM_SPEC_CONFIG=ryzen350_64gb.gcc_O3.cfg cfm mine 823.llvm_s` (uncapped, queued after the stopped `821.gcc_s` mine) |
| Code | `main` at `edb666c` (code as of `8c69c53`, PRs #56-58). It started before PR #59 was pulled, so it ran without #59's warm-up settling and power check, and its power figures are single readings, not #59's 2-second medians |
| Experiment id | 182 |
| Started / finished | 2026-10-27T13:31:41Z / 2026-10-28T20:34:42Z (31h03m) |
| Final status | `converged` |
| Trials | 53 (1126-1178) |
| Candidates screened / confirmed | 7 / 0 (plus 1 fast-tracked, accepted) |
| Fast-tracked (M4) | `-flto` (7 of 8, accepted) |
| Skipped as unchanged code (#58) | none |
| Winning flags | `["-O3", "-flto", "-fprofile-use"]`, +19.96% |
| Thread placement | pthread, not pinned |
| Guards | bandwidth gate 43.0-45.6 GB/s before every run, waited only before the first (30 s); one slow-rep rerun (trial 1169); no audit warnings; baseline recheck not flagged (-0.23%) |
| Power profile | `balanced`; CPU temp 83.1-94.2°C, package power 20.1-22.1 W |

About 32 minutes per trial: a 6-minute build (every trial rebuilds, opportunity #31) and a 25-minute timed
run. LTO trials took about 35 minutes, PGO trials about 44.

## Baseline

| Trial | Role | Ratio |
|---|---|---|
| 1126 | warm-up (excluded from CI) | 0.9323 |
| 1127 | warm-up (excluded from CI) | 0.9225 |
| 1128 | calibration | 0.9243 |
| 1129 | calibration | 0.9271 |
| 1130 | calibration | 0.9244 |
| 1162 | recheck after Phase 4 | 0.9231 (-0.23%, not flagged) |

Calibration mean **0.9252**, 95% CI **[0.9213, 0.9292]** (±0.43%). All six `-O3` reps share one code fingerprint.

As on ntest_s and flac_s, the first warm-up read high after idle time (+0.8%). The two warm-ups differ by
1.05%, so #59's settling rule would have run a third.

**Shape: `frontend-bound`, 58.5%**, `vectorization_density=moderate`, `allocation_pressure=high`, from the corpus
(`reference-matrix:amd-370-64gb`). llvm_r's corpus entry read frontend-bound 61.6%.

## Phase 2 and M4

| Excluded | Tagged |
|---|---|
| `-funroll-loops` | compute- and backend-bound |
| `-Ofast`, `-ffast-math`, `-fno-math-errno` | compute-bound |
| `-fipa-pta` | backend-bound |
| `-fprefetch-loop-arrays` | memory-bound-corroborated |
| `-fgraphite-identity` | backend-bound, memory-bound-corroborated |

`-mprefer-vector-width=256` was held for Phase 6. `-flto` was fast-tracked on its 7-of-8 frontend-bound record.
`-fprofile-use` was also logged as "fast-tracked" (6 of 9), but PGO never enters the fast track and ran in
Phase 6 as usual. PR #59 corrected that log wording. That left seven candidates to screen: #57's six
frontend-tagged flags and `-march=native`.

## Phase 3 screening (vs. most recent calibration rep, 0.9244)

| Flags | Ratio | Delta |
|---|---|---|
| `-fno-stack-protector` | 0.9318 | +0.80% |
| `-fno-pie -no-pie` | 0.9313 | +0.75% |
| `-fcf-protection=none` | 0.9280 | +0.39% |
| `-U_FORTIFY_SOURCE` | 0.9271 | +0.29% |
| `-fno-unswitch-loops` | 0.9268 | +0.26% |
| `-fno-ipa-cp-clone` | 0.9233 | -0.12% |
| `-march=native` | 0.9221 | -0.25% |

All seven survived.

## Phase 4 confirmation (3 reps each, vs. baseline CI [0.9213, 0.9292])

| Flags | Ratios | Mean | 95% CI | Delta | Verdict |
|---|---|---|---|---|---|
| `-flto` (fast-tracked) | 0.9955, 0.9941, 0.9954 | 0.9950 | [0.9932, 0.9968] | **+7.54%** | **accept** |
| `-fno-stack-protector` | 0.9340, 0.9326, 0.9320 | 0.9328 | [0.9303, 0.9354] | +0.82% | reject (CI-clear, under the 1% bar) |
| `-fcf-protection=none` | 0.9295, 0.9291, 0.9294 | 0.9293 | [0.9289, 0.9297] | +0.44% | reject |
| `-fno-pie -no-pie` | 0.9296, 0.9300, 0.9278 | 0.9291 | [0.9262, 0.9320] | +0.42% | reject |
| `-fno-unswitch-loops` | 0.9260, 0.9270, 0.9276 | 0.9269 | [0.9248, 0.9289] | +0.17% | reject |
| `-U_FORTIFY_SOURCE` | 0.9291, 0.9259, 0.9245 | 0.9265 | [0.9206, 0.9324] | +0.14% | reject |
| `-fno-ipa-cp-clone` | 0.9252, 0.9263, 0.9238 | 0.9251 | [0.9220, 0.9282] | -0.02% | reject |
| `-march=native` | 0.9226, 0.9250, 0.9252 | 0.9243 | [0.9207, 0.9278] | -0.11% | reject |

**#57's opt-outs on their first real test.** The three hardening opt-outs that change code paths in every
function (`-fno-stack-protector`, `-fcf-protection=none`, `-fno-pie -no-pie`) each gave +0.4% to +0.8%, small
but consistent from screening to confirmation. `-U_FORTIFY_SOURCE` and the two pass opt-outs were flat.
None is worth a slot alone. Whether the hardening flags add up when combined wasn't measured. Phase 5 only
combines accepted flags, and the pair tournament only draws from them too.

Every one of them built different code from baseline (each has its own fingerprint), so #58's skip didn't
fire here either.

## Phase 5 combination

| Step | Flags | Ratios | Mean | 95% CI | Delta | Verdict |
|---|---|---|---|---|---|---|
| 1 | `-O3 -flto` | 0.9906, 0.9934, 0.9910 | 0.9917 | [0.9879, 0.9955] | +7.18% vs baseline | accept |

With one accepted flag there's no second step and no pair tournament.

## Phase 6 multipliers (on `-O3 -flto`)

| Stage | Flags | Ratios | Mean | 95% CI | Delta | Verdict |
|---|---|---|---|---|---|---|
| PGO | `+ -fprofile-use` | 1.1140, 1.1056, 1.1102 | 1.1099 | [1.0994, 1.1204] | **+11.92%** | **accept** |
| PGO, near-miss variant | `+ -fno-stack-protector -fprofile-use` | ~~0.8018~~, 1.1134, 1.1144, 1.1209 | 1.1162 | [1.1061, 1.1264] | +12.56% | accept, but doesn't replace plain PGO |
| Microarch | `+ -march=znver5` (on PGO) | 1.1190, 1.1152, 1.1117 | 1.1153 | [1.1061, 1.1245] | +0.49% | reject |
| Microarch | `+ -mtune=znver5` (on PGO) | 1.1174, 1.1156, 1.1201 | 1.1177 | [1.1121, 1.1233] | +0.70% | reject |
| Vector width | — | | | | | skipped (no `-march=` in the winning set) |

- **The near-miss variant measured +0.57% over plain PGO**, about what `-fno-stack-protector` gave alone. It
  replaces plain PGO only with a higher mean *and* a non-overlapping CI (`run_pgo_multiplier()`), and the CIs
  overlap, so plain PGO stands. Its mean excludes the 0.8018 rep, which was replaced by trial 1172 (next
  section).
- **The microarch candidates** were flat on top of PGO, as on every other frontend-bound benchmark here
  (`-march=znver5` 0 of 9, `-mtune=znver5` 0 of 9).

## One bad PGO build

Trial 1169, the near-miss variant's first rep, measured 0.8018, 28% below its siblings. The slow-rep rule
(10% below the fastest sibling) re-ran it as trial 1172 (1.1209) and dropped it. Nothing in the environment
was off for 1169: bandwidth 45.4 GB/s, package power 21.05 W, both in the normal range for this run. Its
timed run also took longer (52 minutes from the previous trial against about 44).

**The code fingerprints point to the build.** Every non-PGO flagset in this mine reproduced its fingerprint
exactly across reps (all six `-O3` reps match, as do the three of each Phase 4 candidate and the six `-flto`
reps). Every one of the 13 PGO builds (trials 1166-1178) has a different fingerprint, including the three reps
of each PGO flagset. SPEC retrains for every build, and the training run evidently doesn't record the same
profile twice, so GCC lays out different code. The training run is five `llvm_s` processes compiling
`train.ll` at `-O1`, `-O2`, `-O3`, `-Os` and `-Oz`, run concurrently (`-T 16` in the build directory's
`speccmds.cmd`) and all writing the same profile files. Why the profile varies wasn't investigated. The
other 12 PGO builds measured within 1.5% of each other (1.1056-1.1209). 1169 is the one that didn't.

The slow-rep rule assumes a slow rep is a measurement problem: re-running the same binary should give the
true number. For a PGO flagset, re-running means rebuilding, so the rule replaced a bad binary with a
different, good one. **The reported PGO results therefore describe the typical PGO build, not the
spread.** One of 13 builds here was 28% slower. A single PGO build of llvm_s made this way could
be that one.

Plain PGO's three reps didn't hit a bad build, so the winning number doesn't depend on the rerun. The
variant's verdict does: with 1169 kept, its mean would have been 1.0376, a -6.5% reject.

PR #63 fixed the same issue for the Phoronix backend by training once per flagset and reusing the profile.
Recorded for SPEC as opportunity #32.

## PGO in the speed version

PGO paid +23.1% on llvm_r and +11.9% here, on the same code, the same pattern as ntest (+11.3% rate, +3.7% speed).
Not investigated. Two plausible reasons: the training profile (five concurrent processes, above) may
describe the timed workload less well than rate's does, and a threaded process that shares caches and
synchronizes may give PGO's layout and inlining changes less to gain, as suggested for ntest_s.

## Compared with `723.llvm_r`

| | `723.llvm_r` (2026-10-19) | `823.llvm_s` (this run) |
|---|---|---|
| Copies / threads | 16 copies | one process, pthreads, unpinned |
| Shape | frontend-bound 61.6% | frontend-bound 58.5% |
| Winner | `-O3 -flto -fprofile-use`, +24.83% | the same, +19.96% |
| `-flto` | +1.4% | +7.2% |
| `-fprofile-use` on top | +23.1% | +11.9% |

## Knowledge table after this run (`frontend-bound`, `niwot`)

| Flag | n | Accepted | Mean delta |
|---|---|---|---|
| `-flto` | 9 | 8 | +8.61% |
| `-fprofile-use` | 10 | 7 | +7.30% |
| `-march=native` | 10 | 2 | +4.46% |
| `-fno-stack-protector` | 1 | 0 | +0.82% |
| `-fcf-protection=none` | 1 | 0 | +0.44% |
| `-fno-pie -no-pie` | 1 | 0 | +0.42% |
| `-fno-unswitch-loops` | 1 | 0 | +0.17% |
| `-march=znver5` | 9 | 0 | +0.16% |
| `-U_FORTIFY_SOURCE` | 1 | 0 | +0.14% |
| `-mtune=znver5` | 9 | 0 | +0.03% |
| `-fno-ipa-cp-clone` | 1 | 0 | -0.02% |

The knowledge table still doesn't separate rate from speed records.
