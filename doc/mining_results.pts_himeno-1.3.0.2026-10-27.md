# `cfm mine` results: pts/himeno-1.3.0 on `erie`, 2026-10-27

The fourth Phoronix test mined, and the first floating-point one. Himeno is a Jacobi-iteration Poisson solver
(a 19-point stencil). It runs single-threaded here, pinned to CPU 2 (a 5.09 GHz Zen5 core), and reports
MFLOPS. It was mined twice. The first mine (experiment 13) wasn't trustworthy, for two reasons, and both
were fixed before the second (experiment 15).

## Headline result

**No flag beats `-O3` on himeno.** Experiment 15 screened all 15 candidates and confirmed 12; the other 3
built code identical to `-O3`. It also tried PGO, `-march=znver5` and `-mtune=znver5`, and rejected
everything.

- **The best reads are `-march=native` and `-march=znver5`, which build identical code**, at +0.2% against
  the calibration baseline. Against the baseline recheck, +1.4%. Neither is CI-clear.
- **The flags the first mine never tried are slightly worse, not better:** `-Ofast` -3.1%, `-ffast-math` -2.0%,
  `-funroll-loops` -1.7%. `-fno-math-errno` changed no code at all.
- **The shape read fits:** memory-bound, 62.0%. Grid S's arrays are about 29 MB, larger than the 16 MB L3, so
  each sweep streams from DRAM, and code generation has little to win once the inner loop is vectorized.
  Upstream's recipe already builds with `-mavx2` (kept in the build override), so `-O3` here already has
  256-bit vectors. `-march=native` adds AVX-512 on top.

## Making himeno minable

