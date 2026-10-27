# `cfm mine` results: pts/coremark-1.0.1 on `erie`, 2026-10-26 (re-mine)

A re-mine of [the first coremark run](mining_results.pts_coremark-1.0.1.2026-10-26.md), after three changes
that write-up called for:

1. **Power profile `performance`** instead of `balanced` (`powerprofilesctl set performance`). Under `balanced`,
   package power had sagged from about 24 W to about 20 W partway through, and scores fell with it.
2. **Fixed-work runs.** `_RUN_OVERRIDES` pins coremark at 600,000 iterations per process (9.6M total, about
   25 s). The first mine's runs had switched between 9.6M and 17.6M iterations.
3. **Settle-based warm-up and power-aware reruns** (commit `1853b3d`). Baseline warm-up continues until two
   reps agree within 1% *and* 180 s have passed, capped at 8 reps. Package power is sampled every 2 s
   during each run. A confirmation or calibration rep whose power reads more than 8% below the baseline's is
   rerun after 30 s of idle.

## Headline result

**`-O3 -funroll-loops -fprofile-use`, +8.86% over plain `-O3`** (416,025 vs. 382,163 iterations/sec).

| Step | Mean | 95% CI | Gain on the step before |
|---|---|---|---|
| `-O3` (baseline) | 382,163 | [375,582, 388,744] | — |
| `+ -funroll-loops` (Phase 4/5) | 403,514 | [403,238, 403,790] | +5.59% |
| `+ -fprofile-use` (Phase 6) | 416,025 | [413,178, 418,872] | +3.10% |

- **`-funroll-loops` is a real win, as the first run suspected.** It confirmed at +5.86% in Phase 4 and
  re-confirmed at +5.59% in Phase 5. The first mine screened it at +5.07%, then rejected it as flat, against a
  baseline measured at higher power. This closes `host_erie.md`'s open item 1.
- **PGO stacks on top of it.** It adds +3.10% on `-funroll-loops`. In the first run, PGO alone added +6.65% on
  `-O3` (under `balanced`). The two overlap: GCC's `-fprofile-use` turns on `-funroll-loops` itself, but only
  for loops the profile shows are hot. Unrolling everywhere and then adding PGO still came out ahead.
- **`-march=native` is a small real win on its own (+2.58%) that doesn't stack with unrolling.** Its CI
  ([390,948, 393,067]) clears the baseline's, so it was accepted. Added to `-funroll-loops` in Phase 5, it read
  -0.83%. It was rejected there. The pair tournament measured the same pair at +4.64% against baseline,
  which is below the greedy winner's +5.59%.
- **The guards found nothing to fix, as hoped under `performance`.** Warm-up was settled from its second rep
  and ran 7 reps only because of the 180 s minimum. No rep's power came near the 8% rerun threshold. There
  were no slow-rep reruns. The baseline recheck read -0.49% and wasn't flagged.

## Run metadata

| | |
|---|---|
| Host | `erie`: HP OmniBook 5 laptop, AMD Ryzen AI 7 350 (4 Zen5 + 4 Zen5c, 16 threads), 30 GB RAM, on AC |
| Command | `cfm mine pts/coremark-1.0.1` (uncapped, default `-O3` base, `--warmup-min-seconds` 180 by default, power check on) |
| Code | `feature/phoronix-workload` at `1853b3d` |
| Experiment id | 4 |
| Started / finished | 2026-10-27T01:59:59Z / 2026-10-27T03:08:52Z (69 min) |
| Final status | `converged` |
| Trials | 90 (58-147) |
| Candidates screened / accepted in Phase 4 | 15 / 2 (none pruned at screening) |
| Fast-tracked (M4) | none (see "Knowledge priors" below) |
| Winning flags | `["-O3", "-funroll-loops", "-fprofile-use"]`, +8.86% |
| Workload | coremark 1.0, `MULTITHREAD=16 USE_FORK=1`, 600,000 iterations per process |
| Guards | bandwidth gate passed every run; no slow-rep or low-power reruns; no audit warnings; baseline recheck -0.49%, not flagged |
| Power | platform profile `performance`; CPU temp 84.0-90.2°C; package power 28.0-29.1 W (median per run) |

