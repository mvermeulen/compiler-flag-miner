# `cfm mine` results: 835.gem5_s on `chicago`, 2026-11-28

This is the ninth intspeed benchmark mined on `chicago` (see [`host_chicago.md`](host_chicago.md)). `835.gem5_s` is
the speed version of `735.gem5_r` (the gem5 architecture simulator, C++), tagged `pthread` (`@benchsets`
`cxxthreads intspeed pthread specspeed`) and run unpinned. niwot's mine found `-O3 -flto` at +5.35%, with PGO -8.63%
on top ([write-up](mining_results.835.gem5_s.2026-10-24.md)). This machine's `735.gem5_r` found `-O3 -flto -fno-pie
-no-pie -fno-stack-protector -march=znver5` at +13.05%, with PGO -9.40% ([write-up](mining_results.735.gem5_r.2026-11-23.md)).
Its corpus shape is frontend-bound at 40.4%, under the 55% gate, so nothing was excluded.

## Headline result

**`-O3 -flto -march=znver5`, +5.46% over plain `-O3`** (ratio 5.3897 → 5.6841).

| Step | Mean | Gain on the step before |
|---|---|---|
| `-O3` | 5.3897 | — |
| `-O3 -flto` | 5.6234 | **+4.34%** |
| `+ -march=znver5` | 5.6841 | +1.08% |

- **niwot's winner plus `-march=znver5`.** LTO gained +4.34% against niwot's +5.35%; as there, it's about half
  the LTO gain the rate version gets (+6.65% on gem5_r here). `-march=znver5` added +1.08% on top, against +1.67%
  on gem5_r here, and `-mtune=znver5` read -0.18%, so again the gain is from the instruction sets.
- **PGO lost 8.79% on top of LTO** (CI-clear below), against -8.63% on niwot's gem5_s and -9.40% on gem5_r here.
  gem5's training run evidently doesn't cover what the reference run does (niwot opportunity #21).
- **Non-PIE read +1.10% alone but was rejected on CI overlap**: two reps read 5.480 (+1.68%) and one 5.387. On
  gem5_r here it added +2.84% on top of LTO. With `-flto` the only accept, there was no greedy step to try it on
  top ([opportunity #23](host_chicago.md#open-items)).
- **`-fno-stack-protector` (+0.57%) and `-Ofast` (-0.44%) were fast-tracked and rejected**, along with the rest:
  `-march=native` +0.69%, everything else -0.64% to +0.06%, all CI-overlapping.
- **The baseline recheck was flagged** (-0.60%, 5.3574, below the baseline CI [5.3750, 5.4044]), as on niwot
  (-1.33%). Against the recheck the deltas read about 0.6% higher; the verdicts don't change.

## Run metadata

| | |
|---|---|
| Host | `chicago`: AMD Ryzen AI MAX+ 395 (16 Zen5 cores, 32 threads), 91 GB RAM, power profile `performance`, kernel 7.0.0-43 |
| Command | `python3 -m cfm.cli mine 835.gem5_s` (uncapped, defaults; started by `~/cfm-logs/queue/run_queue.sh`) |
| Code | `main` at `dc4bb4c` (no code changes since `3b15833`, PR #72) |
| SPEC config | `gcc_O3.cfg`, `threads = 32` |
| Thread placement | pthread, not pinned |
| Experiment id | 51 |
| Started / finished | 2026-11-27T22:33:07Z / 2026-11-28T09:20:15Z (10h47m) |
| Final status | `converged` |
| Trials | 75 (2813-2887), none skipped, no reruns |
| Candidates screened / confirmed | 12 / 12 (plus `-flto`, `-Ofast` and `-fno-stack-protector` fast-tracked) |
| Excluded on shape (Phase 2) | none (frontend-bound 40.4% is under the gate) |
| Fast-tracked (M4) | `-flto` (accepted 7 of 11, mean +5.13%), `-Ofast` (2 of 3, +2.40%), `-fno-stack-protector` (9 of 11, +1.84%) |
| Accepted in Phase 4 | `-flto` +4.34% |
| Winning flags | `["-O3", "-flto", "-march=znver5"]`, +5.46% |
| Guards | throttle stop not triggered; bandwidth gate waited 30 s before 45 of 75 timed runs; no reruns; baseline recheck **flagged** (-0.60%) |
| Power | package power median 25.3-26.0 W per trial; CPU temperature 73.1-78.8°C |

A trial took about 8 minutes, an LTO trial about 9, and an LTO+PGO trial about 18.

## Baseline

Shape from the reference-matrix corpus (`amd-370-64gb`): frontend-bound 40.4%, `vectorization_density=moderate`,
`allocation_pressure=low`.

| Trial | Role | Ratio |
|---|---|---|
| 2813 | warm-up | 5.3625 |
| 2814 | warm-up | 5.3444 |
| 2815 | calibration | 5.3829 |
| 2816 | calibration | 5.3924 |
| 2817 | calibration | 5.3938 |
| 2875 | recheck | 5.3574 (-0.60%, flagged) |

The calibration mean is 5.3897, with a 95% CI of [5.3750, 5.4044] (±0.27%). Warm-up settled after the minimum two
reps (1000 s). Every gem5 build had a different code fingerprint, `-O3` included, as on gem5_r here.

## Trials

| Trials | Phase | Flags (on `-O3`) | Mean ratio | Delta | Verdict |
|---|---|---|---|---|---|
| 2818-2829 | screening | 12 candidates | 5.3628-5.4663 | | all survived |
| 2830-2832 | confirmation | `-fno-pie -no-pie` | 5.4491 | +1.10% | reject (CI overlap) |
| 2833-2835 | confirmation | `-fcf-protection=none` | 5.3928 | +0.06% | reject |
| 2836-2838 | confirmation | `-U_FORTIFY_SOURCE` | 5.3862 | -0.07% | reject |
| 2839-2841 | confirmation | `-fno-ipa-cp-clone` | 5.3648 | -0.46% | reject |
| 2842-2844 | confirmation | `-fno-unswitch-loops` | 5.3880 | -0.03% | reject |
| 2845-2847 | confirmation | `-funroll-loops` | 5.3701 | -0.36% | reject |
| 2848-2850 | confirmation | `-fprefetch-loop-arrays` | 5.3731 | -0.31% | reject |
| 2851-2853 | confirmation | `-march=native` | 5.4267 | +0.69% | reject |
| 2854-2856 | confirmation | `-ffast-math` | 5.3671 | -0.42% | reject |
| 2857-2859 | confirmation | `-fno-math-errno` | 5.3640 | -0.48% | reject |
| 2860-2862 | confirmation | `-fipa-pta` | 5.3782 | -0.21% | reject |
| 2863-2865 | confirmation | `-fgraphite-identity` | 5.3550 | -0.64% | reject |
| 2866-2868 | confirmation (fast-tracked) | `-flto` | 5.6234 | +4.34% | **accept** (the greedy start) |
| 2869-2871 | confirmation (fast-tracked) | `-Ofast` | 5.3659 | -0.44% | reject |
| 2872-2874 | confirmation (fast-tracked) | `-fno-stack-protector` | 5.4205 | +0.57% | reject |
| 2875 | baseline recheck | `-O3` | 5.3574 | -0.60% | **flagged** |
| 2876-2878 | PGO | winner `+ -fprofile-use` | 5.1293 | -8.79% | reject (CI-clear, below) |
| 2879-2881 | microarch | winner `+ -march=znver5` | 5.6841 | +1.08% | **accept** |
| 2882-2884 | microarch | winner `+ -mtune=znver5` | 5.6135 | -0.18% | reject |
| 2885-2887 | vector width | `-march=znver5` winner `+ -mprefer-vector-width=256` | 5.6716 | -0.22% | reject |

Phase 4 deltas are against `-O3`, and Phase 6 deltas against the set before each step (`-O3 -flto` for PGO and
microarch, `-O3 -flto -march=znver5` for vector width). With one accept there was no greedy step beyond the start
and no pair tournament. The PGO near-miss list was empty (every Phase 4 reject overlapped baseline's CI), so only
plain PGO was tried.

## Observations

- **With only one Phase 4 accept, nothing was tried on top of LTO but Phase 6.** On gem5_r here non-PIE (+2.84%)
  and `-fno-stack-protector` (+1.38%) both paid on top of LTO. Here non-PIE's CI was wide (±2.5%) from one low rep,
  and `-fno-stack-protector` read +0.57% with a CI overlapping baseline's, so neither reached Phase 5. That's open
  item #23.
- **`-march=znver5` on LTO is very repeatable**: three reps at 5.6814-5.6855 (±0.10%), against the other flagsets'
  ±0.3-2.5%.
- **The `-O3` runs spread 0.9%** (5.3444-5.3938). The two warm-ups and the recheck read lower than the three
  calibration reps, so the calibration mean may sit a little high; that's what the recheck flag shows. It only
  understates the gains.
- **Package power read about 25.7 W**, like vpr_s (24-25 W) and flac_s (28 W): gem5_s is pthread-tagged and runs
  unpinned, but evidently doesn't load the whole chip. gem5_r here ran at 85 W with 32 copies.
- **The bandwidth gate waited before 45 of 75 timed runs**, about 22 minutes in all. No rep was slow and no rerun
  fired.
