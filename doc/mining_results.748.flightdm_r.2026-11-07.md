# `cfm mine` results: 748.flightdm_r on `chicago`, 2026-11-07

This is the ninth benchmark mined on `chicago` (see [`host_chicago.md`](host_chicago.md)), and the second here that
`niwot` has also mined ([2026-11-05](mining_results.748.flightdm_r.2026-11-05.md), +25.81%). `748.flightdm_r` is a
C++ flight-dynamics simulator. Its corpus shape is frontend-bound at 42.0%, under the 55% shape margin, so no
candidate was excluded on shape.

## Headline result

**`-O3 -flto -fno-stack-protector -fprofile-use`, +26.48% over plain `-O3`** (ratio 96.219 → 121.701). This is the
largest gain on this host after astcenc's +29.49%, and close to niwot's +25.81% with `-O3 -flto -fprofile-use`.

| Step | Mean | Gain on the step before |
|---|---|---|
| `-O3` | 96.219 | — |
| `-O3 -flto` | 106.149 | +10.32% |
| `+ -fno-stack-protector` | 108.097 | +1.84% (from the pair tournament, see below) |
| `+ -fprofile-use` | 121.701 | +12.58% |

- **LTO and PGO carry the win, as on niwot.** `-flto` gave +10.69% alone (niwot +10.60%) and PGO +12.58% on top
  (niwot +13.06%). All PGO reps built the same code (`57e53e42`).
- **`-fno-stack-protector` was accepted alone, +1.28%**, with a CI [97.17, 97.73] clear of the baseline's
  [95.66, 96.78]. It's the first security-hardening flag accepted on this host. niwot measured +1.39% and rejected
  it on a wider baseline CI.
- **The pair tournament overrode a greedy-step reject.** The greedy step `-flto -fno-stack-protector` read +1.08% on
  `-flto` but one rep (106.246) widened its CI to ±2.2%, and it was rejected. The pair trial then built the same
  code (`17065556`), read 107.95-108.28, was accepted against `-O3` (+12.34%), and replaced the greedy winner. Over
  all six reps the step is worth about +1.1% to +1.8% on `-flto`.
- **`-march=native` was rejected again, +0.94%** (CI overlap), its second reject in a row here after gmsh. niwot
  measured +1.01%. On top of PGO, `-march=znver5` read +1.02% and was rejected on CI overlap; `-mtune=znver5`
  read -0.16%.
- **The fast-math flags can't act on flightdm.** The SPEC config gives it `PORTABILITY = -fno-fast-math`, which
  lands after `OPTIMIZE` on every compile line. `-ffast-math` and `-fno-math-errno` built the same code as `-O3`
  (`61a5f98a`, the same fingerprint niwot recorded) and were skipped. `-Ofast` changed the code and read -0.11%.
- **`-fno-pie -no-pie` was a real loss, -1.64%**, with all three reps below every `-O3` rep. The rest were within
  ±0.8%.

## Run metadata

| | |
|---|---|
| Host | `chicago`: AMD Ryzen AI MAX+ 395 (16 Zen5 cores, 32 threads), 91 GB RAM, power profile `performance` |
| Command | `python3 -m cfm.cli mine 748.flightdm_r` (uncapped, defaults) |
| Code | `main` at `c7c9baf` (no code changes since `f31ba64`, only docs) |
| Experiment id | 11 |
| Started / finished | 2026-11-07T10:39:33Z / 2026-11-07T16:16:41Z (5h37m) |
| Final status | `converged` |
| Trials | 76 (436-511), 2 skipped as unchanged code, no reruns |
| Candidates screened / confirmed | 12 / 10 (plus 3 fast-tracked: `-march=native`, `-Ofast`, `-ffast-math`) |
| Excluded on shape (Phase 2) | none (frontend-bound 42.0%, under the 55% margin) |
| Fast-tracked (M4) | `-march=native`, `-Ofast`, `-ffast-math` (each accepted 1 of 1, on astcenc); all three rejected or skipped here |
| Skipped as unchanged code | `-fno-math-errno`, `-ffast-math` (same code as `-O3`) |
| Winning flags | `["-O3", "-flto", "-fno-stack-protector", "-fprofile-use"]`, +26.48% |
| Guards | bandwidth gate waited three times (30 s, trials 436, 479 and 507); no reruns; **baseline recheck flagged** (-0.86%, see below) |
| Power | package power median 84.99 W on every trial; CPU temperature 93.8-98.1°C |

Each trial took about 4.5 minutes, and each PGO trial about 6.

## Baseline

Shape from the reference-matrix corpus (`amd-370-64gb`): frontend-bound 42.0%, `vectorization_density=high`,
`allocation_pressure=low`.