The run took 69 minutes against the first mine's 48. Most of the difference is the 5 extra warm-up reps, the
Phase 5 greedy step and pair tournament (6 trials the first run didn't need), and three Phase 6 multipliers
instead of two. Each Phase 6 trial takes about 2 min 43 s (instrumented build, training run, rebuild, timed run).

## Baseline

| Trials | Role | Ratios | Power |
|---|---|---|---|
| 58 | `deep-cpu` characterization (compute-bound, 42.6%) | 384,831 | 29.10 W |
| 59-65 | warm-up (excluded from CI) | 384,739, 385,403, 380,454, 385,063, 384,878, 384,277, 385,186 | 29.10 W |
| 66-68 | calibration | 383,081, 379,177, 384,231 | 29.10 W |
| 129 | recheck after Phase 4 | 380,303 (-0.49%) | 28.07 W |

Warm-up recorded "settled after 7 reps, 206 s". There was no thermal transient this time. The 4.5-minute
`deep-cpu` characterization run, which comes first, had already brought the machine to its steady
temperature. The 2-minute transient seen in the power test came from a cold start.

The baseline CI is ±1.72%, wider than most flagsets' (±0.1% to ±0.9%), because of rep 67 (379,177, about 1%
low). The warm-up had one rep like it too (61, 380,454). About one rep in eight landing about 1% low appears to
be this host's residual noise under `performance`. It is far below the 10% slow-rep threshold. It doesn't change any
verdict here: the two accepts clear the CI by a wide margin, and the closest rejects are below the 1% practical
bar either way.

## Phase 3 screening (vs. most recent calibration rep, 384,231)

Nothing was pruned. All 15 candidates went to Phase 4.

| Trial | Flag | Ratio | Δ |
|---|---|---|---|
| 70 | `-funroll-loops` | 407,799 | +6.13% |
| 69 | `-march=native` | 394,072 | +2.56% |
| 75 | `-fno-pie -no-pie` | 392,013 | +2.03% |
| 82 | `-fipa-pta` | 387,644 | +0.89% |
| 76 | `-fno-stack-protector` | 384,246 | 0.00% |
| 74 | `-flto` | 382,470 | -0.46% |
| 83 | `-fgraphite-identity` | 383,724 | -0.13% |
| 72 | `-ffast-math` | 383,647 | -0.15% |
| 78 | `-U_FORTIFY_SOURCE` | 383,540 | -0.18% |
| 79 | `-fprefetch-loop-arrays` | 382,974 | -0.33% |
| 71 | `-Ofast` | 382,348 | -0.49% |
| 81 | `-fno-unswitch-loops` | 381,391 | -0.74% |
| 80 | `-fno-ipa-cp-clone` | 380,967 | -0.85% |
| 77 | `-fcf-protection=none` | 380,303 | -1.02% |
| 73 | `-fno-math-errno` | 379,327 | -1.28% |

Compare the first run, where the seven flags screened last all read -6% to -7.3% as power fell. Here
screening spans 1.3% below to 6.1% above, all at 29.1 W.

## Phase 4 confirmation (3 reps each, vs. baseline CI [375,582, 388,744])

| Flag | Mean | 95% CI | Δ | Verdict |
|---|---|---|---|---|
| `-funroll-loops` | 404,571 | [401,331, 407,811] | +5.86% | **accept** |
| `-march=native` | 392,008 | [390,948, 393,067] | +2.58% | **accept** |
| `-fno-pie -no-pie` | 384,287 | [383,771, 384,803] | +0.56% | reject |
| `-fipa-pta` | 384,272 | [382,455, 386,090] | +0.55% | reject |
| `-U_FORTIFY_SOURCE` | 379,233 | [377,056, 381,410] | -0.77% | reject |
| `-fprefetch-loop-arrays` | 379,287 | [378,254, 380,320] | -0.75% | reject |
| `-fno-unswitch-loops` | 379,507 | [378,540, 380,474] | -0.69% | reject |
| `-fgraphite-identity` | 379,944 | [377,415, 382,473] | -0.58% | reject |
| `-fno-ipa-cp-clone` | 378,744 | [372,520, 384,968] | -0.89% | reject |
| `-fno-stack-protector` | 377,725 | [376,682, 378,768] | -1.16% | reject |
| `-ffast-math` | 377,200 | [376,685, 377,716] | -1.30% | reject |
| `-fno-math-errno` | 376,444 | [373,401, 379,486] | -1.50% | reject |
| `-flto` | 376,312 | [372,954, 379,669] | -1.53% | reject |
| `-Ofast` | 375,980 | [371,467, 380,493] | -1.62% | reject |
| `-fcf-protection=none` | 374,972 | [373,134, 376,810] | -1.88% | reject |

Every reject is genuine: each CI either overlaps the baseline's or sits below it. None reached the
PGO near-miss list, which needs a CI clear of baseline.

