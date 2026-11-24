# `cfm mine` results: 817.flac_s on `chicago`, 2026-11-24

This is the third intspeed benchmark mined on `chicago` (see [`host_chicago.md`](host_chicago.md)). `817.flac_s` is
the FLAC lossless audio encoder (C/C++, pthreads; `@benchsets` `cxxthreads intspeed pthread specspeed`), run unpinned
as one copy with `threads = 32`, which SPEC passes to every encode as `flac -j 32`. It has no intrate counterpart.
niwot's mine found `-O3 -fprefetch-loop-arrays -march=native -mprefer-vector-width=256` at +148.2% (`-march=native`
+128.5%, `-fprefetch-loop-arrays` +0.88% through the pair tournament, 256-bit vectors +7.64%;
[write-up](mining_results.817.flac_s.2026-10-27.md)). Its corpus shape is memory-bound at 65.1%, over the 55% gate,
so the shape filter excluded ten candidates.

## Headline result

**`-O3 -march=native`, +135.47% over plain `-O3`** (ratio 3.4422 → 8.1055).

| Step | Mean | Gain on the step before |
|---|---|---|
| `-O3` | 3.4422 | — |
| `-O3 -march=native` | 8.1055 | **+135.47%** |

- **`-march=native` more than doubles the speed again**, against +128.5% on niwot. It is the largest single-flag
  gain on this host. niwot's write-up has the background: SPEC builds flac with its intrinsic paths off, so the gain
  is GCC's own vectorization of the encoder loops.
- **`-mprefer-vector-width=256` lost 4.40% on top of `-march=native`** (CI clear, below), where niwot gained +7.64%
  with it. The two hosts disagree on the one step niwot's winner has beyond `-march=native`; see Observations.
- **`-fprefetch-loop-arrays` gained +2.79% alone** (niwot +2.75%) but only +0.88% on top of `-march=native`
  (niwot +0.88% too). Here the greedy step was rejected on CI overlap, and the pair tournament's same-code
  measurement overlapped the winner's CI too, so it didn't replace it.
- **PGO lost 1.99%** on top of `-march=native`, with CIs overlapping (niwot -1.26%).
- **The other Phase 4 candidates were flat**: `-flto` +0.34%, `-fno-math-errno` +0.33%, `-fgraphite-identity`
  -0.05%, all CI-overlapping.

## Run metadata

