# `cfm mine` results: 821.gcc_s on `niwot`, 2026-10-31

The twelfth SPECspeed benchmark mined on `niwot`. `821.gcc_s` is GCC compiling a set of C sources. It
isn't threaded: specinvoke runs about 2,800 `cc1` compiles 16 at a time (`$multiprocess = 'yes'`), so it
runs unpinned. The first attempt, experiment 181 (2026-10-27), pinned all 16 compiles to one CPU and was
stopped (CLAUDE.md trap, 2026-10-27). This is the first mine with PR #60's fix.

## Headline result

**`-O3 -fno-pie -no-pie -flto -fno-stack-protector -fprofile-use`, +16.88% over plain `-O3`** (ratio
1.1018 → 1.2877).

| Step | Mean | Gain on the step before |
|---|---|---|
| `-O3` | 1.1018 | — |
| `-O3 -fno-pie -no-pie` | 1.1297 | +2.54% |
| `+ -flto` | 1.1495 | +1.75% |
| `+ -fprofile-use` | 1.2741 | +10.83% |
| `+ -fno-stack-protector` (PGO near-miss variant) | 1.2877 | +1.07% over plain PGO |

- **Two hardening opt-outs are in the winning set.** `-fno-pie -no-pie` (+2.39%) is the second PR #57 flag
  accepted on `niwot`, after cppcheck_s's `-fno-stack-protector`. On a compiler, the PIE cost is plausibly the
  GOT-relative access to globals, and `cc1` uses many globals. `-fno-stack-protector` was +0.90% alone,
  CI-clear but under the 1% bar. It got in as PGO's near-miss flag, and on top of PGO it added +1.07%.
- **The pattern is the same as on gcc_r: LTO and PGO, mostly PGO.** gcc_r's mine accepted nothing, and its
  follow-up measured `-flto` +1.81% and PGO +8.9% on top of it. Here it's `-flto` +1.75% and PGO +10.8%.
- **`-march=native` lost 0.22%, and `-march=znver5`/`-mtune=znver5` on the winning set were flat**
  (-0.11%, +0.01%). That fits a compiler: branchy integer code with nothing to vectorize.
- **#33 fired for real: all 12 PGO reps were re-run for low power, and the reruns changed nothing.** PGO
  binaries ran at a median 33-34 W against the `-O3` baseline's 37.1 W, more than 8% below. So the rule re-ran
  each of the four PGO flagsets three times. Every rerun read the same power and a ratio within 0.4% of the rep it replaced.
  That cost 12 trials, about 8.2 hours of the 43-hour mine. Details below.

## Run metadata

