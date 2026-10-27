# `cfm mine` results: pts/crafty-1.4.5 on `erie`, 2026-10-27

The third Phoronix test mined. Crafty 25.2 is a full chess engine, much larger than TSCP. Like TSCP it is
single-threaded here and pinned to CPU 2 (a 5.09 GHz Zen5 core). Its `bench` command searches 64 positions to
fixed depths, about 15 s on one thread, and reports raw nodes per second.

## Making crafty minable

- **PTS's crafty build never uses the user's flags.** Its install.sh does read `CFLAGS_OVERRIDE`. It then
  runs `make unix-gcc`, whose target sets
  `CFLAGS='-Wall -Wno-array-bounds -pipe -O3 -fprofile-use -mpopcnt -fprofile-correction -pthread'` on make's
  command line. That overrides the environment. PTS's own binary doesn't even have a `.GCC.command.line`
  section. The backend replaces install.sh for crafty (`_BUILD_OVERRIDES`): the same inner make target, with
  upstream's non-optimization flags (warnings, `-mpopcnt`, `-pthread`) followed by the trial's. Upstream's
  `-fprofile-use`/`-fprofile-correction` are dropped: with no profile data they only switch on what
  `-fprofile-use` implies, and PGO is Phase 6's job. So "`-O3`" in this write-up means
  `-O3 -mpopcnt -pthread`.
- **Only the serial result counts.** After the 64 serial positions, `bench` runs two positions on 2 threads
  "to provide PGO data". That pass's node count varies from run to run, and its printed totals include the
  serial run. The backend takes only the first `Raw nodes per second` line (`_FIRST_SCORE_ONLY`).
- **Validator.** The serial pass always visits 191,258,593 nodes. This held over repeated runs of PTS's build
  and of an `-O1 -fno-plt` build. Every trial's log is checked for it.
- **Timer resolution.** Crafty times in centiseconds over about 14 s, so scores move in steps of about 0.07%.
  Identical values (13,431,080 shows up 9 times) are those steps, not a stuck reading.

## Headline result

**`-O3 -fno-pie -no-pie -mtune=znver5`, +7.23% over `-O3`** (14,412,893 vs. 13,440,532 nodes/sec).

| Step | Mean | 95% CI | Gain on the step before |
|---|---|---|---|
| `-O3` | 13,440,532 | [13,399,860, 13,481,204] | — |
| `+ -fno-pie -no-pie` (Phase 4/5) | 14,094,364 | [13,957,566, 14,231,163] | +4.86% |
| `+ -mtune=znver5` (Phase 6) | 14,412,893 | [14,341,433, 14,484,354] | +2.26% |

- **Non-PIE code is the big win, +4.7% to +4.9%.** Phase 4 and Phase 5 agree. It was a small *loss* on TSCP
  (-0.81%) and on coremark (+0.56%, rejected). Crafty indexes large global tables constantly: attack tables,
  masks, hash keys. In a position-independent executable, each such access has to compute the table address
  RIP-relatively first. In a non-PIE binary, the address can be folded into the load. That is the likely
  reason. It is an inference; the generated code wasn't examined.
- **`-mtune=znver5` helps (+2.26%), but `-march=znver5` hurts (-0.73%)**, and `-march=native` hurts too
  (-1.73% on `-O3`). Scheduling for Zen5 pays; the ISA extensions `-march` enables (AVX-512 and the rest)
  cost something on this integer code. TSCP showed the same `-march` penalty (-3.6%).
- **The tscp priors didn't carry over.** M4 fast-tracked `-funroll-loops` and `-flto`, TSCP's two accepts in
  the same `frontend-bound` cluster. Here `-funroll-loops` lost 1.32%, and `-flto` read +0.76% with a wide
  CI, rejected. Crafty `#include`s every source file into one translation unit (`crafty.c`), so LTO has
  little left to do.
- **PGO probably helps, but didn't clear the bar.** See Phase 6.

## Run metadata

| | |
|---|---|
| Host | `erie` (see [`host_erie.md`](host_erie.md)), `performance` profile, on AC |
| Command | `cfm mine pts/crafty-1.4.5` (uncapped, warm-up minimum 180 s, power check on) |
| Code | `feature/spread-rerun` at `0390150` (with the new spread-relative slow-rep rule) |
| Experiment id | 9 (8 was the smoke test) |
| Started / finished | 2026-10-27T15:17:32Z / 2026-10-27T15:58:27Z (41 min) |
| Final status | `converged` |
| Trials | 86 (233-318) |
| Candidates | 13 screened + 2 fast-tracked (M4); 1 accepted in Phase 4; none pruned |
| Shape | `frontend-bound` 42.6% (local `deep-cpu` trial), vectorization density moderate |
| Guards | no slow-rep (either rule) or low-power reruns; no audit warnings; baseline recheck -0.28% |
| Power / temp | package power 17.1-18.1 W; CPU temp 77.2-81.2°C |

## Baseline

Trial 233 was the characterization run. Warm-up ran to its cap of 8 reps (234-241, 185 s). Its reps ranged
13.20-13.51M, and its last two agreed within 0.4%. Calibration (242-244): 13,459,436, 13,431,080,
13,431,080. Recheck (303): 13,402,844, -0.28%.

