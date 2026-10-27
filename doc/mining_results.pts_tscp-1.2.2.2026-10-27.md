# `cfm mine` results: pts/tscp-1.2.2 on `erie`, 2026-10-27

The second Phoronix test mined, and the first that is single-threaded. TSCP (Tom Kerrigan's Simple Chess
Program 1.81) runs a built-in benchmark: three searches of one fixed position to depth 5. It reports nodes per
second from the fastest of the three. To make it minable, the backend gained these on the same branch
(`feature/pts-tscp`):

- **`CFLAGS_OVERRIDE`.** PTS's tscp profile builds with `CFLAGS="$CFLAGS -O3 -march=native"` unless
  `CFLAGS_OVERRIDE` is set. Without it, `-march=native` would follow every trial's flags. The smoke test's
  compiled-flags audit shows the plain `-O3` build with no `-march`.
- **A validator.** A correct build visits exactly 550,778 nodes and finds the principal variation
  `c2a4 d6c7 g2d5 e6d5 c1e3` in all three searches. Every run's output is checked for both.
- **40 runs per measurement, pinned.** One run takes 0.66 s and times in whole milliseconds. Its score
  therefore moves in 0.45% steps and varies by about 3%. The run override loops it 40 times (about 26 s) under
  `taskset` on CPU 2, a 5.09 GHz Zen5 core. The trial's score is the mean of the 40.

## Headline result

**`-O3 -flto -funroll-loops`, +6.07% over plain `-O3`** (2,732,788 vs. 2,576,439 nodes/sec).

| Flagset | Mean | 95% CI | Δ vs `-O3` |
|---|---|---|---|
| `-O3` (baseline) | 2,576,439 | [2,571,819, 2,581,058] | — |
| `-O3 -flto` | 2,613,364 | [2,607,810, 2,618,918] | +1.43% |
| `-O3 -funroll-loops` | 2,635,575 | [2,633,027, 2,638,123] | +2.30% |
| `-O3 -flto -funroll-loops` | 2,732,788 | [2,726,713, 2,738,863] | **+6.07%** |

- **The two flags compound.** Separately they are worth +1.4% and +2.3%; together they give +6.1%, more than
  the sum. That fits how TSCP is built: six `.c` files, with the move generator and `makemove()` (`board.c`), the
  evaluator (`eval.c`) and the search (`search.c`) in separate files. LTO lets GCC inline across them, and unrolling then has more inlined loop
  bodies to work on. This is an inference from the numbers and the source layout. The generated code wasn't
  examined.
- **`-march=native` costs 3.6%** (2,483,322, CI clear of baseline on the low side). It is the largest
  regression in the run. `-march=znver5` on the winning set cost 1.3%, and `-mtune=znver5` cost 0.45% (both
  rejected). PTS's own default build for this test is `-O3 -march=native`.
- **PGO was rejected (-2.92%), but that verdict is weak.** Two of its three reps ran hot (see below).
- **Measurement was tight.** Most 3-rep CIs were within ±0.1% to ±0.25%, against ±0.4% to ±1.7% on coremark.
  Pinning plus 40 runs per measurement works. The exceptions are two noisy measurements, covered next.

## Run metadata

| | |
|---|---|
| Host | `erie` (see [`host_erie.md`](host_erie.md)), `performance` profile, on AC |
| Command | `cfm mine pts/tscp-1.2.2` (uncapped, default `-O3` base, warm-up minimum 180 s, power check on) |
| Code | `feature/pts-tscp` at `aa8c354` |
| Experiment id | 7 (5 was a `cfm measure` refused before any trial; 6 the smoke test) |
| Started / finished | 2026-10-27T13:33:28Z / 2026-10-27T14:25:57Z (52 min) |
| Final status | `converged` |
| Trials | 83 (149-231) |
| Candidates screened / accepted in Phase 4 | 15 / 2 (none pruned; 2 skipped as unchanged code) |
| Winning flags | `["-O3", "-flto", "-funroll-loops"]`, +6.07% |
| Shape | `frontend-bound` 54.7% (local `deep-cpu` trial), vectorization density low |
| Guards | bandwidth gate passed every run; no slow-rep or low-power reruns; no audit warnings; baseline recheck +0.13% |
| Power / temp | package power 15.0-17.0 W (median per run, one core loaded); CPU temp 75.5-95.0°C |

