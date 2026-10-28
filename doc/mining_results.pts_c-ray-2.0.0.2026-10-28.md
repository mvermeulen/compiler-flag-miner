# `cfm mine` results: pts/c-ray-2.0.0 on `erie`, 2026-10-28

The fifth Phoronix test mined. It is the first multithreaded one (16 pthreads, unpinned) and the first where
lower is better: C-Ray 2.0 renders a sphere-fractal scene at 1920x1080 with 16 rays per pixel and reports
the render time. The score cfm uses is renders per second (1 / seconds), so higher is still better. It was
mined three times. The first mine (experiment 19) rejected correct renders as invalid, and the image check was
fixed before the second (experiment 20). The third (experiment 21) ran with `--no-shape-filter`, followed by
an interleaved A/B of the two mines' winners (experiments 22-30).

The baseline is **`-O3 -ffast-math`**, not `-O3`: that is what C-Ray's Makefile hardcodes, so it is what PTS
(and so Phoronix) actually measures. Every gain below is over PTS's own build.

## Headline result

**`-O3 -ffast-math -march=native -fprofile-use -mprefer-vector-width=256`: 47.3 s against 77.7 s, +64.1%**
(experiment 20). Against all eight baseline measurements across both mines (76.7 s on average), it is +62.0%.

| Step | Render time | Gain on the step before |
|---|---|---|
| `-O3 -ffast-math` (calibration) | 77.65 s | — |
| `+ -march=native` (Phase 5) | 59.02 s | +31.6% |
| `+ -fprofile-use` (Phase 6) | 48.25 s | +22.3% |
| `+ -mprefer-vector-width=256` (Phase 6) | 47.33 s | +2.0% |

- **`-march=native` is worth about 30%.** It was accepted in both mines (+28.1% and +32.9% in Phase 4). C-Ray
  reads as compute-bound (64%) with high vectorization density. `-march=native` gives it AVX-512, and FMA.
- **PGO adds 22% on top.** That is the largest PGO gain seen in this project; coremark's was +3.1%. The PGO
  binary trains on the same scene it is measured on, at 480x270 on one thread (see "PGO training" below), so
  this is the gain with a profile of the exact workload, as PTS's own PGO tests measure it.
- **256-bit vectors beat 512-bit by 2%,** in both mines (+2.42% on `-march=native` alone, +1.96% with PGO).
  With `-march=native` (`znver5`), GCC vectorizes with 512-bit `zmm` registers by default; on this Zen5
  laptop part, C-Ray runs faster with 256-bit ones.
- **`-fipa-pta` is worth +5-6%, but not once PGO is in.** The shape filter had excluded it from experiment 20.
  Experiment 21 accepted it (+6.0% alone, +5.1% on `-march=native`), but in an interleaved A/B, adding it to
  experiment 20's winner made that 0.5% slower. PGO's profile appears to buy the same improvement.
- **Nothing else matters.** `-funroll-loops` and `-Ofast` are within 1% of the baseline in every mine. None of
  the eight other flags the shape filter had excluded helped (experiment 21). `-flto` was 5.6% and 8.2% slower
  in screening and was pruned both times.

## Making C-Ray minable

Set up on `feature/pts-c-ray` (commit `4d0a0a6`); see CLAUDE.md's Non-obvious traps for the details.

- **PTS's C-Ray never sees the user's flags.** Its Makefile assigns `CFLAGS = -pedantic -Wall -g -O3 -ffast-math`,
  which beats the environment, and links with `LDFLAGS` only. The build override passes the trial's flags to
  both the compile and the link.
- **Fixed resolution.** The profile has a resolution menu; the run override fixes it at 1080p, PTS's smallest
  option.
- **Lower-is-better scores.** The backend now takes `Proportion` LIB profiles and applies `DivideResultBy`.
- **Image check.** A reference image is rendered once from an `-O2` build and pinned by sha256. Each run's
  image must match it but for rounding (below).
- **PGO training.** With the backend's usual `-fprofile-update=atomic`, the 16-thread 1080p training render
  hadn't finished after 10 minutes. C-Ray trains on one thread at 480x270 with `-fprofile-update=single`
  (32 s).

## Experiment 19, and the image check that rejected correct renders

