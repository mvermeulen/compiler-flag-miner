# `cfm mine` results: 709.cactus_r on `chicago`, 2026-11-05

The first `709.cactus_r` mine anywhere since the 2026-08 retraction, and the second benchmark mined on `chicago`
(see [`host_chicago.md`](host_chicago.md)). Cactus is a numerical-relativity code (the Cactus framework with the
Einstein Toolkit's BSSN evolution). `niwot` holds it back as one of the three most bandwidth-heavy fprate
benchmarks, alongside `749.fotonik3d_r` and `765.roms_r`.

## Headline result

**`-O3 -march=native`, +16.51% over plain `-O3`** (ratio 91.446 → 106.547).

- **`-march=native` is the whole story.** Its six reps (three in Phase 4, three in Phase 5) read 105.81-107.01,
  against 90.69-91.69 for every `-O3` rep. It was fast-tracked on `782.lbm_r`'s prior (accepted 2 of 2 in the
  memory-bound cluster), but that prior was +2.92%: cactus gains more than five times what lbm did.
- **Nothing else helped.** `-fprefetch-loop-arrays` -0.15%, `-fgraphite-identity` -0.44%, `-flto` -0.08%. On top of
  `-march=native`, PGO was +0.42% and `-mprefer-vector-width=256` +0.02%, both rejected.
- **The baseline recheck flagged -0.83%** (90.691 against a calibration CI of [90.857, 92.036]). That's far too
  small to touch a +16.5% verdict, but it does mean the small Phase 4 deltas above (all within ±0.5%) can't be
  read more finely than "flat".
- **The shape filter dropped 11 of 15 candidates** on a 71.6% memory-bound corpus read, `-Ofast`, `-ffast-math` and
  `-funroll-loops` among them. Cactus's stencil loops are the kind fast-math can help, so this mine's search was
  narrow. A `--no-shape-filter` re-mine would take about 6 hours.

## Run metadata

| | |
|---|---|
| Host | `chicago`: AMD Ryzen AI MAX+ 395 (16 Zen5 cores, 32 threads), 91 GB RAM, power profile `performance` |
| Command | `python3 -m cfm.cli mine 709.cactus_r` (uncapped, defaults) |
| Code | `main` at `f31ba64` |
| Experiment id | 4 |
| Started / finished | 2026-11-05T08:28:32Z / 2026-11-05T11:06:13Z (2h38m) |
| Final status | `converged` |
| Trials | 30 (103-132), no reruns |
| Candidates screened / confirmed | 3 / 1 (plus `-march=native` fast-tracked, accepted) |
| Excluded on shape (Phase 2) | 11 |
| Fast-tracked (M4) | `-march=native` (accepted 2 of 2, both `782.lbm_r`) |
| Skipped as unchanged code | none possible (see below) |
| Winning flags | `["-O3", "-march=native"]`, +16.51% |
| Guards | bandwidth gate waited once (30 s, trial 103); no reruns; baseline recheck **flagged** (-0.83%) |
| Power | package power median 85.00-85.02 W on every trial; CPU temperature 86.6-96.4°C |

Each trial took about 5 minutes.

## Baseline

Shape from the reference-matrix corpus (`amd-370-64gb`): memory-bound 71.6%, `vectorization_density=high`,
`allocation_pressure=moderate`.

| Trial | Role | Ratio |
|---|---|---|
| 103 | warm-up | 91.676 |
| 104 | warm-up | 91.541 |
| 105 | calibration | 91.687 |
| 106 | calibration | 91.212 |
| 107 | calibration | 91.440 |
| 123 | recheck | 90.691 (-0.83%, flagged) |

Calibration mean 91.446, 95% CI [90.857, 92.036] (±0.65%). Warm-up settled after the minimum two reps (679 s).

## Trials

| Trials | Phase | Flags (on `-O3`) | Mean ratio | Delta | Verdict |
|---|---|---|---|---|---|
| 108-110 | screening | `-fprefetch-loop-arrays`, `-fgraphite-identity`, `-flto` | 91.23-91.27 | | all survived |
| 111-113 | confirmation | `-fprefetch-loop-arrays` | 91.308 | -0.15% | reject |
| 114-116 | confirmation | `-fgraphite-identity` | 91.045 | -0.44% | reject |
| 117-119 | confirmation | `-flto` | 91.378 | -0.08% | reject |
| 120-122 | confirmation (fast-tracked) | `-march=native` | 106.513 | +16.48% | **accept** |
| 124-126 | combination | `-march=native` | 106.547 | +16.51% | **accept** |
| 127-129 | PGO | `-march=native -fprofile-use` | 106.991 | +0.42% | reject |
| 130-132 | vector width | `-march=native -mprefer-vector-width=256` | 106.563 | +0.02% | reject |

The Phase 6 deltas are against `-O3 -march=native`; the microarch multiplier was skipped because the winning set
already had `-march=native`.

## Observations

- **Cactus compiles its build time into the binary, so every build has a different code fingerprint.** The Cactus
  flesh's `src/repos/flesh/src/datestamp.c` uses `__DATE__`/`__TIME__` (the built executable carries strings
  like `Nov  5 2026` and `05:01:36`). All 30 trials, the five `-O3` builds included, have distinct fingerprints.
  The no-code-change guard therefore can never skip a cactus trial (it costs a timed run per no-op flag, but
  doesn't make a result wrong), and fingerprints can't show whether two PGO reps built the same code. Same
  class as coremark's `FLAGS_STR` (CLAUDE.md's 2026-10-26 trap entry).
- **Package power sat at 85.0 W on every trial**, as under lbm, so it's this host's sustained package limit
  under 32-copy fprate load, not a property of one benchmark. CPU temperature reached 96.4°C, a degree or two
  higher than lbm.
- **The bandwidth gate waited only once**, before the first trial; probes read 87.2-100.6 GB/s.
- **`-march=native`'s size on cactus fits niwot's fprate picture.** niwot's `731.astcenc_r` mine (2026-11-05)
  also found `-march=native` the main win. Two memory-bound-cluster benchmarks here now range +2.9% (lbm) to
  +16.5% (cactus), so the cluster prior says "try it", not how much it'll give.
