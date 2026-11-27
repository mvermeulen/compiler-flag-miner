# `cfm mine` results: 834.vpr_s on `chicago`, 2026-11-27

This is the eighth intspeed benchmark mined on `chicago` (see [`host_chicago.md`](host_chicago.md)). `834.vpr_s` is
the speed version of `734.vpr_r` (VPR, FPGA place-and-route, C), tagged `pthread` (`@benchsets` `intspeed pthread
specspeed`) and run unpinned. niwot's mine found `-O3 -flto -fprofile-use -march=znver5` at +25.17% (LTO +17.66%,
PGO +4.87%, `-march=znver5` +1.60%; [write-up](mining_results.834.vpr_s.2026-10-24.md)). This machine's `734.vpr_r`
found `-O3 -flto -fprofile-use` at +17.95% (LTO +13.18%, PGO +4.21%; [write-up](mining_results.734.vpr_r.2026-11-23.md)).
Its corpus shape is memory-bound at 35.9%, under the 55% gate, so nothing was excluded and all fourteen ordinary
candidates were screened.

## Headline result

**`-O3 -flto -funroll-loops -fprofile-use -march=znver5`, +24.66% over plain `-O3`** (ratio 4.0891 → 5.0976).

| Step | Mean | Gain on the step before |
|---|---|---|
| `-O3` | 4.0891 | — |
| `-O3 -flto` | 4.7668 | **+16.57%** |
| `+ -funroll-loops` (pair tournament) | 4.7978 | +0.65% |
| `+ -fprofile-use` | 5.0322 | **+4.89%** |
| `+ -march=znver5` | 5.0976 | +1.30% |

- **niwot's three steps reproduce closely**: LTO +16.57% against +17.66%, PGO +4.89% against +4.87%, and
  `-march=znver5` +1.30% against +1.60%. It is the second `-march=znver5` accept on this host's int mines, after `735.gem5_r`, and the first on top of PGO.