- **PTS's own install fails under GCC 15:** `himenobmtxpa.c:263:13: error: implicit declaration of function
  'free'` (`strcpy` too). GCC 14 made implicit declarations an error. The backend replaces install.sh
  (`_BUILD_OVERRIDES["himeno"]`). It uses the same recipe, `cc himenobmtxpa.c -O3 $CFLAGS [-mavx2]`, plus
  `-include stdlib.h -include string.h`.
- **Shorter runs.** Upstream times the solver for a fixed 60 s. The override edits that to 20 s
  (`HIMENO_TARGET_SECONDS`), which changes only how many iterations are timed.
- **Validator.** The run's final residual ("Gosa") underflows to exactly 0 after about 28,000 iterations, so it
  can't be checked against a reference value. The validator checks the 3-iteration rehearsal's residual
  instead: exactly `3.288628e-03` for `-O0` through `-O3` builds. `-ffast-math` and AVX-512 builds, which
  reassociate the sum, give up to `3.288662e-03` (`HIMENO_GOSA_REL_TOL = 1e-4`). The final residual must also
  lie between 0 and the rehearsal's. Since experiment 15, every run in a log is checked.

## Experiment 13: the first mine, and why it didn't count

| | |
|---|---|
| Started / finished | 2026-10-27T18:30:12Z / 18:50:29Z (20 min) |
| Code | `feature/pts-himeno` at `21e8631`, one 20 s run per rep |
| Result | converged, no winner (+0.00%) |

1. **The shape filter dropped most of the candidates.** The baseline read memory-bound at 61.9%, above
   `CONFIDENT_SHAPE_MIN_PCT` (55%). Phase 2 then excluded every flag whose `topdown_signals` all point
   elsewhere: 11 of 15, including `-Ofast`, `-ffast-math`, `-fno-math-errno`, `-funroll-loops`,
   `-fno-pie -no-pie`, `-fipa-pta` and `-fcf-protection=none`. Only `-fprefetch-loop-arrays`,
   `-fgraphite-identity`, `-flto` (shape-exempt) and `-march=native` ran. Excluding the fast-math family from a
   vectorized FP solver on a memory-bound read was the question this mine was meant to answer.
2. **Single runs were too noisy.**
   - The same `-O3` binary read 7,561-7,894 MFLOPS (about 4%), and warm-up hit its 8-rep cap without settling.
   - The calibration reps (7,873, 7,561, 7,629) gave a baseline CI of about ±5%.
   - `-march=native` (+3.84%, tight CI), `-fgraphite-identity` (+3.54%) and `-flto` (+2.84%) were all
     rejected on CI overlap alone.
   - The spread rule fired three times, but it can't repair a baseline that is itself wide.
   - Power held at 20.0 W, temperature at 82-85°C, and bandwidth at 45 GB/s.

Experiment 15 shows the three "near wins" were mostly the low baseline. With the same flags, all three read
within ±0.4% of a well-measured `-O3`.

**Fixes (commit `06670a1`):**

- **`cfm mine --no-shape-filter`** skips `_filter_implausible_candidates()`, so every ranked catalog flag is
  screened. The default is unchanged.
- **`HIMENO_RUNS = 3`.** The run override runs himeno three times per measurement, and `parse_result()`
  averages the three scores, as for TSCP. A trial now takes about 62 s.

## Experiment 15

| | |
|---|---|
| Command | `cfm mine pts/himeno-1.3.0 --no-shape-filter` (uncapped, warm-up minimum 180 s, power check on) |
| Code | `feature/pts-himeno` at `06670a1` |
| Started / finished | 2026-10-27T21:38:15Z / 22:56:01Z (78 min) |
| Final status | `converged` |
| Trials | 68 (534-601) |
| Candidates | 15 screened, none pruned, none fast-tracked (the only priors were experiment 13's rejects); 3 skipped as identical code |
| Shape | `memory-bound` 62.0% (local `deep-cpu` trial), vectorization density high, allocation pressure low |
| Guards | no slow-rep, spread or low-power reruns; no audit warnings; **baseline recheck -1.13%, flagged** |
| Power / temp | package power 19.1-20.0 W; CPU temp 82.4-86.1°C |

### Baseline

Trial 534 was the characterization run (7,681). Warm-up settled after 3 reps (535-537, 185 s): 7,740, 7,683
and 7,645. Calibration (538-540): 7,796, 7,808 and 7,797, mean **7,800.4**, CI [7,784.6, 7,816.3] (±0.2%).
The recheck after Phase 4 (592) read 7,712.1, **-1.13%**, outside the CI.

Averaging three runs did tighten each rep: within-trial standard deviations in Phase 4 ran 0.3-1.2%, against
about 2% between single runs in experiment 13. But the `-O3` reps across the mine still range 7,645-7,808.
The three calibration reps happened to land together at the top of that range, so the CI is narrower than
the benchmark's real variation. All eight `-O3` measurements average **7,733 (sd 0.8%)**. The table gives
each delta against both the calibration mean (the official verdict) and the recheck.

### Phase 4 confirmation (3 reps each)

| Flag | Mean | Δ vs. 7,800 (calibration) | Δ vs. 7,712 (recheck) | Verdict |
|---|---|---|---|---|
| `-march=native` | 7,820.0 | +0.25% | +1.40% | reject |
| `-flto` | 7,797.6 | -0.04% | +1.11% | reject |
| `-fgraphite-identity` | 7,773.7 | -0.34% | +0.80% | reject |
| `-U_FORTIFY_SOURCE` | 7,732.5 | -0.87% | +0.27% | reject |
| `-fno-pie -no-pie` | 7,722.6 | -1.00% | +0.14% | reject |
| `-fno-stack-protector` | 7,712.8 | -1.12% | +0.01% | reject |
| `-fcf-protection=none` | 7,666.4 | -1.72% | -0.59% | reject |
| `-funroll-loops` | 7,666.7 | -1.71% | -0.59% | reject |
| `-fprefetch-loop-arrays` | 7,654.5 | -1.87% | -0.75% | reject |
| `-ffast-math` | 7,647.3 | -1.96% | -0.84% | reject |
| `-fno-unswitch-loops` | 7,572.9 | -2.92% | -1.80% | reject |
| `-Ofast` | 7,557.2 | -3.12% | -2.01% | reject |
| `-fno-math-errno`, `-fno-ipa-cp-clone`, `-fipa-pta` | — | — | — | identical code to `-O3`, not timed |

`-Ofast` and `-ffast-math` build identical code to each other (fingerprint `9b654502`).

### Phase 6 multipliers (on `-O3`)

| Trials | Added | Mean | Δ vs. 7,800 | Verdict |
|---|---|---|---|---|
| 593-595 | `-fprofile-use` | 7,712.9 | -1.12% | reject |
| 596-598 | `-march=znver5` | 7,815.4 | +0.19% | reject (same code as `-march=native`) |
| 599-601 | `-mtune=znver5` | 7,616.2 | -2.36% | reject |

There was no PGO near-miss candidate: nothing in Phase 4 was CI-clear of baseline. The vector-width
multiplier was skipped because the winning set has no `-march=`.

## Is the verdict robust to the baseline offset?

Yes. The flagged recheck means the calibration mean probably sits about 1% high. Against the lowest
reasonable reference, the recheck's 7,712, the best flag is `-march=native` at +1.4%. That is only just past
the 1% practical bar, and the flag's own reps (7,802-7,844) overlap the calibration reps (7,796-7,808)
entirely. So no reading of this run gives himeno a real flag win. `-march=native` is worth at most about 1%.

## Compared with the other PTS tests on erie

| | coremark | tscp | crafty | himeno |
|---|---|---|---|---|
| Shape | compute 42.6% | frontend 54.7% | frontend 42.4% | **memory 62.0%** |
| Winner gain | +8.86% | +6.07% | +7.05% | **0%** |
| `-funroll-loops` | **+5.86%** | **+2.30%** | -1.32% | -1.71% |
| `-flto` | -1.53% | **+1.43%** | +0.76% | -0.04% |
| `-march=native` | **+2.58%** | -3.61% | -1.73% | +0.25% |
| `-fno-pie -no-pie` | +0.56% | -0.81% | **+4.66%** | -1.00% |
| PGO on the winner | **+3.10%** | -2.92% | **+2.54%** | -1.12% |

The three integer tests fit in cache and each had its own winning flag. Himeno streams 29 MB per sweep, so
memory bandwidth bounds it, and no flag moves it. That matches what the memory-bound shape predicted. In
hindsight the shape filter's call was right here, but only a mine without it could show that.

## Follow-ups

1. **A grid that fits in L3.** Size XS (32x32x64, about 3.6 MB) would make himeno a cache-resident FP test,
   where the fast-math and `-march` flags have room to matter. That would be a different benchmark from PTS's,
   whose install.sh hardcodes size S.
2. **Five calibration reps for himeno** (`host_erie.md` item 7). Three calibration reps can land together at
   one end of a 2% range, as here, and give a too-narrow CI that the recheck then flags.
3. **Keep `--no-shape-filter` opt-in.** On niwot the filter's misses were all LTO and PGO, which are handled
   now: LTO is exempt and PGO always runs. Here it excluded correctly. One counter-example isn't a reason to
   change the default.
