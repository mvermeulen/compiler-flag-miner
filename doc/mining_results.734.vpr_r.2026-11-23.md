# `cfm mine` results: 734.vpr_r on `chicago`, 2026-11-23

This is the tenth intrate benchmark mined on `chicago` (see [`host_chicago.md`](host_chicago.md)). `734.vpr_r` is
VPR, an FPGA place-and-route tool (C). This machine's August mine accepted `-march=native` at +1.04%
([write-up](mining_results.734.vpr_r.2026-08-27.md)), and niwot's found `-O3 -march=native` at +1.31%
([write-up](mining_results.734.vpr_r.2026-10-20.md)). Both mines ran while the shape filter still excluded
`-flto` and PGO was skipped on memory-bound shapes. niwot's hand-measured follow-up then found
`-O3 -march=native -flto -fprofile-use` at +15.77%, the pipeline's biggest miss at the time. Its corpus shape is
memory-bound at 45.4%, under the 55% gate, so only `-mprefer-vector-width=256` was excluded.

## Headline result

**`-O3 -flto -fprofile-use`, +17.95% over plain `-O3`** (ratio 46.645 → 55.016).

| Step | Mean | Gain on the step before |
|---|---|---|
| `-O3` | 46.645 | — |
| `-O3 -flto` | 52.792 | **+13.18%** |
| `+ -fprofile-use` | 55.016 | +4.21% |