| | |
|---|---|
| Started / finished | 2026-10-28T09:45:12Z / 10:33:50Z (49 min) |
| Code | `feature/pts-c-ray` at `4d0a0a6` |
| Result | converged, `-O3 -ffast-math -march=native -mprefer-vector-width=256`, +31.8% |

`-flto`'s screening trial and all three PGO trials failed validation, so they recorded no score. They had
rendered fine. The images differed from the reference in about 0.2% of channel values (12,000 of 6.2
million), by 1.16 on average and at most 8 of 255. The first tolerance allowed 0.01%.

- **The differences are rounding, not a wrong region.** They sit in the centre of the image, the fractal,
  where rays reflect many times and rounding compounds. The `-flto` and PGO images differ in the same place.
- **Builds that follow the C standard's floating-point rules strictly differ just as much.** A render from a
  plain `-O2 -mfpmath=387` build (x87 80-bit intermediates, no fast-math) differs from the reference in 0.13%
  of values, by at most 7, in the same place. An `-O2 -march=native` build (FMA contraction) differs in one value.
- **The first tolerance was calibrated on builds that happened to round alike:** `-O0` through `-O3` and PTS's
  own `-O3 -ffast-math` render byte-identical images.

**Fix (commit `2b27bce`):** at most 1% of channel values may differ, none by more than 32/255. That is about
5x and 4x the largest legitimate differences seen. A miscompiled intersection or shading path would be off by
far more. All four rejected images and both test renders pass the new check.

PGO's rejected renders took 48.6 s against the winning set's 58.7 s, which is why the mine was repeated.

## Experiment 20

| | |
|---|---|
| Command | `cfm mine pts/c-ray-2.0.0 --base-flags "-O3 -ffast-math"` (uncapped, warm-up minimum 180 s, power check on, default shape filter) |
| Code | `feature/pts-c-ray` at `2b27bce` |
| Started / finished | 2026-10-28T10:40:53Z / 11:45:22Z (64 min) |
| Final status | `converged` |
| Trials | 46 (636-681) |
| Candidates | 5 screened (`-funroll-loops`, `-Ofast`, `-flto` timed; `-ffast-math`, `-fno-math-errno` identical code to the baseline) + `-march=native` fast-tracked (M4: 2 of 3 accepted before); `-flto` pruned |
| Shape | `compute-bound` 64.1% (local `deep-cpu` trial), vectorization density high, allocation pressure low |
| Excluded on shape | 9 flags: `-fno-pie -no-pie`, `-fno-stack-protector`, `-fcf-protection=none`, `-U_FORTIFY_SOURCE`, `-fprefetch-loop-arrays`, `-fno-ipa-cp-clone`, `-fno-unswitch-loops`, `-fipa-pta`, `-fgraphite-identity` |
| Guards | no slow-rep, spread or low-power reruns; no audit warnings; every image matched; **baseline recheck +1.28%, flagged** |
| Power / temp | package power 26.1-29.1 W; CPU temp 75.5-79.6°C; bandwidth 44.8-45.9 GB/s |

### Baseline

Trial 636 was the characterization run. Warm-up settled after 3 reps (637-639, 246 s). Calibration
(640-642): 77.79, 77.62 and 77.54 s, mean ratio 0.012878, CI ±0.4%. The recheck after Phase 4 (657) read
76.66 s, **+1.28%**, just outside the CI.

**The two mines' baselines differ by about 3.5%:** experiment 19's `-O3 -ffast-math` reps took 74.4-76.3 s,
experiment 20's 77.0-77.8 s. Within each mine the baseline was stable to about 1%. Power and temperature
don't explain it (experiment 19 ran at 27-30 W, 76-82°C; experiment 20 at 26-29 W, 76-80°C).

### Phase 4 and 5

| Flags on `-O3 -ffast-math` | Exp. 19 | Exp. 20 | Δ vs. both mines' baseline mean (76.66 s) |
|---|---|---|---|
| `-march=native` | +28.07%, accept | +32.85%, accept | +31.2% |
| `-funroll-loops` | -1.32%, reject | +2.23%, accept | +0.01% / +0.93% |
| `-Ofast` | -1.60%, reject | +1.83%, accept | -0.27% / +0.52% |
| `-flto` | validation failed | -5.60% screening, pruned | — |