## Phase 4 confirmation (3 reps each, vs. baseline CI [13,399,860, 13,481,204])

| Flag | Mean | 95% CI | Δ | Verdict |
|---|---|---|---|---|
| `-fno-pie -no-pie` | 14,066,632 | [13,983,910, 14,149,354] | +4.66% | **accept** |
| `-flto` (fast-tracked) | 13,543,246 | [13,153,776, 13,932,715] | +0.76% | reject |
| `-fcf-protection=none` | 13,535,653 | [13,494,462, 13,576,845] | +0.71% | reject (near miss) |
| `-Ofast` | 13,516,684 | [13,368,199, 13,665,169] | +0.57% | reject |
| `-fgraphite-identity` | 13,475,403 | [13,333,129, 13,617,677] | +0.26% | reject |
| `-ffast-math` | 13,459,467 | [13,397,265, 13,521,669] | +0.14% | reject |
| `-U_FORTIFY_SOURCE` | 13,431,134 | [13,349,847, 13,512,420] | -0.07% | reject |
| `-fno-ipa-cp-clone` | 13,424,814 | [13,376,113, 13,473,516] | -0.12% | reject |
| `-fno-math-errno` | 13,422,584 | [13,083,005, 13,762,162] | -0.13% | reject |
| `-fno-stack-protector` | 13,415,415 | [13,348,010, 13,482,820] | -0.19% | reject |
| `-fno-unswitch-loops` | 13,406,069 | [13,298,445, 13,513,692] | -0.26% | reject |
| `-fipa-pta` | 13,371,611 | [13,358,205, 13,385,016] | -0.51% | reject |
| `-fprefetch-loop-arrays` | 13,294,294 | [13,163,961, 13,424,627] | -1.09% | reject |
| `-funroll-loops` (fast-tracked) | 13,263,454 | [13,203,050, 13,323,858] | -1.32% | reject |
| `-march=native` | 13,208,520 | [13,126,734, 13,290,307] | -1.73% | reject |

CIs here run ±0.1% to ±2.9%, wider than TSCP's ±0.1% to ±0.25%. Each crafty rep is one 15-second run;
each TSCP rep averaged 40 runs. `-fcf-protection=none` was CI-clear of baseline but under the 1% bar, so it
became Phase 6's PGO near-miss candidate.

## Phase 5

Only one flag was accepted, so the greedy walk re-confirmed it (304-306: +4.86%) and there was nothing to
pair.

## Phase 6 multipliers (on `-O3 -fno-pie -no-pie`, 14,094,364)

| Trials | Added | Mean | 95% CI | Δ | Verdict |
|---|---|---|---|---|---|
| 307-309 | `-fprofile-use` | 14,348,471 | [14,093,084, 14,603,859] | +1.80% | reject (CI overlap) |
| 310-312 | `-fcf-protection=none -fprofile-use` | 14,351,835 | [14,164,056, 14,539,615] | +1.83% | reject (CI overlap) |
| 313-315 | `-march=znver5` | 13,991,223 | [13,874,579, 14,107,868] | -0.73% | reject |
| 316-318 | `-mtune=znver5` | 14,412,893 | [14,341,433, 14,484,354] | +2.26% | **accept** |

**Every PGO rep built different code.** The six PGO trials have six different code fingerprints. Each one
trains on a fresh run of `bench`, and the 2-thread pass at its end, which upstream added for PGO, is
nondeterministic, so each profile differs a little. That spread widens PGO's CI. Both PGO variants read
about +1.8%, above the 1% bar, but their CIs overlap the incoming set's. PGO was also tried before
`-mtune=znver5`, so the pair was never measured together.

## Compared with the other PTS tests on erie

| | coremark | tscp | crafty |
|---|---|---|---|
| Winner gain | +8.86% | +6.07% | +7.23% |
| `-fno-pie -no-pie` | +0.56% (reject) | -0.81% | **+4.66%** |
| `-funroll-loops` | **+5.86%** | **+2.30%** | -1.32% |
| `-flto` | -1.53% | **+1.43%** | +0.76% (reject) |
| `-march=native` | **+2.58%** | -3.61% | -1.73% |
| `-mtune=znver5` on the winner | -0.08% | -0.45% | **+2.26%** |
| PGO on the winner | **+3.10%** | -2.92% (thermal) | +1.80% (reject, CI overlap) |

Three small integer benchmarks on one host, and each winning flag is different. Even the two chess engines
disagree on three of the six rows. It is a concrete case for per-benchmark mining over one set of "good
flags", and for keeping M4's fast track to flags with a majority of accepts.

## Follow-ups

1. **Deterministic PGO training for crafty.** Train with the serial pass only, so every PGO build gets the
   same profile. Then re-try PGO on `-O3 -fno-pie -no-pie -mtune=znver5`. A real +1.8% would make the winner
   about +9%.
2. **Two crafty runs per rep.** One 15-second run gives ±0.3% to ±2.9% CIs; averaging two would tighten them
   for about 15 s more per trial.
3. **`-fno-pie -no-pie` on SPEC.** A +4.7% on crafty suggests checking it on SPEC's `706.stockfish_r`,
   another table-driven chess engine. It's already in the catalog; `niwot`'s `cfm.db` holds its SPEC history.
