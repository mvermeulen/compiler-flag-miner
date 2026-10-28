# `cfm mine` results: pts/c-ray-2.0.0 on `erie`, 2026-10-28

The fifth Phoronix test mined. It is the first multithreaded one (16 pthreads, unpinned) and the first where
lower is better: C-Ray 2.0 renders a sphere-fractal scene at 1920x1080 with 16 rays per pixel and reports
the render time. The score cfm uses is renders per second (1 / seconds), so higher is still better. It was
mined twice. The first mine (experiment 19) rejected correct renders as invalid, and the image check was
fixed before the second (experiment 20).

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
- **Nothing else matters.** `-funroll-loops` and `-Ofast` are within 1% of the baseline in both mines.
  `-flto` was 5.6% slower in its one screening trial and was pruned.

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
| `-march=native` | +2.58% | -3.61% | -1.73% | +0.25% | **+28.1% / +32.9%** |
| `-funroll-loops` | **+5.86%** | **+2.30%** | -1.32% | -1.71% | about 0 |
| `-flto` | -1.53% | **+1.43%** | +0.76% | -0.04% | -5.6% (screening) |
| PGO on the winner | **+3.10%** | -2.92% | **+2.54%** | -1.12% | **+22.3%** |

C-Ray is the first test here where the ISA matters a lot: it is a vectorized floating-point kernel that fits in
cache, the case `-march=native` exists for. Himeno is also vectorized FP, but streams from DRAM.

## Follow-ups

1. **Re-mine with `--no-shape-filter`.** Nine flags were excluded on the compute-bound read, including
   `-fno-pie -no-pie` (crafty's +4.7%). On a 64%-compute-bound read they are unlikely to matter, but this
   wasn't measured.
2. **PGO trained on a different scene.** Training on `simple.scn` or `reflbox.scn` (both ship with C-Ray) and
   measuring on `sphfract.scn` would show how much of the 22% survives a profile that doesn't match the
   workload.
3. **The baseline offset between mines** (about 3.5%) is the largest seen on erie. Both mines' verdicts on the
   big effects agree, but a 1-2% flag can't be resolved across mines here.
4. **`knowledge` counts C-Ray twice** for `-march=native`, `-funroll-loops`, `-Ofast` and
   `-mprefer-vector-width=256` (experiments 19 and 20), as it counts himeno twice for its flags.