| | |
|---|---|
| Host | `chicago`: AMD Ryzen AI MAX+ 395 (16 Zen5 cores, 32 threads), 91 GB RAM, power profile `performance`, kernel 7.0.0-43 |
| Command | `python3 -m cfm.cli mine 817.flac_s` (uncapped, defaults; started by `~/cfm-logs/queue/run_queue.sh`) |
| Code | `main` at `cea1278` (no code changes since `3b15833`, PR #72) |
| SPEC config | `gcc_O3.cfg`, `threads = 32` (`flac -j 32`) |
| Thread placement | pthread, not pinned |
| Experiment id | 45 |
| Started / finished | 2026-11-24T18:57:25Z / 2026-11-24T23:45:46Z (4h48m) |
| Final status | `converged` |
| Trials | 38 (2415-2452), none skipped, one rerun (vector width) |
| Candidates screened / confirmed | 4 / 4 (plus `-march=native` fast-tracked) |
| Excluded on shape (Phase 2) | `-fno-pie -no-pie`, `-fno-stack-protector`, `-fcf-protection=none`, `-U_FORTIFY_SOURCE`, `-fno-ipa-cp-clone`, `-fno-unswitch-loops` (frontend-bound-tagged), `-funroll-loops`, `-Ofast`, `-ffast-math`, `-fipa-pta` (memory-bound 65.1%, over the gate); `-mprefer-vector-width=256` deferred to Phase 6 |
| Fast-tracked (M4) | `-march=native` (accepted 21 of 33, mean +13.85%) |
| Accepted in Phase 4 | `-march=native` +135.47%, `-fprefetch-loop-arrays` +2.79% |
| Winning flags | `["-O3", "-march=native"]`, +135.47% |
| Guards | throttle stop not triggered; bandwidth gate waited 30 s before 23 of 38 timed runs; one slow-rep rerun (trial 2449 → 2452); baseline recheck not flagged (+0.69%) |
| Power | package power median 27.6-33.5 W per trial (28.2 W typical); CPU temperature 80.4-88.1°C |

A trial took about 9 minutes, and a `-march=native` trial about 4.5.

## Baseline

Shape from the reference-matrix corpus (`amd-370-64gb`): memory-bound 65.1%, `vectorization_density=moderate`,
`allocation_pressure=low`.

| Trial | Role | Ratio |
|---|---|---|
| 2415 | warm-up | 3.4586 |
| 2416 | warm-up | 3.4555 |
| 2417 | calibration | 3.4588 |
| 2418 | calibration | 3.4112 |
| 2419 | calibration | 3.4567 |
| 2439 | recheck | 3.4659 (+0.69%) |

The calibration mean is 3.4422, with a 95% CI of [3.3754, 3.5091] (±1.94%). Trial 2418 read 1.3% under the other
five `-O3` runs (3.4555-3.4659), which widened the CI; it was too small a gap for the slow-rep rerun (10%, or 2% for
the spread rule). Warm-up settled after the minimum two reps (1103 s). Every `-O3` build had the same code
fingerprint (`8b1013d6`).

## Trials

| Trials | Phase | Flags (on `-O3`) | Mean ratio | Delta | Verdict |
|---|---|---|---|---|---|
| 2420-2423 | screening | 4 candidates | 3.4517-3.5358 | | all survived |
| 2424-2426 | confirmation | `-fprefetch-loop-arrays` | 3.5382 | +2.79% | **accept** |
| 2427-2429 | confirmation | `-fgraphite-identity` | 3.4407 | -0.05% | reject |
| 2430-2432 | confirmation | `-flto` | 3.4538 | +0.34% | reject |
| 2433-2435 | confirmation | `-fno-math-errno` | 3.4537 | +0.33% | reject |
| 2436-2438 | confirmation (fast-tracked) | `-march=native` | 8.1055 | +135.47% | **accept** (the greedy start) |
| 2439 | baseline recheck | `-O3` | 3.4659 | +0.69% | not flagged |
| 2440-2442 | combination (greedy) | `-march=native -fprefetch-loop-arrays` | 8.1767 | +0.88% | reject (CI overlap) |
| 2443-2445 | combination (pair) | `-fprefetch-loop-arrays -march=native` | 8.1775 | +137.57% | accept, same code as the greedy step; CI overlaps the winner's, so not a replacement |
| 2446-2448 | PGO | winner `+ -fprofile-use` | 7.9439 | -1.99% | reject |
| 2449-2452 | vector width | winner `+ -mprefer-vector-width=256` | 7.7491 | -4.40% | reject (CI-clear, below); trial 2449 (7.3094) replaced by 2452 |

Phase 4 and pair deltas are against `-O3`, and greedy-step and Phase 6 deltas against `-O3 -march=native`. The
greedy walk started from the Phase 4 `-march=native` result rather than re-measuring it. The PGO near-miss list was
empty, so only plain PGO was tried. The microarch multiplier was skipped (`-march=native` in the set).

## Observations

- **The vector-width result is the opposite of niwot's.** Here `-mprefer-vector-width=256` read 7.72-7.78 (CI) on top
  of `-march=native`'s 8.03-8.18; on niwot it gained +7.64%. niwot's Zen5 cores in the Ryzen AI 7 350 and this
  host's in the Ryzen AI MAX+ 395 may not execute 512-bit vectors the same way, but this run doesn't measure why.
  The one rerun fired here too: trial 2449 read 5.6% under its siblings, which agreed within 0.24%.
- **`-fprefetch-loop-arrays` on top of `-march=native` reads about +0.9% six times over**: the greedy step's three
  reps (8.165-8.195) and the pair's (8.169-8.182) built the same code (`002a80b8`) and pool to 8.1771, +0.88% over
  the winner. That is under the 1% bar either way, so its omission doesn't change the result. On niwot the same step
  entered the winner through the pair tournament (+0.88% as well), on a clear CI and no 1% bar (open item 10);
  here the pair's CI [8.160, 8.195] overlapped the winner's [8.034, 8.177].
- **PGO builds differed on every rep** (`8b3db339`, `36c63ab8`, `c38f1a70`; 7.89-7.97), as expected on SPEC
  (CLAUDE.md, 2026-10-28).
- **Package power stayed near 28 W**, against 85 W on the rate mines and the other two intspeed mines. The run is
  unpinned and `speccmds.cmd` passes `-j 32` to all 16 encodes, so this isn't the placement bug `821.gcc_s` and
  `800.pot3d_s` once hit; flac's threading evidently doesn't load the whole chip (niwot read 21-23 W). The CPU ran
  cooler accordingly (80-88°C, against 89-97°C on the five int mines before it).
- **The bandwidth gate waited before 23 of 38 timed runs**, about 11.5 minutes in all. Apart from the vector-width
  rep, no rep was slow.