## Baseline

Trial 149 was the `deep-cpu` characterization. Warm-up (150-155) settled after 6 reps and 181 s; its last two
reps were 2,576,814 and 2,570,812. Calibration (156-158): 2,576,848, 2,578,059, 2,574,409. The recheck after
Phase 4 (trial 213) read 2,579,841, +0.13%.

## Phase 3 screening (vs. the last calibration rep, 2,574,409)

`-fprefetch-loop-arrays` and `-fno-math-errno` built byte-identical code to `-O3`. The no-code-change guard
skipped their timed runs and rejected them. TSCP has no array prefetch candidates and no math calls, so this is
expected. Unlike coremark, TSCP doesn't compile its flags into the binary, so the guard can fire here.

| Flag | Screen | Δ |
|---|---|---|
| `-funroll-loops` | 2,641,392 | +2.60% |
| `-flto` | 2,610,734 | +1.41% |
| `-fgraphite-identity` | 2,587,071 | +0.49% |
| `-fno-stack-protector` | 2,580,767 | +0.25% |
| `-U_FORTIFY_SOURCE` | 2,574,753 | +0.01% |
| `-Ofast` | 2,573,816 | -0.02% |
| `-ffast-math` | 2,571,405 | -0.12% |
| `-fipa-pta` | 2,569,598 | -0.19% |
| `-fno-ipa-cp-clone` | 2,568,129 | -0.24% |
| `-fno-unswitch-loops` | 2,566,336 | -0.31% |
| `-fcf-protection=none` | 2,556,805 | -0.68% |
| `-fno-pie -no-pie` | 2,550,837 | -0.92% |
| `-march=native` | 2,484,979 | -3.47% |

Every screening delta matched its Phase 4 result to within 0.5 points.

## Phase 4 confirmation (vs. baseline CI [2,571,819, 2,581,058])

| Flag | Mean | 95% CI | Δ | Verdict |
|---|---|---|---|---|
| `-funroll-loops` | 2,635,575 | [2,633,027, 2,638,123] | +2.30% | **accept** |
| `-flto` | 2,613,364 | [2,607,810, 2,618,918] | +1.43% | **accept** |
| `-fno-stack-protector` | 2,577,951 | [2,574,908, 2,580,994] | +0.06% | reject |
| `-fgraphite-identity` | 2,576,118 | [2,573,048, 2,579,188] | -0.01% | reject |
| `-U_FORTIFY_SOURCE` | 2,573,835 | [2,568,042, 2,579,628] | -0.10% | reject |
| `-ffast-math` | 2,572,035 | [2,567,552, 2,576,518] | -0.17% | reject |
| `-Ofast` | 2,571,720 | [2,565,346, 2,578,093] | -0.18% | reject |
| `-fipa-pta` | 2,569,501 | [2,566,901, 2,572,101] | -0.27% | reject |
| `-fno-unswitch-loops` | 2,566,618 | [2,562,187, 2,571,048] | -0.38% | reject |
| `-fno-ipa-cp-clone` | 2,564,247 | [2,547,002, 2,581,493] | -0.47% | reject |
| `-fcf-protection=none` | 2,558,186 | [2,556,549, 2,559,824] | -0.71% | reject |
| `-fno-pie -no-pie` | 2,555,674 | [2,553,426, 2,557,923] | -0.81% | reject |
| `-march=native` | 2,483,322 | [2,471,734, 2,494,909] | -3.61% | reject |

Several rejects are small but real regressions, with CIs clear of baseline on the low side:
`-fcf-protection=none`, `-fno-pie -no-pie` and `-march=native`. TSCP is an integer, branch-heavy program
with no FP or vector work. That is why `-Ofast` and `-ffast-math` do nothing.

## Phase 5 combination: one slow rep, rescued by the pair tournament

| Trials | Flagset | Reps | Mean | Δ | Verdict |
|---|---|---|---|---|---|
| 214-216 | greedy step 1: `-O3 -funroll-loops` vs. baseline | 2,634,426, **2,490,616**, 2,628,773 | 2,584,605 (CI ±7.8%) | +0.32% | **reject** |
| 217-219 | greedy step 2: `-O3 -flto` vs. baseline | 2,610,090, 2,612,558, 2,609,126 | 2,610,591 | +1.33% | accept |
| 220-222 | pair `-flto -funroll-loops` vs. baseline | 2,730,730, 2,732,143, 2,735,491 | 2,732,788 | +6.07% | accept, replaces greedy winner |