**A small power step mid-run.** Package power fell by about 1 W (29.0 → 28.1 W) between trials 87 and 88,
during `-funroll-loops`'s confirmation, and stayed at 28.0-28.1 W for the rest of the run. The sensor under
all-core load sits pinned at the platform's limit (29.02-29.07 W in a separate 15-second check right after
the run), so this looks like the firmware lowering that limit by about 1 W, not the workload changing. A 3.5% drop is well under the 8% rerun
threshold, by design. Its effect on scores was small: the recheck at 28.07 W read -0.49% against the 29.1 W
baseline. It still means the rejects measured from trial 88 on (all but `-march=native`) carry a bias of about
-0.5%. Only `-fno-pie -no-pie` and `-fipa-pta` (+0.56%, +0.55%) would come near the 1% bar if
corrected, and neither would clear it.

## Phase 5 combination

| Trials | Flagset | Mean | Δ | Verdict |
|---|---|---|---|---|
| 130-132 | `-O3 -funroll-loops` (greedy step 1, vs. baseline) | 403,514 | +5.59% | accept |
| 133-135 | `+ -march=native` (greedy step 2, vs. step 1) | 400,168 | -0.83% | reject |
| 136-138 | pair `-funroll-loops -march=native` (vs. baseline) | 399,890 | +4.64% | accept, but below the greedy winner |

Winner: `-O3 -funroll-loops`, 403,514.

## Phase 6 multipliers (on `-O3 -funroll-loops`)

| Trials | Added | Mean | 95% CI | Δ on incoming set | Verdict |
|---|---|---|---|---|---|
| 139-141 | `-fprofile-use` | 416,025 | [413,178, 418,872] | +3.10% | **accept** |
| 142-144 | `-march=znver5` (on the PGO set) | 418,730 | [414,793, 422,668] | +0.65% | reject |
| 145-147 | `-mtune=znver5` (on the PGO set) | 415,708 | [407,870, 423,547] | -0.08% | reject |

No vector-width candidates were deferred, so that multiplier didn't run. `-mprefer-vector-width=256` was
excluded in Phase 2, since `vectorization_density` is `low`. `-mprefer-vector-width=512` was retired from the
catalog earlier, because it is already the default once `-march=znver5` is set.

## Compared with the first run

| | First run (exp. 3) | Re-mine (exp. 4) |
|---|---|---|
| Power profile | `balanced` | `performance` |
| Package power | 19.0-24.1 W, sagging | 28.0-29.1 W, one 1 W step |
| `-O3` baseline | 361,329 | 382,163 (+5.8%) |
| Baseline recheck | -3.34%, flagged | -0.49% |
| Screening prunes | 7 (power artifacts) | 0 |
| `-funroll-loops` | rejected (-0.16%) | accepted (+5.86%) |
| `-march=native` | rejected (-4.55%) | accepted (+2.58%), doesn't stack |
| Winner | `-O3 -fprofile-use`, 385,356 | `-O3 -funroll-loops -fprofile-use`, 416,025 |
| Gain vs. own `-O3` | +6.65% | **+8.86%** |

The re-mine's winner is 8.0% faster in absolute terms than the first run's winner. About 5.8 points of that
is the power profile and 3 points is the better flagset.

## Knowledge priors

The knowledge table already had one row per flag from the first run, in cluster `compute-bound`. M4
fast-tracks only flags accepted in a strict majority of trials. `-fprofile-use` was the only one (1 of 1). It
printed "fast-tracked", but PGO isn't an ordinary candidate: it always runs as Phase 6's multiplier. So the
fast-track list was empty, and the log line is misleading. Every other flag was screened normally.

After this run (`compute-bound`, `erie`):

| Flag | Trials | Accepted | Mean Δ |
|---|---|---|---|
| `-fprofile-use` | 2 | 2 | +4.88% |
| `-funroll-loops` | 2 | 1 | +2.85% |
| `-march=native` | 2 | 1 | -0.98% |
| everything else | 1-2 | 0 | +0.55% to -3.63% |

The first run's rows are biased low by the power sag, so these means understate `-funroll-loops` and
`-march=native`. They're left in place, not cleared: those trials measured what they claim, just on a host in
a worse state. The `balanced` profile is part of that history.

## Follow-ups

1. ~~**Don't print "fast-tracked" for `-fprofile-use`.**~~ Fixed in the same branch: a prior for a flag that
   isn't a Phase 2-5 candidate now reads "tried in Phase 6" (PGO) or "not a candidate here".
2. **The occasional 1%-low rep** (2 of 10 baseline reps here) widens the baseline CI to ±1.7%. Five
   calibration reps instead of three, or a rerun threshold nearer 1% for coremark-length runs, would tighten
   it. Not urgent: no verdict here depended on it.
3. **A PGO-alone trial under `performance`** would show how much unrolling and PGO overlap. The mine never
   tests PGO on bare `-O3` once Phase 5 has a winner.
4. **More Phoronix tests** (`host_erie.md` item 5; candidates in
   [`phoronix_cflags_survey.md`](phoronix_cflags_survey.md)).
