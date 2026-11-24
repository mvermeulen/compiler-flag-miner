# `cfm mine` results: 800.pot3d_s on `niwot`, 2026-11-23

The eighth fpspeed benchmark mined on `niwot` (see [`host_niwot.md`](host_niwot.md)). `800.pot3d_s` is POT3D, a
Fortran potential-field solver for the solar corona whose loops are written as `DO CONCURRENT` and parallelized by
the config's `-ftree-parallelize-loops=16`. `chicago` mined it on 2026-11-10
([write-up](mining_results.800.pot3d_s.2026-11-10.md), after a pinned first mine that PR #70 fixed). Its corpus shape
is memory-bound at 52.0%, under the 55% margin, so no candidate was excluded on shape.

## Headline result

**`-O3 -Ofast`, +20.73% over plain `-O3`** (ratio 0.7936 → 0.9582), the same winner as `chicago` (+28.25%).

- **`-Ofast` and `-ffast-math` both won big**: +20.73% and +18.05%, every rep far above every `-O3` rep
  (0.792-0.794). As on `chicago`, `-Ofast -ffast-math` built the same code as `-Ofast` (`04ef5118`).
- **The fast-math builds run in two modes here.** Their reps fall between about 0.90 and 0.97, mostly in a slow
  band (0.90-0.93, mostly at 15.0-15.1 W) and a fast band (0.94-0.97, mostly at 16.0 W). The spread rule replaced four
  slow reps (#41), so the reported +20.73% is mostly the fast mode; the nine runs of the `-Ofast` code average
  +19.47%. Either is a clear accept. Every non-fast-math flagset ran in one mode.
- **Phase 6 found nothing on top, but its verdicts depend on the modes.** `-march=znver5` read -3.57% with two of
  its three reps in the slow mode and one (0.967) at the top of the fast one; PGO -0.44% and `-mtune=znver5` -2.10%
  each had one slow rep replaced. `chicago` read +0.27%, -0.13% and -0.17% for the same three, so all three are most
  likely flat here too.
- **`-fno-unswitch-loops` lost 6.6% at screening** and was pruned (`chicago`: -31.8%), at 28 W against 17 W for
  `-O3`.
- **`-march=native` alone read -0.54%** (`chicago`: -0.00%). Every other candidate was within ±0.6% of `-O3`, apart
  from `-fno-ipa-cp-clone` at -1.47% with one low rep; `-fno-stack-protector`, `-fcf-protection=none` and
  `-frecursive` built the same code as `-O3` and were skipped.

## Run metadata

| | |
|---|---|
| Host | `niwot`: AMD Ryzen AI 7 350 (4 Zen5 + 4 Zen5c cores, 16 threads), 64 GB RAM |
| Command | `cfm mine 800.pot3d_s --settle-seconds 600` (uncapped, from the fpspeed queue) |
| Code | `main` at `85ed51e` (no code changes since PR #72) |
| SPEC config | `ryzen350_64gb.gcc_O3.cfg`: `threads = 16`; `-ftree-parallelize-loops=16` |
| Thread placement | OpenMP (`doconcurrent`, PR #70): `OMP_PLACES=threads OMP_PROC_BIND=close` |
| Experiment id | 210 |
| Started / finished | 2026-11-23T20:34:50Z / 2026-11-24T21:19:21Z (24h44m) |
| Final status | `converged` |
| Trials | 66 (2786-2851), 4 skipped as unchanged code, 4 spread-rule reruns |
| Candidates screened / confirmed | 13 / 9 (plus `-march=native` fast-tracked; `-fno-unswitch-loops` pruned; 3 skipped) |
| Excluded on shape (Phase 2) | none (memory-bound 52.0%, under the 55% margin) |
| Fast-tracked (M4) | `-march=native` (accepted 16 of 28, mean +21.93%) |
| Skipped as unchanged code | `-fno-stack-protector`, `-fcf-protection=none`, `-frecursive` (same code as `-O3`); `-Ofast -ffast-math` (same as `-Ofast`) |
| Accepted in Phase 4 | `-Ofast` +20.73%, `-ffast-math` +18.05% |
| Winning flags | `["-O3", "-Ofast"]`, +20.73% |
| Guards | throttle stop not triggered; bandwidth gate waited 30 s before the first run only (43.1-45.8 GB/s); four spread-rule reruns, all on fast-math code; baseline recheck not flagged (+0.05%) |
| Power | package power median 17.0 W on `-O3`-class code, 16.1 W on `-march=native`, 15.0-16.0 W on fast-math code, 28.0 W on `-fno-unswitch-loops`; CPU temperature 87.5-95.8°C |

A `-O3`-class trial took about 24 minutes with the settle, a fast-math trial about 22 and a PGO trial about 27.
`chicago` ran its 63 trials in 7h56m. Every timed run's `.rsf` reads `valid: S`. `chicago` drew 74.6 W on `-O3`.

## Baseline

Shape from the reference-matrix corpus (`amd-370-64gb`): memory-bound 52.0%, `vectorization_density=moderate`,
`allocation_pressure=low`.

| Trial | Role | Ratio |
|---|---|---|
| 2786 | warm-up | 0.79387 |
| 2787 | warm-up | 0.79215 |
| 2788 | calibration | 0.79417 |
| 2789 | calibration | 0.79274 |
| 2790 | calibration | 0.79398 |
| 2835 | recheck | 0.79402 (+0.05%) |

Warm-up settled after the minimum 2 reps (2962 s). The calibration mean is 0.79363, 95% CI ±0.24%. Every `-O3`
build had one fingerprint (`0bc96e5b`).

## Phase 3/4: screening and confirmation

Screening read 0.789-0.795 for every non-fast-math candidate except `-fno-unswitch-loops` (0.742, -6.6% against the
last calibration rep, pruned), and 0.927 and 0.971 for `-Ofast` and `-ffast-math`.

| Flag | Reps | Mean | Delta | Verdict |
|---|---|---|---|---|
| `-Ofast` | 0.963, 0.957, 0.954 (0.927 replaced) | 0.9582 | +20.73% | **accept** |
| `-ffast-math` | 0.968, 0.921, 0.921 | 0.9368 | +18.05% | **accept** |
| `-funroll-loops` | 0.794, 0.794, 0.793 | 0.7935 | -0.02% | reject |
| `-fno-pie -no-pie` | 0.794, 0.794, 0.792 | 0.7932 | -0.05% | reject |
| `-fgraphite-identity` | 0.794, 0.793, 0.792 | 0.7929 | -0.09% | reject |
| `-fstack-arrays` | 0.789, 0.794, 0.795 | 0.7925 | -0.14% | reject |
| `-fprefetch-loop-arrays` | 0.788, 0.790, 0.790 | 0.7894 | -0.53% | reject |
| `-march=native` (fast-tracked) | 0.787, 0.791, 0.790 | 0.7893 | -0.54% | reject |
| `-flto` | 0.790, 0.784, 0.794 | 0.7891 | -0.57% | reject |
| `-fno-ipa-cp-clone` | 0.792, 0.770, 0.784 | 0.7820 | -1.47% | reject |

## Phase 5: combination

The greedy walk started from `-O3 -Ofast` (Phase 4's top accept, reused under #39). Adding `-ffast-math` built the
same code (`04ef5118`) and was skipped (trial 2836). The pair tournament then measured `-Ofast` + `-ffast-math`
against baseline anyway: 0.969, 0.967, 0.969 (0.901 replaced), the same binary as the greedy winner, about 90
minutes spent re-measuring it (#35). It read 1.1% above the winner's Phase 4 reps, inside the CI, so the winner
stood. `chicago`'s run did the same.

## Phase 6: multipliers

| Flagset (on `-O3 -Ofast`) | Reps | Mean | Delta | Verdict |
|---|---|---|---|---|
| `-fprofile-use` | 0.948, 0.947, 0.967 (0.902 replaced) | 0.9539 | -0.44% | reject |
| `-mtune=znver5` | 0.943, 0.940, 0.932 (0.895 replaced) | 0.9381 | -2.10% | reject |
| `-march=znver5` | 0.967, 0.901, 0.904 | 0.9239 | -3.57% | reject |

No near-miss variant (no Phase 4 reject was CI-clear above baseline), and the vector-width multiplier was skipped
because the winning set has no `-march=`. All four PGO builds had one fingerprint (`d79e82e3`), so its slow rep
was the same binary as its fast ones.

## The two modes of the fast-math code

| Code | Flagset | Runs | Slow band (0.90-0.93) | Fast band (0.94-0.97) |
|---|---|---|---|---|
| `04ef5118` | `-Ofast` (and the pair) | 9 | 0.927, 0.927, 0.901 | 0.954-0.969 (6) |
| `a1f7aeff` | `-ffast-math` | 4 | 0.921, 0.921 | 0.968, 0.971 |
| `d79e82e3` | `-Ofast -fprofile-use` | 4 | 0.902 | 0.947-0.967 (3) |
| `742b4410` | `-Ofast -march=znver5` | 3 | 0.901, 0.904 | 0.967 |
| `bb671c0d` | `-Ofast -mtune=znver5` | 4 | 0.895, 0.932 | 0.940, 0.943 |

Of the 10 slow-band runs, 9 drew 15.0-15.1 W; of the 14 fast-band runs, 12 drew 16.0 W. The
bandwidth probe read 43-46 GB/s before every run in either band. The `-O3`-class builds (17.0 W) never left one
band. Only the fast-math builds show the second mode, so it looks tied to that code, like sph_exa_s's
`-march=native` (#41), not to the host, though nothing recorded explains it.

Its effect on the result: the spread rule replaced the slow rep whenever the other two reps were both fast (four
times), and could not when two of three were slow (`-ffast-math`, `-march=znver5`). The accept/reject verdicts
against `-O3` hold either way, but the comparisons among the fast-math variants, `-Ofast` against `-ffast-math`
and every Phase 6 step, compare mode mixes rather than code.

## Power runs opposite to `chicago`

On `chicago` the fast-math builds raised package power from 74.6 W to 85 W, and `-fno-unswitch-loops` cut it to
48.6 W, which that write-up read as fast-math parallelizing more loops. Here the fast-math builds *lower* power
(17 → 15-16 W) while gaining 20%, and `-fno-unswitch-loops` *raises* it to 28 W while losing 6.6%. The winners and
losers agree across hosts; the power signal doesn't. On this host power may track spinning OpenMP threads more than
useful work, as #36 suggested for graph500_s, but this run doesn't test it.

## Knowledge table

The memory-bound rows this run changed most:

| Flag | Before | After |
|---|---|---|
| `-Ofast` | 3 of 10, +0.54% | 4 of 11, +2.38% |
| `-ffast-math` | 3 of 9, +0.58% | 4 of 10, +2.33% |
| `-march=native` | 16 of 28, +21.93% | 16 of 29, +21.16% |
| `-march=znver5` | 4 of 12, +1.12% | 4 of 13, +0.76% |
| `-mtune=znver5` | 0 of 12, -0.14% | 0 of 13, -0.29% |
| `-fprofile-use` | 5 of 23, -3.97% | 5 of 24, -3.82% |
| `-fno-ipa-cp-clone` | 1 of 6, +0.47% | 1 of 7, +0.19% |

The `-march=znver5` and `-mtune=znver5` rows carry this run's mode-dependent -3.57% and -2.10%.

## Compared with `chicago`

| | `chicago` (2026-11-10) | `niwot` |
|---|---|---|
| Baseline | 1.4446, ±0.21%, 74.6 W | 0.7936, ±0.24%, 17.0 W |
| `-Ofast` | +28.25% | +20.73% (+19.47% over all nine runs) |
| `-ffast-math` | +27.78% | +18.05% |
| `-fno-unswitch-loops` (screening) | -31.8%, 48.6 W | -6.6%, 28.0 W |
| `-march=native` alone | -0.00% | -0.54% |
| On top of `-Ofast`: PGO / `-march=znver5` / `-mtune=znver5` | -0.13% / +0.27% / -0.17% | -0.44% / -3.57% / -2.10% (mode-dependent) |
| Fast-math reps | one mode | two modes, about 4% apart |
| Total | +28.25% | +20.73% |
| Run | 63 trials, 7h56m | 66 trials, 24h44m |