| | |
|---|---|
| Host | `niwot`: AMD Ryzen AI 7 350 (4 Zen5 + 4 Zen5c, 16 threads), 60 GB RAM |
| Command | `CFM_SPEC_CONFIG=ryzen350_64gb.gcc_O3.cfg cfm mine 821.gcc_s` (uncapped) |
| Code | `main` at `1da015c` |
| Experiment id | 186 |
| Started / finished | 2026-10-31T01:50:16Z / 2026-11-01T20:54:56Z (43h05m) |
| Final status | `converged` |
| Trials | 71 (1340-1410), 12 of them low-power reruns |
| Candidates screened / confirmed | 7 / 1 (plus `-flto` fast-tracked and accepted) |
| Fast-tracked (M4) | `-flto` (8 of 10 frontend-bound accepts) |
| Skipped as unchanged code (#58) | none |
| Winning flags | `["-O3", "-fno-pie -no-pie", "-flto", "-fno-stack-protector", "-fprofile-use"]`, +16.88% |
| Thread placement | multiprocess, not pinned (PR #60) |
| Guards | bandwidth gate 41.4-45.5 GB/s, waited only before the first run (30 s); no slow-rep reruns; 12 low-power reruns (all PGO); no audit warnings; **baseline recheck flagged (+0.64%)** |
| Power profile | `balanced`; CPU temp 94.8-99.8°C; package power median 37.0-38.0 W for `-O3`, 35-36 W with `-flto`, 33-34 W with PGO |

About 33.5 minutes per `-O3` trial and 40.5 for PGO (two builds and a training run).

## Baseline

| Trial | Role | Ratio |
|---|---|---|
| 1340 | warm-up (excluded from CI) | 1.1261 |
| 1341 | warm-up (excluded from CI) | 1.1046 |
| 1342 | warm-up (excluded from CI) | 1.1029 |
| 1343 | calibration | 1.1016 |
| 1344 | calibration | 1.1002 |
| 1345 | calibration | 1.1034 |
| 1377 | recheck after Phase 4 | 1.1088 (+0.64%, **flagged**) |

Calibration mean **1.10176**, 95% CI **[1.09776, 1.10577]** (±0.36%). Warm-up settled after three reps
(6059 s). The first read +2% high after idle, the largest first-rep jump of the speed mines.

The recheck read 0.28% above the CI's top, and the flag fires at that distance. It doesn't change a verdict here: the one Phase 4
accept (`-fno-pie -no-pie`, CI low 1.1157) clears the recheck too, and `-fno-stack-protector` (1.1117) would
read +0.26% against it instead of +0.90%. Its later win came on top of PGO, against PGO's own reps, so the
baseline doesn't enter it.

**Shape: `frontend-bound`, 59.7%**, `vectorization_density=low`, `allocation_pressure=moderate`, from the
corpus (`reference-matrix:amd-370-64gb`). gcc_r read `memory-bound` 45.2% on the same corpus, so the rate
and speed versions of GCC land in different clusters.

## Phase 2

At 59.7%, past the 55% gate, the shape excluded eight candidates: `-funroll-loops`, `-fprefetch-loop-arrays`,
`-mprefer-vector-width=256`, `-Ofast`, `-ffast-math`, `-fno-math-errno`, `-fipa-pta` and
`-fgraphite-identity`. `-flto` was fast-tracked. That left seven to screen, all six frontend-tagged #57 flags
plus `-march=native`.

## Phase 3 screening (vs. most recent calibration rep, 1.1034)

| Flags | Ratio | Delta |
|---|---|---|
| `-fno-pie -no-pie` | 1.1300 | **+2.41%** |
| `-fno-stack-protector` | 1.1158 | +1.12% |
| `-fcf-protection=none` | 1.1056 | +0.20% |
| `-fno-unswitch-loops` | 1.1051 | +0.15% |
| `-U_FORTIFY_SOURCE` | 1.1024 | -0.10% |
| `-fno-ipa-cp-clone` | 1.1004 | -0.28% |
| `-march=native` | 1.0957 | -0.70% |

All seven survived.

## Phase 4 confirmation (3 reps each, vs. baseline CI [1.09776, 1.10577])

| Flags | Ratios | Mean | 95% CI | Delta | Verdict |
|---|---|---|---|---|---|
| `-fno-pie -no-pie` | 1.1246, 1.1338, 1.1259 | 1.1281 | [1.1157, 1.1405] | **+2.39%** | **accept** |
| `-flto` (fast-tracked) | 1.1205, 1.1229, 1.1265 | 1.1233 | [1.1158, 1.1308] | **+1.95%** | **accept** |
| `-fno-stack-protector` | 1.1124, 1.1116, 1.1111 | 1.1117 | [1.1101, 1.1133] | +0.90% | reject (CI-clear, under 1%) |
| `-fcf-protection=none` | 1.1082, 1.1048, 1.1019 | 1.1050 | [1.0971, 1.1128] | +0.29% | reject |
| `-fno-unswitch-loops` | 1.1005, 1.1062, 1.1035 | 1.1034 | [1.0963, 1.1105] | +0.15% | reject |
| `-fno-ipa-cp-clone` | 1.1028, 1.1011, 1.1045 | 1.1028 | [1.0986, 1.1070] | +0.09% | reject |
| `-march=native` | 1.1017, 1.0992, 1.0970 | 1.0993 | [1.0935, 1.1051] | -0.22% | reject |
| `-U_FORTIFY_SOURCE` | 1.0955, 1.1033, 1.0971 | 1.0986 | [1.0884, 1.1089] | -0.28% | reject |

## Phase 5 combination

| Step | Flags | Ratios | Mean | 95% CI | Delta | Verdict |
|---|---|---|---|---|---|---|
| 1 | `-O3 -fno-pie -no-pie` | 1.1301, 1.1312, 1.1279 | 1.1297 | [1.1256, 1.1339] | +2.54% vs baseline | accept |
| 2 | `+ -flto` | 1.1461, 1.1540, 1.1485 | 1.1495 | [1.1395, 1.1596] | +1.75% vs step 1 | accept |
| Pair | `-flto` + `-fno-pie -no-pie` | 1.1506, 1.1466, 1.1444 | 1.1472 | [1.1394, 1.1550] | +4.12% vs baseline | same flagset as the greedy winner, no change |

The pair trial built the same code as greedy step 2 (fingerprint `bc88f2f7` for both, flags in a different
order). The #58 skip compares a pair only against the baseline, so it measured the same binary three more times
(about 1h50m). Cheap to catch: skip a pair whose sorted flagset equals the greedy winner's.

## Phase 6 multipliers (on `-O3 -fno-pie -no-pie -flto`)

| Stage | Flags | Kept reps | Mean | 95% CI | Delta | Verdict |
|---|---|---|---|---|---|---|
| PGO | `+ -fprofile-use` | 1.2751, 1.2740, 1.2731 | 1.2741 | [1.2716, 1.2766] | **+10.83%** | **accept** |
| PGO near-miss | `+ -fno-stack-protector -fprofile-use` | 1.2861, 1.2885, 1.2887 | 1.2877 | [1.2842, 1.2914] | **+12.02%** | **accept, replaces plain PGO** |
| Microarch | `+ -march=znver5` | 1.2892, 1.2873, 1.2823 | 1.2863 | [1.2774, 1.2951] | -0.11% | reject |
| Microarch | `+ -mtune=znver5` | 1.2920, 1.2848, 1.2867 | 1.2878 | [1.2786, 1.2971] | +0.01% | reject |
| Vector width | — | | | | | skipped (`=256` excluded in Phase 2) |

- **PGO pays at least as much as on gcc_r** (+10.8% on top of LTO, against +8.9% there). That breaks the speed pattern so far,
  where PGO paid a third to a half of its rate gain (ntest, llvm). Running many separate `cc1` processes, gcc_s
  behaves like a rate benchmark, not a threaded one.
- **This is the first mine on `niwot` where the near-miss variant won.** It needs a higher mean and a CI clear of plain
  PGO's, and it cleared plain PGO's CI top by 0.6%. `-fno-stack-protector` paid a little more on top of PGO
  (+1.07%) than alone (+0.90%).
- **PGO build variance was small (#32).** All 24 PGO builds had different code fingerprints, as on every SPEC PGO
  mine. The six reps of each flagset spread 0.28-0.6%.

### The low-power rerun on PGO (#33)

The rule re-runs a rep whose median package power reads more than 8% below the `-O3` calibration reps'
median (37.08 W), up to three times per flagset. Every PGO rep read 33.0-34.1 W:

| Flagset | Reps measured | Power (W) | Ratios | Kept |
|---|---|---|---|---|
| PGO | 1387-1392 | 34.01-34.05 | 1.2699-1.2767 | 1387, 1390, 1392 |
| PGO near-miss | 1393-1398 | 33.06-33.08 | 1.2842-1.2887 | 1393, 1397, 1398 |
| `+ -march=znver5` | 1399-1404 | 33.03-33.06 | 1.2823-1.2899 | 1402, 1403, 1404 |
| `+ -mtune=znver5` | 1405-1410 | 33.03-33.07 | 1.2848-1.2920 | 1407, 1409, 1410 |

The power drop is the code, not the machine: it's flat within each flagset and steps down with each change
(`-O3` 37 W, `-flto` 35-36 W, PGO 33-34 W). The bandwidth probe read normally before every rerun (44.5-45.5
GB/s). No verdict changed, since each kept mean is within 0.1% of the first three reps'. But a third of the
trials after Phase 5 were wasted, and opportunity #33 predicted exactly this.

## Knowledge table after this run (`frontend-bound`, `niwot`)

| Flag | n | Accepted | Mean delta |
|---|---|---|---|
| `-fprofile-use` | 12 | 9 | +7.73% |
| `-flto` | 11 | 9 | +7.21% |
| `-march=native` | 12 | 2 | +3.76% |
| `-fno-stack-protector` | 3 | 1 | +1.55% |
| `-fno-pie -no-pie` | 3 | 1 | +1.21% |
| `-fno-unswitch-loops` | 3 | 1 | +0.66% |
| `-fno-ipa-cp-clone` | 3 | 0 | +0.64% |
| `-U_FORTIFY_SOURCE` | 3 | 0 | +0.40% |
| `-fcf-protection=none` | 3 | 0 | +0.28% |
| `-march=znver5` | 11 | 0 | +0.16% |
| `-mtune=znver5` | 11 | 0 | +0.05% |

Across the three frontend-bound speed mines (llvm_s, cppcheck_s, gcc_s), `-fno-stack-protector` and
`-fno-pie -no-pie` have each been accepted once.