**The `-funroll-loops` and `-Ofast` verdicts flipped between mines, and both are baseline artifacts.** Their
absolute scores barely moved (76.65 s / 75.95 s for unrolling, 76.87 s / 76.26 s for `-Ofast`). What moved
is the calibration they were compared with: experiment 19's reps were still drifting slower (74.99, 75.61,
76.32 s), and experiment 20's sat 1.3% below its own recheck. Against the baseline across both mines, both
flags are within 1%. Neither matters once `-march=native` is in: Phase 5 rejected each on top of it
(+0.24%, +0.32%), and the pair tournament's best pair (`-Ofast -march=native`, 58.57 s) didn't beat the
greedy winner by enough to replace it.

### Phase 6 multipliers (on `-O3 -ffast-math -march=native`, 59.02 s)

| Trials | Added | Render time | Δ | Verdict |
|---|---|---|---|---|
| 676-678 | `-fprofile-use` | 48.25 s | +22.32% | **accept** |
| 679-681 | `-mprefer-vector-width=256` (on PGO) | 47.33 s | +1.96% | **accept** |

The microarch multiplier was skipped because the winning set already has `-march=native`. There was no PGO
near-miss candidate. The PGO reps share one code fingerprint (`b5a8c3a0`), so they measured one binary.

## Experiment 21: without the shape filter

| | |
|---|---|
| Command | `cfm mine pts/c-ray-2.0.0 --base-flags "-O3 -ffast-math" --no-shape-filter` |
| Code | `main` at `24984ab` |
| Started / finished | 2026-10-28T13:26:00Z / 15:14:38Z (109 min) |
| Final status | `converged` |
| Trials | 76 (682-757) |
| Candidates | 14 screened (2 identical code to the baseline) + `-march=native` fast-tracked; `-flto` pruned |
| Shape | `compute-bound`, 64% (local `deep-cpu` trial) |
| Guards | 3 low-power reruns (735, 742, 743); no audit warnings; every image matched; **baseline recheck -3.90%, flagged** |
| Power / temp | package power 25.1-30.0 W; CPU temp 74.0-85.1°C |
| Result | `-O3 -ffast-math -march=native -fipa-pta -fprofile-use -mprefer-vector-width=256`, 49.6 s, +53.2% |

**The baseline was measured while package power was still falling.** The characterization trial ran at 30 W,
the calibration reps at 29 W then 28 W, and from Phase 3 on the host held about 26 W. The calibration renders
took 75.5-76.6 s; the recheck after Phase 4 took 79.1 s (-3.90%). The low-power rule reruns a rep more than 8%
under the calibration median (28.06 W), so 26 W didn't trigger it, and every Phase 4 delta reads about 3-4%
low. The table gives each flag against both references.

| Flag on `-O3 -ffast-math` | Render time | Δ vs. calibration (76.0 s) | Δ vs. recheck (79.1 s) | Verdict |
|---|---|---|---|---|
| `-march=native` | 60.32 s | +26.04% | +31.15% | accept |
| `-fipa-pta` | 71.72 s | +6.00% | +10.29% | **accept** |
| `-funroll-loops` | 77.14 s | -1.45% | +2.55% | reject |
| `-fno-stack-protector` | 77.43 s | -1.81% | +2.17% | reject |
| `-fcf-protection=none` | 78.04 s | -2.59% | +1.36% | reject |
| `-fprefetch-loop-arrays` | 78.44 s | -3.08% | +0.85% | reject |
| `-U_FORTIFY_SOURCE` | 78.56 s | -3.23% | +0.69% | reject |
| `-Ofast` | 78.56 s | -3.23% | +0.70% | reject |
| `-fno-pie -no-pie` | 78.78 s | -3.51% | +0.40% | reject |
| `-fno-unswitch-loops` | 78.98 s | -3.74% | +0.16% | reject |
| `-fno-ipa-cp-clone` | 79.04 s | -3.82% | +0.08% | reject |
| `-fgraphite-identity` | 79.36 s | -4.20% | -0.32% | reject |

`-fipa-pta` is the only new flag that stands out against either reference. In screening it was the fastest
trial by 9% over the next. The rest sit within about 2.5% of the recheck. `-funroll-loops` reads +2.6% there,
but it was flat in the other two mines.

**Phase 5 and 6:** `-fipa-pta` on `-march=native` added +5.10% (59.4 s → 57.4 s). PGO on that added +14.58%,
against +22.3% on `-march=native` alone in experiment 20, and 256-bit vectors +1.03%.

