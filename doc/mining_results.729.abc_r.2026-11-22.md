# `cfm mine` results: 729.abc_r on `chicago`, 2026-11-22

This is the ninth intrate benchmark mined on `chicago` (see [`host_chicago.md`](host_chicago.md)). `729.abc_r` is
ABC, a logic synthesis and verification system (C), and this is its first mine on this machine. niwot's mine
accepted nothing, but its shape filter had excluded `-flto` and skipped PGO. A hand-measured follow-up there found
`-O3 -flto` at +2.49% (+3.10% against its own control) and PGO at -8.8% on top of LTO
([write-up](mining_results.729.abc_r.2026-10-17.md#follow-up-lto-and-pgo-2026-10-21)). Its corpus shape is
memory-bound at 38.2%, under the 55% gate, so only `-mprefer-vector-width=256` was excluded (on
`vectorization_density=low`).

## Headline result

**`-O3 -flto`, +2.26% over plain `-O3`** (ratio 59.809 → 61.162).

| Step | Mean | Gain on the step before |
|---|---|---|
| `-O3` | 59.809 | — |
| `-O3 -flto` | 61.162 | +2.26% |

- **This mine reproduces niwot's hand-measured answer**: `-flto` +2.26% here against +2.49% there, and PGO on top
  of LTO -8.59% here against -8.77% there. The mine now gets this on its own, since `-flto` is exempt from the
  shape filter and PGO is always tried.
- **PGO lost 8.59%**, the largest PGO loss in this intrate run (stockfish's -1.14% was the only other reject). The near-miss
  variant with `-fprefetch-loop-arrays` lost the same (-8.50%). niwot's `-fprofile-partial-training` check
  recovered about 60% of the loss but still lost 3.5%, so the training workload's hot paths seem to differ from
  the reference run's on abc.
- **Three flags were accepted alone but added nothing on top of `-flto`**: `-fgraphite-identity` (+1.43% alone,
  -0.12% on top), `-U_FORTIFY_SOURCE` (+1.01% alone, 0.00% on top), and the two together read only +0.41%.
- **Non-PIE was flat (+0.28%)**, as on cppcheck. Non-PIE is in five of the nine intrate winning sets here.
- **`-march=native` read +0.80%**, CI-clear but under the 1% bar, after being fast-tracked on 19 accepts of 28 in
  the memory-bound cluster. On top of `-flto`, `-march=znver5` read -0.24% and `-mtune=znver5` -1.16%.

## Run metadata

| | |
|---|---|
| Host | `chicago`: AMD Ryzen AI MAX+ 395 (16 Zen5 cores, 32 threads), 91 GB RAM, power profile `performance`, kernel 7.0.0-43 |
| Command | `python3 -m cfm.cli mine 729.abc_r` (uncapped, defaults; started by `~/cfm-logs/queue/run_queue.sh`) |
| Code | `main` at `03e712c` (no code changes since `3b15833`, PR #72) |
| SPEC config | `gcc_O3.cfg`, `copies = 32` |
| Experiment id | 37 |
| Started / finished | 2026-11-22T05:33:38Z / 2026-11-22T14:17:59Z (8h44m) |
| Final status | `converged` |
| Trials | 92 (1917-2008), none skipped, no reruns |
| Candidates screened / confirmed | 14 / 14 (plus `-march=native` fast-tracked) |
| Excluded on shape (Phase 2) | `-mprefer-vector-width=256` (`vectorization_density=low`); none on `resource_dominance` (38.2% is under the gate) |
| Fast-tracked (M4) | `-march=native` (accepted 19 of 28, mean +15.82%) |
| Accepted in Phase 4 | `-flto` +2.26%, `-fgraphite-identity` +1.43%, `-U_FORTIFY_SOURCE` +1.01% |
| Winning flags | `["-O3", "-flto"]`, +2.26% |
| Guards | throttle stop not triggered; bandwidth gate waited 30 s before 5 of 92 timed runs; no reruns; baseline recheck not flagged (-0.27%) |
| Power | package power median 84.98-85.00 W on every trial; CPU temperature 90.1-94.9°C |

A trial took about 5 minutes, an LTO trial about 6.5, and a PGO trial about 10.5.

## Baseline

Shape from the reference-matrix corpus (`amd-370-64gb`): memory-bound 38.2% (low confidence; frontend-bound close
behind on niwot's read), `vectorization_density=low`, `allocation_pressure=moderate`.

| Trial | Role | Ratio |
|---|---|---|
| 1917 | warm-up | 60.003 |
| 1918 | warm-up | 59.758 |
| 1919 | calibration | 59.806 |
| 1920 | calibration | 59.816 |
| 1921 | calibration | 59.803 |
| 1981 | recheck | 59.648 (-0.27%) |

The calibration mean is 59.809, with a 95% CI of [59.792, 59.826] (±0.03%), the tightest of the nine intrate mines
here. Warm-up settled after the minimum two reps (623 s). Every `-O3` build had the same code fingerprint
(`6a928fcb`).

## Trials

| Trials | Phase | Flags (on `-O3`) | Mean ratio | Delta | Verdict |
|---|---|---|---|---|---|
| 1922-1935 | screening | 14 candidates | 59.59-61.23 | | all survived |
| 1936-1938 | confirmation | `-fprefetch-loop-arrays` | 60.384 | +0.96% | reject (CI-clear, under the 1% bar) |
| 1939-1941 | confirmation | `-fgraphite-identity` | 60.667 | +1.43% | **accept** |
| 1942-1944 | confirmation | `-flto` | 61.162 | +2.26% | **accept** (the greedy start) |
| 1945-1947 | confirmation | `-fno-pie -no-pie` | 59.973 | +0.28% | reject |
| 1948-1950 | confirmation | `-fno-stack-protector` | 59.889 | +0.13% | reject (CI-clear, under the 1% bar) |
| 1951-1953 | confirmation | `-fcf-protection=none` | 59.823 | +0.02% | reject |
| 1954-1956 | confirmation | `-U_FORTIFY_SOURCE` | 60.411 | +1.01% | **accept** |
| 1957-1959 | confirmation | `-funroll-loops` | 59.805 | -0.01% | reject |
| 1960-1962 | confirmation | `-Ofast` | 59.806 | 0.00% | reject |
| 1963-1965 | confirmation | `-ffast-math` | 59.876 | +0.11% | reject |
| 1966-1968 | confirmation | `-fno-math-errno` | 59.723 | -0.14% | reject |
| 1969-1971 | confirmation | `-fno-ipa-cp-clone` | 59.861 | +0.09% | reject |
| 1972-1974 | confirmation | `-fno-unswitch-loops` | 59.776 | -0.05% | reject |
| 1975-1977 | confirmation | `-fipa-pta` | 59.870 | +0.10% | reject |
| 1978-1980 | confirmation (fast-tracked) | `-march=native` | 60.290 | +0.80% | reject (CI-clear, under the 1% bar) |
| 1981 | baseline recheck | `-O3` | 59.648 | -0.27% | not flagged |
| 1982-1984 | combination (greedy) | `-flto -fgraphite-identity` | 61.089 | -0.12% | reject |
| 1985-1987 | combination (greedy) | `-flto -U_FORTIFY_SOURCE` | 61.161 | 0.00% | reject |
| 1988-1990 | combination (pair) | `-U_FORTIFY_SOURCE -fgraphite-identity` | 60.055 | +0.41% | reject (CI-clear, under the 1% bar) |
| 1991-1993 | combination (pair) | `-U_FORTIFY_SOURCE -flto` | 61.072 | +2.11% | accept, same code as the greedy step, not enough to replace the winner |
| 1994-1996 | combination (pair) | `-fgraphite-identity -flto` | 61.113 | +2.18% | accept, same code as the greedy step, not enough to replace the winner |
| 1997-1999 | PGO | winner `+ -fprofile-use` | 55.906 | -8.59% | reject (CI-clear, below) |
| 2000-2002 | PGO (near-miss variant) | winner `+ -fprefetch-loop-arrays -fprofile-use` | 55.962 | -8.50% | reject (CI-clear, below) |
| 2003-2005 | microarch | winner `+ -march=znver5` | 61.016 | -0.24% | reject |
| 2006-2008 | microarch | winner `+ -mtune=znver5` | 60.453 | -1.16% | reject (CI-clear, below) |

Phase 4 and pair deltas are against `-O3`, greedy-step deltas against `-O3 -flto`, and Phase 6 deltas against
`-O3 -flto`. The greedy walk started from the Phase 4 `-flto` result rather than re-measuring it. The PGO
near-miss list was `-fprefetch-loop-arrays`, `-march=native` and `-fno-stack-protector`; only the first was tried.
The vector-width multiplier had no candidate (the shape filter had excluded `256`).

## Observations

- **The 1% bar decided most verdicts here, not CI overlap.** With the baseline CI at ±0.03%, six flags were
  CI-clear of baseline, from `-fno-stack-protector`'s +0.13% (three reps at 59.885-59.893) up. `-U_FORTIFY_SOURCE`
  cleared the bar by 0.01 points. The recheck read 0.27% below the calibration mean, but the mean of all six `-O3`
  runs is 59.806, so the deltas stand. Against the recheck alone, `-fprefetch-loop-arrays` (+1.23%) and
  `-march=native` (+1.08%) would clear the bar too, but that is one rep.
- **PGO's loss is a consistent build, not a bad profile.** All three plain-PGO reps built identical code
  (`b8bee259`) and read 55.88-55.96; the near-miss variant's three reps were also identical (`ccbdfe1e`). So
  abc's training run is deterministic, as cppcheck's and omnetpp's are, and on abc it trains the wrong weights.
  `-fprofile-partial-training` isn't in the catalog, so the mine can't try niwot's partial fix.
- **`-U_FORTIFY_SOURCE` and `-fgraphite-identity` together lose most of each one's gain** (60.06, against 60.41 and
  60.67 alone), with a code fingerprint different from both. The run doesn't show why. On top of `-flto`, neither
  helps at all.
- **The pair tournament re-measured both greedy steps' code** (`3460b2da`: 61.07 against 61.16; `ad81a980`: 61.11
  against 61.09), six timed runs at about 6.5 minutes each (niwot opportunity #35).
- **Most flags were flat to within 0.15%**, and every flagset's three reps were within 0.4% of each other. Like
  gcc_r, abc is very repeatable on this host.