- **The mine now finds vpr's LTO and PGO on its own.** `-flto` gave +13.18% here against +11.35% in niwot's
  follow-up, and PGO +4.21% on top, against about +3% on top there. This is the case that motivated exempting
  `-flto` from the shape filter and always trying PGO (niwot opportunities #20, #25, #28).
- **`-march=native` read +0.77%**, CI-clear but under the 1% bar, after being fast-tracked on 19 accepts of 29.
  Both earlier mines accepted it at about +1%, so this is the same small effect, just under the bar. On top of
  PGO, `-march=znver5` read +0.15% and `-mtune=znver5` -0.20%. The winning set has no `-march=`, unlike niwot's.
- **Non-PIE (+1.35%) and `-ffast-math` (+1.02%) were accepted alone but not on top of `-flto`** (+0.83% and
  +0.40%, both CI overlap). Non-PIE is in five of the ten intrate winning sets here.
- **Four more flags were CI-clear but under the 1% bar**: `-fprefetch-loop-arrays` +0.92%, `-fno-stack-protector`
  +0.87%, `-fcf-protection=none` +0.79% and `-march=native` +0.77%. The PGO near-miss variant with
  `-fprefetch-loop-arrays` read the same as plain PGO (+4.22% against +4.21%).

## Run metadata

| | |
|---|---|
| Host | `chicago`: AMD Ryzen AI MAX+ 395 (16 Zen5 cores, 32 threads), 91 GB RAM, power profile `performance`, kernel 7.0.0-43 |
| Command | `python3 -m cfm.cli mine 734.vpr_r` (uncapped, defaults; started by `~/cfm-logs/queue/run_queue.sh`) |
| Code | `main` at `b4126e9` (no code changes since `3b15833`, PR #72) |
| SPEC config | `gcc_O3.cfg`, `copies = 32` |
| Experiment id | 38 |
| Started / finished | 2026-11-22T14:18:59Z / 2026-11-23T00:44:25Z (10h25m) |
| Final status | `converged` |
| Trials | 92 (2009-2100), none skipped, no reruns |
| Candidates screened / confirmed | 14 / 14 (plus `-march=native` fast-tracked) |
| Excluded on shape (Phase 2) | `-mprefer-vector-width=256`; none on `resource_dominance` (45.4% is under the gate) |
| Fast-tracked (M4) | `-march=native` (accepted 19 of 29, mean +15.30%) |
| Accepted in Phase 4 | `-flto` +13.18%, `-fno-pie -no-pie` +1.35%, `-ffast-math` +1.02% |
| Winning flags | `["-O3", "-flto", "-fprofile-use"]`, +17.95% |
| Guards | throttle stop not triggered; bandwidth gate waited 30 s before 3 of 92 timed runs; no reruns; baseline recheck not flagged (-0.01%) |
| Power | package power median 84.99-85.00 W on every trial; CPU temperature 90.9-96.5°C |

A trial took about 6 minutes, an LTO trial about 7, and a PGO trial about 10.

## Baseline

Shape from the reference-matrix corpus (`amd-370-64gb`): memory-bound 45.4%, `vectorization_density=moderate`,
`allocation_pressure=high`.

| Trial | Role | Ratio |
|---|---|---|
| 2009 | warm-up | 46.553 |
| 2010 | warm-up | 46.766 |
| 2011 | calibration | 46.668 |
| 2012 | calibration | 46.656 |
| 2013 | calibration | 46.611 |
| 2073 | recheck | 46.642 (-0.01%) |

The calibration mean is 46.645, with a 95% CI of [46.571, 46.719] (±0.16%). Warm-up settled after the minimum two
reps (790 s). Every `-O3` build had the same code fingerprint (`32d16cbc`).

## Trials

| Trials | Phase | Flags (on `-O3`) | Mean ratio | Delta | Verdict |
|---|---|---|---|---|---|
| 2014-2027 | screening | 14 candidates | 46.39-52.81 | | all survived |
| 2028-2030 | confirmation | `-fprefetch-loop-arrays` | 47.073 | +0.92% | reject (CI-clear, under the 1% bar) |
| 2031-2033 | confirmation | `-fgraphite-identity` | 46.554 | -0.20% | reject |
| 2034-2036 | confirmation | `-flto` | 52.792 | +13.18% | **accept** (the greedy start) |
| 2037-2039 | confirmation | `-fno-pie -no-pie` | 47.276 | +1.35% | **accept** |
| 2040-2042 | confirmation | `-fno-stack-protector` | 47.048 | +0.87% | reject (CI-clear, under the 1% bar) |
| 2043-2045 | confirmation | `-fcf-protection=none` | 47.015 | +0.79% | reject (CI-clear, under the 1% bar) |
| 2046-2048 | confirmation | `-U_FORTIFY_SOURCE` | 46.609 | -0.08% | reject |
| 2049-2051 | confirmation | `-funroll-loops` | 46.832 | +0.40% | reject |
| 2052-2054 | confirmation | `-Ofast` | 46.988 | +0.73% | reject (CI overlap) |
| 2055-2057 | confirmation | `-ffast-math` | 47.121 | +1.02% | **accept** |
| 2058-2060 | confirmation | `-fno-math-errno` | 46.611 | -0.07% | reject |
| 2061-2063 | confirmation | `-fno-ipa-cp-clone` | 46.490 | -0.33% | reject |
| 2064-2066 | confirmation | `-fno-unswitch-loops` | 46.659 | +0.03% | reject |
| 2067-2069 | confirmation | `-fipa-pta` | 46.638 | -0.01% | reject |
| 2070-2072 | confirmation (fast-tracked) | `-march=native` | 47.003 | +0.77% | reject (CI-clear, under the 1% bar) |
| 2073 | baseline recheck | `-O3` | 46.642 | -0.01% | not flagged |
| 2074-2076 | combination (greedy) | `-flto -fno-pie -no-pie` | 53.229 | +0.83% | reject (CI overlap) |
| 2077-2079 | combination (greedy) | `-flto -ffast-math` | 53.003 | +0.40% | reject (CI overlap) |
| 2080-2082 | combination (pair) | `-ffast-math -flto` | 53.023 | +13.67% | accept, same code as the greedy step, not enough to replace the winner |
| 2083-2085 | combination (pair) | `-ffast-math -fno-pie -no-pie` | 47.382 | +1.58% | accept, not enough to replace the winner |
| 2086-2088 | combination (pair) | `-flto -fno-pie -no-pie` | 53.036 | +13.70% | accept, same code as the greedy step, not enough to replace the winner |
| 2089-2091 | PGO | winner `+ -fprofile-use` | 55.016 | +4.21% | **accept** |
| 2092-2094 | PGO (near-miss variant) | winner `+ -fprefetch-loop-arrays -fprofile-use` | 55.018 | +4.22% | accept, CI overlaps plain PGO's |
| 2095-2097 | microarch | winner + PGO `+ -march=znver5` | 55.099 | +0.15% | reject |
| 2098-2100 | microarch | winner + PGO `+ -mtune=znver5` | 54.907 | -0.20% | reject |

Phase 4 and pair deltas are against `-O3`, greedy-step deltas against `-O3 -flto`, and Phase 6 deltas against the
set they were layered on. The greedy walk started from the Phase 4 `-flto` result rather than re-measuring it. The
PGO near-miss list was `-fprefetch-loop-arrays`, `-fno-stack-protector`, `-fcf-protection=none` and `-march=native`;
only the first was tried. The vector-width multiplier was skipped because the winning set has no `-march=`.

## Observations

- **Non-PIE on top of `-flto` was a narrow miss, measured six times.** Its code (`4a88f2f0`) read 53.23 as the
  greedy step and 53.04 as the pair, about 0.6-0.8% above `-flto`'s 52.79, and both times its CI overlapped. On
  omnetpp, non-PIE added +0.16% on top of LTO; on gcc it added +1.61%.
- **PGO's three reps built identical code** (`4ac36bfa`) and read 54.89-55.09, so vpr's training run looks
  deterministic, as abc's, cppcheck's and omnetpp's do. Unlike abc's, it trains useful weights.
- **The pair tournament re-measured both greedy steps' code** (`21d37511` and `4a88f2f0`), six timed runs at about
  7 minutes each (niwot opportunity #35).
- **niwot's winning set had `-march=native` in it; this one doesn't.** That's no disagreement: niwot's follow-up
  measured LTO and PGO on top of the mine's `-march=native` winner, and `-march=native` itself was worth about 1%
  on both hosts. Here it read +0.77% alone and `-march=znver5` +0.15% on top of PGO.