| Trial | Role | Ratio |
|---|---|---|
| 436 | warm-up | 96.144 |
| 437 | warm-up | 95.499 |
| 438 | calibration | 96.019 |
| 439 | calibration | 96.176 |
| 440 | calibration | 96.462 |
| 493 | recheck | 95.392 (-0.86%) |

The calibration mean is 96.219, with a 95% CI of [95.661, 96.777] (±0.58%). Warm-up settled after the minimum two
reps (558 s). Every `-O3` build had the same code fingerprint (`61a5f98a`).

The recheck read 0.86% under the mean, just past the warning threshold, and was flagged. It sits close to the
second warm-up rep (95.499), so it looks like ordinary spread at the low end rather than drift. Read the 0.1-0.8%
Phase 4 deltas with that in mind; the accepted deltas (+10.7%, +1.28%) are larger than the offset, and every
`-fno-stack-protector` rep beat every calibration rep.

## Trials

| Trials | Phase | Flags (on `-O3`) | Mean ratio | Delta | Verdict |
|---|---|---|---|---|---|
| 441-452 | screening | 12 candidates | 94.26-106.00 | | all survived (`-fno-math-errno` skipped as unchanged code) |
| 453-455 | confirmation | `-flto` | 106.502 | +10.69% | **accept** |
| 456-458 | confirmation | `-fno-pie -no-pie` | 94.638 | -1.64% | reject (CI clear below baseline) |
| 459-461 | confirmation | `-fno-stack-protector` | 97.449 | +1.28% | **accept** |
| 462-464 | confirmation | `-fcf-protection=none` | 96.313 | +0.10% | reject |
| 465-467 | confirmation | `-U_FORTIFY_SOURCE` | 96.246 | +0.03% | reject |
| 468-470 | confirmation | `-fno-ipa-cp-clone` | 96.136 | -0.09% | reject |
| 471-473 | confirmation | `-fno-unswitch-loops` | 96.787 | +0.59% | reject |
| 474-476 | confirmation | `-funroll-loops` | 96.954 | +0.76% | reject |
| 477-479 | confirmation | `-fprefetch-loop-arrays` | 96.464 | +0.25% | reject |
| 480-482 | confirmation | `-fipa-pta` | 95.476 | -0.77% | reject |
| 483-485 | confirmation | `-fgraphite-identity` | 96.429 | +0.22% | reject |
| 486-488 | confirmation (fast-tracked) | `-march=native` | 97.127 | +0.94% | reject (CI overlap) |
| 489-491 | confirmation (fast-tracked) | `-Ofast` | 96.116 | -0.11% | reject |
| 492 | confirmation (fast-tracked) | `-ffast-math` | | | skipped (same code as `-O3`) |
| 494-496 | combination (greedy) | `-flto` | 106.149 | +10.32% | **accept** |
| 497-499 | combination (greedy) | `-flto -fno-stack-protector` | 107.300 | +1.08% | reject (CI ±2.2%) |
| 500-502 | combination (pair) | `-flto -fno-stack-protector` | 108.097 | +12.34% | **accept**, replaced the greedy winner |
| 503-505 | PGO | `-flto -fno-stack-protector -fprofile-use` | 121.701 | +12.58% | **accept** |
| 506-508 | microarch | `+ -march=znver5` | 122.939 | +1.02% | reject (CI overlap) |
| 509-511 | microarch | `+ -mtune=znver5` | 121.507 | -0.16% | reject |

The greedy deltas are against the step before, the pair delta against `-O3`, and the Phase 6 deltas against the
step before. The vector-width multiplier was skipped because the winning set has no `-march=`.

## Observations

- **flightdm transfers between hosts.** The `-O3` build matches niwot's fingerprint, and the LTO (+10.7% against
  +10.6%) and PGO (+12.6% against +13.1%) steps agree within half a point, despite twice the copies and 85 W
  against about 50 W. astcenc showed the same thing. For these compute-bound C++ codes, a flag result from one
  Zen5 host carries over to the other.
- **The tighter baseline let a small flag through.** `-fno-stack-protector` read about +1.3-1.4% on both hosts; the
  baseline CI here (±0.58%, against niwot's ±2.4%) is what made it an accept.
- **The pair tournament did useful work here**, for once. On astcenc and ocio it only re-measured code already
  timed. Here it re-measured the greedy step's code after one low rep had sunk it, and recovered the step.
- **`-march=native` has now been rejected twice in a row here**, after 8 accepts: gmsh (-0.42%, memory-bound
  cluster) and flightdm (+0.94%, frontend-bound cluster). Both were fast-tracked on accepted priors and rejected on
  their own measurements, so the fast-track cost nothing extra.
- **Package power read 85.0 W on every trial**, for the ninth mine in a row.