- **`-funroll-loops` is the one difference, and a small one.** It gained +1.09% alone. As a greedy step on top of
  `-flto` it read +0.22% (CI overlap), but the pair tournament measured the same code (`a385f841`) at 4.7978,
  CI-clear of LTO alone, and a pair replaces the winner with no 1% bar ([opportunity #10](host_chicago.md#open-items)).
  Pooling all six runs of that code gives +0.44% over LTO, so it is worth well under 1%.
- **`-march=native` (+1.85%), `-ffast-math` (+1.36%) and `-Ofast` (+1.14%) were also accepted alone**, and each
  read +0.12% to +0.74% on top of `-flto` (CI overlap). In the pair tournament `-ffast-math -flto` read 4.8031,
  the highest pair, but its CI overlapped the `-flto -funroll-loops` winner's, which had replaced LTO one pair
  earlier.
- **Vector width didn't help**: `-mprefer-vector-width=256` on the winner read +0.33% (CI overlap), and
  `-mtune=znver5` -0.22%.

## Run metadata

| | |
|---|---|
| Host | `chicago`: AMD Ryzen AI MAX+ 395 (16 Zen5 cores, 32 threads), 91 GB RAM, power profile `performance`, kernel 7.0.0-43 |
| Command | `python3 -m cfm.cli mine 834.vpr_s` (uncapped, defaults; started by `~/cfm-logs/queue/run_queue.sh`) |
| Code | `main` at `e82d83a` (no code changes since `3b15833`, PR #72) |
| SPEC config | `gcc_O3.cfg`, `threads = 32` |
| Thread placement | pthread, not pinned |
| Experiment id | 50 |
| Started / finished | 2026-11-27T10:53:27Z / 2026-11-27T22:32:06Z (11h39m) |
| Final status | `converged` |
| Trials | 122 (2691-2812), none skipped, three reruns (`-fno-math-errno`) |
| Candidates screened / confirmed | 14 / 14 (plus `-march=native` fast-tracked) |
| Excluded on shape (Phase 2) | none (memory-bound 35.9% is under the gate; `vectorization_density=moderate`) |
| Fast-tracked (M4) | `-march=native` (accepted 22 of 35, mean +16.92%) |
| Accepted in Phase 4 | `-flto` +16.57%, `-march=native` +1.85%, `-ffast-math` +1.36%, `-Ofast` +1.14%, `-funroll-loops` +1.09% |
| Winning flags | `["-O3", "-flto", "-funroll-loops", "-fprofile-use", "-march=znver5"]`, +24.66% |
| Guards | throttle stop not triggered; bandwidth gate waited 30 s before 99 of 122 timed runs; three slow-rep reruns (trial 2742 → 2743 → 2744 → 2745); baseline recheck not flagged (+0.04%) |
| Power | package power median 23.9-25.2 W per trial; CPU temperature 72.0-76.8°C |

A trial took about 5.5 minutes, and a PGO trial about 9.

## Baseline

Shape from the reference-matrix corpus (`amd-370-64gb`): memory-bound 35.9%, `vectorization_density=moderate`,
`allocation_pressure=moderate`.

| Trial | Role | Ratio |
|---|---|---|
| 2691 | warm-up | 4.0720 |
| 2692 | warm-up | 4.0684 |
| 2693 | calibration | 4.0816 |
| 2694 | calibration | 4.0889 |
| 2695 | calibration | 4.0968 |
| 2758 | recheck | 4.0909 (+0.04%) |

The calibration mean is 4.0891, with a 95% CI of [4.0702, 4.1080] (±0.46%). Warm-up settled after the minimum two
reps (655 s), but the calibration reps kept rising (4.0816 → 4.0968), which widened the CI. Every `-O3` build had
the same code fingerprint (`32d16cbc`).

## Trials

| Trials | Phase | Flags (on `-O3`) | Mean ratio | Delta | Verdict |
|---|---|---|---|---|---|
| 2696-2709 | screening | 14 candidates | 4.0780-4.7640 | | all survived |
| 2710-2712 | confirmation | `-fprefetch-loop-arrays` | 4.1049 | +0.38% | reject |
| 2713-2715 | confirmation | `-fgraphite-identity` | 4.0793 | -0.24% | reject |
| 2716-2718 | confirmation | `-flto` | 4.7668 | +16.57% | **accept** (the greedy start) |
| 2719-2721 | confirmation | `-fno-pie -no-pie` | 4.1100 | +0.51% | reject |
| 2722-2724 | confirmation | `-fno-stack-protector` | 4.1087 | +0.48% | reject |
| 2725-2727 | confirmation | `-fcf-protection=none` | 4.1153 | +0.64% | reject |
| 2728-2730 | confirmation | `-U_FORTIFY_SOURCE` | 4.0864 | -0.07% | reject |
| 2731-2733 | confirmation | `-funroll-loops` | 4.1337 | +1.09% | **accept** |
| 2734-2736 | confirmation | `-Ofast` | 4.1356 | +1.14% | **accept** |
| 2737-2739 | confirmation | `-ffast-math` | 4.1447 | +1.36% | **accept** |
| 2740-2745 | confirmation | `-fno-math-errno` | 4.0320 | -1.40% | reject; trials 2742-2744 replaced in turn, 2745 kept |
| 2746-2748 | confirmation | `-fno-ipa-cp-clone` | 4.0982 | +0.22% | reject |
| 2749-2751 | confirmation | `-fno-unswitch-loops` | 4.0941 | +0.12% | reject |
| 2752-2754 | confirmation | `-fipa-pta` | 4.1147 | +0.63% | reject |
| 2755-2757 | confirmation (fast-tracked) | `-march=native` | 4.1649 | +1.85% | **accept** |
| 2758 | baseline recheck | `-O3` | 4.0909 | +0.04% | not flagged |
| 2759-2761 | combination (greedy) | `-flto -march=native` | 4.7726 | +0.12% | reject |
| 2762-2764 | combination (greedy) | `-flto -ffast-math` | 4.8018 | +0.73% | reject |
| 2765-2767 | combination (greedy) | `-flto -Ofast` | 4.8021 | +0.74% | reject |
| 2768-2770 | combination (greedy) | `-flto -funroll-loops` | 4.7774 | +0.22% | reject |
| 2771-2773 | combination (pair) | `-Ofast -flto` | 4.7966 | +17.30% | accept, CI overlaps LTO's, not a replacement |
| 2774-2776 | combination (pair) | `-flto -funroll-loops` | 4.7978 | +17.33% | **accept**, same code as the greedy step; replaces the LTO winner |
| 2777-2779 | combination (pair) | `-Ofast -ffast-math` | 4.1427 | +1.31% | accept, not enough to replace the winner |
| 2780-2782 | combination (pair) | `-ffast-math -funroll-loops` | 4.1770 | +2.15% | accept, not enough to replace the winner |
| 2783-2785 | combination (pair) | `-flto -march=native` | 4.7771 | +16.82% | accept, same code as the greedy step, not enough to replace the winner |
| 2786-2788 | combination (pair) | `-Ofast -funroll-loops` | 4.1774 | +2.16% | accept, not enough to replace the winner |
| 2789-2791 | combination (pair) | `-funroll-loops -march=native` | 4.1603 | +1.74% | accept, not enough to replace the winner |
| 2792-2794 | combination (pair) | `-ffast-math -flto` | 4.8031 | +17.46% | accept, same code as the greedy step; CI overlaps the new winner's |
| 2795-2797 | combination (pair) | `-ffast-math -march=native` | 4.1823 | +2.28% | accept, not enough to replace the winner |
| 2798-2800 | combination (pair) | `-Ofast -march=native` | 4.1794 | +2.21% | accept, not enough to replace the winner |
| 2801-2803 | PGO | winner `+ -fprofile-use` | 5.0322 | +4.89% | **accept** |
| 2804-2806 | microarch | PGO winner `+ -march=znver5` | 5.0976 | +1.30% | **accept** |
| 2807-2809 | microarch | PGO winner `+ -mtune=znver5` | 5.0210 | -0.22% | reject |
| 2810-2812 | vector width | `-march=znver5` winner `+ -mprefer-vector-width=256` | 5.1142 | +0.33% | reject |

Phase 4 and pair deltas are against `-O3`, greedy-step deltas against `-O3 -flto`, the PGO delta against
`-O3 -flto -funroll-loops`, microarch deltas against the PGO winner, and the vector-width delta against the
`-march=znver5` winner. The greedy walk started from the Phase 4 `-flto` result rather than re-measuring it. The PGO
near-miss list was empty (every Phase 4 reject overlapped baseline's CI), so only plain PGO was tried.

## Observations

- **The pair tournament's order picked the winner.** Pairs replace the winner in the order they're measured, each
  against the current winner. `-flto -funroll-loops` (CI [4.7936, 4.8019]) cleared LTO's [4.7479, 4.7857] and
  replaced it; `-ffast-math -flto`, measured later at a higher 4.8031 ([4.7943, 4.8118]), then overlapped the new
  winner. The two are within 0.11% of each other, so the choice doesn't matter here, and PGO and `-march=znver5`
  were only tried on top of the unroll set.
- **Four pairs re-measured greedy-step code** (`-flto` with `-funroll-loops`, `-march=native`, `-ffast-math` and
  `-Ofast`), twelve timed runs at about 5.5 minutes each (niwot opportunity #35). Same-code reads differed by up
  to 0.43% (`-funroll-loops`: 4.7774 then 4.7978).
- **`-fno-math-errno` ran into four slow reps in a row.** Its first two reps read 4.0818 and 4.0763; the next four,
  each a re-run of the one before, read 3.9379-3.9601, about 3% lower, until the three-rerun cap kept the last one.
  All six built the same code (`a5b237b0`), bandwidth probes read normal (104-106 GB/s), and package power was about
  0.6 W lower (23.9-24.1 W against 24.6-24.9 W). The trial after it (`-fno-ipa-cp-clone`) read normally. The cause
  isn't known; the reject doesn't depend on it, since the two normal reps alone read -0.25%.
- **Package power read about 24-25 W**, against 85 W on the gcc_s, llvm_s and cppcheck_s mines. vpr_s is a pthread
  benchmark run unpinned, so this isn't a placement bug; like flac_s (28 W), its threading evidently doesn't load
  the whole chip. vpr_r here ran at 85 W with 32 copies.
- **PGO built identical code on every rep** (`86e3cb6a`, 5.0264-5.0428), as did the `-march=znver5` variant, like
  ntest_s and abc_s and unlike the other SPEC PGO mines here (CLAUDE.md, 2026-10-28).
- **The bandwidth gate waited before 99 of 122 timed runs**, about 50 minutes in all, the most of any int mine here.