### A/B: does `-fipa-pta` help on top of PGO?

The two mines' winners can't be compared directly, because experiment 21's host ran slower: its
`-march=native` reps took 60.3 s against 58.5 s in experiment 20. So `cfm measure` alternated them in one
session (experiments 22-30), after one discarded warm-up, four runs each, at the mine's `quick` profile.

| Flags | Runs | Render time | sd |
|---|---|---|---|
| `-O3 -ffast-math -march=native -fprofile-use -mprefer-vector-width=256` (exp. 20's winner) | 4 | **47.05 s** | 0.18% |
| `+ -fipa-pta` (exp. 21's winner) | 4 | 47.29 s | 0.21% |

**Adding `-fipa-pta` to the PGO build costs 0.5%.** It is small but consistent: every run with it was slower
than every run without. So experiment 20's winner stands. Package power held 30 W through the A/B, and both
sets' code fingerprints matched their mine builds (`82cc4ba8`, `eff4d01c`), so the trained profiles are
reproducible across sessions.

## PGO training

PTS has no separate training input, so the profile comes from rendering the same `sphfract.scn` scene at
480x270 on one thread. The measured render is the same scene at 1080p on 16 threads. So the profile matches
the measured workload far more closely than a real deployment's profile would match its inputs. The gain on
another scene would likely be smaller. `-fprofile-use` also turns on `-funroll-loops`, `-fpeel-loops` and
`-ftracer`, but unrolling alone was flat on top of `-march=native` (+0.24%), so most of the 22% should come
from the profile itself (branch layout and inlining decisions in the intersection loop).

## Compared with the other PTS tests on erie

| | coremark | tscp | crafty | himeno | c-ray |
|---|---|---|---|---|---|
| Threads | 16 | 1 | 1 | 1 | 16 |
| Shape | compute 42.6% | frontend 54.7% | frontend 42.4% | memory 62.0% | **compute 64.1%** |
| Baseline | `-O3` | `-O3` | `-O3` | `-O3` | **`-O3 -ffast-math`** |
| Winner gain | +8.86% | +6.07% | +7.05% | 0% | **+64.1%** |
| `-march=native` | +2.58% | -3.61% | -1.73% | +0.25% | **+26.0% to +32.9%** |
| `-funroll-loops` | **+5.86%** | **+2.30%** | -1.32% | -1.71% | about 0 |
| `-flto` | -1.53% | **+1.43%** | +0.76% | -0.04% | -5.6%, -8.2% (screening) |
| `-fipa-pta` | +0.55% | -0.27% | -0.51% | identical code | **+6.0%**, but -0.5% with PGO |
| `-fno-pie -no-pie` | +0.56% | -0.81% | **+4.66%** | -1.00% | about 0 |
| PGO on the winner | **+3.10%** | -2.92% | **+2.54%** | -1.12% | **+22.3%** |

C-Ray is the first test here where the ISA matters a lot: it is a vectorized floating-point kernel that fits in
cache, the case `-march=native` exists for. Himeno is also vectorized FP, but streams from DRAM.

## Follow-ups

1. ~~**Re-mine with `--no-shape-filter`.**~~ Done (experiment 21): of the nine excluded flags only
   `-fipa-pta` helps, and not once PGO is in. The filter cost nothing on C-Ray's final result, but it did hide
   a real +6% flag.
2. **PGO trained on a different scene.** Training on `simple.scn` or `reflbox.scn` (both ship with C-Ray) and
   measuring on `sphfract.scn` would show how much of the 22% survives a profile that doesn't match the
   workload.
3. **The baseline offset between mines** (about 3.5%, and 3.9% within experiment 21) is the largest seen on
   erie. Experiment 21's came from package power falling 30 → 26 W during calibration, too little for the 8%
   low-power rule. A rerun threshold relative to the run's own power plateau, or a longer warm-up when power is
   still falling, would catch it. Both mines' verdicts on the
   big effects agree, but a 1-2% flag can't be resolved across mines here.
4. **`knowledge` counts C-Ray two or three times** for `-march=native`, `-funroll-loops`, `-Ofast` and
   `-mprefer-vector-width=256` (experiments 19-21), as it counts himeno twice for its flags.