Trial 215 ran 5.5% slow for its whole 26 seconds, and all 40 runs inside it were slow (2.45M-2.54M,
against about 2.63M). It was the same binary as its siblings (identical code fingerprint). Package power
(16.06 W), temperature (76°C), and the bandwidth probe before it were all normal, and the journal is empty for
that window. A steady 5.5% loss on a pinned single-thread run looks like another thread sharing the core.
CPU 2's SMT sibling is CPU 10, and nothing keeps other work off it. This is a guess; it wasn't observed.

The rep was 5.5% below its fastest sibling, under the 10% slow-rep rerun threshold, so it stayed in. It
widened that step's CI to ±7.8% and the greedy walk rejected `-funroll-loops`, a flag Phase 4 had just
accepted with a ±0.10% CI. The pair tournament happened to test exactly the right pair and recovered it. On
a different draw of the random pairs, the mine would have stopped at `-O3 -flto` (+1.33%) and missed most of
the gain.

## Phase 6 multipliers (on `-O3 -flto -funroll-loops`, 2,732,788)

| Trials | Added | Reps | Mean | Δ | Verdict |
|---|---|---|---|---|---|
| 223-225 | `-fprofile-use` | 2,648,014, 2,617,830, 2,693,352 | 2,653,065 (CI ±3.6%) | -2.92% | reject |
| 226-228 | `-march=znver5` | 2,699,982, 2,700,970, 2,690,410 | 2,697,121 | -1.31% | reject |
| 229-231 | `-mtune=znver5` | 2,715,582, 2,720,609, 2,725,347 | 2,720,513 | -0.45% | reject |

**The PGO reps ran hot.** The CPU read 91.8°C and 95.0°C after reps 223 and 224, against 75-79°C for
almost every other trial in the run. Within rep 224, the 40 runs slid from 2.635M to 2.598M as it went. A
PGO trial keeps the pinned core busy far longer than other trials: instrumented build, a 40-run training run
of the slower instrumented binary, rebuild, then the timed run, with no idle between. Rep 225 read 78.4°C
and 2,693,352. That is still 1.4% below the incoming set, so PGO probably doesn't help here, but the -2.92%
overstates it. A clean answer needs PGO reps with idle time after the training run.

## Compared with coremark on the same host

| | `pts/coremark-1.0.1` (re-mine) | `pts/tscp-1.2.2` |
|---|---|---|
| Threads | 16 processes | 1, pinned to CPU 2 |
| Shape | compute-bound 42.6% | frontend-bound 54.7% |
| Winner | `-O3 -funroll-loops -fprofile-use`, +8.86% | `-O3 -flto -funroll-loops`, +6.07% |
| `-funroll-loops` alone | +5.86% | +2.30% |
| `-flto` | -1.53% | +1.43% (and +6.07% with unrolling) |
| PGO on the winner | +3.10% | -2.92% (weak, thermal) |
| `-march=native` | +2.58% (doesn't stack) | -3.61% |
| Typical 3-rep CI | ±0.1% to ±1.7% | ±0.1% to ±0.25% |

`-funroll-loops` won on both. Coremark is a single file per kernel with little to gain from LTO; TSCP's
cross-file calls are where LTO pays.

## Follow-ups

1. **A rerun threshold suited to tight measurements.** The 10% slow-rep threshold was sized for SPEC's
   multi-minute, noisier reps. Here a 5.5% outlier sat in a set whose other reps agreed to 0.1%, and it nearly
   cost the result. Something relative to the flagset's own spread (e.g. more than 2% below the fastest
   sibling when the other two agree within 0.5%) would have caught it.
2. **Idle after a PGO training run** on single-threaded tests, or rep-level temperature checks, before trusting
   a PGO verdict here.
3. **Keep the pinned core's SMT sibling idle**, e.g. pin the benchmark to CPU 2 and move other work off
   CPU 10 for the duration (or run with SMT siblings excluded via `taskset` on everything else). Worth
   testing whether trial 215's loss reproduces when CPU 10 is loaded on purpose.
4. **`crafty`** is next on the survey's list. It uses the same `CFLAGS_OVERRIDE` convention and is also a chess
   engine, so it would show whether TSCP's LTO+unroll pattern generalizes.
